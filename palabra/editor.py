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
        self.palabra_window.update_window()

    def on_expose_event(self, drawing_area, event):
        context = drawing_area.window.cairo_create()
        
        self.puzzle.view.render_background(context)
        
        #secondary_selection_red = preferences.prefs["color_secondary_selection_red"] / 65535.0
        #secondary_selection_green = preferences.prefs["color_secondary_selection_green"] / 65535.0
        #secondary_selection_blue = preferences.prefs["color_secondary_selection_blue"] / 65535.0
        
        x = self.settings["selection_x"]
        y = self.settings["selection_y"]
        if self.puzzle.grid.is_valid(x, y):
            if not self.puzzle.grid.is_block(x, y):
                r = preferences.prefs["color_current_word_red"] / 65535.0
                g = preferences.prefs["color_current_word_green"] / 65535.0
                b = preferences.prefs["color_current_word_blue"] / 65535.0
                if self.settings["direction"] == "horizontal":
                    self.puzzle.view.render_horizontal_line(context, x, y, r, g, b)
                elif self.settings["direction"] == "vertical":
                    self.puzzle.view.render_vertical_line(context, x, y, r, g, b)
                
            r = preferences.prefs["color_primary_selection_red"] / 65535.0
            g = preferences.prefs["color_primary_selection_green"] / 65535.0
            b = preferences.prefs["color_primary_selection_blue"] / 65535.0
            self.puzzle.view.render_location(context, x, y, r, g, b)
        
        if self.current_x >= 0 and self.current_y >= 0:
            r = preferences.prefs["color_secondary_active_red"] / 65535.0
            g = preferences.prefs["color_secondary_active_green"] / 65535.0
            b = preferences.prefs["color_secondary_active_blue"] / 65535.0
            if self.settings["keep_horizontal_symmetry"]:
                x = self.current_x
                y = (self.puzzle.grid.height - 1) - self.current_y
                self.puzzle.view.render_location(context, x, y, r, g, b)
            if self.settings["keep_vertical_symmetry"]:
                x = (self.puzzle.grid.width - 1) - self.current_x
                y = self.current_y
                self.puzzle.view.render_location(context, x, y, r, g, b)
            if ((self.settings["keep_horizontal_symmetry"] and
                self.settings["keep_vertical_symmetry"]) or
                self.settings["keep_point_symmetry"]):
                x = (self.puzzle.grid.width - 1) - self.current_x
                y = (self.puzzle.grid.height - 1) - self.current_y
                self.puzzle.view.render_location(context, x, y, r, g, b)
                
            # draw current cell last to prevent
            # symmetrical cells from overlapping it
            x = self.current_x
            y = self.current_y
            r = preferences.prefs["color_primary_active_red"] / 65535.0
            g = preferences.prefs["color_primary_active_green"] / 65535.0
            b = preferences.prefs["color_primary_active_blue"] / 65535.0
            self.puzzle.view.render_location(context, x, y, r, g, b)
        
        self.puzzle.view.render(context, mode=constants.VIEW_MODE_EDITOR)
        
        return True
        
    def on_button_press_event(self, drawing_area, event):
        if 1 <= event.button <= 3:
            self.mouse_buttons_down[event.button - 1] = True

        drawing_area.grab_focus()
        
        prev_x = self.settings["selection_x"]
        prev_y = self.settings["selection_y"]
        
        x = self.puzzle.view.screen_to_grid_x(event.x)
        y = self.puzzle.view.screen_to_grid_y(event.y)
        
        if not self.puzzle.grid.is_valid(x, y):
            self.set_selection(-1, -1)
            
        if event.button == 1 and not (event.state & gtk.gdk.SHIFT_MASK):
            if self.puzzle.grid.is_valid(x, y):
                self.set_selection(x, y)
        
        if (event.state & gtk.gdk.SHIFT_MASK) or event.type == gtk.gdk._2BUTTON_PRESS:
            if self.puzzle.grid.is_valid(x, y):
                if event.button == 1:
                    self.transform_blocks(x, y, True)
                elif event.button == 3:
                    self.transform_blocks(x, y, False)
        
        if self.settings["direction"] == "horizontal":
            self.puzzle.view.refresh_horizontal_line(drawing_area, prev_y)
        elif self.settings["direction"] == "vertical":
            self.puzzle.view.refresh_vertical_line(drawing_area, prev_x)
        
        x = self.settings["selection_x"]
        y = self.settings["selection_y"]
        if self.settings["direction"] == "horizontal":
            self.puzzle.view.refresh_horizontal_line(drawing_area, y)
        elif self.settings["direction"] == "vertical":
            self.puzzle.view.refresh_vertical_line(drawing_area, x)
        
        return True
        
    def on_button_release_event(self, drawing_area, event):
        if 1 <= event.button <= 3:
            self.mouse_buttons_down[event.button - 1] = False
        return True
        
    def on_motion_notify_event(self, drawing_area, event):
        prev_x = self.current_x
        prev_y = self.current_y
        
        self.puzzle.view.refresh_horizontal_line(drawing_area, prev_y)
        self.puzzle.view.refresh_vertical_line(drawing_area, prev_x)
        self.update_symmetry(drawing_area, prev_x, prev_y)
        
        self.current_x = self.puzzle.view.screen_to_grid_x(event.x)
        self.current_y = self.puzzle.view.screen_to_grid_y(event.y)
        
        cx = self.current_x
        cy = self.current_y
        
        if (prev_x, prev_y) != (cx, cy):
            self.puzzle.view.refresh_location(drawing_area, cx, cy)
            self.update_symmetry(drawing_area, cx, cy)
        
        if self.puzzle.grid.is_valid(cx, cy):
            if self.mouse_buttons_down[0] and (event.state & gtk.gdk.SHIFT_MASK):
                self.transform_blocks(cx, cy, True)
            elif self.mouse_buttons_down[2] and (event.state & gtk.gdk.SHIFT_MASK):
                self.transform_blocks(cx, cy, False)
        
        return True
        
    def set_symmetry(self, options):
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
            self.puzzle.view.refresh_location(drawing_area, x, y)
        if self.settings["keep_vertical_symmetry"]:
            x = (self.puzzle.grid.width - 1) - main_x
            y = main_y
            self.puzzle.view.refresh_location(drawing_area, x, y)
        if ((self.settings["keep_horizontal_symmetry"] and
            self.settings["keep_vertical_symmetry"]) or
            self.settings["keep_point_symmetry"]):
            x = (self.puzzle.grid.width - 1) - main_x
            y = (self.puzzle.grid.height - 1) - main_y
            self.puzzle.view.refresh_location(drawing_area, x, y)

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
        if ((self.settings["keep_horizontal_symmetry"] and
            self.settings["keep_vertical_symmetry"]) or
            self.settings["keep_point_symmetry"]):
            p = self.puzzle.grid.width - 1 - x
            q = self.puzzle.grid.height - 1 - y
            if status != self.puzzle.grid.is_block(p, q):
                blocks.append((p, q, status))
        if len(blocks) > 0:
            self.palabra_window.transform_grid(transform.modify_blocks, blocks=blocks)
            x = self.settings["selection_x"]
            y = self.settings["selection_y"]
            if (x, y, True) in blocks:
                self.set_selection(-1, -1)

    # needed to capture the press of a tab button
    # so focus won't switch to the toolbar
    def on_key_press_event(self, drawing_area, event):
        return True
        
    def on_key_release_event(self, drawing_area, event):
        # prevent conflicts with menu shortcut keys
        if ((event.state & gtk.gdk.SHIFT_MASK) or
            (event.state & gtk.gdk.CONTROL_MASK)):
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
                    if self.puzzle.grid.is_available(x, y):
                        self.palabra_window.transform_grid(transform.modify_char
                            , x=x
                            , y=y
                            , next_char='')
                        self.settings["selection_x"] -= 1
                elif self.settings["direction"] == "vertical":
                    x = self.settings["selection_x"]
                    y = self.settings["selection_y"] - 1
                    if self.puzzle.grid.is_available(x, y):
                        self.palabra_window.transform_grid(transform.modify_char
                            , x=x
                            , y=y
                            , next_char='')
                        self.settings["selection_y"] -= 1
        elif event.keyval == gtk.keysyms.Tab:
            self.change_typing_direction()
        elif event.keyval == gtk.keysyms.Home:
            x = self.settings["selection_x"]
            y = self.settings["selection_y"]
            if self.settings["direction"] == "horizontal":
                for i in reversed(range(x)):
                    if self.puzzle.grid.is_block(i, y):
                        self.settings["selection_x"] = i + 1
                        break
                else:
                    if not self.puzzle.grid.is_block(0, y):
                        self.settings["selection_x"] = 0
                self.puzzle.view.refresh_horizontal_line(drawing_area, y)
            elif self.settings["direction"] == "vertical":
                for i in reversed(range(y)):
                    if self.puzzle.grid.is_block(x, i):
                        self.settings["selection_y"] = i + 1
                        break
                else:
                    if not self.puzzle.grid.is_block(x, 0):
                        self.settings["selection_y"] = 0
                self.puzzle.view.refresh_vertical_line(drawing_area, x)
        elif event.keyval == gtk.keysyms.Left:
            x = self.settings["selection_x"]
            y = self.settings["selection_y"]
            if self.puzzle.grid.is_available(x - 1, y):
                self.puzzle.view.refresh_vertical_line(drawing_area, x)
                self.settings["selection_x"] -=1
                self.puzzle.view.refresh_vertical_line(drawing_area, x - 1)
        elif event.keyval == gtk.keysyms.Up:
            x = self.settings["selection_x"]
            y = self.settings["selection_y"]
            if self.puzzle.grid.is_available(x, y - 1):
                self.puzzle.view.refresh_horizontal_line(drawing_area, y)
                self.settings["selection_y"] -= 1
                self.puzzle.view.refresh_horizontal_line(drawing_area, y - 1)
        elif event.keyval == gtk.keysyms.Right:
            x = self.settings["selection_x"]
            y = self.settings["selection_y"]
            if self.puzzle.grid.is_available(x + 1, y):
                self.puzzle.view.refresh_vertical_line(drawing_area, x)
                self.settings["selection_x"] += 1
                self.puzzle.view.refresh_vertical_line(drawing_area, x + 1)
        elif event.keyval == gtk.keysyms.Down:
            x = self.settings["selection_x"]
            y = self.settings["selection_y"]
            if self.puzzle.grid.is_available(x, y + 1):
                self.puzzle.view.refresh_horizontal_line(drawing_area, y)
                self.settings["selection_y"] += 1
                self.puzzle.view.refresh_horizontal_line(drawing_area, y + 1)
        elif event.keyval == gtk.keysyms.End:
            x = self.settings["selection_x"]
            y = self.settings["selection_y"]
            if self.settings["direction"] == "horizontal":
                for i in range(x, self.puzzle.grid.width):
                    if self.puzzle.grid.is_block(i, y):
                        self.settings["selection_x"] = i - 1
                        break
                else:
                    if not self.puzzle.grid.is_block(self.puzzle.grid.width - 1, y):
                        self.settings["selection_x"] = self.puzzle.grid.width - 1
                self.puzzle.view.refresh_horizontal_line(drawing_area, y)
            elif self.settings["direction"] == "vertical":
                for i in range(y, self.puzzle.grid.height):
                    if self.puzzle.grid.is_block(x, i):
                        self.settings["selection_y"] = i - 1
                        break
                else:
                    if not self.puzzle.grid.is_block(x, self.puzzle.grid.height - 1):
                        self.settings["selection_y"] = self.puzzle.grid.height - 1
                self.puzzle.view.refresh_vertical_line(drawing_area, x)
        elif event.keyval == gtk.keysyms.Delete:
            x = self.settings["selection_x"]
            y = self.settings["selection_y"]
            self.puzzle.grid.clear_char(x, y)
            self.puzzle.view.refresh_location(drawing_area, x, y)
        else:
            if gtk.keysyms.a <= event.keyval <= gtk.keysyms.z:
                x = self.settings["selection_x"]
                y = self.settings["selection_y"]
                if self.puzzle.grid.is_valid(x, y):
                    c = chr(event.keyval).capitalize()
                    
                    self.palabra_window.transform_grid(transform.modify_char
                            , x=x
                            , y=y
                            , next_char=c)
                    if self.settings["direction"] == "horizontal":
                        if self.puzzle.grid.is_available(x + 1, y):
                            self.settings["selection_x"] += 1
                        self.puzzle.view.refresh_horizontal_line(drawing_area, y)
                    elif self.settings["direction"] == "vertical":
                        if self.puzzle.grid.is_available(x, y + 1):
                            self.settings["selection_y"] += 1
                        self.puzzle.view.refresh_vertical_line(drawing_area, x)
        return True
        
    def change_typing_direction(self):
        other = {"horizontal": "vertical", "vertical": "horizontal"}
        self.settings["direction"] = other[self.settings["direction"]]
        self.drawing_area.queue_draw()
