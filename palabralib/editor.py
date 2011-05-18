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
import gtk
import pangocairo
import webbrowser
from collections import namedtuple
from itertools import chain

import action
from appearance import CellPropertiesDialog
import constants
from grid import Grid, decompose_word
from preferences import read_pref_color
import transform
from view import GridPreview, DEFAULTS_CELL
from word import (CWordList,
    search_wordlists,
    analyze_words,
)
import cPalabra

DEFAULT_FILL_OPTIONS = {
    constants.FILL_OPTION_START: constants.FILL_START_AT_AUTO
    , constants.FILL_OPTION_NICE: constants.FILL_NICE_FALSE
    , constants.FILL_OPTION_DUPLICATE: constants.FILL_DUPLICATE_FALSE
    , constants.FILL_NICE_COUNT: 0
}

Selection = namedtuple('Selection', ['x', 'y', 'direction'])
EditorAction = namedtuple('EditorAction', ['type', 'args'])

mouse_buttons_down = [False, False, False]

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

def compute_search_args(grid, slot, force=False):
    x, y, d = slot
    if not grid.is_available(x, y):
        return None
    p, q = grid.get_start_word(x, y, d)
    length = grid.word_length(p, q, d)
    if length <= 1:
        return None
    constraints = grid.gather_constraints(p, q, d)
    if len(constraints) == length and not force:
        return None
    more = grid.gather_all_constraints(x, y, d)
    return length, constraints, more

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
    """
    Return a grid with possibly the given words filled in.
    This is not intended as full-blown search so keep len(words) small.
    """ 
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
        elif f == "cells":
            cells = [(x, y, "across", 1) for x, y in arg]
        elif f == "slot":
            x, y, d = arg
            cells = [(x, y, d, grid.word_length(x, y, d))]
    return cells

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
    width, height = puzzle.grid.size
    cs = [(x, y) for x, y in cells if 0 <= x < width and 0 <= y < height]
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
    actions = determine_editor_actions(puzzle.grid, e_settings.selection, event.keyval)
    process_editor_actions(window, puzzle, e_settings, actions)
    return True

def determine_editor_actions(grid, selection, key):
    """
    Determine all actions that need to take place given the current grid,
    the current selection and the key that the user has pressed.
    """
    actions = []
    if key == gtk.keysyms.BackSpace:
        actions = on_backspace(grid, selection)
    elif key == gtk.keysyms.Tab:
        actions = [EditorAction("swapdir", None)]
    elif key == gtk.keysyms.Home:
        x, y = grid.get_cell_of_slot(selection, "start")
        actions = [EditorAction("selection", {'x': x, 'y': y})]
    elif key == gtk.keysyms.End:
        x, y = grid.get_cell_of_slot(selection, "end")
        actions = [EditorAction("selection", {'x': x, 'y': y})]
    elif key == gtk.keysyms.Left:
        actions = apply_selection_delta(grid, selection, -1, 0)
    elif key == gtk.keysyms.Up:
        actions = apply_selection_delta(grid, selection, 0, -1)
    elif key == gtk.keysyms.Right:
        actions = apply_selection_delta(grid, selection, 1, 0)
    elif key == gtk.keysyms.Down:
        actions = apply_selection_delta(grid, selection, 0, 1)
    elif key == gtk.keysyms.Delete:
        actions = on_delete(grid, selection)
    else:
        actions = on_typing(grid, key, selection)
    return actions
    
def process_editor_actions(window, puzzle, e_settings, actions):
    """
    Process all the editor actions and apply them to the grid and editor controls.
    """
    for a in actions:
        if a.type == "blocks":
            if e_settings.settings["locked_grid"]:
                continue
            x = a.args['x']
            y = a.args['y']
            status = a.args['status']
            r_transform_blocks(window, puzzle, e_settings, x, y, status)
        elif a.type == "char":
            if e_settings.settings["locked_grid"]:
                continue
            c = a.args['char']
            x = a.args['x']
            y = a.args['y']
            window.transform_grid(transform.modify_char, x=x, y=y, next_char=c)
        elif a.type == "chars":
            if e_settings.settings["locked_grid"]:
                continue
            cells = a.args['cells']
            window.transform_grid(transform.modify_chars, chars=cells)
        elif a.type == "selection":
            x = a.args['x']
            y = a.args['y']
            set_selection(window, puzzle, e_settings, x, y)
        elif a.type == "swapdir":
            set_selection(window, puzzle, e_settings, other_dir=True)
        elif a.type == "popup":
            x = a.args['x']
            y = a.args['y']
            event = a.args['event']
            _create_popup_menu(window, puzzle, event, x, y)

