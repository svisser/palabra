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

import gobject
import gtk

from files import read_container, read_containers
from grid import Grid
from newpuzzle import GridPreview

class PatternFileEditor(gtk.Dialog):
    def __init__(self, palabra_window):
        gtk.Dialog.__init__(self, u"Pattern file manager"
            , palabra_window, gtk.DIALOG_MODAL)
        self.palabra_window = palabra_window
        self.set_size_request(640, 640)
        
        self.preview = GridPreview()
        self.preview.set_size_request(200, 250)
        
        self.patterns = read_containers(self.palabra_window.pattern_files)
        
        # display_string filename grid
        self.store = gtk.TreeStore(str, str, gobject.TYPE_PYOBJECT)
        self.display_files()
        
        self.tree = gtk.TreeView(self.store)
        self.tree.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.tree.get_selection().connect("changed", self.on_selection_changed)
        
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(u"Pattern files")
        column.pack_start(cell, True)
        column.set_attributes(cell, text=0)
        self.tree.append_column(column)
        
        right_vbox = gtk.VBox(False, 6)
        
        label = gtk.Label()
        label.set_markup(u"<b>Pattern files</b>")
        align = gtk.Alignment(0, 0.5)
        align.add(label)
        right_vbox.pack_start(align, False, False, 0)
        
        add_button = gtk.Button(stock=gtk.STOCK_ADD)
        add_button.connect("clicked", lambda button: self.add_file())
        align = add_button.get_children()[0]
        hbox = align.get_children()[0]
        image, label = hbox.get_children()
        label.set_text(u"Add pattern file");
        right_vbox.pack_start(add_button, False, False, 0)
        
        self.remove_button = gtk.Button(stock=gtk.STOCK_REMOVE)
        self.remove_button.connect("clicked", lambda button: self.remove_file())
        self.remove_button.set_sensitive(False)
        align = self.remove_button.get_children()[0]
        hbox = align.get_children()[0]
        image, label = hbox.get_children()
        label.set_text(u"Remove pattern file");
        right_vbox.pack_start(self.remove_button, False, False, 0)

        label = gtk.Label()
        label.set_markup(u"<b>Patterns</b>")
        align = gtk.Alignment(0, 0.5)
        align.add(label)
        right_vbox.pack_start(align, False, False, 0)
        
        self.copy_pattern_button = gtk.Button(u"Copy pattern(s) to file...")
        self.copy_pattern_button.set_sensitive(False)
        self.copy_pattern_button.connect("clicked", self.on_copy_pattern)
        self.move_pattern_button = gtk.Button(u"Move pattern(s) to file...")
        self.move_pattern_button.set_sensitive(False)
        self.move_pattern_button.connect("clicked", self.on_move_pattern)
        
        right_vbox.pack_start(self.copy_pattern_button, False, False, 0)
        right_vbox.pack_start(self.move_pattern_button, False, False, 0)
        
        self.add_pattern_button = gtk.Button(stock=gtk.STOCK_ADD);
        self.add_pattern_button.set_sensitive(False)
        self.add_pattern_button.connect("clicked", self.on_add_pattern)
        align = self.add_pattern_button.get_children()[0]
        hbox = align.get_children()[0]
        image, label = hbox.get_children()
        label.set_text(u"Add current pattern to file...");
        right_vbox.pack_start(self.add_pattern_button, False, False, 0)
        
        self.remove_pattern_button = gtk.Button(stock=gtk.STOCK_REMOVE);
        self.remove_pattern_button.set_sensitive(False)     
        self.remove_pattern_button.connect("clicked", self.on_remove_pattern)   
        align = self.remove_pattern_button.get_children()[0]
        hbox = align.get_children()[0]
        image, label = hbox.get_children()
        label.set_text(u"Remove pattern(s)");
        right_vbox.pack_start(self.remove_pattern_button, False, False, 0)
        
        hbox1 = gtk.HBox(True, 12)
        hbox1.pack_start(self.tree, True, True, 0)
        hbox1.pack_start(right_vbox, True, True, 0)
        
        self.info = gtk.TextView()
        self.info.set_buffer(gtk.TextBuffer())
        
        hbox2 = gtk.HBox(True, 12)
        hbox2.pack_start(self.preview, True, True, 0)
        hbox2.pack_start(self.info, True, True, 0)
        
        options_vbox = gtk.VBox(False, 12)
        options_vbox.pack_start(hbox1, True, True, 0)
        options_vbox.pack_start(hbox2, False, False, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        hbox.pack_start(options_vbox, True, True, 0)
        self.vbox.pack_start(hbox, True, True, 0)
        
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        
    def display_files(self):
        self.store.clear()
        for (f, metadata, data) in self.patterns:
            s = ("".join([metadata["title"], " (", f, ")"])
                if "title" in metadata else f)
            parent = self.store.append(None, [s, f, None])
            for grid in data:
                blocks = grid.count_blocks()
                words = grid.count_words()
                s = "".join([str(words), " words, ", str(blocks), " blocks"])
                self.store.append(parent, [s, f, grid])
                
    def display_metadata(self, metadata=None, clear=False):
        text = "" if clear else str(metadata)
        self.info.get_buffer().set_text(text)
        
    def add_file(self):
        dialog = gtk.FileChooserDialog(u"Add pattern file"
            , self
            , gtk.FILE_CHOOSER_ACTION_OPEN
            , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
            , gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.show_all()
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            path = dialog.get_filename()
            for (f, metadata, data) in self.patterns:
                if f == path:
                    dialog.destroy()
                    
                    mdialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL
                        , gtk.MESSAGE_INFO, gtk.BUTTONS_NONE, u"This file is already in the list.")
                    mdialog.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
                    mdialog.set_title("Duplicate file")
                    mdialog.run()
                    mdialog.destroy()
                    break
            else:
                self.palabra_window.pattern_files.append(path)
                
                metadata, data = read_container(path)
                self.patterns.append((path, metadata, data))
                self.display_files()
                dialog.destroy()
        
    def remove_file(self):
        store, paths = self.tree.get_selection().get_selected_rows()
        if len(paths) == 1:
            it = store.get_iter(paths[0])
            filename = store.get_value(it, 1)
            store.remove(it)
            self.palabra_window.pattern_files.remove(filename)
        
    def on_selection_changed(self, selection):
        store, paths = selection.get_selected_rows()
        self.remove_button.set_sensitive(False)
        for path in paths:
            it = store.get_iter(path)
            parent = store.iter_parent(it)
            if len(paths) == 1:
                if parent is None:
                    self.remove_button.set_sensitive(True)
                display = store.get_value(it, 2) if parent is not None else Grid(0, 0)
                self.preview.display(display)
            else:
                self.preview.display(Grid(0, 0))
        
        def is_file(store, path):
            it = store.get_iter(path)
            parent = store.iter_parent(it)
            return parent is None
        only_patterns = True not in [is_file(store, path) for path in paths]
        self.copy_pattern_button.set_sensitive(only_patterns)
        self.move_pattern_button.set_sensitive(only_patterns)
        self.add_pattern_button.set_sensitive(only_patterns)
        self.remove_pattern_button.set_sensitive(only_patterns)
        
        def get_file(store, path):
            it = store.get_iter(path)
            pit = store.iter_parent(it)
            return store.get_value(pit, 1) if pit is not None else store.get_value(it, 1)
        files = list(set([get_file(store, path) for path in paths]))
        if len(files) == 1:
            for (f, metadata, data) in self.patterns:
                if f == files[0]:
                    self.display_metadata(metadata)
                    break
        else:
            self.display_metadata(clear=True)
    
    def on_copy_pattern(self, button):
        patterns = self._gather_selected_patterns()        
        path = self._get_pattern_file()
        print "TODO"
        
    def on_move_pattern(self, button):
        patterns = self._gather_selected_patterns()        
        path = self._get_pattern_file()
        print "TODO"
        
    def on_add_pattern(self, button):
        print "TODO"
    
    def on_remove_pattern(self, button):
        patterns = self._gather_selected_patterns()
        print "TODO"
        
    def _get_pattern_file(self):
        dialog = gtk.FileChooserDialog(u"Select a pattern file"
            , self
            , gtk.FILE_CHOOSER_ACTION_OPEN
            , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
            , gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.show_all()
        
        path = None
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            path = dialog.get_filename()
        dialog.destroy()
        return path
        
    def _gather_selected_patterns(self):
        patterns = {}
        
        store, paths = self.tree.get_selection().get_selected_rows()
        for path in paths:
            it = store.get_iter(path)
            parent = store.iter_parent(it)
            grid = store.get_value(it, 2)
            try:
                patterns[store.get_value(parent, 1)].append(grid)
            except KeyError:
                patterns[store.get_value(parent, 1)] = [grid]
        return patterns

class Pattern:
    def __init__(self):
        self.blocks = []
        self.voids = []
        self.bars = []

def apply_pattern(grid, pattern):
    for x, y in pattern.blocks:
        grid.set_block(x, y, True)
    for x, y in pattern.voids:
        grid.set_void(x, y, True)
    for x, y, side in pattern.bars:
        grid.set_bar(x, y, side, True)

def tile_from_cell(width, height, x, y):
    pattern = Pattern()
    xs = [i for i in xrange(x, width, 2)]
    ys = [j for j in xrange(y, height, 2)]
    pattern.blocks = [(p, q) for p in xs for q in ys]
    return pattern
    
def example(grid):
    p = tile_from_cell(grid.width, grid.height, 1, 1)
    apply_pattern(grid, p)
