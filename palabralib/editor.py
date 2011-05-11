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
import copy
import gobject
import gtk
import pangocairo
import webbrowser
from collections import namedtuple

import action
from appearance import CellPropertiesDialog
import constants
from files import get_real_filename
from grid import Grid, decompose_word
from preferences import read_pref_color
import transform
from view import GridPreview, DEFAULTS_CELL
from word import CWordList, search_wordlists, analyze_words
import cPalabra

DEFAULT_FILL_OPTIONS = {
    constants.FILL_OPTION_START: constants.FILL_START_AT_AUTO
    , constants.FILL_OPTION_NICE: constants.FILL_NICE_FALSE
    , constants.FILL_OPTION_DUPLICATE: constants.FILL_DUPLICATE_FALSE
    , constants.FILL_NICE_COUNT: 0
}

def get_char_slots(grid, c):
    return [(x, y, "across", 1) for x, y in grid.cells() if grid.data[y][x]["char"] == c]
    
def get_length_slots(grid, length):
    cells = []
    for d in ["across", "down"]:
        for n, x, y in grid.words_by_direction(d):
            if grid.word_length(x, y, d) == length:
                cells.append((x, y, d, length))
    return cells
    
def get_open_slots(grid):
    return [(x, y, "across", 1) for x, y in grid.compute_open_squares()]
    
def expand_slots(slots):
    cells = []
    for x, y, d, l in slots:
        if d == "across":
            cells += [(x, y) for x in xrange(x, x + l)]
        elif d == "down":
            cells += [(x, y) for y in xrange(y, y + l)]
    return cells

def apply_symmetry(grid, symms, x, y):
    """Apply one or more symmetrical transforms to (x, y)."""
    if not grid.is_valid(x, y):
        return []
    cells = []
    width = grid.width
    height = grid.height
    if constants.SYM_HORIZONTAL in symms:
        cells.append((x, height - 1 - y))
    if constants.SYM_VERTICAL in symms:
        cells.append((width - 1 - x, y))
    if ((constants.SYM_HORIZONTAL in symms and constants.SYM_VERTICAL in symms)
        or constants.SYM_180 in symms
        or constants.SYM_90 in symms
        or constants.SYM_DIAGONALS in symms):
        p = width - 1 - x
        q = height - 1 - y
        cells.append((p, q))
    if constants.SYM_DIAGONALS in symms:
        p = int((y / float(height - 1)) * (width - 1))
        q = int((x / float(width - 1)) * (height - 1))
        cells.append((p, q))
        r = width - 1 - p
        s = height - 1 - q
        cells.append((r, s))
    if constants.SYM_90 in symms:
        cells.append((width - 1 - y, x))
        cells.append((y, height - 1 - x))
    return cells

def transform_blocks(grid, symms, x, y, status):
    """Determine cells that need to modified a block at (x, y) and its symmetrical cells."""
    if not grid.is_valid(x, y):
        return []
    blocks = []
    if status != grid.data[y][x]["block"]:
        blocks.append((x, y, status))
    for p, q in apply_symmetry(grid, symms, x, y):
        if status != grid.data[q][p]["block"]:
            blocks.append((p, q, status))
    return blocks

def compute_overlay(grid, word, x, y, d):
    if word is None:
        return []
    p, q = grid.get_start_word(x, y, d)
    result = decompose_word(word, p, q, d)
    return [(x, y, c.upper()) for x, y, c in result if grid.data[y][x]["char"] == ""]

def get_cell_of_slot(grid, slot, target):
    if target == "start":
        return grid.get_start_word(*slot)
    elif target == "end":
        return grid.get_end_word(*slot)
    return None
    
def compute_insert(grid, word, x, y, d):
    p, q = grid.get_start_word(x, y, d)
    chars = decompose_word(word, p, q, d)
    return [(x, y, c.upper()) for x, y, c in chars if grid.data[y][x]["char"] != c.upper()]

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
        if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
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