def on_typing(grid, keyval, selection):
    """Place an alphabetical character in the grid and move the selection."""
    valid = gtk.keysyms.a <= keyval <= gtk.keysyms.z or keyval == gtk.keysyms.period
    if not valid:
        return []
    x, y, direction = selection
    if not grid.is_available(x, y):
        return []
    actions = []
    if keyval == gtk.keysyms.period:
        actions.append(EditorAction("blocks", {'x': x, 'y': y, 'status': True}))
    else:
        c = chr(keyval).capitalize()
        if c != grid.get_char(x, y):
            actions.append(EditorAction("char", {'x': x, 'y': y, 'char': c}))
    dx = 1 if direction == "across" else 0
    dy = 1 if direction == "down" else 0
    nx, ny = x + dx, y + dy
    if grid.is_available(nx, ny):
        actions.append(EditorAction("selection", {'x': nx, 'y': ny}))
    return actions

def on_delete(grid, selection):
    """Remove the character in the selected cell."""
    x, y, d = selection
    if grid.get_char(x, y) != "":
        return [EditorAction("char", {'x': x, 'y': y, 'char': ''})]
    return []

def r_transform_blocks(window, puzzle, e_settings, x, y, status):
    """Place or remove a block at (x, y) and its symmetrical cells."""
    blocks = transform_blocks(puzzle.grid, e_settings.settings["symmetries"], x, y, status)
    if not blocks:
        return
    window.transform_grid(transform.modify_blocks, blocks=blocks)
    cells = [(x, y) for x, y, status in blocks]
    _render_cells(puzzle, cells, e_settings, window.drawing_area)

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
    # if selection really changed compared to previous one, clear overlay
    if selection_changed:
        set_overlay(window, puzzle, e_settings, None)
    e_settings.selection = e_settings.selection._replace(x=nx, y=ny, direction=ndir)
    if full_update:
        window.update_window()
    else:
        cells = chain(grid.slot(*prev), grid.slot(nx, ny, ndir))
        _render_cells(puzzle, cells, e_settings, window.drawing_area)

def set_overlay(window, puzzle, e_settings, word=None):
    """
    Display the word in the selected slot without storing it the grid.
    If the word is None, the overlay will be cleared.
    """
    if not puzzle.view.overlay and word is None:
        return
    x, y, d = e_settings.selection
    cells = compute_word_cells(puzzle.grid, word, x, y, d)
    old = puzzle.view.overlay
    puzzle.view.overlay = cells
    render = [(x, y) for x, y, c in (old + cells)]
    _render_cells(puzzle, render, e_settings, window.drawing_area)

def apply_selection_delta(grid, selection, dx, dy):
    """Move the selection to an available nearby cell."""
    x, y, d = selection
    nx, ny = x + dx, y + dy
    if grid.is_available(nx, ny):
        return [EditorAction("selection", {'x': nx, 'y': ny})]
    return []

def on_backspace(grid, selection):
    """Remove a character in the current or previous cell."""
    x, y, direction = selection
    if grid.data[y][x]["char"] != "":
        return [EditorAction("char", {'x': x, 'y': y, 'char': ''})]
    actions = []
    x -= (1 if direction == "across" else 0)
    y -= (1 if direction == "down" else 0)
    if grid.is_available(x, y):
        if grid.data[y][x]["char"] != "":
            actions.append(EditorAction("char", {'x': x, 'y': y, 'char': ''}))
        actions.append(EditorAction("selection", {'x': x, 'y': y}))
    return actions

def insert(grid, slot, word):
    """Insert a word in the selected slot."""
    x, y, d = slot
    if not grid.is_available(x, y):
        return []
    cells = compute_word_cells(grid, word, x, y, d)
    if not cells:
        return []
    return [EditorAction("chars", {'cells': cells})]

def highlight_cells(window, puzzle, f=None, arg=None, clear=False):
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
    
def on_button_press(grid, event, prev, next):
    prev_x, prev_y = prev
    x, y = next
    if not grid.is_valid(x, y):
        return [EditorAction("selection", {'x': -1, 'y': -1})]
    actions = []
    if (event.state & gtk.gdk.SHIFT_MASK):
        if event.button in [1, 3]:
            args = {'x': x, 'y': y, 'status': event.button == 1}
            actions.append(EditorAction("blocks", args))
    else:
        if event.button == 1:
            # type is needed to assure rapid clicking
            # doesn't trigger it multiple times
            if (prev_x, prev_y) == (x, y) and event.type == gtk.gdk._2BUTTON_PRESS:
                actions.append(EditorAction("swapdir", None))
            if grid.is_available(x, y):
                actions.append(EditorAction("selection", {'x': x, 'y': y}))
        elif event.button == 3:
            if grid.is_valid(x, y):
                actions.append(EditorAction("popup", {'event': event, 'x': x, 'y': y}))
                # popup menu right-click should not interfere with
                # normal editing controls
                mouse_buttons_down[2] = False
    return actions

