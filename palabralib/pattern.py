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
        
        self.store = gtk.TreeStore(str, gobject.TYPE_PYOBJECT)
        self.display_files()
        
        self.tree = gtk.TreeView(self.store)
        self.tree.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.tree.get_selection().connect("changed", self.on_selection_changed)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(u"Pattern files")
        column.pack_start(cell, True)
        column.set_attributes(cell, text=0)
        self.tree.append_column(column)
        
        buttonbox = gtk.HButtonBox()
        buttonbox.set_layout(gtk.BUTTONBOX_END)
        
        add_button = gtk.Button(stock=gtk.STOCK_ADD)
        add_button.connect("clicked", lambda button: self.add_file())
        buttonbox.pack_start(add_button, False, False, 0)
        
        self.remove_button = gtk.Button(stock=gtk.STOCK_REMOVE)
        self.remove_button.connect("clicked", lambda button: self.remove_file())
        self.remove_button.set_sensitive(False)
        buttonbox.pack_start(self.remove_button, False, False, 0)
        
        options_vbox = gtk.VBox(False, 6)
        options_vbox.pack_start(self.tree, True, True, 0)
        options_vbox.pack_start(buttonbox, False, False, 0)
        options_vbox.pack_start(self.preview, False, False, 0)
        
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
            parent = self.store.append(None, [f, None])
            for grid in data:
                blocks = grid.count_blocks()
                words = grid.count_words()
                s = "".join([str(words), " words, ", str(blocks), " blocks"])
                self.store.append(parent, [s, grid])
        
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
            self.palabra_window.pattern_files.append(path)
            
            metadata, data = read_container(path)
            self.patterns.append((path, metadata, data))
            self.display_files()
        dialog.destroy()
        
    def remove_file(self):
        store, paths = self.tree.get_selection().get_selected_rows()
        if len(paths) == 1:
            it = store.get_iter(paths[0])
            filename = store.get_value(it, 0)
            store.remove(it)
            self.palabra_window.pattern_files.remove(filename)
        
    def on_selection_changed(self, selection):
        store, paths = selection.get_selected_rows()
        self.remove_button.set_sensitive(False)
        for p in paths:
            it = store.get_iter(p)
            parent = store.iter_parent(it)
            display = store.get_value(it, 1) if parent is not None else Grid(0, 0)
            self.preview.display(display)
            if len(paths) == 1 and parent is None:
                self.remove_button.set_sensitive(True)

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