class FillTool:
    def __init__(self, editor):
        self.editor = editor
        self.starts = [
            (constants.FILL_START_AT_ZERO, "First slot")
            , (constants.FILL_START_AT_AUTO, "Suitably chosen slot")
        ]
        self.editor.fill_options.update(DEFAULT_FILL_OPTIONS)
        
    def create(self):
        main = gtk.VBox(False, 0)
        main.set_spacing(9)
        
        button = gtk.Button("Fill")
        button.connect("pressed", self.on_button_pressed)
        main.pack_start(button, False, False, 0)
        
        start_combo = gtk.combo_box_new_text()
        for i, (c, txt) in enumerate(self.starts):
            start_combo.append_text(txt)
            if c == self.editor.fill_options[constants.FILL_OPTION_START]:
                start_combo.set_active(i)
        def on_start_changed(combo):
            self.editor.fill_options[constants.FILL_OPTION_START] = self.starts[combo.get_active()][0]
        start_combo.connect("changed", on_start_changed)
        
        label = gtk.Label(u"Start filling from:")
        label.set_alignment(0, 0.5)
        main.pack_start(label, False, False, 0)
        main.pack_start(start_combo, False, False, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(6)
        hbox.set_spacing(6)
        hbox.pack_start(main, True, True, 0)
        return hbox
        
    def on_button_pressed(self, button):
        self.editor.fill()

def search(wordlists, grid, selection, force_refresh):
    x, y, d = selection
    if not grid.is_available(x, y) and not force_refresh:
        return []
    p, q = grid.get_start_word(x, y, d)
    length = grid.word_length(p, q, d)
    if length <= 1 and not force_refresh:
        return []
    constraints = grid.gather_constraints(p, q, d)
    if len(constraints) == length and not force_refresh:
        return []
    more = grid.gather_all_constraints(x, y, d)
    return search_wordlists(wordlists, length, constraints, more)
    
def fill(grid, words, fill_options):
    meta = []
    g_words = [i for i in grid.words(allow_duplicates=True, include_dir=True)]
    g_lengths = {}
    g_cs = {}
    for n, x, y, d in g_words:
        g_lengths[x, y, d] = grid.word_length(x, y, d)
        g_cs[x, y, d] = grid.gather_constraints(x, y, d)
    result = analyze_words(grid, g_words, g_cs, g_lengths, words)
    for n, x, y, d in g_words:
        d_i = 0 if d == "across" else 1
        l = g_lengths[x, y, d]
        cs = g_cs[x, y, d]
        meta.append((x, y, d_i, l, cs, result[x, y, d]))
    return cPalabra.fill(grid, words, meta, fill_options)

def attempt_fill(grid, words):
    """Return a grid with possibly the given words filled in."""
    clist = CWordList(words, index=constants.MAX_WORD_LISTS)
    options = {}
    options.update(DEFAULT_FILL_OPTIONS)
    options.update({
        constants.FILL_OPTION_NICE: constants.FILL_NICE_TRUE
        , constants.FILL_OPTION_DUPLICATE: constants.FILL_DUPLICATE_TRUE
        , constants.FILL_NICE_COUNT: len(words)
    })
    results = fill(grid, clist.words, options)
    if results:
        g = copy.deepcopy(grid)
        transform.modify_chars(g, chars=results[0])
        return g
    return grid

Selection = namedtuple('Selection', ['x', 'y', 'direction'])

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
        self.fill_options = {}
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
        
        # warnings for undesired cells
        render = []
        for wx, wy in view.render_warnings_of_cells(context, cells):
            r, g, b = read_pref_color("color_warning")
            render.append((wx, wy, r, g, b))
        
        # blacklist
        for p, q in cells:
            if view.settings["warn_blacklist"] and False: # TODO until ready
                for bx, by, direction, length in self.blacklist:
                    if direction == "across" and bx <= p < bx + length and by == q:
                        render.append((p, q, r, g, b))
                    elif direction == "down" and by <= q < by + length and bx == p:
                        render.append((p, q, r, g, b))
        
        # selection line
        sx, sy, sdir = self.selection
        r, g, b = read_pref_color("color_current_word")
        startx, starty = grid.get_start_word(sx, sy, sdir)
        for i, j in grid.in_direction(startx, starty, sdir):
            if (i, j) in cells:
                render.append((i, j, r, g, b))
        
        cx, cy = self.current
        symms = apply_symmetry(grid, self.settings["symmetries"], cx, cy)
        for p, q in cells:
            # selection cell
            if (p, q) == (sx, sy):
                r, g, b = read_pref_color("color_primary_selection")
                render.append((p, q, r, g, b))
                
            # current cell and symmetrical cells
            if 0 <= cx < grid.width and 0 <= cy < grid.height:
                if (p, q) in symms:
                    r, g, b = read_pref_color("color_secondary_active")
                    render.append((p, q, r, g, b))
                
                # draw current cell last to prevent
                # symmetrical cells from overlapping it
                if (p, q) == self.current:
                    r, g, b = read_pref_color("color_primary_active")
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
        x, y = self.puzzle.view.properties.screen_to_grid(event.x, event.y)
        
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
                    self.set_selection(other_dir=True)
                if self.puzzle.grid.is_available(x, y):
                    self.set_selection(x, y)
            elif event.button == 3:
                if self.puzzle.grid.is_valid(x, y):
                    self._create_popup_menu(event, x, y)
                    # popup menu right-click should not interfere with
                    # normal editing controls
                    self.mouse_buttons_down[2] = False
        return True
    
    def _create_popup_menu(self, event, x, y):
        menu = gtk.Menu()
        update_status = self.palabra_window.update_status
        pop_status = self.palabra_window.pop_status
        def on_clear_slot_select(item, direction, x, y):
            grid = self.puzzle.grid
            sx, sy = grid.get_start_word(x, y, direction)
            msg = ''.join(["Clear all letters in the slot: "
                , str(grid.data[sy][sx]["number"]), " "
                , {"across": "across", "down": "down"}[direction]])
            update_status(constants.STATUS_MENU, msg)
        on_clear_slot_deselect = lambda item: pop_status(constants.STATUS_MENU)
        on_clear_slot = lambda item, d: self.clear_slot_of(x, y, d)
        def has_chars(x, y, direction):
            grid = self.puzzle.grid
            return any([grid.data[q][p]["char"] != ''
                for p, q in grid.slot(x, y, direction)])
        clearable = lambda slot: self.puzzle.grid.is_part_of_word(*slot) and has_chars(*slot)
        item = gtk.MenuItem("Clear across slot")
        item.connect("activate", on_clear_slot, "across")
        item.connect("select", on_clear_slot_select, "across", x, y)
        item.connect("deselect", on_clear_slot_deselect)
        item.set_sensitive(clearable((x, y, "across")))
        menu.append(item)
        item = gtk.MenuItem("Clear down slot")
        item.connect("activate", on_clear_slot, "down")
        item.connect("select", on_clear_slot_select, "down", x, y)
        item.connect("deselect", on_clear_slot_deselect)
        item.set_sensitive(clearable((x, y, "down")))
        menu.append(item)
        menu.append(gtk.SeparatorMenuItem())
        def on_cell_properties(item):
            puzzle = self.puzzle
            grid = puzzle.grid
            def determine_type(c):
                if grid.is_block(*c):
                    return "block"
                elif grid.is_void(*c):
                    return "void"
                return "letter"
            props = {"cell": (x, y), "grid": grid, "defaults": {}}
            for k in DEFAULTS_CELL:
                props[k] = puzzle.view.properties.style(x, y)[k]
                props["defaults"][k] = puzzle.view.properties.style()[k]
            w = CellPropertiesDialog(self.palabra_window, props)
            w.show_all()
            if w.run() == gtk.RESPONSE_OK:
                puzzle.view.properties.update(x, y, w.gather_appearance().items())
                self._render_cells([(x, y)])
            w.destroy()
        item = gtk.MenuItem("Properties")
        item.connect("activate", on_cell_properties)
        menu.append(item)
        menu.show_all()
        menu.popup(None, None, None, event.button, event.time)
        
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
        cx, cy = props.screen_to_grid(ex, ey)
        prev_x, prev_y = self.current
        self.current = (cx, cy)

        if (prev_x, prev_y) != (cx, cy):
            grid = self.puzzle.grid
            symms = self.settings["symmetries"]
            c0 = apply_symmetry(grid, symms, prev_x, prev_y)
            c1 = apply_symmetry(grid, symms, cx, cy)
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
        grid = self.puzzle.grid
        chars = [(r, s, "") for r, s in grid.slot(x, y, direction)
            if grid.data[s][r]["char"] != '']
        if len(chars) > 0:
            self.palabra_window.transform_grid(transform.modify_chars, chars=chars)
            
    def highlight_cells(self, f=None, arg=None, clear=False):
        """
        Highlight cells according to a specified function.
        Use clear=True to clear the highlights.
        """
        cells = []
        if not clear:
            grid = self.puzzle.grid
            if f == "length":
                cells = get_length_slots(grid, arg)
            elif f == "char":
                cells = get_char_slots(grid, arg)
            elif f == "open":
                cells = get_open_slots(grid)
        old = self.puzzle.view.highlights
        self.puzzle.view.highlights = cells
        self._render_cells(list(set(expand_slots(old + cells))))
        return cells
        
    def refresh_clues(self):
        """Reload all the word/clue items and select the currently selected item."""
        p, q = self.puzzle.grid.get_start_word(*self.selection)
        self.tools["clue"].load_items(self.puzzle)
        self.tools["clue"].select(p, q, self.selection[2])
        
    def refresh_words(self, force_refresh=False):
        """
        Update the list of words according to active constraints of letters
        and the current settings (e.g., show only words with intersections).
        """
        result = search(self.palabra_window.wordlists, self.puzzle.grid
            , self.selection, force_refresh)
        self.tools["word"].display_words(result)
        
    def fill(self):
        for path, wordlist in self.palabra_window.wordlists.items():
            results = fill(self.puzzle.grid, wordlist.words, self.fill_options)
            self.palabra_window.transform_grid(transform.modify_chars, chars=results[0])
            break
            
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
        if self.settings["locked_grid"]:
            return
        x, y, d = self.selection
        grid = self.puzzle.grid
        if not grid.is_available(x, y):
            return
        cells = compute_insert(grid, word, x, y, d)
        if not cells:
            return
        self.palabra_window.transform_grid(transform.modify_chars, chars=cells)
            
    def set_overlay(self, word=None):
        """
        Display the word in the selected slot without storing it the grid.
        If the word is None, the overlay will be cleared.
        """
        x, y, d = self.selection
        cells = compute_overlay(self.puzzle.grid, word, x, y, d)
        old = self.puzzle.view.overlay
        self.puzzle.view.overlay = cells
        self._render_cells([(x, y) for x, y, c in (old + cells)])
            
    def transform_blocks(self, x, y, status):
        """Place or remove a block at (x, y) and its symmetrical cells."""
        blocks = transform_blocks(self.puzzle.grid, self.settings["symmetries"], x, y, status)
        if not blocks:
            return
        self.palabra_window.transform_grid(transform.modify_blocks, blocks=blocks)
        if (self.selection.x, self.selection.y, True) in blocks:
            self.set_selection(-1, -1)
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
        key = event.keyval
        grid = self.puzzle.grid
        if key == gtk.keysyms.BackSpace and not self.settings["locked_grid"]:
            self.on_backspace()
        elif key == gtk.keysyms.Tab:
            self.set_selection(other_dir=True)
        elif key == gtk.keysyms.Home:
            self.set_selection(*get_cell_of_slot(grid, self.selection, "start"))
        elif key == gtk.keysyms.End:
            self.set_selection(*get_cell_of_slot(grid, self.selection, "end"))
        elif key == gtk.keysyms.Left:
            self.on_arrow_key(-1, 0)
        elif key == gtk.keysyms.Up:
            self.on_arrow_key(0, -1)
        elif key == gtk.keysyms.Right:
            self.on_arrow_key(1, 0)
        elif key == gtk.keysyms.Down:
            self.on_arrow_key(0, 1)
        elif key == gtk.keysyms.Delete and not self.settings["locked_grid"]:
            self.on_delete()
        elif not self.settings["locked_grid"]:
            self.on_typing(key)
        return True
        
    def on_backspace(self):
        """Remove a character in the current or previous cell."""
        x, y, direction = self.selection
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
        nx, ny = self.selection.x + dx, self.selection.y + dy
        if self.puzzle.grid.is_available(nx, ny):
            self.set_selection(nx, ny)
        
    def on_delete(self):
        """Remove the character in the selected cell."""
        x, y = self.selection.x, self.selection.y
        if self.puzzle.grid.get_char(x, y) != "":
            self.palabra_window.transform_grid(transform.modify_char
                , x=x
                , y=y
                , next_char="")
            self._check_blacklist_for_cell(x, y)
            self._render_cells([(x, y)])
        
    def on_typing(self, keyval):
        """Place an alphabetical character in the grid and move the selection."""
        valid = gtk.keysyms.a <= keyval <= gtk.keysyms.z or keyval == gtk.keysyms.period
        if not valid:
            return
        x, y, direction = self.selection
        grid = self.puzzle.grid
        if not grid.is_valid(x, y):
            return
        if keyval == gtk.keysyms.period:
            self.transform_blocks(x, y, True)
        else:
            c = chr(keyval).capitalize()
            if c != grid.get_char(x, y):
                self.palabra_window.transform_grid(transform.modify_char
                        , x=x
                        , y=y
                        , next_char=c)
                self._check_blacklist_for_cell(x, y)
        nx = x + (1 if direction == "across" else 0)
        ny = y + (1 if direction == "down" else 0)
        cells = [(x, y)]
        if grid.is_available(nx, ny):
            self.selection = self.selection._replace(x=nx, y=ny)
            cells += [(nx, ny)]
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
        
    def refresh_visual_size(self):
        # TODO fix design
        self.puzzle.view.grid = self.puzzle.grid
        self.puzzle.view.properties.grid = self.puzzle.grid
        size = self.puzzle.view.properties.visual_size()
        self.drawing_area.set_size_request(*size)

    def set_selection(self, x=None, y=None, direction=None, full_update=True, other_dir=False):
        """
        Select (x, y), the direction or both.
        Use other_dir to switch the typing direction to the other direction.
        """
        if other_dir:
            direction = {"across": "down", "down": "across"}[self.selection.direction]
        prev = self.selection
        
        # determine whether updating is needed
        has_xy = x is not None and y is not None
        has_dir = direction is not None
        if has_xy and not has_dir and (x, y) == (prev[0], prev[1]):
            return
        if not has_xy and has_dir and direction == prev[2]:
            return
        if has_xy and has_dir and (x, y, direction) == prev:
            return
        
        # determine the next selection
        nx = x if x is not None else prev[0]
        ny = y if y is not None else prev[1]
        ndir = direction if direction is not None else prev[2]
        
        # update the selection of the clue tool when the grid selection changes
        grid = self.puzzle.grid
        clue_tool = self.tools["clue"]
        if grid.is_part_of_word(nx, ny, ndir):
            p, q = grid.get_start_word(nx, ny, ndir)
            clue_tool.select(p, q, ndir)
        else:
            clue_tool.deselect()
        self.set_overlay(None)
        self._render_cells(self.puzzle.grid.slot(*prev), editor=False)
        self.selection = self.selection._replace(x=nx, y=ny, direction=ndir)
        self._render_cells(self.puzzle.grid.slot(nx, ny, ndir), editor=True)
        if full_update:
            self.palabra_window.update_window()
        
    def get_selection(self):
        """Return the (x, y) of the selected cell."""
        return (self.selection.x, self.selection.y)