def _create_popup_menu(window, puzzle, event, x, y):
    menu = gtk.Menu()
    update_status = window.update_status
    pop_status = window.pop_status
    def on_clear_slot_select(item, direction, x, y):
        grid = puzzle.grid
        sx, sy = grid.get_start_word(x, y, direction)
        msg = ''.join(["Clear all letters in the slot: "
            , str(grid.data[sy][sx]["number"]), " "
            , {"across": "across", "down": "down"}[direction]])
        update_status(constants.STATUS_MENU, msg)
    on_clear_slot_deselect = lambda item: pop_status(constants.STATUS_MENU)
    on_clear_slot = lambda item, d: clear_slot_of(window, puzzle.grid, x, y, d)
    def has_chars(x, y, direction):
        grid = puzzle.grid
        return any([grid.data[q][p]["char"] != ''
            for p, q in grid.slot(x, y, direction)])
    clearable = lambda slot: puzzle.grid.is_part_of_word(*slot) and has_chars(*slot)
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
        w = CellPropertiesDialog(window, props)
        w.show_all()
        if w.run() == gtk.RESPONSE_OK:
            puzzle.view.properties.update(x, y, w.gather_appearance().items())
            #self._render_cells([(x, y)])
        w.destroy()
    item = gtk.MenuItem("Properties")
    item.connect("activate", on_cell_properties)
    menu.append(item)
    menu.show_all()
    menu.popup(None, None, None, event.button, event.time)

def clear_slot_of(window, grid, x, y, direction):
    """Clear all letters of the slot in the specified direction
    that contains (x, y)."""
    chars = [(r, s, "") for r, s in grid.slot(x, y, direction)
        if grid.data[s][r]["char"] != '']
    if len(chars) > 0:
        window.transform_grid(transform.modify_chars, chars=chars)

def on_button_press_event(drawing_area, event, window, puzzle, e_settings):
    if 1 <= event.button <= 3:
        mouse_buttons_down[event.button - 1] = True
    drawing_area.grab_focus()
    prev_x, prev_y = e_settings.selection.x, e_settings.selection.y
    x, y = puzzle.view.properties.screen_to_grid(event.x, event.y)
    actions = on_button_press(puzzle.grid, event, (prev_x, prev_y), (x, y))
    process_editor_actions(window, puzzle, e_settings, actions)
    return True

class Editor:
    def __init__(self, window):
        self.window = window
        self.blacklist = []
        self.fill_options = {}
        self.EVENTS = {"expose_event": self.on_expose_event
            , "button_press_event": (on_button_press_event, self.window, self.puzzle, e_settings)
            , "button_release_event": on_button_release_event
            , "motion_notify_event": self.on_motion_notify_event
            , "key_press_event": on_key_press_event
            , "key_release_event": (on_key_release_event, self.window, self.puzzle, e_settings)
        }
        self.force_redraw = True
        
    def get_puzzle(self):
        return self.window.puzzle_manager.current_puzzle
        
    puzzle = property(get_puzzle)
    
    def _render_cells(self, cells, editor=True):
        _render_cells(self.puzzle, cells, e_settings, self.window.drawing_area, editor)
        
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
        context = self.window.drawing_area.window.cairo_create()
        context.set_source(e_settings.pattern)
        context.paint()
        return True
        
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
        args = compute_search_args(self.puzzle.grid, e_settings.selection, force_refresh)
        if args:
            result = search_wordlists(self.window.wordlists, *args)
        else:
            result = []
        e_tools["word"].display_words(result)
        
    def fill(self):
        for wlist in self.window.wordlists:
            results = fill(self.puzzle.grid, wlist.words, self.fill_options)
            self.window.transform_grid(transform.modify_chars, chars=results[0])
            break
            
    def clue(self, x, y, direction, key, value):
        """
        Update the clue data by creating or updating the latest undo action.
        """
        self.window.transform_clues(transform.modify_clue
                , x=x
                , y=y
                , direction=direction
                , key=key
                , value=value)
        
    def insert(self, word):
        """Insert a word in the selected slot."""
        actions = insert(self.puzzle.grid, e_settings.selection, word)
        process_editor_actions(self.window, self.puzzle, e_settings, actions)
            
    def set_overlay(self, word=None):
        """
        Display the word in the selected slot without storing it the grid.
        If the word is None, the overlay will be cleared.
        """
        set_overlay(self.window, self.puzzle, e_settings, word)
            
    def transform_blocks(self, x, y, status):
        """Place or remove a block at (x, y) and its symmetrical cells."""
        r_transform_blocks(self.window, self.puzzle, e_settings, x, y, status)
        
    def refresh_visual_size(self):
        # TODO fix design
        self.puzzle.view.grid = self.puzzle.grid
        self.puzzle.view.properties.grid = self.puzzle.grid
        size = self.puzzle.view.properties.visual_size()
        self.window.drawing_area.set_size_request(*size)

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
        set_selection(self.window, self.puzzle, e_settings, x, y, direction, full_update, other_dir, selection_changed)
        
    def get_selection(self):
        """Return the (x, y) of the selected cell."""
        return (e_settings.selection.x, e_settings.selection.y)
