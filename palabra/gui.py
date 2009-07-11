# This file is part of Palabra
#
# Copyright (C) 2009 Simeon Visser
#
# Palabra is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gtk
import os

import action
from clue import (
    ClueEditor,
)
from files import (
    import_puzzle,
    export_puzzle,
    export_template,
    export_to_png,
    export_to_txt,
    export_to_csv,
)
import grid
from grid import (
    Grid,
)
from newpuzzle import (
    NewWindow,
    SizeWindow,
)
import preferences
from preferences import (
    PreferencesWindow,
    write_config_file,
)
from properties import (
    PropertiesWindow,
)
from puzzle import (
    Puzzle,
    PuzzleManager,
)
import transform

STATUS_MENU = "STATUS_MENU"
STATUS_GRID = "STATUS_GRID"

PALABRA_VERSION = "0.1"

class Tool(gtk.HBox):
    def __init__(self, palabra_window, drawing_area, puzzle):
        gtk.HBox.__init__(self)
        self.palabra_window = palabra_window
        self.drawing_area = drawing_area
        self.puzzle = puzzle
        
        self.settings = {}
        self.settings["selection_x"] = -1
        self.settings["selection_y"] = -1
        self.settings["direction"] = "horizontal"
        self.settings["keep_horizontal_symmetry"] = False
        self.settings["keep_vertical_symmetry"] = False
        self.settings["keep_point_symmetry"] = False
        self.settings["keep_point_symmetry"] = True
        
        self.typing_direction = "horizontal"
        self.selected_x = -1
        self.selected_y = -1
        self.current_x = -1
        self.current_y = -1
        
        self.mouse_buttons_down = [False, False, False]
        
        self.drawing_area.set_flags(gtk.CAN_FOCUS)
        
        self.expose_event_id = \
            self.drawing_area.connect("expose_event", self.on_expose_event)
        self.button_press_event_id = \
            self.drawing_area.connect("button_press_event", self.on_button_press_event)
        self.button_release_event_id = \
            self.drawing_area.connect("button_release_event", self.on_button_release_event)
        self.motion_notify_event_id = \
            self.drawing_area.connect("motion_notify_event", self.on_motion_notify_event)
        self.key_press_event_id = \
            self.drawing_area.connect("key_press_event", self.on_key_press_event)
        self.key_release_event_id = \
            self.drawing_area.connect("key_release_event", self.on_key_release_event)
            
        self.palabra_window.update_status(STATUS_GRID, self.puzzle.grid.determine_status_message())
                
    def cleanup(self):
        self.drawing_area.unset_flags(gtk.CAN_FOCUS)
        self.drawing_area.disconnect(self.expose_event_id)
        self.drawing_area.disconnect(self.button_press_event_id)
        self.drawing_area.disconnect(self.button_release_event_id)
        self.drawing_area.disconnect(self.motion_notify_event_id)
        self.drawing_area.disconnect(self.key_press_event_id)
        self.drawing_area.disconnect(self.key_release_event_id)
        
    def get_selection(self):
        return (self.settings["selection_x"], self.settings["selection_y"])
        
    def set_selection(self, x, y):
        self.settings["selection_x"] = x
        self.settings["selection_y"] = y
        valid = self.puzzle.grid.is_valid(x, y)
        self.palabra_window.update_selection_based_tools(valid)

    def on_expose_event(self, drawing_area, event):
        context = drawing_area.window.cairo_create()
        
        self.puzzle.view.draw_background(context)
        
        line_red = 1.0
        line_green = 1.0
        line_blue = 0.75
        
        primary_selection_red = preferences.prefs["color_primary_selection_red"] / 65535.0
        primary_selection_green = preferences.prefs["color_primary_selection_green"] / 65535.0
        primary_selection_blue = preferences.prefs["color_primary_selection_blue"] / 65535.0
        
        #secondary_selection_red = preferences.prefs["color_secondary_selection_red"] / 65535.0
        #secondary_selection_green = preferences.prefs["color_secondary_selection_green"] / 65535.0
        #secondary_selection_blue = preferences.prefs["color_secondary_selection_blue"] / 65535.0
        
        current_word_red = preferences.prefs["color_current_word_red"] / 65535.0
        current_word_green = preferences.prefs["color_current_word_green"] / 65535.0
        current_word_blue = preferences.prefs["color_current_word_blue"] / 65535.0
        
        primary_active_red = preferences.prefs["color_primary_active_red"] / 65535.0
        primary_active_green = preferences.prefs["color_primary_active_green"] / 65535.0
        primary_active_blue = preferences.prefs["color_primary_active_blue"] / 65535.0
        
        secondary_active_red = preferences.prefs["color_secondary_active_red"] / 65535.0
        secondary_active_green = preferences.prefs["color_secondary_active_green"] / 65535.0
        secondary_active_blue = preferences.prefs["color_secondary_active_blue"] / 65535.0
        
        x = self.settings["selection_x"]
        y = self.settings["selection_y"]
        if self.puzzle.grid.is_valid(x, y):
            if not self.puzzle.grid.is_block(x, y):
                if self.settings["direction"] == "horizontal":
                    r = current_word_red
                    g = current_word_green
                    b = current_word_blue
                    self.puzzle.view.draw_horizontal_line(context, x, y, r, g, b)
                elif self.settings["direction"] == "vertical":
                    r = current_word_red
                    g = current_word_green
                    b = current_word_blue
                    self.puzzle.view.draw_vertical_line(context, x, y, r, g, b)
                
            r = primary_selection_red
            g = primary_selection_green
            b = primary_selection_blue
            self.puzzle.view.draw_location(context, x, y, r, g, b)
        
        if self.current_x >= 0 and self.current_y >= 0:
            if self.settings["keep_horizontal_symmetry"]:
                self.puzzle.view.draw_location(context \
                , self.current_x, (self.puzzle.grid.height - 1) - self.current_y \
                , secondary_active_red, secondary_active_green, secondary_active_blue)
            if self.settings["keep_vertical_symmetry"]:
                self.puzzle.view.draw_location(context \
                , (self.puzzle.grid.width - 1) - self.current_x, self.current_y \
                , secondary_active_red, secondary_active_green, secondary_active_blue)
            if (self.settings["keep_horizontal_symmetry"] and self.settings["keep_vertical_symmetry"]) \
                or self.settings["keep_point_symmetry"]:
                self.puzzle.view.draw_location(context \
                , (self.puzzle.grid.width - 1) - self.current_x
                , (self.puzzle.grid.height - 1) - self.current_y
                , secondary_active_red, secondary_active_green, secondary_active_blue)
                
            # draw current cell last to prevent
            # symmetrical cells from overlapping it
            self.puzzle.view.draw_location(context \
                , self.current_x, self.current_y \
                , primary_active_red, primary_active_green, primary_active_blue)
        
        self.puzzle.view.update_view(context)
        
        return True
        
    def on_button_press_event(self, drawing_area, event):
        #if event.button == 3 and not (event.state & gtk.gdk.SHIFT_MASK) and \
        #    (self.current_x >= 0 and self.current_y >= 0):
        #    menu = self.create_popup_menu()
        #   menu.show_all()
        #    menu.popup(None, None, None, event.button, event.time)
        #    return True
            
        if 1 <= event.button <= 3:
            self.mouse_buttons_down[event.button - 1] = True

        drawing_area.grab_focus()
        
        prev_x = self.settings["selection_x"]
        prev_y = self.settings["selection_y"]
        
        current_x = self.puzzle.view.screen_to_grid_x(event.x)
        current_y = self.puzzle.view.screen_to_grid_y(event.y)
        
        if not self.puzzle.grid.is_valid(self.current_x, self.current_y):
            self.set_selection(-1, -1)
            
        if event.button == 1 and not (event.state & gtk.gdk.SHIFT_MASK):
            if self.puzzle.grid.is_valid(self.current_x, self.current_y):
                self.set_selection(current_x, current_y)
        
        if (event.state & gtk.gdk.SHIFT_MASK):
            if self.puzzle.grid.is_valid(self.current_x, self.current_y):
                if event.button == 1:
                    self.transform_blocks(current_x, current_y, True)
                elif event.button == 3:
                    self.transform_blocks(current_x, current_y, False)
        
        if self.settings["direction"] == "horizontal":
            self.puzzle.view.update_horizontal_line(drawing_area, prev_y)
        elif self.settings["direction"] == "vertical":
            self.puzzle.view.update_vertical_line(drawing_area, prev_x)
            
        if (event.button == 1 and not (event.state & gtk.gdk.SHIFT_MASK)
            and prev_x == current_x
            and prev_y == current_y
            and event.type == gtk.gdk.BUTTON_PRESS):
            if self.settings["direction"] == "horizontal":
                self.settings["direction"] = "vertical"
            elif self.settings["direction"] == "vertical":
                self.settings["direction"] = "horizontal"
        
        if self.settings["direction"] == "horizontal":
            self.puzzle.view.update_horizontal_line(drawing_area
                , self.settings["selection_y"])
        elif self.settings["direction"] == "vertical":
            self.puzzle.view.update_vertical_line(drawing_area
                , self.settings["selection_x"])
        
        return True
        
    def on_button_release_event(self, drawing_area, event):
        if 1 <= event.button <= 3:
            self.mouse_buttons_down[event.button - 1] = False
        return True
        
    def on_motion_notify_event(self, drawing_area, event):
        tmp_x = self.current_x
        tmp_y = self.current_y
        
        self.puzzle.view.update_horizontal_line(drawing_area, tmp_y)
        self.puzzle.view.update_vertical_line(drawing_area, tmp_x)
        
        self.update_symmetry(drawing_area, tmp_x, tmp_y)
        
        self.current_x = self.puzzle.view.screen_to_grid_x(event.x)
        self.current_y = self.puzzle.view.screen_to_grid_y(event.y)
        
        if tmp_x != self.current_x or tmp_y != self.current_y:
            self.puzzle.view.update_location(drawing_area, self.current_x, self.current_y)
        
        if self.puzzle.grid.is_valid(self.current_x, self.current_y):
            if self.mouse_buttons_down[0] and (event.state & gtk.gdk.SHIFT_MASK):
                self.transform_blocks(self.current_x, self.current_y, True)
            elif self.mouse_buttons_down[2] and (event.state & gtk.gdk.SHIFT_MASK):
                self.transform_blocks(self.current_x, self.current_y, False)
            else:
                if tmp_x != self.current_x or tmp_y != self.current_y:
                    self.puzzle.view.update_location(drawing_area, self.current_x, self.current_y)
                    
                    self.update_symmetry(drawing_area, self.current_x, self.current_y)    
        
        return True
        
    def set_symmetry(self, options):
        self.settings["keep_horizontal_symmetry"] = False
        self.settings["keep_vertical_symmetry"] = False
        self.settings["keep_point_symmetry"] = False
        
        symmetries = \
            ["keep_horizontal_symmetry"
            ,"keep_vertical_symmetry"
            ,"keep_point_symmetry"
            ]
        for key in symmetries:
            self.settings[key] = key in options
        
    def update_symmetry(self, drawing_area, main_x, main_y):
        if self.settings["keep_horizontal_symmetry"]:
            x = main_x
            y = (self.puzzle.grid.height - 1) - main_y
            self.puzzle.view.update_location(drawing_area, x, y)
        if self.settings["keep_vertical_symmetry"]:
            x = (self.puzzle.grid.width - 1) - main_x
            y = main_y
            self.puzzle.view.update_location(drawing_area, x, y)
        if (self.settings["keep_horizontal_symmetry"] and \
            self.settings["keep_vertical_symmetry"]) or \
            self.settings["keep_point_symmetry"]:
            x = (self.puzzle.grid.width - 1) - main_x
            y = (self.puzzle.grid.height - 1) - main_y
            self.puzzle.view.update_location(drawing_area, x, y)

    def transform_blocks(self, x, y, status):
        blocks = []
        if status != self.puzzle.grid.is_block(x, y):
            blocks.append((x, y, status))
        if self.settings["keep_horizontal_symmetry"]:
            p = x
            q = self.puzzle.grid.height - 1 - y
            if status != self.puzzle.grid.is_block(p, q):
                blocks.append((p, q, status))
        if self.settings["keep_vertical_symmetry"]:
            p = self.puzzle.grid.width - 1 - x
            q = y
            if status != self.puzzle.grid.is_block(p, q):
                blocks.append((p, q, status))
        if (self.settings["keep_horizontal_symmetry"] and \
            self.settings["keep_vertical_symmetry"]) or \
            self.settings["keep_point_symmetry"]:
            p = self.puzzle.grid.width - 1 - x
            q = self.puzzle.grid.height - 1 - y
            if status != self.puzzle.grid.is_block(p, q):
                blocks.append((p, q, status))
        if len(blocks) > 0:
            self.palabra_window.transform_grid(transform.modify_blocks, blocks=blocks)
            sel_x = self.settings["selection_x"]
            sel_y = self.settings["selection_y"]
            if (sel_x, sel_y, True) in blocks:
                self.set_selection(-1, -1)

    def on_key_press_event(self, drawing_area, event):
        return True
        
    def on_key_release_event(self, drawing_area, event):
        # prevent conflicts with menu shortcut keys
        if (event.state & gtk.gdk.SHIFT_MASK) or \
            (event.state & gtk.gdk.CONTROL_MASK):
            return True
            
        if event.keyval == gtk.keysyms.BackSpace:
            current_char = self.puzzle.grid.get_char(self.settings["selection_x"], self.settings["selection_y"])
            if current_char != '':
                self.palabra_window.transform_grid(transform.modify_char
                    , x=self.settings["selection_x"]
                    , y=self.settings["selection_y"]
                    , next_char='')
            else:
                if self.settings["direction"] == "horizontal":
                    x = self.settings["selection_x"] - 1
                    y = self.settings["selection_y"]
                    if self.puzzle.grid.is_valid(x, y) and not self.puzzle.grid.is_block(x, y):
                        
                        self.palabra_window.transform_grid(transform.modify_char
                            , x=x
                            , y=y
                            , next_char='')
                        
                        self.settings["selection_x"] -= 1
                elif self.settings["direction"] == "vertical":
                    x = self.settings["selection_x"]
                    y = self.settings["selection_y"] - 1
                    if self.puzzle.grid.is_valid(x, y) \
                        and not self.puzzle.grid.is_block(x, y):
                        
                        self.palabra_window.transform_grid(transform.modify_char
                            , x=x
                            , y=y
                            , next_char='')
                            
                        self.settings["selection_y"] -= 1
        elif event.keyval == gtk.keysyms.Tab:
            self.change_typing_direction()
        elif event.keyval == gtk.keysyms.Home:
            if self.settings["direction"] == "horizontal":
                for i in reversed(range(self.settings["selection_x"])):
                    if self.puzzle.grid.is_block(i, self.settings["selection_y"]):
                        self.settings["selection_x"] = i + 1
                        break
                else:
                    if not self.puzzle.grid.is_block(0, self.settings["selection_y"]):
                        self.settings["selection_x"] = 0
                self.puzzle.view.update_horizontal_line(drawing_area, self.settings["selection_y"])
            elif self.settings["direction"] == "vertical":
                for i in reversed(range(self.settings["selection_y"])):
                    if self.puzzle.grid.is_block(self.settings["selection_x"], i):
                        self.settings["selection_y"] = i + 1
                        break
                else:
                    if not self.puzzle.grid.is_block(self.settings["selection_x"], 0):
                        self.settings["selection_y"] = 0
                self.puzzle.view.update_vertical_line(drawing_area, self.settings["selection_x"])
        elif event.keyval == gtk.keysyms.Left:
            if self.puzzle.grid.is_available(self.settings["selection_x"] - 1, self.settings["selection_y"]):
                self.puzzle.view.update_vertical_line(drawing_area, self.settings["selection_x"])
                self.settings["selection_x"] -=1
                self.puzzle.view.update_vertical_line(drawing_area, self.settings["selection_x"])
        elif event.keyval == gtk.keysyms.Up:
            if self.puzzle.grid.is_available(self.settings["selection_x"], self.settings["selection_y"] - 1):
                self.puzzle.view.update_horizontal_line(drawing_area, self.settings["selection_y"])
                self.settings["selection_y"] -= 1
                self.puzzle.view.update_horizontal_line(drawing_area, self.settings["selection_y"])
        elif event.keyval == gtk.keysyms.Right:
            if self.puzzle.grid.is_available(self.settings["selection_x"] + 1, self.settings["selection_y"]):
                self.puzzle.view.update_vertical_line(drawing_area, self.settings["selection_x"])
                self.settings["selection_x"] += 1
                self.puzzle.view.update_vertical_line(drawing_area, self.settings["selection_x"])
        elif event.keyval == gtk.keysyms.Down:
            if self.puzzle.grid.is_available(self.settings["selection_x"], self.settings["selection_y"] + 1):
                self.puzzle.view.update_horizontal_line(drawing_area, self.settings["selection_y"])
                self.settings["selection_y"] += 1
                self.puzzle.view.update_horizontal_line(drawing_area, self.settings["selection_y"])
        elif event.keyval == gtk.keysyms.End:
            if self.settings["direction"] == "horizontal":
                for i in range(self.settings["selection_x"], self.puzzle.grid.width):
                    if self.puzzle.grid.is_block(i, self.settings["selection_y"]):
                        self.settings["selection_x"] = i - 1
                        break
                else:
                    if not self.puzzle.grid.is_block(self.puzzle.grid.width - 1, self.settings["selection_y"]):
                        self.settings["selection_x"] = self.puzzle.grid.width - 1
                self.puzzle.view.update_horizontal_line(drawing_area, self.settings["selection_y"])
            elif self.settings["direction"] == "vertical":
                for i in range(self.settings["selection_y"], self.puzzle.grid.height):
                    if self.puzzle.grid.is_block(self.settings["selection_x"], i):
                        self.settings["selection_y"] = i - 1
                        break
                else:
                    if not self.puzzle.grid.is_block(self.settings["selection_x"], self.puzzle.grid.height - 1):
                        self.settings["selection_y"] = self.puzzle.grid.height - 1
                self.puzzle.view.update_vertical_line(drawing_area, self.settings["selection_x"])
        elif event.keyval == gtk.keysyms.Delete:
            self.puzzle.grid.clear_char(self.settings["selection_x"], self.settings["selection_y"])
            self.puzzle.view.update_location(drawing_area, self.settings["selection_x"], self.settings["selection_y"])
        else:
            if gtk.keysyms.a <= event.keyval <= gtk.keysyms.z:
                if self.puzzle.grid.is_valid(self.settings["selection_x"], self.settings["selection_y"]):
                    c = chr(event.keyval).capitalize()
                    
                    self.palabra_window.transform_grid(transform.modify_char
                            , x=self.settings["selection_x"]
                            , y=self.settings["selection_y"]
                            , next_char=c)
                    if self.settings["direction"] == "horizontal":
                        if self.puzzle.grid.is_available(self.settings["selection_x"] + 1, self.settings["selection_y"]):
                            self.settings["selection_x"] += 1
                        self.puzzle.view.update_horizontal_line(drawing_area, self.settings["selection_y"])
                    elif self.settings["direction"] == "vertical":
                        if self.puzzle.grid.is_available(self.settings["selection_x"], self.settings["selection_y"] + 1):
                            self.settings["selection_y"] += 1
                        self.puzzle.view.update_vertical_line(drawing_area, self.settings["selection_x"])
        return True
        
    def change_typing_direction(self):
        if self.settings["direction"] == "horizontal":
            self.settings["direction"] = "vertical"
        elif self.settings["direction"] == "vertical":
            self.settings["direction"] = "horizontal"
            
        self.drawing_area.queue_draw()

