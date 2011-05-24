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
import operator
import os
import pango

import constants
from editor import attempt_fill
from files import read_containers, get_real_filename
import grid
from grid import Grid
from pattern import GridEditor
import preferences
from view import GridPreview, GridView

class SizeComponent(gtk.VBox):
    def __init__(self, title=None, callback=None):
        gtk.VBox.__init__(self)
        
        self.callback = callback
        
        size_vbox = gtk.VBox(False, 0)
        
        initial_width = preferences.prefs[constants.PREF_INITIAL_WIDTH]
        initial_height = preferences.prefs[constants.PREF_INITIAL_HEIGHT]
        
        adj = gtk.Adjustment(initial_width
            , constants.MINIMUM_WIDTH, constants.MAXIMUM_WIDTH, 1, 0, 0)
        self.width_spinner = gtk.SpinButton(adj, 0.0, 0)
        self.width_spinner.connect("value-changed", self.on_spinner_changed)
        adj = gtk.Adjustment(initial_height
            , constants.MINIMUM_WIDTH, constants.MAXIMUM_WIDTH, 1, 0, 0)
        self.height_spinner = gtk.SpinButton(adj, 0.0, 0)
        self.height_spinner.connect("value-changed", self.on_spinner_changed)
        self.suppress_spinner = False
        
        spinners = gtk.HBox(False, 0)
        
        spinners.pack_start(gtk.Label("Columns:"), False, False, 6)
        spinners.pack_start(self.width_spinner, False, False, 6)
        spinners.pack_start(gtk.Label("Rows:"), False, False, 6)
        spinners.pack_start(self.height_spinner, False, False, 6)
        size_vbox.pack_start(spinners, True, True, 0)
        
        size_table = gtk.Table(3, 4)
        size_table.set_row_spacings(3)
        size_table.set_col_spacings(12)
        
        button = gtk.RadioButton(None, "9 x 9")
        button.set_active(initial_width == 9 and initial_height == 9)
        button.connect("toggled", self.on_size_change, 9)
        size_table.attach(button, 0, 1, 0, 1)
        
        button = gtk.RadioButton(button, "11 x 11")
        button.set_active(initial_width == 11 and initial_height == 11)
        button.connect("toggled", self.on_size_change, 11)
        size_table.attach(button, 0, 1, 1, 2)
        
        button = gtk.RadioButton(button, "13 x 13")
        button.set_active(initial_width == 13 and initial_height == 13)
        button.connect("toggled", self.on_size_change, 13)
        size_table.attach(button, 0, 1, 2, 3)
        
        button = gtk.RadioButton(button, "15 x 15")
        button.set_active(initial_width == 15 and initial_height == 15)
        button.connect("toggled", self.on_size_change, 15)
        size_table.attach(button, 1, 2, 0, 1)
        
        button = gtk.RadioButton(button, "17 x 17")
        button.set_active(initial_width == 17 and initial_height == 17)
        button.connect("toggled", self.on_size_change, 17)
        size_table.attach(button, 1, 2, 1, 2)
        
        button = gtk.RadioButton(button, "19 x 19")
        button.set_active(initial_width == 19 and initial_height == 19)
        button.connect("toggled", self.on_size_change, 19)
        size_table.attach(button, 1, 2, 2, 3)
        
        button = gtk.RadioButton(button, "21 x 21")
        button.set_active(initial_width == 21 and initial_height == 21)
        button.connect("toggled", self.on_size_change, 21)
        size_table.attach(button, 2, 3, 0, 1)
        
        button = gtk.RadioButton(button, "23 x 23")
        button.set_active(initial_width == 23 and initial_height == 23)
        button.connect("toggled", self.on_size_change, 23)
        size_table.attach(button, 2, 3, 1, 2)
        
        button = gtk.RadioButton(button, "25 x 25")
        button.set_active(initial_width == 25 and initial_height == 25)
        button.connect("toggled", self.on_size_change, 25)
        size_table.attach(button, 2, 3, 2, 3)
        
        button = gtk.RadioButton(button, "27 x 27")
        button.set_active(initial_width == 27 and initial_height == 27)
        button.connect("toggled", self.on_size_change, 27)
        size_table.attach(button, 3, 4, 0, 1)
        
        button = gtk.RadioButton(button, "29 x 29")
        button.set_active(initial_width == 29 and initial_height == 29)
        button.connect("toggled", self.on_size_change, 29)
        size_table.attach(button, 3, 4, 1, 2)
        
        button = gtk.RadioButton(button, "31 x 31")
        button.set_active(initial_width == 31 and initial_height == 31)
        button.connect("toggled", self.on_size_change, 31)
        size_table.attach(button, 3, 4, 2, 3)
        
        size_vbox.pack_start(size_table, False, False, 6)
        
        align = gtk.Alignment(0, 0)
        align.set_padding(0, 0, 12, 0)
        align.add(size_vbox)
        
        if title is not None:
            label = gtk.Label()
            label.set_alignment(0, 0)
            label.set_markup(title)
            self.pack_start(label, False, False, 6)
        self.pack_start(align, False, False, 0)
        
    def on_spinner_changed(self, widget, data=None):
        if not self.suppress_spinner:
            self.perform_callback()
        
    def on_size_change(self, widget, data=None):
        if widget.get_active() == 1:
            self.suppress_spinner = True
            self.width_spinner.set_value(data)
            self.height_spinner.set_value(data)
            self.suppress_spinner = False
            self.perform_callback()
                
    def perform_callback(self):
        if self.callback is not None:
            width = self.width_spinner.get_value_as_int()
            height = self.height_spinner.get_value_as_int()
            self.callback(width, height)
            
    def get_size(self):
        width = self.width_spinner.get_value_as_int()
        height = self.height_spinner.get_value_as_int()
        return (width, height)

