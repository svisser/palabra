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
    cells = [(x, y)] + apply_symmetry(grid, symms, x, y)
    return [(p, q, status) for p, q in cells if status != grid.data[q][p]["block"]]

def compute_word_cells(grid, word, x, y, d):
    """Compute the cells and the characters that are part of the overlay."""
    if word is None:
        return []
    p, q = grid.get_start_word(x, y, d)
    result = decompose_word(word, p, q, d)
    return [(x, y, c.upper()) for x, y, c in result if grid.data[y][x]["char"] == ""]

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

mouse_buttons_down = [False, False, False]

def configure_drawing_area(widget, events):
    widget.set_flags(gtk.CAN_FOCUS)
    widget.add_events(gtk.gdk.POINTER_MOTION_HINT_MASK)
    ids = []
    for k, e in events.items():
        if isinstance(e, tuple):
            ids.append(widget.connect(k, *e))
        else:
            ids.append(widget.connect(k, e))
    return ids
    
def cleanup_drawing_area(widget, ids):
    widget.unset_flags(gtk.CAN_FOCUS)
    for i in ids:
        widget.disconnect(i)

def compute_warnings_of_cells(grid, cells, settings):
    """Determine undesired cells."""
    lengths = {}
    starts = {}
    warn_unchecked = settings[constants.WARN_UNCHECKED]
    warn_consecutive = settings[constants.WARN_CONSECUTIVE]
    warn_two_letter = settings[constants.WARN_TWO_LETTER]
    check_count = grid.get_check_count
    width, height = grid.size
    if warn_unchecked or warn_consecutive:
        counts = grid.get_check_count_all()
    if warn_two_letter:
        get_start_word = grid.get_start_word
        in_direction = grid.in_direction
        word_length = grid.word_length
    for p, q in cells:
        if warn_unchecked:
            # Color cells that are unchecked. Isolated cells are also colored.
            if 0 <= counts[p, q] <= 1:
                yield p, q
                continue
        if warn_consecutive:
            # Color consecutive (two or more) unchecked cells.
            warn = False
            if 0 <= counts[p, q] <= 1:
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    if not (0 <= p + dx < width and 0 <= q + dy < height):
                        continue
                    if 0 <= counts[p + dx, q + dy] <= 1:
                        warn = True
                        break
            if warn:
                yield p, q
                continue
        if warn_two_letter:
            # Color words with length two.
            warn = False
            for d in ["across", "down"]:
                if (p, q, d) in starts:
                    sx, sy = starts[p, q, d]
                else:
                    sx, sy = get_start_word(p, q, d)
                    starts[p, q, d] = sx, sy
                    for zx, zy in in_direction(sx, sy, d):
                        starts[zx, zy, d] = sx, sy
                    lengths[sx, sy, d] = word_length(sx, sy, d)
                if lengths[sx, sy, d] == 2:
                    warn = True
                    break
            if warn:
                yield p, q
                continue

# cells = 1 cell or all cells of grid
def compute_editor_of_cell(cells, puzzle, e_settings):
    """Compute cells that have editor related colors."""
    grid = puzzle.grid
    selection = e_settings.selection
    current = e_settings.current
    symmetries = e_settings.settings["symmetries"]
    warnings = e_settings.warnings
    # warnings for undesired cells
    render = []
    for wx, wy in compute_warnings_of_cells(grid, cells, warnings):
        render.append((wx, wy, constants.COLOR_WARNING))
    # blacklist
    for p, q in cells:
        if False: # TODO until ready
            for bx, by, direction, length in self.blacklist:
                if direction == "across" and bx <= p < bx + length and by == q:
                    render.append((p, q, constants.COLOR_WARNING))
                elif direction == "down" and by <= q < by + length and bx == p:
                    render.append((p, q, constants.COLOR_WARNING))
    # selection line
    render.extend([(i, j, constants.COLOR_CURRENT_WORD) for i, j in grid.slot(*selection) if (i, j) in cells])
    cx, cy = current
    for p, q in cells:
        # selection cell
        if (p, q) == (selection.x, selection.y):
            render.append((p, q, constants.COLOR_PRIMARY_SELECTION))
        # current cell and symmetrical cells
        if 0 <= cx < grid.width and 0 <= cy < grid.height:
            if (p, q) in apply_symmetry(grid, symmetries, cx, cy):
                render.append((p, q, constants.COLOR_SECONDARY_ACTIVE))
            # draw current cell last to prevent
            # symmetrical cells from overlapping it
            if (p, q) == current:
                render.append((p, q, constants.COLOR_PRIMARY_ACTIVE))
    return render

