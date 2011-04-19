# This file is part of Palabra
#
# Copyright (C) 2009 - 2011 Simeon Visser
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
import gobject
import gtk
import pangocairo
import webbrowser

import action
import constants
from files import get_real_filename
import preferences
import transform
from word import search_wordlists

class CellPropertiesDialog(gtk.Dialog):
    def __init__(self, palabra_window, properties):
        gtk.Dialog.__init__(self, u"Cell properties", palabra_window
            , gtk.DIALOG_MODAL)
        self.palabra_window = palabra_window
        self.set_size_request(384, 256)
        
        tabs = gtk.Notebook()
        tabs.append_page(self.create_general_tab(properties), gtk.Label(u"General"))
        tabs.append_page(self.create_appearance_tab(properties), gtk.Label(u"Appearance"))
        
        x, y = properties["cell"]
        title = ''.join(['Properties of cell ', str((x + 1, y + 1))])
        #self.set_title(title)
        label = gtk.Label()
        label.set_alignment(0, 0)
        label.set_markup(''.join(['<b>', title, '</b>']))
        
        hbox = gtk.VBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(9)
        #hbox.pack_start(label, False, False, 0)
        hbox.pack_start(tabs, True, True, 0)
        
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.add_button(gtk.STOCK_APPLY, gtk.RESPONSE_OK)
        self.vbox.add(hbox)
        
    def create_general_tab(self, properties):
        table = gtk.Table(1, 2, False)
        table.set_col_spacings(18)
        table.set_row_spacings(6)
        
        def create_row(table, title, value, x, y):
            label = gtk.Label()
            label.set_markup(title)
            label.set_alignment(0, 0)
            table.attach(label, x, x + 1, y, y + 1)
            label = gtk.Label(value)
            label.set_alignment(0, 0)
            table.attach(label, x + 1, x + 2, y, y + 1)
        
        x, y = properties["cell"]
        location = str((x + 1, y + 1))
        types = {"letter": u"Letter", "block": u"Block", "void": u"Void"}
        create_row(table, "Location", location, 0, 0)
        create_row(table, "Type", types[properties["type"]], 0, 1)
        content = u"(none)"
        if properties["type"] == "letter" and properties["content"]:
            content = properties["content"]
        create_row(table, "Content", content, 0, 2)

        main = gtk.VBox(False, 0)
        main.set_spacing(18)
        main.pack_start(table, False, False, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        hbox.pack_start(main, True, True, 0)
        return hbox
        
    def create_appearance_tab(self, properties):
        main = gtk.HBox(False, 0)
        main.set_spacing(18)
        main.pack_start(gtk.Label(u"TODO"), False, False, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        hbox.pack_start(main, True, True, 0)
        return hbox

class WordPropertiesDialog(gtk.Dialog):
    def __init__(self, palabra_window, properties):
        gtk.Dialog.__init__(self, u"Word properties", palabra_window
            , gtk.DIALOG_MODAL)
        self.palabra_window = palabra_window
        self.set_size_request(384, 256)
        
        label = gtk.Label()
        label.set_markup(''.join(['<b>', properties["word"], '</b>']))
        
        main = gtk.VBox(False, 0)
        main.set_spacing(18)
        main.pack_start(label, True, True, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        hbox.pack_start(main, True, True, 0)
        
        self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_ACCEPT)
        self.vbox.add(hbox)

class FillTool:
    def __init__(self, editor):
        self.editor = editor
        
    def create(self):
        return gtk.Label(u"Not yet implemented.")

class WordWidget(gtk.DrawingArea):
    def __init__(self, editor):
        super(WordWidget, self).__init__()
        self.STEP = 24
        self.selection = None
        self.editor = editor
        self.set_words([])
        self.set_flags(gtk.CAN_FOCUS)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.connect('expose_event', self.expose)
        self.connect("button_press_event", self.on_button_press)
        
    def set_words(self, words):
        self.words = words
        self.selection = None
        self.set_size_request(-1, self.STEP * len(self.words))
        self.queue_draw()
        
    def on_button_press(self, widget, event):
        offset = self.get_word_offset(event.y)
        if offset >= len(self.words):
            self.selection = None
            self.editor.set_overlay(None)
            return
        word = self.words[offset][0]
        if event.type == gtk.gdk._2BUTTON_PRESS:
            self.editor.insert(word)
            self.selection = None
            self.editor.set_overlay(None)
        else:
            self.selection = offset
            self.editor.set_overlay(word)
        self.queue_draw()
        return True
            
    def get_selected_word(self):
        if self.selection is None:
            return None
        return self.words[self.selection][0]
        
    def get_word_offset(self, y):
        return max(0, int(y / self.STEP)) 
        
    def expose(self, widget, event):
        ctx = widget.window.cairo_create()
        pcr = pangocairo.CairoContext(ctx)
        pcr_layout = pcr.create_layout()
        x, y, width, height = event.area
        ctx.set_source_rgb(65535, 65535, 65535)
        ctx.rectangle(*event.area)
        ctx.fill()
        ctx.set_source_rgb(0, 0, 0)
        offset = self.get_word_offset(y)
        n_rows = 30 #(height / self.STEP) + 1
        for i, (w, h) in enumerate(self.words[offset:offset + n_rows]):
            n = offset + i
            color = (0, 0, 0) if h else (65535.0 / 2, 65535.0 / 2, 65535.0 / 2)
            ctx.set_source_rgb(*[c / 65535.0 for c in color])
            markup = ['''<span font_desc="Monospace 12"''']
            if n == self.selection:
                ctx.set_source_rgb(65535, 0, 0)
                markup += [''' underline="double"''']
            markup += [">", w, "</span>"]
            pcr_layout.set_markup(''.join(markup))
            ctx.move_to(5, n * self.STEP)
            pcr.show_layout(pcr_layout)

class WordTool:
    def __init__(self, editor):
        self.editor = editor
        self.show_intersect = False
        self.show_used = True
    
    def create(self):
        img = gtk.Image()
        img.set_from_file(get_real_filename("resources/icon1.png"))
        def on_button_toggled(self, button):
            self.show_intersect = button.get_active()
            self.display_words()
        toggle_button = gtk.ToggleButton()
        toggle_button.set_property("image", img)
        toggle_button.set_tooltip_text(u"Show only words with intersecting words")
        toggle_button.connect("toggled", lambda b: on_button_toggled(self, b))
        
        img = gtk.Image()
        img.set_from_file(get_real_filename("resources/icon2.png"))
        def on_button2_toggled(self, button):
            self.show_used = not button.get_active()
            self.display_words()
        toggle_button2 = gtk.ToggleButton()
        toggle_button2.set_property("image", img)
        toggle_button2.set_tooltip_text(u"Show only unused words")
        toggle_button2.connect("toggled", lambda b: on_button2_toggled(self, b))
        
        buttons = gtk.HButtonBox()
        buttons.set_layout(gtk.BUTTONBOX_START)
        buttons.add(toggle_button)
        buttons.add(toggle_button2)
        
        self.main = gtk.VBox(False, 0)
        self.main.set_spacing(9)
        self.main.pack_start(buttons, False, False, 0)
        
        self.view = WordWidget(self.editor)
        sw = gtk.ScrolledWindow(None, None)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add_with_viewport(self.view)
        self.main.pack_start(sw, True, True, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(6)
        hbox.set_spacing(6)
        hbox.pack_start(self.main, True, True, 0)
        return hbox
        
    def display_words(self, words=None):
        if words is not None:
            self.words = words
        entries = []
        if not self.show_used:
            entries = [e.lower() for e in self.editor.puzzle.grid.entries() if constants.MISSING_CHAR not in e]
        shown = [row for row in self.words if 
            not ( (self.show_intersect and not row[1]) or (not self.show_used and row[0] in entries) ) ]
        self.view.set_words(shown)
        
    def get_selected_word(self):
        return self.view.get_selected_word()
        
    def deselect(self):
        self.view.selection = None

class Selection:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.direction = direction

def search(wordlists, grid, selection, force_refresh):
    x = selection.x
    y = selection.y
    dir = selection.direction
    if not grid.is_available(x, y) and not force_refresh:
        return []
    p, q = grid.get_start_word(x, y, dir)
    length = grid.word_length(p, q, dir)
    if length <= 1 and not force_refresh:
        return []
    constraints = grid.gather_constraints(p, q, dir)
    if len(constraints) == length and not force_refresh:
        return []
    more = grid.gather_all_constraints(x, y, dir)
    return search_wordlists(wordlists, length, constraints, more)

class Editor(gtk.HBox):
    def __init__(self, palabra_window, drawing_area):
        gtk.HBox.__init__(self)
        self.palabra_window = palabra_window
        self.drawing_area = drawing_area
        self.tools = {}
        self.editor_surface = None
        self.editor_pattern = None
        self.blacklist = []
        self.force_redraw = True
        if not palabra_window.editor_settings:
            sett = {}
            sett["symmetries"] = ["180_degree"]
            sett["locked_grid"] = False
            palabra_window.editor_settings = sett
        self.settings = palabra_window.editor_settings
        self.current = (-1, -1)
        self.selection = Selection(-1, -1, "across")
        self.mouse_buttons_down = [False, False, False]
        self.drawing_area.set_flags(gtk.CAN_FOCUS)
        events = {"expose_event": self.on_expose_event
            , "button_press_event": self.on_button_press_event
            , "button_release_event": self.on_button_release_event
            , "motion_notify_event": self.on_motion_notify_event
            , "key_press_event": self.on_key_press_event
            , "key_release_event": self.on_key_release_event
        }
        self.ids = [self.drawing_area.connect(*e) for e in events.items()]
        self.drawing_area.add_events(gtk.gdk.POINTER_MOTION_HINT_MASK)
        
    def get_puzzle(self):
        return self.palabra_window.puzzle_manager.current_puzzle
        
    puzzle = property(get_puzzle)
                
    def cleanup(self):
        self.drawing_area.unset_flags(gtk.CAN_FOCUS)
        for i in self.ids:
            self.drawing_area.disconnect(i)
    
    def _render_cells(self, cells, editor=True):
        if not cells:
            return
        self.puzzle.view.select_mode(constants.VIEW_MODE_EDITOR)
        if self.editor_surface:
            context = cairo.Context(self.editor_surface)
            cs = [c for c in cells if self.puzzle.grid.is_valid(*c)]
            self.puzzle.view.render_bottom(context, cs)
            if editor:
                self._render_editor_of_cell(context, cs)
            self.puzzle.view.render_top(context, cs)
            context = self.drawing_area.window.cairo_create()
            context.set_source(self.editor_pattern)
            context.paint()
        
    # cells = 1 cell or all cells of grid
    def _render_editor_of_cell(self, context, cells):
        """Render everything editor related colors for cells."""
        grid = self.puzzle.grid
        view = self.puzzle.view
        
        render = []
        for wx, wy in view.render_warnings_of_cells(context, cells):
            # warnings for undesired cells
            r = preferences.prefs["color_warning_red"] / 65535.0
            g = preferences.prefs["color_warning_green"] / 65535.0
            b = preferences.prefs["color_warning_blue"] / 65535.0
            render.append((wx, wy, r, g, b))
        
        for p, q in cells:
            # blacklist
            if view.settings["warn_blacklist"] and False: # TODO until ready
                for bx, by, direction, length in self.blacklist:
                    if direction == "across" and bx <= p < bx + length and by == q:
                        render.append((p, q, r, g, b))
                    elif direction == "down" and by <= q < by + length and bx == p:
                        render.append((p, q, r, g, b))
        
        sx = self.selection.x
        sy = self.selection.y
        sdir = self.selection.direction
        
        # selection line
        r = preferences.prefs["color_current_word_red"] / 65535.0
        g = preferences.prefs["color_current_word_green"] / 65535.0
        b = preferences.prefs["color_current_word_blue"] / 65535.0
        startx, starty = grid.get_start_word(sx, sy, sdir)
        for i, j in grid.in_direction(startx, starty, sdir):
            if (i, j) in cells:
                render.append((i, j, r, g, b))
        
        symms = list(self.apply_symmetry(*self.current))
        for p, q in cells:
            # selection cell
            if (p, q) == (sx, sy):
                r = preferences.prefs["color_primary_selection_red"] / 65535.0
                g = preferences.prefs["color_primary_selection_green"] / 65535.0
                b = preferences.prefs["color_primary_selection_blue"] / 65535.0
                render.append((p, q, r, g, b))
                
            # current cell and symmetrical cells
            cx, cy = self.current
            if 0 <= cx < grid.width and 0 <= cy < grid.height:
                r = preferences.prefs["color_secondary_active_red"] / 65535.0
                g = preferences.prefs["color_secondary_active_green"] / 65535.0
                b = preferences.prefs["color_secondary_active_blue"] / 65535.0
                if (p, q) in symms:
                    render.append((p, q, r, g, b))
                
                # draw current cell last to prevent
                # symmetrical cells from overlapping it
                r = preferences.prefs["color_primary_active_red"] / 65535.0
                g = preferences.prefs["color_primary_active_green"] / 65535.0
                b = preferences.prefs["color_primary_active_blue"] / 65535.0
                if (p, q) == self.current:
                    render.append((p, q, r, g, b))
        view.render_locations(context, render)
        
    def on_expose_event(self, drawing_area, event):
        """Render the main editing component."""
        if not self.editor_surface or self.force_redraw:
            width, height = self.puzzle.view.properties.visual_size(True)
            self.editor_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
            self.editor_pattern = cairo.SurfacePattern(self.editor_surface)
            # TODO should not be needed
            self.puzzle.view.grid = self.puzzle.grid
            self.force_redraw = False
            self._render_cells(list(self.puzzle.grid.cells()), editor=True)
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
        props = self.puzzle.view.properties
        cx = props.screen_to_grid_x(ex)
        cy = props.screen_to_grid_y(ey)
        prev_x, prev_y = self.current
        self.current = (cx, cy)

        apply_symmetry = self.apply_symmetry
        if (prev_x, prev_y) != (cx, cy):
            c0 = apply_symmetry(prev_x, prev_y)
            c1 = apply_symmetry(cx, cy)
            self._render_cells(c0 + c1 + [(prev_x, prev_y), (cx, cy)])
        
        mouse_buttons_down = self.mouse_buttons_down
        transform_blocks = self.transform_blocks
        if (estate & gtk.gdk.SHIFT_MASK and not self.settings["locked_grid"]):
            if mouse_buttons_down[0]:
                transform_blocks(cx, cy, True)
            elif mouse_buttons_down[2]:
                transform_blocks(cx, cy, False)
        return True
        
    def clear_slot_of(self, x, y, direction):
        """Clear all letters of the slot in the specified direction
        that contains (x, y)."""
        chars = [(r, s, "") for r, s in self.puzzle.grid.slot(x, y, direction)]
        if len(chars) > 0:
            self.palabra_window.transform_grid(transform.modify_chars, chars=chars)
        
    def highlight_words(self, length):
        """Highlight the words with the specified length."""
        new = []
        for d in ["across", "down"]:
            for n, x, y in self.puzzle.grid.words_by_direction(d):
                if self.puzzle.grid.word_length(x, y, d) == length:
                    new.append((x, y, d, length))
        self._render_highlighted_words(new)
        
    def highlight_chars(self, char):
        """Highlight all occurrences of the specified character."""
        new = []
        grid = self.puzzle.grid
        for x, y in grid.cells():
            if grid.data[y][x]["char"] == char:
                new.append((x, y, "across", 1))
        self._render_highlighted_words(new)
        
    def clear_highlighted_words(self): 
        """Clear all highlighted words, if there are any."""
        self._render_highlighted_words([])
        
    def _render_highlighted_words(self, new):
        """Render the cells of the highlighted words and the previous cells."""
        old = self.puzzle.view.highlights
        self.puzzle.view.highlights = new
        cells = []
        for x, y, d, l in (old + new):
            if d == "across":
                cells += [(x, y) for x in xrange(x, x + l)]
            elif d == "down":
                cells += [(x, y) for y in xrange(y, y + l)]
        self._render_cells(cells)
        
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
        result = search(self.palabra_window.wordlists, self.puzzle.grid
            , self.selection, force_refresh)
        self.tools["word"].display_words(result)
            
    def select(self, x, y, direction, full_update=True):
        """Select the word at (x, y, direction) in the grid."""
        self._set_full_selection(x, y, direction, full_update)
        
    def clue(self, x, y, direction, key, value):
        """
        Update the clue data by creating or updating the latest undo action.
        """
        self.palabra_window.transform_clues(transform.modify_clue
                , x=x
                , y=y
                , direction=direction
                , key=key
                , value=value)
        
    def insert(self, word):
        """Insert a word in the selected slot."""
        x = self.selection.x
        y = self.selection.y
        direction = self.selection.direction
        grid = self.puzzle.grid
        if grid.is_available(x, y):
            p, q = grid.get_start_word(x, y, direction)
            w = grid.decompose_word(word, p, q, direction)
            self._insert_word(w)
            
    def set_overlay(self, word):
        """
        Display the word in the selected slot without storing it the grid.
        If the word is None, the overlay will be cleared.
        """
        def render_overlay(new):
            """Display the (x, y, c) items in the grid's overlay."""
            old = self.puzzle.view.overlay
            self.puzzle.view.overlay = new
            self._render_cells([(x, y) for x, y, c in (old + new)])
        if word is None:
            render_overlay([])
            return
        x = self.selection.x
        y = self.selection.y
        direction = self.selection.direction
        grid = self.puzzle.grid
        p, q = grid.get_start_word(x, y, direction)
        result = grid.decompose_word(word, p, q, direction)
        overlay = [(x, y, c.upper()) for x, y, c in result
            if grid.data[y][x]["char"] == ""]
        render_overlay(overlay)
            
    def _insert_word(self, chars):
        """Insert a word by storing the list of (x, y, c) items in the grid."""
        if self.settings["locked_grid"]:
            return
        actual = [(x, y, c.upper()) for x, y, c in chars
            if self.puzzle.grid.get_char(x, y) != c.upper()]
        if len(actual) > 0:
            self.palabra_window.transform_grid(transform.modify_chars, chars=actual)
            
    def apply_symmetry(self, x, y):
        """Apply one or more symmetrical transforms to (x, y)."""
        grid = self.puzzle.grid
        if not grid.is_valid(x, y):
            return []
        cells = []
        width = grid.width
        height = grid.height
        symms = self.settings["symmetries"]
        if "horizontal" in symms:
            cells.append((x, height - 1 - y))
        if "vertical" in symms:
            cells.append((width - 1 - x, y))
        if (("horizontal" in symms and "vertical" in symms)
            or "180_degree" in symms
            or "90_degree" in symms
            or "diagonals" in symms):
            p = width - 1 - x
            q = height - 1 - y
            cells.append((p, q))
        if "diagonals" in symms:
            p = int((y / float(height - 1)) * (width - 1))
            q = int((x / float(width - 1)) * (height - 1))
            cells.append((p, q))
            r = width - 1 - p
            s = height - 1 - q
            cells.append((r, s))
        if "90_degree" in symms:
            cells.append((width - 1 - y, x))
            cells.append((y, height - 1 - x))
        return cells

    def transform_blocks(self, x, y, status):
        """Place or remove a block at (x, y) and its symmetrical cells."""
        grid = self.puzzle.grid
        if not grid.is_valid(x, y):
            return []
        
        # determine blocks that need to be modified
        blocks = []
        if status != grid.data[y][x]["block"]:
            blocks.append((x, y, status))
        for p, q in self.apply_symmetry(x, y):
            if status != grid.data[q][p]["block"]:
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
            
            self._render_cells([(x, y) for x, y, status in blocks])

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
        grid = self.puzzle.grid
        transform_grid = self.palabra_window.transform_grid
        modify_char = transform.modify_char
        
        # remove character in selected cell if it has one
        if grid.data[y][x]["char"] != "":
            transform_grid(modify_char, x=x, y=y, next_char="")
            self._check_blacklist_for_cell(x, y)
            self._render_cells([(x, y)])
        else:
            # remove character in previous cell if needed and move selection
            if direction == "across":
                x -= 1
            elif direction == "down":
                y -=1
            if grid.is_available(x, y):
                if grid.data[y][x]["char"] != "":
                    transform_grid(modify_char, x=x, y=y, next_char="")
                self._check_blacklist_for_cell(x, y)
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
        grid = self.puzzle.grid
        if target == "start":
            cell = grid.get_start_word(x, y, direction)
        elif target == "end":
            cell = grid.get_end_word(x, y, direction)
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
            self._check_blacklist_for_cell(x, y)
            self._render_cells([(x, y)])
        
    def on_typing(self, keyval):
        """Place an alphabetical character in the grid and move the selection."""
        if gtk.keysyms.a <= keyval <= gtk.keysyms.z or keyval == gtk.keysyms.period:
            x = self.selection.x
            y = self.selection.y
            direction = self.selection.direction
            if self.puzzle.grid.is_valid(x, y):
                if keyval == gtk.keysyms.period:
                    self.transform_blocks(x, y, True)
                else:
                    c = chr(keyval).capitalize()
                    if c != self.puzzle.grid.get_char(x, y):
                        self.palabra_window.transform_grid(transform.modify_char
                                , x=x
                                , y=y
                                , next_char=c)
                        self._check_blacklist_for_cell(x, y)
                nx = x + (1 if direction == "across" else 0)
                ny = y + (1 if direction == "down" else 0)
                cells = [(x, y)]
                if self.puzzle.grid.is_available(nx, ny):
                    self.selection.x = nx
                    self.selection.y = ny
                    cells += [(nx, ny)]
                x = self.selection.x
                y = self.selection.y
                self._render_cells(cells)
                
    def _check_blacklist_for_cell(self, x, y):
        """
        Check whether the cell (x, y) is part of a blacklisted word.
        The blacklist is updated accordingly.
        """
        return # TODO until ready
        def get_segment(direction, x, y, dx, dy):
            """Gather the content of the cells touching and including (x, y)."""
            segment = []
            for p, q in self.puzzle.grid.in_direction(x + dx, y + dy, direction):
                c = self.puzzle.grid.get_char(p, q)
                if not c:
                    break
                segment.append((p, q, c))
            segment.insert(0, (x, y, self.puzzle.grid.get_char(x, y)))
            for p, q in self.puzzle.grid.in_direction(x - dx, y - dy, direction, reverse=True):
                c = self.puzzle.grid.get_char(p, q)
                if not c:
                    break
                segment.insert(0, (p, q, c))
            return direction, segment
        def check_segment(direction, segment):
            """Determine the cells that need to be blacklisted."""
            result = []
            word = "".join([c.lower() if c else " " for x, y, c in segment])
            badwords = self.palabra_window.blacklist.get_substring_matches(word)
            for i in xrange(len(word)):
                for b in badwords:
                    if word[i:i + len(b)] == b:
                        p, q, c = segment[i]
                        result.append((p, q, direction, len(b)))
            return result
        def clear_blacklist(direction, segment):
            """Remove all blacklist entries related to cells in data."""
            remove = []
            for p, q, bdir, length in self.blacklist:
                for r, s, c in segment:
                    if (p, q, bdir) == (r, s, direction):
                        remove.append((p, q, bdir, length))
            for x in remove:
                self.blacklist.remove(x)
        across = get_segment("across", x, y, 1, 0)
        down = get_segment("down", x, y, 0, 1)
        for data in [across, down]:
            clear_blacklist(*data)
            self.blacklist.extend(check_segment(*data))
                    
    def change_typing_direction(self):
        """Switch the typing direction to the other direction."""
        d = {"across": "down", "down": "across"}[self.selection.direction]
        self._set_full_selection(direction=d)
        
    def refresh_visual_size(self):
        # TODO fix design
        self.puzzle.view.grid = self.puzzle.grid
        self.puzzle.view.properties.grid = self.puzzle.grid
        size = self.puzzle.view.properties.visual_size()
        self.drawing_area.set_size_request(*size)

    def _clear_selection(self, x, y, direction):
        """
        Clear the selection containing (x, y) in the specified direction.
        """
        self._render_selection(x, y, direction, editor=False)
        
    def _render_selection(self, x, y, direction, editor=True):
        """
        Render the selected cells containing (x, y) in the specified direction.
        """
        self._render_cells(self.puzzle.grid.slot(x, y, direction), editor=editor)
       
    def _set_full_selection(self, x=None, y=None, direction=None, full_update=True):
        """Select (x, y), the direction or both."""
        prev_x = self.selection.x
        prev_y = self.selection.y
        prev_dir = self.selection.direction
        
        # determine whether updating is needed
        has_xy = x is not None and y is not None
        has_dir = direction is not None
        if has_xy and not has_dir and (x, y) == (prev_x, prev_y):
            return
        if not has_xy and has_dir and direction == prev_dir:
            return
        if has_xy and has_dir and (x, y, direction) == (prev_x, prev_y, prev_dir):
            return
        
        # determine the next selection
        nx = x if x is not None else prev_x
        ny = y if y is not None else prev_y
        ndir = direction if direction is not None else prev_dir
        
        # update the selection of the clue tool when the grid selection changes
        grid = self.puzzle.grid
        clue_tool = self.tools["clue"]
        if grid.is_part_of_word(nx, ny, ndir):
            p, q = grid.get_start_word(nx, ny, ndir)
            clue_tool.select(p, q, ndir)
        else:
            clue_tool.deselect()
            
        self.set_overlay(None)
        self._clear_selection(prev_x, prev_y, prev_dir)
        self.selection.x = nx
        self.selection.y = ny
        self.selection.direction = ndir
        self._render_selection(nx, ny, ndir)
        if full_update:
            self.palabra_window.update_window()
        
    def set_selection(self, x, y, direction=None):
        """Select the specified cell (x, y)."""
        self._set_full_selection(x=x, y=y, direction=direction)
        
    def get_selection(self):
        """Return the (x, y) of the selected cell."""
        return (self.selection.x, self.selection.y)