class SizeWindow(gtk.Dialog):
    def __init__(self, parent, puzzle):
        flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                   gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
        super(SizeWindow, self).__init__("Resize grid", parent, flags, buttons)
        
        self.set_size_request(424, -1)
        self.puzzle = puzzle
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        
        main = gtk.VBox(False, 0)
        main.set_spacing(18)
        
        hbox.pack_start(main, True, True, 0)
        
        self.size_component = SizeComponent()
        
        main.pack_start(self.size_component, False, False, 0)
        
        self.vbox.pack_start(hbox, False, False, 0)
        
    def get_size(self):
        return self.size_component.get_size()

class FindPatternDialog(gtk.Dialog):
    def __init__(self, parent):
        gtk.Dialog.__init__(self, u"Find grids", parent, gtk.DIALOG_MODAL)
        
        self.text = gtk.TextView()
        self.text.set_size_request(320, 320)
        self.text.modify_font(pango.FontDescription("Monospace 12"))
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        
        main = gtk.VBox(False, 0)
        main.set_spacing(18)
        main.pack_start(gtk.Label(u"Type a small number of words that you wish to fit into the grid:"), False, False, 0)
        main.pack_start(self.text, True, True, 0)
        
        hbox.pack_start(main, True, True, 0)
        
        self.vbox.pack_start(hbox, False, False, 0)
        
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)