def _render_cells(puzzle, cells, e_settings, drawing_area, editor=True):
    if not cells or not e_settings.surface:
        return
    view = puzzle.view
    view.select_mode(constants.VIEW_MODE_EDITOR)
    context = cairo.Context(e_settings.surface)
    cs = [c for c in cells if puzzle.grid.is_valid(*c)]
    view.render_bottom(context, cs)
    if editor:
        e_cells = compute_editor_of_cell(cs, puzzle, e_settings)
        render = []
        for x, y, code in e_cells:
            r, g, b = read_pref_color(code)
            render.append((x, y, r, g, b))
        view.render_locations(context, render)
    view.render_top(context, cs)
    context = drawing_area.window.cairo_create()
    context.set_source(e_settings.pattern)
    context.paint()

class EditorSettings:
    def __init__(self):
        self.surface = None
        self.pattern = None
        self.selection = Selection(-1, -1, "across")
        self.current = (-1, -1)
        self.settings = {
            "symmetries": constants.SYM_180
            , "locked_grid": False
        }
        self.warnings = {}
        for w in constants.WARNINGS:
            self.warnings[w] = False
e_settings = EditorSettings()
e_tools = {}

def on_button_release_event(drawing_area, event):
    if 1 <= event.button <= 3:
        mouse_buttons_down[event.button - 1] = False
    return True

# needed to capture the press of a tab button
# so focus won't switch to the toolbar
def on_key_press_event(drawing_area, event):
    return True

def on_key_release_event(drawing_area, event, window, puzzle, e_settings):
    # prevent conflicts with menu shortcut keys
    if ((event.state & gtk.gdk.SHIFT_MASK) or
        (event.state & gtk.gdk.CONTROL_MASK)):
        return True
    key = event.keyval
    grid = puzzle.grid
    if key == gtk.keysyms.BackSpace and not e_settings.settings["locked_grid"]:
        on_backspace(window, puzzle, e_settings)
    elif key == gtk.keysyms.Tab:
        set_selection(window, puzzle, e_settings, other_dir=True)
    elif key == gtk.keysyms.Home:
        cell = grid.get_cell_of_slot(e_settings.selection, "start")
        set_selection(window, puzzle, e_settings, *cell)
    elif key == gtk.keysyms.End:
        cell = grid.get_cell_of_slot(e_settings.selection, "end")
        set_selection(window, puzzle, e_settings, *cell)
    elif key == gtk.keysyms.Left:
        apply_selection_delta(window, puzzle, e_settings, -1, 0)
    elif key == gtk.keysyms.Up:
        apply_selection_delta(window, puzzle, e_settings, 0, -1)
    elif key == gtk.keysyms.Right:
        apply_selection_delta(window, puzzle, e_settings, 1, 0)
    elif key == gtk.keysyms.Down:
        apply_selection_delta(window, puzzle, e_settings, 0, 1)
    elif key == gtk.keysyms.Delete and not e_settings.settings["locked_grid"]:
        on_delete(window, puzzle, e_settings)
    elif not e_settings.settings["locked_grid"]:
        on_typing(window, puzzle, key, e_settings)
    return True

def on_typing(window, puzzle, keyval, e_settings):
    """Place an alphabetical character in the grid and move the selection."""
    valid = gtk.keysyms.a <= keyval <= gtk.keysyms.z or keyval == gtk.keysyms.period
    if not valid:
        return
    grid = puzzle.grid
    x, y, direction = e_settings.selection
    if not grid.is_valid(x, y):
        return
    if keyval == gtk.keysyms.period:
        r_transform_blocks(window, puzzle, e_settings, x, y, True)
    else:
        c = chr(keyval).capitalize()
        if c != grid.get_char(x, y):
            window.transform_grid(transform.modify_char
                    , x=x
                    , y=y
                    , next_char=c)
            #self._check_blacklist_for_cell(x, y)
    nx = x + (1 if direction == "across" else 0)
    ny = y + (1 if direction == "down" else 0)
    cells = [(x, y)]
    if grid.is_available(nx, ny):
        e_settings.selection = e_settings.selection._replace(x=nx, y=ny)
        cells += [(nx, ny)]
    _render_cells(puzzle, cells, e_settings, window.drawing_area)

def r_transform_blocks(window, puzzle, e_settings, x, y, status):
    """Place or remove a block at (x, y) and its symmetrical cells."""
    blocks = transform_blocks(puzzle.grid, e_settings.settings["symmetries"], x, y, status)
    if not blocks:
        return
    window.transform_grid(transform.modify_blocks, blocks=blocks)
    cells = [(x, y) for x, y, status in blocks]
    _render_cells(puzzle, cells, e_settings, window.drawing_area)

def on_delete(window, puzzle, e_settings):
    """Remove the character in the selected cell."""
    x, y = e_settings.selection.x, e_settings.selection.y
    if puzzle.grid.get_char(x, y) != "":
        window.transform_grid(transform.modify_char
            , x=x
            , y=y
            , next_char="")
        #self._check_blacklist_for_cell(x, y)
        _render_cells(puzzle, [(x, y)], e_settings, window.drawing_area)

