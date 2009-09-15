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

import action
from action import ClueTransformAction
import constants
import preferences
import transform
from word import search_wordlists

class WordTool:
    def __init__(self, callbacks):
        self.callbacks = callbacks
    
    def create(self):
        # word displayed_string
        self.store = gtk.ListStore(str, str)
        self.tree = gtk.TreeView(self.store)
        self.tree.connect("row-activated", self.on_row_activated)
        self.tree.get_selection().connect("changed", self.on_selection_changed)
        self.tree.connect("button_press_event", self.on_tree_clicked)
        self.tree.set_headers_visible(False)
        
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("")
        column.pack_start(cell, True)
        column.set_attributes(cell, markup=1)
        self.tree.append_column(column)
        
        tree_window = gtk.ScrolledWindow(None, None)
        tree_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        tree_window.add(self.tree)
        tree_window.set_size_request(192, -1)
        
        check_button = gtk.CheckButton("Show only words with\nintersecting words")
        check_button.connect("toggled", self.on_button_toggled)
        
        main = gtk.VBox(False, 0)
        main.set_spacing(9)
        main.pack_start(tree_window, True, True, 0)
        main.pack_start(check_button, False, False, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(6)
        hbox.set_spacing(6)
        hbox.pack_start(main, True, True, 0)
        return hbox
        
    def on_button_toggled(self, button):
        self.callbacks["toggle"](button.get_active())
        
    def on_row_activated(self, tree, path, column):
        store, it = self.tree.get_selection().get_selected()
        self.callbacks["insert"](store.get_value(it, 0))
        
    def on_selection_changed(self, selection):
        store, it = selection.get_selected()
        self._perform_overlay_callback(it)
        
    def on_tree_clicked(self, tree, event):
        if event.button == 1:
            x = int(event.x)
            y = int(event.y)
            
            item = tree.get_path_at_pos(x, y)
            if item is not None:
                path, col, cellx, celly = item
                if tree.get_selection().path_is_selected(path):
                    it = tree.get_model().get_iter(path)
                    self._perform_overlay_callback(it)
                    
    def _perform_overlay_callback(self, it):
        if it is None:
            self.callbacks["overlay"](None)
        else:
            self.callbacks["overlay"](self.store.get_value(it, 0))
        
    def display(self, strings):
        self.store.clear()
        for s in strings:
            self.store.append([s, s])
        self.tree.queue_draw()

class Editor(gtk.HBox):
    def __init__(self, palabra_window, drawing_area, puzzle):
        gtk.HBox.__init__(self)
        self.palabra_window = palabra_window
        self.drawing_area = drawing_area
        self.puzzle = puzzle
        
        self.tools = {}
        
        self.settings = {}
        self.settings["selection_x"] = -1
        self.settings["selection_y"] = -1
        self.settings["direction"] = "across"
        self.settings["keep_horizontal_symmetry"] = False
        self.settings["keep_vertical_symmetry"] = False
        self.settings["keep_point_symmetry"] = False
        self.settings["keep_point_symmetry"] = True
        
        self.settings["word_search_parameters"] = None
        self.settings["show_intersecting_words"] = False
        
        self.settings["locked_grid"] = False
        
        self.current_x = -1
        self.current_y = -1
        
        self.mouse_buttons_down = [False, False, False]
        
        self.drawing_area.set_flags(gtk.CAN_FOCUS)
        
        self.expose_event_id = self.drawing_area.connect("expose_event"
            , self.on_expose_event)
        self.button_press_event_id = self.drawing_area.connect("button_press_event"
            , self.on_button_press_event)
        self.button_release_event_id = self.drawing_area.connect("button_release_event"
            , self.on_button_release_event)
        self.motion_notify_event_id = self.drawing_area.connect("motion_notify_event"
            , self.on_motion_notify_event)
        self.key_press_event_id = self.drawing_area.connect("key_press_event"
            , self.on_key_press_event)
        self.key_release_event_id = self.drawing_area.connect("key_release_event"
            , self.on_key_release_event)
                
    def cleanup(self):
        self.drawing_area.unset_flags(gtk.CAN_FOCUS)
        self.drawing_area.disconnect(self.expose_event_id)
        self.drawing_area.disconnect(self.button_press_event_id)
        self.drawing_area.disconnect(self.button_release_event_id)
        self.drawing_area.disconnect(self.motion_notify_event_id)
        self.drawing_area.disconnect(self.key_press_event_id)
        self.drawing_area.disconnect(self.key_release_event_id)
        
    def on_expose_event(self, drawing_area, event):
        context = drawing_area.window.cairo_create()
        
        self.puzzle.view.select_mode(constants.VIEW_MODE_EDITOR)
        
        self.puzzle.view.render_background(context, event.area)
        
        r = preferences.prefs["color_warning_red"] / 65535.0
        g = preferences.prefs["color_warning_green"] / 65535.0
        b = preferences.prefs["color_warning_blue"] / 65535.0
        self.puzzle.view.render_warnings(context, event.area, r, g, b)
        
        if self.palabra_window.blacklist is not None:
            self.puzzle.view.render_blacklist(context, event.area, r, g, b, self.palabra_window.blacklist)
        
        x = self.settings["selection_x"]
        y = self.settings["selection_y"]
        if self.puzzle.grid.is_valid(x, y):
            if not self.puzzle.grid.is_block(x, y):
                direction = self.settings["direction"]
                r = preferences.prefs["color_current_word_red"] / 65535.0
                g = preferences.prefs["color_current_word_green"] / 65535.0
                b = preferences.prefs["color_current_word_blue"] / 65535.0
                self.puzzle.view.render_line(context, event.area, x, y, direction, r, g, b)
                
            r = preferences.prefs["color_primary_selection_red"] / 65535.0
            g = preferences.prefs["color_primary_selection_green"] / 65535.0
            b = preferences.prefs["color_primary_selection_blue"] / 65535.0
            self.puzzle.view.render_location(context, event.area, x, y, r, g, b)
        
        if self.current_x >= 0 and self.current_y >= 0:
            r = preferences.prefs["color_secondary_active_red"] / 65535.0
            g = preferences.prefs["color_secondary_active_green"] / 65535.0
            b = preferences.prefs["color_secondary_active_blue"] / 65535.0
            for p, q in self.apply_symmetry(self.current_x, self.current_y):
                self.puzzle.view.render_location(context, event.area, p, q, r, g, b)
                
            # draw current cell last to prevent
            # symmetrical cells from overlapping it
            x = self.current_x
            y = self.current_y
            r = preferences.prefs["color_primary_active_red"] / 65535.0
            g = preferences.prefs["color_primary_active_green"] / 65535.0
            b = preferences.prefs["color_primary_active_blue"] / 65535.0
            self.puzzle.view.render_location(context, event.area, x, y, r, g, b)
        
        self.puzzle.view.render(context, event.area)
        
        return True
        
    def on_button_press_event(self, drawing_area, event):
        if 1 <= event.button <= 3:
            self.mouse_buttons_down[event.button - 1] = True

        drawing_area.grab_focus()
        
        prev_x = self.settings["selection_x"]
        prev_y = self.settings["selection_y"]
        
        x = self.puzzle.view.properties.screen_to_grid_x(event.x)
        y = self.puzzle.view.properties.screen_to_grid_y(event.y)
        
        if not self.puzzle.grid.is_valid(x, y):
            self.set_selection(-1, -1)
            return True
            
        if (event.state & gtk.gdk.SHIFT_MASK):
            if self.puzzle.grid.is_valid(x, y):
                if event.button in [1, 3] and not self.settings["locked_grid"]:
                    self.transform_blocks(x, y, event.button == 1)
        else:
            if event.button == 1:
                # type is needed to assure rapid clicking
                # doesn't trigger it multiple times
                if (prev_x, prev_y) == (x, y) and event.type == gtk.gdk._2BUTTON_PRESS:
                    x = self.settings["selection_x"]
                    y = self.settings["selection_y"]
                    direction = self.settings["direction"]
                    
                    self.puzzle.view.refresh_line(drawing_area, prev_x, prev_y, direction)
                    self.change_typing_direction()
                    self.puzzle.view.refresh_line(drawing_area, x, y, direction)
                if self.puzzle.grid.is_available(x, y):
                    self.set_selection(x, y)
        return True
        
    def on_button_release_event(self, drawing_area, event):
        if 1 <= event.button <= 3:
            self.mouse_buttons_down[event.button - 1] = False
        return True
        
    def on_motion_notify_event(self, drawing_area, event):
        prev_x = self.current_x
        prev_y = self.current_y
        self.current_x = cx = self.puzzle.view.properties.screen_to_grid_x(event.x)
        self.current_y = cy = self.puzzle.view.properties.screen_to_grid_y(event.y)

        if (prev_x, prev_y) != (cx, cy):
            self.refresh_symmetry(drawing_area, prev_x, prev_y)
            self.refresh_symmetry(drawing_area, cx, cy)
            self.puzzle.view.refresh_location(drawing_area, prev_x, prev_y)
            self.puzzle.view.refresh_location(drawing_area, cx, cy)
        
        if (self.puzzle.grid.is_valid(cx, cy)
            and (event.state & gtk.gdk.SHIFT_MASK)
            and not self.settings["locked_grid"]):
                if self.mouse_buttons_down[0]:
                    self.transform_blocks(cx, cy, True)
                elif self.mouse_buttons_down[2]:
                    self.transform_blocks(cx, cy, False)
        return True
        
    def refresh_clues(self):
        """Reload all the word/clue items and select the currently selected item."""
        x = self.settings["selection_x"]
        y = self.settings["selection_y"]
        direction = self.settings["direction"]
        
        p, q = self.puzzle.grid.get_start_word(x, y, direction)
        self.tools["clue"].load_items(self.puzzle)
        self.tools["clue"].select(p, q, direction)
        
    def refresh_words(self, force_refresh=False):
        """
        Update the list of words according to active constraints of letters
        and the current settings (e.g., show only words with intersections).
        """
        show_intersecting = self.settings["show_intersecting_words"]
        x = self.settings["selection_x"]
        y = self.settings["selection_y"]
        result = None
        if self.puzzle.grid.is_available(x, y):
            parameters = self._get_search_parameters(x, y, self.settings["direction"])
            length, constraints = parameters
            if (self.settings["word_search_parameters"] == parameters
                and not show_intersecting and not force_refresh):
                return
            if length <= 1:
                # if this is the case, don't search and clear the words list
                pass
            elif len(constraints) != length:
                more = None
                if show_intersecting:
                    more = self._gather_all_constraints(x, y, self.settings["direction"])
                wordlists = self.palabra_window.wordlists
                result = search_wordlists(wordlists, length, constraints, more)
        if result is not None:
            self.settings["word_search_parameters"] = parameters
            self.tools["word"].display(result)
        else:
            self.settings["word_search_parameters"] = None
            self.tools["word"].display([])
            
    def get_clue_tool_callbacks(self):
        def select(x, y, direction):
            """Select the word at (x, y, direction) in the grid."""
            self.tools["clue"].settings["use_scrolling"] = False
            self.set_typing_direction(direction)
            self.set_selection(x, y)
            self.tools["clue"].settings["use_scrolling"] = True
        def clue(x, y, direction, key, value):
            """
            Update the clue data by creating or updating the latest undo action.
            """
            a = action.stack.peek_action()
            if (isinstance(a, ClueTransformAction)
                and a.matches(x, y, direction, key)):
                self.puzzle.grid.store_clue(x, y, direction, key, value)
                a.update(x, y, direction, key, value)
            else:
                self.palabra_window.transform_clues(transform.modify_clue
                        , x=x
                        , y=y
                        , direction=direction
                        , key=key
                        , value=value)
        return {"select": select, "clue": clue}
        
    def get_word_tool_callbacks(self):
        """Return the callback functions for the word tool in the main window."""
        def insert(word):
            """Insert a word in the selected slot."""
            x = self.settings["selection_x"]
            y = self.settings["selection_y"]
            direction = self.settings["direction"]
            if self.puzzle.grid.is_available(x, y):
                p, q = self.puzzle.grid.get_start_word(x, y, direction)
                w = self.puzzle.grid.decompose_word(word, p, q, direction)
                self._insert_word(w)
        def toggle(status):
            """Toggle the status of the intersecting words option."""
            self.settings["show_intersecting_words"] = status
            self.refresh_words(True)
        def overlay(word):
            """
            Display the word in the selected slot without storing it the grid.
            """
            if word is not None:
                x = self.settings["selection_x"]
                y = self.settings["selection_y"]
                direction = self.settings["direction"]
                p, q = self.puzzle.grid.get_start_word(x, y, direction)
                result = self.puzzle.grid.decompose_word(word, p, q, direction)
                
                result = [(x, y, c.upper()) for x, y, c in result
                    if self.puzzle.grid.get_char(x, y) != c.upper()]
                self._display_overlay(result)
            else:
                self._display_overlay([])
        return {"insert": insert, "toggle": toggle, "overlay": overlay}
        
    def _display_overlay(self, new):
        """Display the (x, y, c) items in the grid's overlay."""
        old = self.puzzle.view.overlay
        self.puzzle.view.overlay = new
        for x, y, c in (old + new):
            self.puzzle.view.refresh_location(self.drawing_area, x, y)
        
    def _get_search_parameters(self, x, y, direction):
        """Determine the length and the constraints of the word at (x, y, direction)."""
        p, q = self.puzzle.grid.get_start_word(x, y, direction)
        length = self.puzzle.grid.word_length(p, q, direction)
        constraints = self.puzzle.grid.gather_constraints(p, q, direction)
        return (length, constraints)
        
    def _gather_all_constraints(self, x, y, direction):
        """
        Gather constraints of all intersecting words of the word at (x, y).
        
        This function returns a list with tuples that contain the
        letters and positions of intersecting words. The item at place i of
        the list corresponds to the intersecting word at position i.
        
        Each tuple contains the position at which the word at
        (x, y, direction) intersects the intersecting word, the length
        of the intersecting word and the constraints.
        """
        result = []
        other = {"across": "down", "down": "across"}[direction]
        sx, sy = self.puzzle.grid.get_start_word(x, y, direction)
        for s, t in self.puzzle.grid.in_direction(direction, sx, sy):
            p, q = self.puzzle.grid.get_start_word(s, t, other)
            length = self.puzzle.grid.word_length(p, q, other)
            
            if other == "across":
                index = x - p
            elif other == "down":
                index = y - q
            
            constraints = self.puzzle.grid.gather_constraints(p, q, other)
            item = (index, length, constraints)
            result.append(item)
        return result
    
    def _insert_word(self, chars):
        """Insert a word by storing the list of (x, y, c) items in the grid."""
        if self.settings["locked_grid"]:
            return
        actual = [(x, y, c.upper()) for x, y, c in chars
            if self.puzzle.grid.get_char(x, y) != c.upper()]
        if len(actual) > 0:
            self.palabra_window.transform_grid(transform.modify_chars, chars=actual)
        
    def set_symmetry(self, options):
        symmetries = \
            ["keep_horizontal_symmetry"
            ,"keep_vertical_symmetry"
            ,"keep_point_symmetry"
            ]
        for key in symmetries:
            self.settings[key] = key in options
            
    def apply_symmetry(self, x, y):
        """Apply one or more symmetrical transforms to (x, y)."""
        names = []
        if self.settings["keep_horizontal_symmetry"]:
            names.append("horizontal")
        if self.settings["keep_vertical_symmetry"]:
            names.append("vertical")
        if self.settings["keep_point_symmetry"]:
            names.append("point")
        
        cells = []
        if "horizontal" in names:
            cells.append((x, self.puzzle.grid.height - 1 - y))
        if "vertical" in names:
            cells.append((self.puzzle.grid.width - 1 - x, y))
        if (("horizontal" in names and "vertical" in names)
            or "point" in names):
            p = self.puzzle.grid.width - 1 - x
            q = self.puzzle.grid.height - 1 - y
            cells.append((p, q))
        return cells
        
    def refresh_symmetry(self, drawing_area, x, y):
        """
        Refresh the cells that correspond to the current symmetry settings.
        """
        for p, q in self.apply_symmetry(x, y):
            self.puzzle.view.refresh_location(drawing_area, p, q)

    def transform_blocks(self, x, y, status):
        """Place or remove a block at (x, y) and its symmetrical cells."""
        blocks = []
        
        # determine blocks that need to be modified
        if status != self.puzzle.grid.is_block(x, y):
            blocks.append((x, y, status))
        for p, q in self.apply_symmetry(x, y):
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
            
        if event.keyval == gtk.keysyms.BackSpace and not self.settings["locked_grid"]:
            self.on_backspace(drawing_area, event)
        elif event.keyval == gtk.keysyms.Tab:
            self.change_typing_direction()
        elif event.keyval == gtk.keysyms.Home:
            self._on_jump_to_cell(drawing_area, "start")
        elif event.keyval == gtk.keysyms.End:
            self._on_jump_to_cell(drawing_area, "end")
        elif event.keyval == gtk.keysyms.Left:
            self.on_arrow_key(drawing_area, event, -1, 0)
        elif event.keyval == gtk.keysyms.Up:
            self.on_arrow_key(drawing_area, event, 0, -1)
        elif event.keyval == gtk.keysyms.Right:
            self.on_arrow_key(drawing_area, event, 1, 0)
        elif event.keyval == gtk.keysyms.Down:
            self.on_arrow_key(drawing_area, event, 0, 1)
        elif event.keyval == gtk.keysyms.Delete and not self.settings["locked_grid"]:
            self.on_delete(drawing_area, event)
        elif not self.settings["locked_grid"]:
            self.on_typing(drawing_area, event)
        return True
        
    def on_backspace(self, drawing_area, event):
        """Remove a character in the current or previous cell."""
        x = self.settings["selection_x"]
        y = self.settings["selection_y"]
        direction = self.settings["direction"]
        
        # remove character in selected cell if it has one
        if self.puzzle.grid.get_char(x, y) != "":
            self.palabra_window.transform_grid(transform.modify_char
                , x=x
                , y=y
                , next_char="")
        else:
            # remove character in previous cell if needed and move selection
            x += (-1 if direction == "across" else 0)
            y += (-1 if direction == "down" else 0)
            if self.puzzle.grid.is_available(x, y):
                if self.puzzle.grid.get_char(x, y) != "":
                    self.palabra_window.transform_grid(transform.modify_char
                        , x=x
                        , y=y
                        , next_char="")
                self.set_selection(x, y)
            
    def on_arrow_key(self, drawing_area, event, dx, dy):
        """Move the selection to an available nearby cell."""
        x = self.settings["selection_x"]
        y = self.settings["selection_y"]
        if self.puzzle.grid.is_available(x + dx, y + dy):
            self.set_selection(x + dx, y + dy)
            if dy != 0:
                self.puzzle.view.refresh_horizontal_line(drawing_area, y)
                self.puzzle.view.refresh_horizontal_line(drawing_area, y + dy)
            if dx != 0:
                self.puzzle.view.refresh_vertical_line(drawing_area, x)
                self.puzzle.view.refresh_vertical_line(drawing_area, x + dx)
            self.refresh_words()
        
    def _on_jump_to_cell(self, drawing_area, target):
        """Jump to the start or end (i.e., first or last cell) of a word."""
        x = self.settings["selection_x"]
        y = self.settings["selection_y"]
        direction = self.settings["direction"]
        if target == "start":
            p, q = self.puzzle.grid.get_start_word(x, y, direction)
        elif target == "end":
            p, q = self.puzzle.grid.get_end_word(x, y, direction)
        self.set_selection(p, q)
        self.puzzle.view.refresh_line(drawing_area, x, y, direction)
        
    def on_delete(self, drawing_area, event):
        """Remove the character in the selected cell."""
        x = self.settings["selection_x"]
        y = self.settings["selection_y"]
        if self.puzzle.grid.get_char(x, y) != "":
            self.palabra_window.transform_grid(transform.modify_char
                , x=x
                , y=y
                , next_char="")
            self.puzzle.view.refresh_location(drawing_area, x, y)
        
    def on_typing(self, drawing_area, event):
        """Place an alphabetical character in the grid and move the selection."""
        if gtk.keysyms.a <= event.keyval <= gtk.keysyms.z:
            x = self.settings["selection_x"]
            y = self.settings["selection_y"]
            direction = self.settings["direction"]
            if self.puzzle.grid.is_valid(x, y):
                c = chr(event.keyval).capitalize()
                
                self.palabra_window.transform_grid(transform.modify_char
                        , x=x
                        , y=y
                        , next_char=c)
                if direction == "across":
                    if self.puzzle.grid.is_available(x + 1, y):
                        self.settings["selection_x"] += 1
                    self.puzzle.view.refresh_horizontal_line(drawing_area, y)
                elif direction == "down":
                    if self.puzzle.grid.is_available(x, y + 1):
                        self.settings["selection_y"] += 1
                    self.puzzle.view.refresh_vertical_line(drawing_area, x)
        
    def change_typing_direction(self):
        """Switch the typing direction to the other direction."""
        other = {"across": "down", "down": "across"}
        self.set_typing_direction(other[self.settings["direction"]])
        
    def set_typing_direction(self, direction):
        self.settings["direction"] = direction
        self._on_selection_change()
        self.drawing_area.queue_draw()
        self.refresh_words()
        self._display_overlay([])
        
    def refresh_visual_size(self):
        self.puzzle.view.refresh_visual_size(self.drawing_area)
        
    def get_selection(self):
        return (self.settings["selection_x"], self.settings["selection_y"])
        
    def set_selection(self, x, y):
        self.settings["selection_x"] = x
        self.settings["selection_y"] = y
        self._on_selection_change()
        self.palabra_window.update_window()
        self._display_overlay([])
        
    def _on_selection_change(self):
        """
        Update the selection of the clue tool when the grid selection changes.
        """
        x = self.settings["selection_x"]
        y = self.settings["selection_y"]
        direction = self.settings["direction"]
        if x >= 0 and y >= 0:
            p, q = self.puzzle.grid.get_start_word(x, y, direction)
            self.tools["clue"].select(p, q, self.settings["direction"])
        else:
            self.tools["clue"].deselect()