class NewWindow(gtk.Dialog):
    def __init__(self, palabra_window):
        flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
        super(NewWindow, self).__init__("New puzzle", palabra_window, flags, buttons)
        
        self.showing_pattern = False
        
        self.preview = GridPreview()
        self.preview.set_size_request(300, 400)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        
        options_vbox = gtk.VBox(False, 0)
        hbox.pack_start(options_vbox, True, True, 0)
        hbox.pack_start(self.preview, True, True, 0)
        
        self.vbox.pack_start(hbox, True, True, 0)
        
        self.size_component = SizeComponent(
            title=u"<b>Dimensions</b>"
            , callback=self.load_empty_grid)
        options_vbox.pack_start(self.size_component, False, False, 0)
        
        label = gtk.Label()
        label.set_alignment(0, 0)
        label.set_markup(u"<b>Grids</b>")
        options_vbox.pack_start(label, False, False, 6)
        
        # display_string grid
        self.store = gtk.ListStore(str, gobject.TYPE_PYOBJECT)
        self.tree = gtk.TreeView(self.store)
        self.tree.set_headers_visible(False)
        self.tree.get_selection().connect("changed", self.on_pattern_changed)
        
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("")
        column.pack_start(cell, True)
        column.set_attributes(cell, text=0)
        self.tree.append_column(column)
        
        window = gtk.ScrolledWindow(None, None)
        window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        window.add(self.tree)
        
        self.clear_button = gtk.Button("Clear grid")
        self.clear_button.connect("clicked", self.clear_pattern)
        
        self.files = []
        for f in constants.STANDARD_PATTERN_FILES + preferences.prefs["pattern_files"]:
            self.files.append(get_real_filename(f))
        
        self.patterns = []
        for f, meta, data in palabra_window.patterns:
            if f is not None:
                self.patterns.append((f, meta, [p.grid for p in data]))
        
        file_combo = gtk.combo_box_new_text()
        file_combo.append_text("All files")
        file_combo.set_active(0)
        for path, metadata, data in self.patterns:
            filename = path[path.rfind(os.sep) + 1:]
            caption = metadata["title"] if "title" in metadata else filename
            file_combo.append_text(caption)
        file_combo.connect("changed", self.on_file_changed)
        
        patterns_vbox = gtk.VBox(False, 0)
        
        files_hbox = gtk.HBox(False, 0)
        files_hbox.pack_start(gtk.Label(u"Show grids from: "), False, False, 0)
        align = gtk.Alignment(0, 0.5, 0, 0)
        align.add(file_combo)
        files_hbox.pack_start(align, False, False, 0)
        self.find_button = gtk.Button(u"Find grids")
        self.find_button.connect("clicked", self.on_find_patterns)
        files_hbox.pack_start(self.find_button, False, False, 0)
        
        patterns_vbox.pack_start(files_hbox, False, False, 6)
        
        patterns_vbox.pack_start(window, True, True, 0)
        
        buttons_hbox = gtk.HBox(False, 6)
        generate_button = gtk.Button(u"Construct grid")
        generate_button.connect("clicked", self.construct_pattern)
        buttons_hbox.pack_start(generate_button, False, False, 0)
        align = gtk.Alignment(0, 0, 1, 0)
        align.add(self.clear_button)
        buttons_hbox.pack_start(align, False, False, 0)
        
        patterns_vbox.pack_start(buttons_hbox, False, False, 6)
        
        align = gtk.Alignment(0, 0, 1, 1)
        align.set_padding(0, 0, 12, 0)
        align.add(patterns_vbox)
        options_vbox.pack_start(align, True, True, 0)

        self.clear_button.set_sensitive(False)
        self._load_pattern_list(self.files)
        
    def on_file_changed(self, combo):
        index = combo.get_active()
        files = self.files if index == 0 else self.files[index - 1:index]
        if files:
            self._load_pattern_list(files)    
            
    def _load_pattern_list(self, files):
        data = [d for (f, _, d) in self.patterns if f in files]
        grids = reduce(operator.add, data) if data else []
        stats = [(g.count_words(), g.count_blocks(), g) for g in grids]
        stats.sort()
        self.grids = [grid for (_, _, grid) in stats]
        self.load_empty_grid(*self.size_component.get_size())
        
    def on_pattern_changed(self, selection):
        store, it = selection.get_selected()
        if it is not None:
            self.show_grid(store.get_value(it, 1))
            
    def show_grid(self, grid, showing_pattern=True):
        self.showing_pattern = showing_pattern
        self.grid = grid
        self.preview.display(self.grid)
        self.clear_button.set_sensitive(showing_pattern)
            
    def clear_pattern(self, button=None):
        """Display an empty grid without the currently selected pattern."""
        self.show_grid(Grid(*self.grid.size), False)
        self.tree.get_selection().unselect_all()
        
    def construct_pattern(self, button):
        """Open the pattern editor to construct a pattern."""
        editor = GridEditor(self, size=self.grid.size)
        editor.show_all()
        if editor.run() == gtk.RESPONSE_OK:
            self.show_grid(editor.grid)
            self.tree.get_selection().unselect_all()
        editor.destroy()
        
    def on_find_patterns(self, button):
        d = FindPatternDialog(self)
        d.show_all()
        if d.run() == gtk.RESPONSE_OK:
            buff = d.text.get_buffer()
            text = buff.get_text(*buff.get_bounds())
            words = [w for w in text.split() if w != '']
            if words:
                w, h = self.grid.size
                c = self.generate_criteria(list(set(words)))
                self.clear_pattern()
                self.display_patterns(w, h, criteria=c)
        d.destroy()        
            
    def load_empty_grid(self, width, height):
        """Load an empty grid with the specified dimensions and load patterns."""
        self.grid = Grid(width, height)
        self.preview.display(self.grid)
        self.display_patterns(width, height, criteria=None)
        
    def generate_criteria(self, words):
        """Determine search criteria per word length."""
        counts = {}
        for word in words:
            l = len(word)
            if l in counts:
                counts[l] += 1
            else:
                counts[l] = 1
        return {"counts": counts, "words": words}
        
    def _check_grid(self, grid, criteria):
        """Return a grid or None when the grid meets all the search criteria."""
        if "counts" in criteria:
            counts = grid.determine_word_counts()
            for k, v in criteria["counts"].items():
                if k not in counts or counts[k] < v:
                    return None
        if "words" in criteria:
            return attempt_fill(grid, criteria["words"])
        return grid
        
    def display_patterns(self, width, height, criteria=None):
        gs = []
        for grid in self.grids:
            if grid.size != (width, height):
                continue
            if not criteria:
                gs.append(grid)
                continue
            g = self._check_grid(grid, criteria)
            if g is not None and g.has_chars():
                gs.append(g)
        self.store.clear()
        self.find_button.set_sensitive(len(gs) > 0)
        for g in gs:
            blocks = g.count_blocks()
            words = g.count_words()
            s = ''.join([str(words), " words, ", str(blocks), " blocks"])
            self.store.append([s, g])
                
    def get_configuration(self):
        configuration = {}
        configuration["type"] = "crossword"
        
        if self.grid is not None:
            configuration["grid"] = copy.deepcopy(self.grid)
        return configuration