class PalabraWindow(gtk.Window):
    def __init__(self):
        super(PalabraWindow, self).__init__()
        self.reset_title()
        self.set_size_request(800, 600)
        
        self.puzzle_toggle_items = []
        self.selection_toggle_items = []
        
        self.puzzle_manager = PuzzleManager()
        
        self.menubar = gtk.MenuBar()
        self.menubar.append(self.create_file_menu())
        self.menubar.append(self.create_edit_menu())
        self.menubar.append(self.create_view_menu())
        self.menubar.append(self.create_help_menu())
        
        self.toolbar = self.create_toolbar()
        
        self.panel = gtk.VBox(False, 0)
        
        self.statusbar = gtk.Statusbar()
        
        self.main = gtk.VBox(False, 0)
        self.main.pack_start(self.menubar, False, False, 0)
        self.main.pack_start(self.toolbar, False, False, 0)
        self.main.pack_start(self.panel, True, True, 0)
        self.main.pack_start(self.statusbar, False, False, 0)
        
        self.add(self.main)
        
        self.connect("destroy", lambda widget: quit())
        
    def to_empty_panel(self):
        for widget in self.panel.get_children():
            self.panel.remove(widget)
        self.tool.cleanup()
    
    def to_edit_panel(self):
        drawing_area = gtk.DrawingArea()
        drawing_area.add_events(
            gtk.gdk.BUTTON_PRESS_MASK
            | gtk.gdk.BUTTON_RELEASE_MASK
            | gtk.gdk.POINTER_MOTION_MASK
            | gtk.gdk.KEY_PRESS_MASK
            | gtk.gdk.KEY_RELEASE_MASK
            )
        scrolled_window = gtk.ScrolledWindow(None, None)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add_with_viewport(drawing_area)
        
        self.puzzle_manager.current_puzzle.view.update_visual_size(drawing_area)
        drawing_area.queue_draw()
        
        self.tool = Tool(self, drawing_area, self.puzzle_manager.current_puzzle)
        
        options_hbox = gtk.HBox(False, 0)
        options_hbox.set_border_width(12)
        options_hbox.set_spacing(18)
        
        options_vbox = gtk.VBox(False, 0)
        options_vbox.set_spacing(15)
        options_hbox.pack_start(options_vbox, True, True, 0)
        
        options = gtk.VBox(False, 0)
        options_vbox.pack_start(options, True, True, 0)
        
        combo_symmetry = gtk.combo_box_new_text()
        combo_symmetry.append_text("None")
        combo_symmetry.append_text("Horizontal axis")
        combo_symmetry.append_text("Vertical axis")
        combo_symmetry.append_text("Both axes")
        combo_symmetry.append_text("Point symmetry")
        combo_symmetry.connect("changed", self.on_combo_symmetry_changed)
        combo_symmetry.set_active(4)
        
        label = gtk.Label()
        label.set_alignment(0, 0)
        label.set_markup("<b>Symmetry mode</b>")
        options.pack_start(label, False, False, 6)
        align = gtk.Alignment(0, 0)
        align.set_padding(0, 0, 12, 0)
        align.add(combo_symmetry)
        options.pack_start(align, False, False, 0)
        
        edit_clues_button = gtk.Button("Edit clues")
        edit_clues_button.connect("clicked", lambda button: self.edit_clues())
        
        label = gtk.Label()
        label.set_alignment(0, 0)
        label.set_markup("<b>Clues</b>")
        options.pack_start(label, False, False, 6)
        align = gtk.Alignment(0, 0)
        align.set_padding(0, 0, 12, 0)
        align.add(edit_clues_button)
        options.pack_start(align, False, False, 0)
        
        scrolled_options = gtk.ScrolledWindow(None, None)
        scrolled_options.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scrolled_options.add_with_viewport(options_hbox)
        
        main = gtk.HBox(False, 0)
        main.pack_start(scrolled_window, True, True, 0)
        main.pack_start(scrolled_options, False, False, 0)
        
        all_vbox = gtk.VBox(False, 0)
        all_vbox.pack_start(main, True, True, 0)
        self.panel.pack_start(all_vbox, True, True, 0)
        self.panel.show_all()
        
    def on_combo_symmetry_changed(self, combo):
        options = []
        
        if combo.get_active() == 0:
            pass
        elif combo.get_active() == 1:
            options.append("keep_horizontal_symmetry")
        elif combo.get_active() == 2:
            options.append("keep_vertical_symmetry")
        elif combo.get_active() == 3:
            options.append("keep_horizontal_symmetry")
            options.append("keep_vertical_symmetry")
        elif combo.get_active() == 4:
            options.append("keep_point_symmetry")
        self.tool.set_symmetry(options)
        
    def get_selection(self):
        try:
            return self.tool.get_selection()
        except AttributeError:
            return None
        
    def update_status(self, context_string, message):
        context_id = self.statusbar.get_context_id(context_string)
        self.statusbar.pop(context_id)
        self.statusbar.push(context_id, message)

    def pop_status(self, context_string):
        context_id = self.statusbar.get_context_id(context_string)
        self.statusbar.pop(context_id)
        return context_id
        
    def new_puzzle(self):
        self.close_puzzle()
        if not self.puzzle_manager.has_puzzle():
            window = NewWindow(self)
            window.show_all()
            
            response = window.run()
            if response == gtk.RESPONSE_ACCEPT:
                self.update_title(None)
                configuration = window.get_configuration()
                self.puzzle_manager.new_puzzle(configuration)
                
                self.load_puzzle()
            window.destroy()
    
    def open_puzzle(self):
        self.close_puzzle()
        if not self.puzzle_manager.has_puzzle():
            dialog = gtk.FileChooserDialog("Open Puzzle"
                , self
                , gtk.FILE_CHOOSER_ACTION_OPEN
                , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
                , gtk.STOCK_OPEN, gtk.RESPONSE_OK))
            filter = gtk.FileFilter()
            filter.set_name("Palabra puzzle files (*.xml)")
            filter.add_pattern("*.xml")
            dialog.add_filter(filter)
            
            filter = gtk.FileFilter()
            filter.set_name("All files")
            filter.add_pattern("*")
            dialog.add_filter(filter)
            
            dialog.show_all()
            response = dialog.run()
            if response == gtk.RESPONSE_OK:
                dialog.hide()

                filename = dialog.get_filename()
                puzzle = import_puzzle(filename)
                if puzzle is None:
                    message = "This file does not appear to be a valid Palabra puzzle file."
                    mdialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL
                        , gtk.MESSAGE_INFO, gtk.BUTTONS_NONE, message)
                    mdialog.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
                    mdialog.run()
                    mdialog.destroy()
                else:
                    puzzle.filename = filename
                    self.update_title(filename)
                    
                    self.puzzle_manager.current_puzzle = puzzle
                    self.load_puzzle()
            dialog.destroy()
            
    def reset_title(self):
        self.set_title("Palabra")
            
    def update_title(self, path=None):
        title = "Unsaved puzzle - Palabra"
        if path is not None:
            filename_start = path.rfind(os.sep) + 1
            filename = path[filename_start:]
            title = ''.join([filename, " - Palabra"])
        self.set_title(title)
    
    def save_puzzle(self, save_as=False):
        if save_as or self.puzzle_manager.current_puzzle.filename is None:
            dialog = gtk.FileChooserDialog("Save Puzzle"
                , self
                , gtk.FILE_CHOOSER_ACTION_SAVE
                , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
                , gtk.STOCK_SAVE, gtk.RESPONSE_OK))
            dialog.set_do_overwrite_confirmation(True)
            filter = gtk.FileFilter()
            filter.set_name("Palabra puzzle files (*.xml)")
            filter.add_pattern("*.xml")
            dialog.add_filter(filter)
            
            dialog.show_all()
            response = dialog.run()
            if response == gtk.RESPONSE_OK:
                filename = dialog.get_filename()
                self.puzzle_manager.current_puzzle.filename = filename
                export_puzzle(self.puzzle_manager.current_puzzle)
                self.update_title(self.puzzle_manager.current_puzzle.filename)
            dialog.destroy()
        else:
            export_puzzle(self.puzzle_manager.current_puzzle)
        action.stack.distance_from_saved_puzzle = 0
    
    def export_as_template(self):
        dialog = gtk.FileChooserDialog("Export as template"
            , self
            , gtk.FILE_CHOOSER_ACTION_SAVE
            , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
            , gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        dialog.set_do_overwrite_confirmation(True)
        filter = gtk.FileFilter()
        filter.set_name("Palabra template files (*.xml)")
        filter.add_pattern("*.xml")
        dialog.add_filter(filter)
        
        dialog.show_all()
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            grid = self.puzzle_manager.current_puzzle.grid
            filename = dialog.get_filename()
            export_template(grid, filename)
        dialog.destroy()
    
    def load_puzzle(self):
        self.to_edit_panel()

        for item in self.puzzle_toggle_items:
            item.set_sensitive(True)
    
    def close_puzzle(self):
        need_to_close, need_to_save = self.check_close_puzzle()
        if need_to_close:
            if need_to_save:
                self.save_puzzle(False)
            
            self.puzzle_manager.current_puzzle = None
            
            self.reset_title()
            self.to_empty_panel()
            self.pop_status(STATUS_GRID)
            
            for item in self.puzzle_toggle_items:
                item.set_sensitive(False)
                
            action.stack.clear()
            self.update_undo_redo()
            self.update_selection_based_tools(False)

    def check_close_puzzle(self):
        if not self.puzzle_manager.has_puzzle():
            return False, False

        need_to_close = True
        need_to_save = False
        if action.stack.distance_from_saved_puzzle != 0:
            image = gtk.Image()
            image.set_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG)
            dialog = gtk.Dialog("Close puzzle" \
                , self
                , gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_MODAL
                , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
                , gtk.STOCK_NO, gtk.RESPONSE_NO
                , gtk.STOCK_YES, gtk.RESPONSE_YES))
            dialog.set_default_response(gtk.RESPONSE_CLOSE)
            dialog.set_title("Close without saving")

            label = gtk.Label("Save the changes to the current puzzle before closing?")
            hbox = gtk.HBox(False, 0)
            hbox.pack_start(image, False, False, 0)
            hbox.pack_start(label, True, False, 10)
            dialog.vbox.pack_start(hbox, False, False, 10)
            dialog.set_resizable(False)
            dialog.set_modal(True)
            dialog.show_all()
            
            response = dialog.run()
            if response == gtk.RESPONSE_YES:
                need_to_close = True
                need_to_save = True
            elif response == gtk.RESPONSE_CANCEL:
                need_to_close = False
                need_to_save = False
            else:
                need_to_close = True
                need_to_save = False
            dialog.destroy()
        return need_to_close, need_to_save
            
    def export_to_png(self, mode):
        dialog = gtk.FileChooserDialog("Export to PNG"
            , self
            , gtk.FILE_CHOOSER_ACTION_SAVE
            , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
            , gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        dialog.set_do_overwrite_confirmation(True)
        dialog.show_all()
        
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            filename = dialog.get_filename()
            export_to_png(self.puzzle_manager.current_puzzle, filename, mode)
        dialog.destroy()
    
    def export_clues(self, export_title, export_function, **args):
        dialog = gtk.FileChooserDialog(export_title
            , self
            , gtk.FILE_CHOOSER_ACTION_SAVE
            , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
            , gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        dialog.set_do_overwrite_confirmation(True)
        dialog.show_all()
        
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            filename = dialog.get_filename()
            export_function(self.puzzle_manager.current_puzzle, filename, **args)
        dialog.destroy()
        
    def view_puzzle_properties(self):
        dialog = PropertiesWindow(self, self.puzzle_manager.current_puzzle)
        dialog.show_all()
        dialog.run()
        dialog.destroy()
        
    def create_toolbar(self):
        toolbar = gtk.Toolbar()
        toolbar.set_orientation(gtk.ORIENTATION_HORIZONTAL)
        
        item = gtk.ToolButton()
        item.set_stock_id(gtk.STOCK_NEW)
        item.connect("clicked", lambda item: self.new_puzzle())
        item.show()
        toolbar.insert(item, -1)
        
        item = gtk.ToolButton()
        item.set_stock_id(gtk.STOCK_OPEN)
        item.connect("clicked", lambda item: self.open_puzzle())
        item.show()
        toolbar.insert(item, -1)
        
        item = gtk.ToolButton()
        item.set_stock_id(gtk.STOCK_SAVE)
        item.connect("clicked", lambda item: self.save_puzzle(False))
        item.show()
        item.set_sensitive(False)
        toolbar.insert(item, -1)
        self.puzzle_toggle_items += [item]
        
        toolbar.insert(gtk.SeparatorToolItem(), -1)
        
        self.undo_tool_item = gtk.ToolButton()
        self.undo_tool_item.set_stock_id(gtk.STOCK_UNDO)
        self.undo_tool_item.connect("clicked", lambda item: self.undo_action())
        self.undo_tool_item.show()
        toolbar.insert(self.undo_tool_item, -1)
        self.undo_tool_item.set_sensitive(False)
        
        self.redo_tool_item = gtk.ToolButton()
        self.redo_tool_item.set_stock_id(gtk.STOCK_REDO)
        self.redo_tool_item.connect("clicked", lambda item: self.redo_action())
        self.redo_tool_item.show()
        toolbar.insert(self.redo_tool_item, -1)
        self.redo_tool_item.set_sensitive(False)
        
        toolbar.insert(gtk.SeparatorToolItem(), -1)
        
        item = gtk.ToolButton()
        item.set_stock_id(gtk.STOCK_PROPERTIES)
        item.connect("clicked", lambda item: self.view_puzzle_properties())
        item.show()
        item.set_sensitive(False)
        toolbar.insert(item, -1)
        self.puzzle_toggle_items += [item]
        
        return toolbar
    
    def create_file_menu(self):
        menu = gtk.Menu()
        
        accel_group = gtk.AccelGroup()
        self.add_accel_group(accel_group)
        
        activate = lambda item: self.new_puzzle()
        select = lambda item: self.update_status(STATUS_MENU
            , "Create a new puzzle")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.ImageMenuItem(gtk.STOCK_NEW, None)
        key, mod = gtk.accelerator_parse("<Ctrl>N")
        item.add_accelerator("activate", accel_group, key, mod, gtk.ACCEL_VISIBLE)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        menu.append(item)
        
        activate = lambda item: self.open_puzzle()
        select = lambda item: self.update_status(STATUS_MENU
            , "Open a puzzle")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.ImageMenuItem(gtk.STOCK_OPEN, None)
        key, mod = gtk.accelerator_parse("<Ctrl>O")
        item.add_accelerator("activate", accel_group, key, mod, gtk.ACCEL_VISIBLE)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        menu.append(item)
        
        menu.append(gtk.SeparatorMenuItem())
        
        activate = lambda item: self.save_puzzle(False)
        select = lambda item: self.update_status(STATUS_MENU
            , "Save the current puzzle")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.ImageMenuItem(gtk.STOCK_SAVE, None)
        key, mod = gtk.accelerator_parse("<Ctrl>S")
        item.add_accelerator("activate", accel_group, key, mod, gtk.ACCEL_VISIBLE)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        item.set_sensitive(False)
        menu.append(item)
        self.puzzle_toggle_items += [item]
        
        activate = lambda item: self.save_puzzle(True)
        select = lambda item: self.update_status(STATUS_MENU
            , "Save the current puzzle with a different name")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.ImageMenuItem(gtk.STOCK_SAVE_AS, None)
        key, mod = gtk.accelerator_parse("<Shift><Ctrl>S")
        item.add_accelerator("activate", accel_group, key, mod, gtk.ACCEL_VISIBLE)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        item.set_sensitive(False)
        menu.append(item)
        self.puzzle_toggle_items += [item]
        
        menu.append(gtk.SeparatorMenuItem())
        
        item = self.create_export_menu()
        item.set_sensitive(False)
        menu.append(item)
        self.puzzle_toggle_items += [item]
        
        activate = lambda item: self.export_as_template()
        select = lambda item: self.update_status(STATUS_MENU
            , "Save the grid as a template without the words and clues")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.MenuItem("Export as _template...", True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        item.set_sensitive(False)
        menu.append(item)
        self.puzzle_toggle_items += [item]
        
        menu.append(gtk.SeparatorMenuItem())
        
        activate = lambda item: self.view_puzzle_properties()
        select = lambda item: self.update_status(STATUS_MENU
            , "View the properties of the current puzzle")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.ImageMenuItem(gtk.STOCK_PROPERTIES, None)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        item.set_sensitive(False)
        menu.append(item)
        self.puzzle_toggle_items += [item]
        
        menu.append(gtk.SeparatorMenuItem())
        
        activate = lambda item: self.close_puzzle()
        select = lambda item: self.update_status(STATUS_MENU
            , "Close the current puzzle")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.ImageMenuItem(gtk.STOCK_CLOSE, None)
        key, mod = gtk.accelerator_parse("<Ctrl>W")
        item.add_accelerator("activate", accel_group, key, mod, gtk.ACCEL_VISIBLE)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        item.set_sensitive(False)
        menu.append(item)
        self.puzzle_toggle_items += [item]
        
        activate = lambda item: quit()
        select = lambda item: self.update_status(STATUS_MENU
            , "Quit the application")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.ImageMenuItem(gtk.STOCK_QUIT, None)
        key, mod = gtk.accelerator_parse("<Ctrl>Q")
        item.add_accelerator("activate", accel_group, key, mod, gtk.ACCEL_VISIBLE)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        menu.append(item)
        
        file_menu = gtk.MenuItem("_File", True)
        file_menu.set_submenu(menu)
        return file_menu
        
    def create_export_menu(self):
        menu = gtk.Menu()
        
        activate = lambda item: self.export_to_png(grid.VIEW_MODE_EMPTY);
        select = lambda item: self.update_status(STATUS_MENU
            , "Export the empty puzzle to PNG")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.MenuItem("_PNG (empty grid)", True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        menu.append(item)
        
        activate = lambda item: self.export_to_png(grid.VIEW_MODE_SOLUTION);
        select = lambda item: self.update_status(STATUS_MENU
            , "Export the solution of the puzzle to PNG")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.MenuItem("P_NG (solution)", True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        menu.append(item)
        
        menu.append(gtk.SeparatorMenuItem())
        
        activate = lambda item: self.export_clues("Export to TXT", export_to_txt);
        select = lambda item: self.update_status(STATUS_MENU
            , "Export the clues of the puzzle to a text file")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.MenuItem("_TXT (clues, tab delimited)", True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        menu.append(item)
        
        activate = lambda item: self.export_clues("Export to CSV"
            , export_to_csv, options={"separator": ","});
        select = lambda item: self.update_status(STATUS_MENU
            , "Export the clues of the puzzle to a comma-separated values file")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.MenuItem("_CSV (clues, comma-separated values)", True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        menu.append(item)
       
        export_grid_to_menu = gtk.MenuItem("_Export", True)
        export_grid_to_menu.set_submenu(menu)
        return export_grid_to_menu
        
    def edit_clues(self):
        editor = ClueEditor(self, self.puzzle_manager.current_puzzle)
        editor.show_all()
        
        editor.run()
        editor.destroy()

    def resize_grid(self):
        window = SizeWindow(self, self.puzzle_manager.current_puzzle)
        window.show_all()
        response = window.run()
        if response == gtk.RESPONSE_ACCEPT:
            width, height = window.get_size()
            if self.puzzle_manager.current_puzzle.grid.width != width or \
                self.puzzle_manager.current_puzzle.grid.height != height:
                self.transform_grid(transform.resize_grid, width=width, height=height)
        window.destroy()
        
    def view_preferences(self):
        preferences = PreferencesWindow(self)
        preferences.show_all()
        
        preferences.run()
        preferences.destroy()
        
    def undo_action(self):
        action.stack.undo_action(self.puzzle_manager.current_puzzle)
        self.update_window()
        
    def redo_action(self):
        action.stack.redo_action(self.puzzle_manager.current_puzzle)
        self.update_window()
        
    def update_undo_redo(self):
        self.undo_menu_item.set_sensitive(len(action.stack.undo_stack) > 0)
        self.redo_menu_item.set_sensitive(len(action.stack.redo_stack) > 0)
        
        self.undo_tool_item.set_sensitive(len(action.stack.undo_stack) > 0)
        self.redo_tool_item.set_sensitive(len(action.stack.redo_stack) > 0)
        
    def create_edit_menu(self):
        menu = gtk.Menu()
        
        accel_group = gtk.AccelGroup()
        self.add_accel_group(accel_group)
        
        activate = lambda item: self.undo_action()
        select = lambda item: self.update_status(STATUS_MENU
            , "Undo the last action")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        self.undo_menu_item = gtk.ImageMenuItem(gtk.STOCK_UNDO, None)
        key, mod = gtk.accelerator_parse("<Ctrl>Z")
        self.undo_menu_item.add_accelerator("activate", accel_group, key, mod, gtk.ACCEL_VISIBLE)
        self.undo_menu_item.connect("activate", activate)
        self.undo_menu_item.connect("select", select)
        self.undo_menu_item.connect("deselect", deselect)
        self.undo_menu_item.set_sensitive(False)
        menu.append(self.undo_menu_item)
        
        activate = lambda item: self.redo_action()
        select = lambda item: self.update_status(STATUS_MENU
            , "Redo the last undone action")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        self.redo_menu_item = gtk.ImageMenuItem(gtk.STOCK_REDO, None)
        key, mod = gtk.accelerator_parse("<Shift><Ctrl>Z")
        self.redo_menu_item.add_accelerator("activate", accel_group, key, mod, gtk.ACCEL_VISIBLE)
        self.redo_menu_item.connect("activate", activate)
        self.redo_menu_item.connect("select", select)
        self.redo_menu_item.connect("deselect", deselect)
        self.redo_menu_item.set_sensitive(False)
        menu.append(self.redo_menu_item)
        
        menu.append(gtk.SeparatorMenuItem())
        
        activate = lambda item: self.edit_clues()
        select = lambda item: self.update_status(STATUS_MENU
            , "Edit clues")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.MenuItem("Edit _clues", True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        item.set_sensitive(False)
        menu.append(item)
        self.puzzle_toggle_items += [item]
        
        menu.append(gtk.SeparatorMenuItem())
        
        activate = lambda item: self.transform_grid(transform.shift_grid_up)
        select = lambda item: self.update_status(STATUS_MENU
            , "Move the content of the grid up by one square")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.MenuItem("Move content _up", True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        item.set_sensitive(False)
        menu.append(item)
        self.puzzle_toggle_items += [item]
        
        activate = lambda item: self.transform_grid(transform.shift_grid_down)
        select = lambda item: self.update_status(STATUS_MENU
            , "Move the content of the grid down by one square")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.MenuItem("Move content _down", True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        item.set_sensitive(False)
        menu.append(item)
        self.puzzle_toggle_items += [item]
        
        activate = lambda item: self.transform_grid(transform.shift_grid_left)
        select = lambda item: self.update_status(STATUS_MENU
            , "Move the content of the grid left by one square")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.MenuItem("Move content _left", True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        item.set_sensitive(False)
        menu.append(item)
        self.puzzle_toggle_items += [item]
        
        activate = lambda item: self.transform_grid(transform.shift_grid_right)
        select = lambda item: self.update_status(STATUS_MENU            
            , "Move the content of the grid right by one square")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.MenuItem("Move content _right", True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        item.set_sensitive(False)
        menu.append(item)
        self.puzzle_toggle_items += [item]
        
        menu.append(gtk.SeparatorMenuItem())
        
        activate = lambda item: \
            self.resize_grid()
        select = lambda item: \
            self.update_status(STATUS_MENU
                , "Change the size of the grid")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.MenuItem("_Resize grid", True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        item.set_sensitive(False)
        menu.append(item)
        self.puzzle_toggle_items += [item]
        
        menu.append(gtk.SeparatorMenuItem())
        
        activate = lambda item: \
            self.perform_selection_based_transform(transform.insert_row_above)
        select = lambda item: \
            self.update_status(STATUS_MENU
                , "Insert an empty row above this cell")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.MenuItem("Insert row (above)", False)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        item.set_sensitive(False)
        menu.append(item)
        self.selection_toggle_items += [(item, lambda puzzle: True)]
        
        activate = lambda item: \
            self.perform_selection_based_transform(transform.insert_row_below)
        select = lambda item: \
            self.update_status(STATUS_MENU
                , "Insert an empty row below this cell")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.MenuItem("Insert row (below)", False)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        item.set_sensitive(False)
        menu.append(item)
        self.selection_toggle_items += [(item, lambda puzzle: True)]
        
        activate = lambda item: \
            self.perform_selection_based_transform(transform.insert_column_left)
        select = lambda item: \
            self.update_status(STATUS_MENU
                , "Insert an empty column to the left of this cell")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.MenuItem("Insert column (left)", False)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        item.set_sensitive(False)
        menu.append(item)
        self.selection_toggle_items += [(item, lambda puzzle: True)]
        
        activate = lambda item: \
            self.perform_selection_based_transform(transform.insert_column_right)
        select = lambda item: \
            self.update_status(STATUS_MENU
                , "Insert an empty column to the right of this cell")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.MenuItem("Insert column (right)", False)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        item.set_sensitive(False)
        menu.append(item)
        self.selection_toggle_items += [(item, lambda puzzle: True)]
        
        menu.append(gtk.SeparatorMenuItem())
        
        activate = lambda item: \
            self.perform_selection_based_transform(transform.remove_row)
        select = lambda item: \
            self.update_status(STATUS_MENU
                , "Remove the row containing this cell")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.MenuItem("Remove row", False)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        item.set_sensitive(False)
        menu.append(item)
        self.selection_toggle_items += [(item, lambda puzzle: puzzle.grid.height > 3)]
        
        activate = lambda item: \
            self.perform_selection_based_transform(transform.remove_column)
        select = lambda item: \
            self.update_status(STATUS_MENU
                , "Remove the column containing this cell")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.MenuItem("Remove column", False)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        item.set_sensitive(False)
        menu.append(item)
        self.selection_toggle_items += [(item, lambda puzzle: puzzle.grid.width > 3)]
        
        menu.append(gtk.SeparatorMenuItem())
        
        activate = lambda item: self.transform_grid(transform.clear_all)
        select = lambda item: self.update_status(STATUS_MENU
            , "Clear the blocks, the letters and the clues of the puzzle")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.MenuItem("Clear _all", True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        item.set_sensitive(False)
        menu.append(item)
        self.puzzle_toggle_items += [item]
        
        activate = lambda item: self.transform_grid(transform.clear_chars)
        select = lambda item: self.update_status(STATUS_MENU
            , "Clear the letters and the clues of the puzzle")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.MenuItem("Clear _letters", True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        item.set_sensitive(False)
        menu.append(item)
        self.puzzle_toggle_items += [item]
        
        activate = lambda item: self.transform_grid(transform.clear_clues)
        select = lambda item: self.update_status(STATUS_MENU
            , "Clear the clues of the puzzle")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.MenuItem("Clear clu_es", True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        item.set_sensitive(False)
        menu.append(item)
        self.puzzle_toggle_items += [item]
        
        menu.append(gtk.SeparatorMenuItem())
        
        activate = lambda item: self.view_preferences()
        select = lambda item: self.update_status(STATUS_MENU
            , "Configure the application")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES, None)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        menu.append(item)
                
        edit_menu = gtk.MenuItem("_Edit", True)
        edit_menu.set_submenu(menu)
        return edit_menu
        
    def perform_selection_based_transform(self, transform):
        selection = self.get_selection()
        if selection is not None:
            sel_x, sel_y = selection
            self.transform_grid(transform, x=sel_x, y=sel_y)
        
    def update_selection_based_tools(self, status):
        for item, predicate in self.selection_toggle_items:
            item.set_sensitive(status and predicate(self.puzzle_manager.current_puzzle))
        
    def transform_grid(self, transform, **args):
        a = transform(self.puzzle_manager.current_puzzle, **args)
        action.stack.push_action(a)
        self.update_window()
        
    def update_window(self):
        message = self.puzzle_manager.current_puzzle.grid.determine_status_message()
        self.update_undo_redo()
        self.update_status(STATUS_GRID, message)
        
        selection = self.get_selection()
        if selection is not None:
            sel_x, sel_y = selection
            valid = self.puzzle_manager.current_puzzle.grid.is_valid(sel_x, sel_y)
            self.update_selection_based_tools(valid)
        self.panel.queue_draw()
        
    def create_view_menu(self):
        menu = gtk.Menu()
        
        activate = lambda item: self.toggle_toolbar(item)
        select = lambda item: self.update_status(STATUS_MENU
            , "Show or hide the toolbar")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.CheckMenuItem("_Toolbar", True)
        item.set_active(True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        menu.append(item)
        
        activate = lambda item: self.toggle_statusbar(item)
        select = lambda item: self.update_status(STATUS_MENU
            , "Show or hide the statusbar")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.CheckMenuItem("_Statusbar", True)
        item.set_active(True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        menu.append(item)
        
        view_menu = gtk.MenuItem("_View", True)
        view_menu.set_submenu(menu)
        return view_menu

    def toggle_toolbar(self, widget):
        if widget.active:
            self.toolbar.show()
        else:
            self.toolbar.hide()        
        
    def toggle_statusbar(self, widget):
        if widget.active:
            self.statusbar.show()
        else:
            self.statusbar.hide()

    def create_help_menu(self):
        menu = gtk.Menu()
        
        activate = self.on_help_about_activate
        select = lambda item: self.update_status(STATUS_MENU
            , "About this application")
        deselect = lambda item: self.pop_status(STATUS_MENU)
        item = gtk.ImageMenuItem(gtk.STOCK_ABOUT, None)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        menu.append(item)
        
        help_menu = gtk.MenuItem("_Help", True)
        help_menu.set_submenu(menu)
        return help_menu
        
    def on_help_about_activate(self, widget, data=None):
        dialog = gtk.AboutDialog()
        dialog.set_title("About Palabra")
        dialog.set_program_name("Palabra")
        dialog.set_comments("Crossword creation software")
        dialog.set_version(PALABRA_VERSION)
        dialog.set_authors(["Simeon Visser"])
        dialog.set_copyright("Copyright 2009 Simeon Visser")
        dialog.set_license("""This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
                
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses/>.""")
        dialog.set_wrap_license(True)
        dialog.set_transient_for(self)
        dialog.connect("response", lambda dialog, response: dialog.destroy())
        dialog.show_all()

def quit():
    gtk.main_quit()
    write_config_file()