def compute_selection(prev, x=None, y=None, direction=None, other_dir=False):
    if other_dir:
        direction = {"across": "down", "down": "across"}[prev.direction]
    nx = x if x is not None else prev[0]
    ny = y if y is not None else prev[1]
    ndir = direction if direction is not None else prev[2]
    return nx, ny, ndir

def set_selection(window, puzzle, e_settings
    , x=None
    , y=None
    , direction=None
    , full_update=True
    , other_dir=False
    , selection_changed=True):
    """
    Select (x, y), the direction or both.
    Use other_dir to switch the typing direction to the other direction.
    """
    prev = e_settings.selection
    nx, ny, ndir = compute_selection(prev, x, y, direction, other_dir)
    
    # update the selection of the clue tool when the grid selection changes
    grid = puzzle.grid
    clue_tool = e_tools["clue"]
    if grid.is_part_of_word(nx, ny, ndir):
        p, q = grid.get_start_word(nx, ny, ndir)
        clue_tool.select(p, q, ndir)
    else:
        clue_tool.deselect()
    if selection_changed:
        set_overlay(window, puzzle, e_settings, None)
    _render_cells(puzzle, grid.slot(*prev), e_settings, window.drawing_area, editor=False)
    e_settings.selection = e_settings.selection._replace(x=nx, y=ny, direction=ndir)
    _render_cells(puzzle, grid.slot(nx, ny, ndir), e_settings, window.drawing_area, editor=True)
    if full_update:
        window.update_window()

def set_overlay(window, puzzle, e_settings, word=None):
    """
    Display the word in the selected slot without storing it the grid.
    If the word is None, the overlay will be cleared.
    """
    x, y, d = e_settings.selection
    cells = compute_word_cells(puzzle.grid, word, x, y, d)
    old = puzzle.view.overlay
    puzzle.view.overlay = cells
    render = [(x, y) for x, y, c in (old + cells)]
    _render_cells(puzzle, render, e_settings, window.drawing_area)

def apply_selection_delta(window, puzzle, e_settings, dx, dy):
    """Move the selection to an available nearby cell."""
    nx, ny = e_settings.selection.x + dx, e_settings.selection.y + dy
    if puzzle.grid.is_available(nx, ny):
        set_selection(window, puzzle, e_settings, nx, ny)

def on_backspace(window, puzzle, e_settings):
    """Remove a character in the current or previous cell."""
    x, y, direction = e_settings.selection
    grid = puzzle.grid
    transform_grid = window.transform_grid
    modify_char = transform.modify_char
    
    # remove character in selected cell if it has one
    if grid.data[y][x]["char"] != "":
        transform_grid(modify_char, x=x, y=y, next_char="")
        #self._check_blacklist_for_cell(x, y)
        _render_cells(puzzle, [(x, y)], e_settings, window.drawing_area)
    else:
        # remove character in previous cell if needed and move selection
        if direction == "across":
            x -= 1
        elif direction == "down":
            y -=1
        if grid.is_available(x, y):
            if grid.data[y][x]["char"] != "":
                transform_grid(modify_char, x=x, y=y, next_char="")
            #self._check_blacklist_for_cell(x, y)
            set_selection(window, puzzle, e_settings, x, y)

def insert(window, grid, slot, word):
    """Insert a word in the selected slot."""
    x, y, d = slot
    if not grid.is_available(x, y):
        return
    cells = compute_word_cells(grid, word, x, y, d)
    if not cells:
        return
    window.transform_grid(transform.modify_chars, chars=cells)

def compute_highlights(grid, f=None, arg=None, clear=False):
    """Compute the cells to highlight according to the specified function."""
    cells = []
    if not clear:
        if f == "length":
            cells = get_length_slots(grid, arg)
        elif f == "char":
            cells = get_char_slots(grid, arg)
        elif f == "open":
            cells = get_open_slots(grid)
    return cells

def highlight_cells(window, puzzle, e_settings, f=None, arg=None, clear=False):
    """
    Highlight cells according to a specified function.
    Use clear=True to clear the highlights.
    """
    cells = compute_highlights(puzzle.grid, f, arg, clear)
    old = puzzle.view.highlights
    puzzle.view.highlights = cells
    render = list(set(expand_slots(old + cells)))
    _render_cells(puzzle, render, e_settings, window.drawing_area)
    return cells

