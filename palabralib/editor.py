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

import cairo
import gtk

import action
from action import ClueTransformAction
import constants
from itertools import *
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
        word = self.store.get_value(it, 0) if it is not None else None
        self.callbacks["overlay"](word)
        
    def display(self, strings, show_intersections):
        self.store.clear()
        for word, has_intersections in strings:
            if show_intersections and not has_intersections:
                continue
            color = "black" if has_intersections else "gray"
            display = "".join(["<span color=\"", color,"\">", word, "</span>"])
            self.store.append([word, display])
        self.tree.queue_draw()
        
    def display_overlay(self):
        store, it = self.tree.get_selection().get_selected()
        self._perform_overlay_callback(it)
        
    def clear_overlay(self):
        self._perform_overlay_callback(None)

class Cell:
    def __init__(self, x=-1, y=-1):
        self.x = x
        self.y = y
        
class Selection:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.direction = direction

class Editor(gtk.HBox):
    def __init__(self, palabra_window, drawing_area, puzzle):
        gtk.HBox.__init__(self)
        self.palabra_window = palabra_window
        self.drawing_area = drawing_area
        self.puzzle = puzzle
        
        self.tools = {}
        
        self.editor_surface = None
        self.editor_pattern = None
        
        self.force_redraw = True
        
        self.settings = {}
        self.settings["keep_horizontal_symmetry"] = False
        self.settings["keep_vertical_symmetry"] = False
        self.settings["keep_point_symmetry"] = False
        self.settings["keep_point_symmetry"] = True
        self.settings["show_intersecting_words"] = False
        self.settings["locked_grid"] = False
        
        self.current = Cell(-1, -1)
        self.selection = Selection(-1, -1, "across")
        
        self.mouse_buttons_down = [False, False, False]
        
        self.drawing_area.set_flags(gtk.CAN_FOCUS)
        self.id_expose = self.drawing_area.connect("expose_event", self.on_expose_event)
        self.id_bpress = self.drawing_area.connect("button_press_event", self.on_button_press_event)
        self.id_brelease = self.drawing_area.connect("button_release_event", self.on_button_release_event)
        self.id_motion = self.drawing_area.connect("motion_notify_event", self.on_motion_notify_event)
        self.id_key_press = self.drawing_area.connect("key_press_event", self.on_key_press_event)
        self.id_key_release = self.drawing_area.connect("key_release_event", self.on_key_release_event)
        self.drawing_area.add_events(gtk.gdk.POINTER_MOTION_HINT_MASK)
                
    def cleanup(self):
        self.drawing_area.unset_flags(gtk.CAN_FOCUS)
        self.drawing_area.disconnect(self.id_expose)
        self.drawing_area.disconnect(self.id_bpress)
        self.drawing_area.disconnect(self.id_brelease)
        self.drawing_area.disconnect(self.id_motion)
        self.drawing_area.disconnect(self.id_key_press)
        self.drawing_area.disconnect(self.id_key_release)
    
    def _render_cells(self, cells, editor=True):
        self.puzzle.view.select_mode(constants.VIEW_MODE_EDITOR)
        context = cairo.Context(self.editor_surface)
        for x, y in cells:
            if self.puzzle.grid.is_valid(x, y):
                self.puzzle.view.render_bottom(context, x, y)
                if editor:
                    self._render_editor_of_cell(context, x, y)
                self.puzzle.view.render_top(context, x, y)
        context = self.drawing_area.window.cairo_create()
        context.set_source(self.editor_pattern)
        context.paint()
        
    def _render_cell(self, x, y):
        self._render_cells([(x, y)])
        
    def _clear_selection(self, x, y, direction):
        p = self.puzzle.grid.in_direction(direction, x, y)
        q = self.puzzle.grid.in_direction(direction, x, y, reverse=True)
        self._render_cells(chain(p, q), editor=False)
        
    def _render_selection(self, x, y, direction):
        p = self.puzzle.grid.in_direction(direction, x, y)
        q = self.puzzle.grid.in_direction(direction, x, y, reverse=True)
        self._render_cells(chain(p, q))
    
    def _render_editor_of_cell(self, context, x, y):
        # TODO speed
        r = preferences.prefs["color_warning_red"] / 65535.0
        g = preferences.prefs["color_warning_green"] / 65535.0
        b = preferences.prefs["color_warning_blue"] / 65535.0
        #self.puzzle.view.render_warnings(context, None, r, g, b)
        
        # TODO speed
        #if self.palabra_window.blacklist is not None:
        #    self.puzzle.view.render_blacklist(context, None, r, g, b, self.palabra_window.blacklist)
        
        sx = self.selection.x
        sy = self.selection.y
        sdir = self.selection.direction
        
        # selection line
        if self.puzzle.grid.is_valid(x, y):
            if not self.puzzle.grid.is_block(x, y):
                r = preferences.prefs["color_current_word_red"] / 65535.0
                g = preferences.prefs["color_current_word_green"] / 65535.0
                b = preferences.prefs["color_current_word_blue"] / 65535.0
                
                p = self.puzzle.grid.in_direction(sdir, sx, sy)
                q = self.puzzle.grid.in_direction(sdir, sx, sy, reverse=True)
                for cell in chain(p, q):
                    if (x, y) == cell:
                        self.puzzle.view.render_location(context, None, x, y, r, g, b)
                        break
        
        # selection cell                    
        if (x, y) == (sx, sy):
            r = preferences.prefs["color_primary_selection_red"] / 65535.0
            g = preferences.prefs["color_primary_selection_green"] / 65535.0
            b = preferences.prefs["color_primary_selection_blue"] / 65535.0
            self.puzzle.view.render_location(context, None, x, y, r, g, b)
                
        # current cell and symmetrical cells
        if self.current.x >= 0 and self.current.y >= 0:
            r = preferences.prefs["color_secondary_active_red"] / 65535.0
            g = preferences.prefs["color_secondary_active_green"] / 65535.0
            b = preferences.prefs["color_secondary_active_blue"] / 65535.0
            if (x, y) in self.apply_symmetry(self.current.x, self.current.y):
                self.puzzle.view.render_location(context, None, x, y, r, g, b)
                
            # draw current cell last to prevent
            # symmetrical cells from overlapping it
            r = preferences.prefs["color_primary_active_red"] / 65535.0
            g = preferences.prefs["color_primary_active_green"] / 65535.0
            b = preferences.prefs["color_primary_active_blue"] / 65535.0
            if (x, y) == (self.current.x, self.current.y):
                self.puzzle.view.render_location(context, None, x, y, r, g, b)
        
    def on_expose_event(self, drawing_area, event):
        if not self.editor_pattern or self.force_redraw:
            width = self.puzzle.view.properties.visual_width(True)
            height = self.puzzle.view.properties.visual_height(True)
            self.editor_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
            
            self.editor_pattern = cairo.SurfacePattern(self.editor_surface)
            self.puzzle.view.select_mode(constants.VIEW_MODE_EDITOR)
            context = cairo.Context(self.editor_surface)
            for x, y in self.puzzle.grid.cells():
                self.puzzle.view.render_bottom(context, x, y)
                self._render_editor_of_cell(context, x, y)
                self.puzzle.view.render_top(context, x, y)
            self.force_redraw = False
        context = self.drawing_area.window.cairo_create()
        context.set_source(self.editor_pattern)
        context.paint()
        return True
        
    def on_button_press_event(self, drawing_area, event):
        if 1 <= event.button <= 3:
            self.mouse_buttons_down[event.button - 1] = True
        drawing_area.grab_focus()
        prev_x = self.selection.x
        prev_y = self.selection.y
        x = self.puzzle.view.properties.screen_to_grid_x(event.x)
        y = self.puzzle.view.properties.screen_to_grid_y(event.y)
        
        if not self.puzzle.grid.is_valid(x, y):
            self.set_selection(-1, -1)
            return True
            
        if (event.state & gtk.gdk.SHIFT_MASK):
            if event.button in [1, 3] and not self.settings["locked_grid"]:
                self.transform_blocks(x, y, event.button == 1)
        else:
            if event.button == 1:
                # type is needed to assure rapid clicking
                # doesn't trigger it multiple times
                if (prev_x, prev_y) == (x, y) and event.type == gtk.gdk._2BUTTON_PRESS:
                    self.change_typing_direction()
                if self.puzzle.grid.is_available(x, y):
                    self.set_selection(x, y)
        return True
        
    def on_button_release_event(self, drawing_area, event):
        if 1 <= event.button <= 3:
            self.mouse_buttons_down[event.button - 1] = False
        return True
        
    def on_motion_notify_event(self, drawing_area, event):
        if event.is_hint:
            ex, ey, estate = event.window.get_pointer()
        else:
            ex, ey, estate = event.x, event.y, event.state
        cx = self.puzzle.view.properties.screen_to_grid_x(ex)
        cy = self.puzzle.view.properties.screen_to_grid_y(ey)
        prev_x = self.current.x
        prev_y = self.current.y
        self.current.x = cx
        self.current.y = cy

        if (prev_x, prev_y) != (cx, cy):
            c0 = self.apply_symmetry(prev_x, prev_y)
            c1 = self.apply_symmetry(cx, cy)
            self._render_cells(c0 + c1 + [(prev_x, prev_y), (cx, cy)])
        
        if (estate & gtk.gdk.SHIFT_MASK and not self.settings["locked_grid"]):
            if self.mouse_buttons_down[0]:
                self.transform_blocks(cx, cy, True)
            elif self.mouse_buttons_down[2]:
                self.transform_blocks(cx, cy, False)
        return True
        
    def refresh_clues(self):
        """Reload all the word/clue items and select the currently selected item."""
        x = self.selection.x
        y = self.selection.y
        direction = self.selection.direction
        
        p, q = self.puzzle.grid.get_start_word(x, y, direction)
        self.tools["clue"].load_items(self.puzzle)
        self.tools["clue"].select(p, q, direction)
        
    def refresh_words(self, force_refresh=False):
        """
        Update the list of words according to active constraints of letters
        and the current settings (e.g., show only words with intersections).
        """
        show_intersections = self.settings["show_intersecting_words"]
        x = self.selection.x
        y = self.selection.y
        result = None
        if self.puzzle.grid.is_available(x, y):
            parameters = self._get_search_parameters(x, y, self.selection.direction)
            length, constraints = parameters
            if length <= 1:
                # if this is the case, don't search and clear the words list
                pass
            elif len(constraints) != length:
                more = self._gather_all_constraints(x, y, self.selection.direction)
                wordlists = self.palabra_window.wordlists
                result = search_wordlists(wordlists, length, constraints, more)
        if result is not None:
            self.tools["word"].display(result, show_intersections)
        else:
            self.tools["word"].display([], show_intersections)
            
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
            x = self.selection.x
            y = self.selection.y
            direction = self.selection.direction
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
                x = self.selection.x
                y = self.selection.y
                direction = self.selection.direction
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
        
        x = self.selection.x
        y = self.selection.y
        direction = self.selection.direction
        for x, y, c in (old + new):
            self._render_cell(x, y)
            
    def clear_overlay(self):
        self._display_overlay([])
        
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
        symmetries = ["keep_horizontal_symmetry"
            ,"keep_vertical_symmetry"
            ,"keep_point_symmetry"]
        for key in symmetries:
            self.settings[key] = key in options
            
    def apply_symmetry(self, x, y):
        """Apply one or more symmetrical transforms to (x, y)."""
        cells = []
        if self.settings["keep_horizontal_symmetry"]:
            cells.append((x, self.puzzle.grid.height - 1 - y))
        if self.settings["keep_vertical_symmetry"]:
            cells.append((self.puzzle.grid.width - 1 - x, y))
        if ((self.settings["keep_horizontal_symmetry"]
            and self.settings["keep_vertical_symmetry"])
            or self.settings["keep_point_symmetry"]):
            p = self.puzzle.grid.width - 1 - x
            q = self.puzzle.grid.height - 1 - y
            cells.append((p, q))
        return cells

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
            x = self.selection.x
            y = self.selection.y
            direction = self.selection.direction
            self._clear_selection(x, y, direction)
            
            self.palabra_window.transform_grid(transform.modify_blocks, blocks=blocks)
            if (x, y, True) in blocks:
                self.set_selection(-1, -1)
                
            x = self.selection.x
            y = self.selection.y
            direction = self.selection.direction
            self._render_selection(x, y, direction)
            
            for x, y, status in blocks:
                self._render_cell(x, y)

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
            self.on_backspace()
        elif event.keyval == gtk.keysyms.Tab:
            self.change_typing_direction()
        elif event.keyval == gtk.keysyms.Home:
            self._on_jump_to_cell("start")
        elif event.keyval == gtk.keysyms.End:
            self._on_jump_to_cell("end")
        elif event.keyval == gtk.keysyms.Left:
            self.on_arrow_key(-1, 0)
        elif event.keyval == gtk.keysyms.Up:
            self.on_arrow_key(0, -1)
        elif event.keyval == gtk.keysyms.Right:
            self.on_arrow_key(1, 0)
        elif event.keyval == gtk.keysyms.Down:
            self.on_arrow_key(0, 1)
        elif event.keyval == gtk.keysyms.Delete and not self.settings["locked_grid"]:
            self.on_delete()
        elif not self.settings["locked_grid"]:
            self.on_typing(event.keyval)
        return True
        
    def on_backspace(self):
        """Remove a character in the current or previous cell."""
        x = self.selection.x
        y = self.selection.y
        direction = self.selection.direction
        
        # remove character in selected cell if it has one
        if self.puzzle.grid.get_char(x, y) != "":
            self.palabra_window.transform_grid(transform.modify_char
                , x=x
                , y=y
                , next_char="")
            self._render_cell(x, y)
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
            
    def on_arrow_key(self, dx, dy):
        """Move the selection to an available nearby cell."""
        nx = self.selection.x + dx
        ny = self.selection.y + dy
        if self.puzzle.grid.is_available(nx, ny):
            self.set_selection(nx, ny)
        
    def _on_jump_to_cell(self, target):
        """Jump to the start or end (i.e., first or last cell) of a word."""
        x = self.selection.x
        y = self.selection.y
        direction = self.selection.direction
        if target == "start":
            cell = self.puzzle.grid.get_start_word(x, y, direction)
        elif target == "end":
            cell = self.puzzle.grid.get_end_word(x, y, direction)
        self.set_selection(*cell)
        
    def on_delete(self):
        """Remove the character in the selected cell."""
        x = self.selection.x
        y = self.selection.y
        if self.puzzle.grid.get_char(x, y) != "":
            self.palabra_window.transform_grid(transform.modify_char
                , x=x
                , y=y
                , next_char="")
            self._render_cell(x, y)
        
    def on_typing(self, keyval):
        """Place an alphabetical character in the grid and move the selection."""
        if gtk.keysyms.a <= keyval <= gtk.keysyms.z:
            x = self.selection.x
            y = self.selection.y
            direction = self.selection.direction
            if self.puzzle.grid.is_valid(x, y):
                self.palabra_window.transform_grid(transform.modify_char
                        , x=x
                        , y=y
                        , next_char=chr(keyval).capitalize())
                nx = x + (1 if direction == "across" else 0)
                ny = y + (1 if direction == "down" else 0)
                if self.puzzle.grid.is_available(nx, ny):
                    self.selection.x = nx
                    self.selection.y = ny
                x = self.selection.x
                y = self.selection.y
                self._render_selection(x, y, direction)
                    
    def change_typing_direction(self):
        """Switch the typing direction to the other direction."""
        other = {"across": "down", "down": "across"}
        self.set_typing_direction(other[self.selection.direction])
        
    def refresh_visual_size(self):
        self.puzzle.view.refresh_visual_size(self.drawing_area)
        
    def get_selection(self):
        return (self.selection.x, self.selection.y)
        
    def set_selection(self, x, y):
        px = self.selection.x
        py = self.selection.y
        pdir = self.selection.direction
        if (x, y) == (px, py):
            return
        self._clear_selection(px, py, pdir)
        
        self.selection.x = x
        self.selection.y = y
        self._on_selection_change()
        self._render_selection(x, y, pdir)
        self.palabra_window.update_window()
        self.clear_overlay()
        
    def set_typing_direction(self, direction):
        px = self.selection.x
        py = self.selection.y
        pdir = self.selection.direction
        if pdir == direction:
            return
        self._clear_selection(px, py, pdir)
        
        self.selection.direction = direction
        self._on_selection_change()
        self._render_selection(px, py, direction)
        self.palabra_window.update_window()
        self.clear_overlay()
        
    def _on_selection_change(self):
        """
        Update the selection of the clue tool when the grid selection changes.
        """
        x = self.selection.x
        y = self.selection.y
        direction = self.selection.direction
        if x >= 0 and y >= 0:
            p, q = self.puzzle.grid.get_start_word(x, y, direction)
            self.tools["clue"].select(p, q, direction)
        else:
            self.tools["clue"].deselect()
