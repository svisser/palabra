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

import constants
import preferences
import transform

class Editor(gtk.HBox):
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
            
        self.palabra_window.update_status(constants.STATUS_GRID, self.puzzle.grid.determine_status_message())
                
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
        
        self.puzzle.view.update_view(context, mode=constants.VIEW_MODE_EDITOR)
        
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
        
        if (event.state & gtk.gdk.SHIFT_MASK) or event.type == gtk.gdk._2BUTTON_PRESS:
            if self.puzzle.grid.is_valid(self.current_x, self.current_y):
                if event.button == 1:
                    self.transform_blocks(current_x, current_y, True)
                elif event.button == 3:
                    self.transform_blocks(current_x, current_y, False)
        
        if self.settings["direction"] == "horizontal":
            self.puzzle.view.update_horizontal_line(drawing_area, prev_y)
        elif self.settings["direction"] == "vertical":
            self.puzzle.view.update_vertical_line(drawing_area, prev_x)
        
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