class Editor(gtk.HBox):
    def __init__(self, palabra_window, drawing_area):
        gtk.HBox.__init__(self)
        self.palabra_window = palabra_window
        self.blacklist = []
        self.fill_options = {}
        events = {"expose_event": self.on_expose_event
            , "button_press_event": self.on_button_press_event
            , "button_release_event": on_button_release_event
            , "motion_notify_event": self.on_motion_notify_event
            , "key_press_event": on_key_press_event
            , "key_release_event": (on_key_release_event, self.palabra_window, self.puzzle, e_settings)
        }
        self.ids = configure_drawing_area(self.palabra_window.drawing_area, events)
        self.force_redraw = True
        
    def get_puzzle(self):
        return self.palabra_window.puzzle_manager.current_puzzle
        
    puzzle = property(get_puzzle)
    
    def _render_cells(self, cells, editor=True):
        _render_cells(self.puzzle, cells, e_settings, self.palabra_window.drawing_area, editor)
        
    def on_expose_event(self, drawing_area, event):
        """Render the main editing component."""
        if not e_settings.surface or self.force_redraw:
            width, height = self.puzzle.view.properties.visual_size(True)
            e_settings.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
            e_settings.pattern = cairo.SurfacePattern(e_settings.surface)
            # TODO should not be needed
            self.puzzle.view.grid = self.puzzle.grid
            self.force_redraw = False
            self._render_cells(list(self.puzzle.grid.cells()), editor=True)
        context = self.palabra_window.drawing_area.window.cairo_create()
        context.set_source(e_settings.pattern)
        context.paint()
        return True
        
    def on_button_press_event(self, drawing_area, event):
        if 1 <= event.button <= 3:
            mouse_buttons_down[event.button - 1] = True
        drawing_area.grab_focus()
        prev_x, prev_y = e_settings.selection.x, e_settings.selection.y
        x, y = self.puzzle.view.properties.screen_to_grid(event.x, event.y)
        
        if not self.puzzle.grid.is_valid(x, y):
            self.set_selection(-1, -1)
            return True
            
        if (event.state & gtk.gdk.SHIFT_MASK):
            if event.button in [1, 3] and not e_settings.settings["locked_grid"]:
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
                    mouse_buttons_down[2] = False
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
        
    def on_motion_notify_event(self, drawing_area, event):
        if event.is_hint:
            ex, ey, estate = event.window.get_pointer()
        else:
            ex, ey, estate = event.x, event.y, event.state
        props = self.puzzle.view.properties
        cx, cy = props.screen_to_grid(ex, ey)
        prev_x, prev_y = e_settings.current
        e_settings.current = (cx, cy)

        if (prev_x, prev_y) != (cx, cy):
            grid = self.puzzle.grid
            symms = e_settings.settings["symmetries"]
            c0 = apply_symmetry(grid, symms, prev_x, prev_y)
            c1 = apply_symmetry(grid, symms, cx, cy)
            self._render_cells(c0 + c1 + [(prev_x, prev_y), (cx, cy)])
        
        transform_blocks = self.transform_blocks
        if (estate & gtk.gdk.SHIFT_MASK and not e_settings.settings["locked_grid"]):
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
        return highlight_cells(self.palabra_window, self.puzzle, e_settings, f, arg, clear)
        
    def refresh_clues(self):
        """Reload all the word/clue items and select the currently selected item."""
        p, q = self.puzzle.grid.get_start_word(*e_settings.selection)
        e_tools["clue"].load_items(self.puzzle)
        e_tools["clue"].select(p, q, e_settings.selection[2])
        
    def refresh_words(self, force_refresh=False):
        """
        Update the list of words according to active constraints of letters
        and the current settings (e.g., show only words with intersections).
        """
        result = search(self.palabra_window.wordlists, self.puzzle.grid
            , e_settings.selection, force_refresh)
        e_tools["word"].display_words(result)
        
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
        if e_settings.settings["locked_grid"]:
            return
        insert(self.palabra_window, self.puzzle.grid, e_settings.selection, word)
            
    def set_overlay(self, word=None):
        """
        Display the word in the selected slot without storing it the grid.
        If the word is None, the overlay will be cleared.
        """
        set_overlay(self.palabra_window, self.puzzle, e_settings, word)
            
    def transform_blocks(self, x, y, status):
        """Place or remove a block at (x, y) and its symmetrical cells."""
        r_transform_blocks(self.palabra_window, self.puzzle, e_settings, x, y, status)
            
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
        self.palabra_window.drawing_area.set_size_request(*size)

    def set_selection(self
        , x=None
        , y=None
        , direction=None
        , full_update=True
        , other_dir=False
        , selection_changed=True):
        """
        Select (x, y), the direction or both.
        Use other_dir to switch the typing direction to the other direction.
        """
        set_selection(self.palabra_window, self.puzzle, e_settings, x, y, direction, full_update, other_dir, selection_changed)
        
    def get_selection(self):
        """Return the (x, y) of the selected cell."""
        return (e_settings.selection.x, e_settings.selection.y)
