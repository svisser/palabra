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

import gobject
import gtk

from files import ParserError
from grid import Grid
from gui_common import (
    create_combo,
    create_label,
    PalabraDialog,
)
import preferences
from view import GridPreview

class PatternFileEditor(gtk.Dialog):
    def __init__(self, palabra_window):
        gtk.Dialog.__init__(self, u"Pattern file manager"
            , palabra_window, gtk.DIALOG_MODAL)
        self.palabra_window = palabra_window
        self.set_size_request(640, 512)
        
        self.preview = GridPreview()
        self.preview.set_size_request(200, 256)
        
        self.patterns = {}
        # display_string filename id_of_grid
        self.store = gtk.TreeStore(str, str, str)
        self.reset_pattern_list()
        
        self.tree = gtk.TreeView(self.store)
        self.tree.set_headers_visible(False)
        self.tree.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.tree.get_selection().connect("changed", self.on_selection_changed)
        
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn()
        column.pack_start(cell, True)
        column.set_attributes(cell, text=0)
        self.tree.append_column(column)
        
        right_vbox = gtk.VBox(False, 6)
        
        label = gtk.Label()
        label.set_markup(u"<b>Options for pattern files</b>")
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
        label.set_text(u"Remove pattern file(s)");
        right_vbox.pack_start(self.remove_button, False, False, 0)

        label = gtk.Label()
        label.set_markup(u"<b>Options for patterns</b>")
        align = gtk.Alignment(0, 0.5)
        align.add(label)
        right_vbox.pack_start(align, False, False, 0)
        
        self.copy_pattern_button = gtk.Button(u"Copy pattern(s) to file...")
        self.copy_pattern_button.set_sensitive(False)
        self.copy_pattern_button.connect("clicked", self.on_copy_patterns)
        right_vbox.pack_start(self.copy_pattern_button, False, False, 0)
        self.move_pattern_button = gtk.Button(u"Move pattern(s) to file...")
        self.move_pattern_button.set_sensitive(False)
        self.move_pattern_button.connect("clicked", self.on_move_patterns)
        right_vbox.pack_start(self.move_pattern_button, False, False, 0)
        
        self.add_pattern_button = gtk.Button(stock=gtk.STOCK_ADD);
        try:
            grid = self.palabra_window.puzzle_manager.current_puzzle.grid
        except AttributeError:
            # TODO
            self.add_pattern_button.set_sensitive(False)
        self.add_pattern_button.connect("clicked", self.on_add_pattern)
        align = self.add_pattern_button.get_children()[0]
        hbox = align.get_children()[0]
        image, label = hbox.get_children()
        label.set_text(u"Add current pattern to file...");
        right_vbox.pack_start(self.add_pattern_button, False, False, 0)
        
        self.remove_pattern_button = gtk.Button(stock=gtk.STOCK_REMOVE);
        self.remove_pattern_button.set_sensitive(False)     
        self.remove_pattern_button.connect("clicked", self.on_remove_patterns)   
        align = self.remove_pattern_button.get_children()[0]
        hbox = align.get_children()[0]
        image, label = hbox.get_children()
        label.set_text(u"Remove pattern(s)");
        right_vbox.pack_start(self.remove_pattern_button, False, False, 0)
        
        scrolled_window = gtk.ScrolledWindow(None, None)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add_with_viewport(self.tree)
        
        vbox1 = gtk.VBox(False, 12)
        label = gtk.Label()
        label.set_markup(u"<b>Pattern files</b>")
        align = gtk.Alignment(0, 0.5)
        align.add(label)
        vbox1.pack_start(align, False, False, 0)
        vbox1.pack_start(scrolled_window, True, True, 0)
        vbox1.pack_start(self.preview, False, False, 0)
        
        self.info = gtk.TextView()
        self.info.set_buffer(gtk.TextBuffer())
        self.info.set_editable(False)
        scrolled_window = gtk.ScrolledWindow(None, None)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add_with_viewport(self.info)
        
        vbox2 = gtk.VBox(False, 12)
        vbox2.pack_start(right_vbox, False, False, 0)
        label = gtk.Label()
        label.set_markup(u"<b>Information</b>")
        align = gtk.Alignment(0, 0.5)
        align.add(label)
        vbox2.pack_start(align, False, False, 0)
        vbox2.pack_start(scrolled_window, True, True, 0)
        
        options_hbox = gtk.HBox(True, 12)
        options_hbox.pack_start(vbox1, True, True, 0)
        options_hbox.pack_start(vbox2, True, True, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        hbox.pack_start(options_hbox, True, True, 0)
        self.vbox.pack_start(hbox, True, True, 0)
        
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        
    def reset_pattern_list(self):
        self.store.clear()
        for f in preferences.prefs["pattern_files"]:
            try:
                g, meta, data = read_pattern_file(f)
                self.patterns[f] = {"metadata": meta, "data": data}
            except ParserError:
                # TODO
                pass
        for item in self.patterns.items():
            self._append_file(*item)
                
    def _append_file(self, path, patterns):
        meta = patterns["metadata"]
        data = patterns["data"]
        s = meta["title"] if "title" in meta else path
        parent = self.store.append(None, [s, path, "0"])
        for id, grid in data.items():
            blocks = str(grid.count_blocks())
            words = str(grid.count_words())
            s = "".join([words, " words, ", blocks, " blocks"])
            self.store.append(parent, [s, path, id])
        
    def add_file(self):
        dialog = gtk.FileChooserDialog(u"Add pattern file"
            , self
            , gtk.FILE_CHOOSER_ACTION_OPEN
            , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
            , gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        filter = gtk.FileFilter()
        filter.set_name(u"Palabra pattern files (*.xml)")
        filter.add_pattern("*.xml")
        dialog.add_filter(filter)
        dialog.show_all()
        response = dialog.run()
        path = dialog.get_filename()
        dialog.destroy()
        if response == gtk.RESPONSE_OK:
            for g, pattern in self.patterns.items():
                if g == path:
                    mdialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL
                        , gtk.MESSAGE_INFO, gtk.BUTTONS_NONE, u"This file is already in the list.")
                    mdialog.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
                    mdialog.set_title("Duplicate file")
                    mdialog.run()
                    mdialog.destroy()
                    break
            else:
                try:
                    g, meta, data = read_pattern_file(path)
                    preferences.prefs["pattern_files"].append(path)
                    self.patterns[path] = {"metadata": meta, "data": data}
                    self._append_file(path, self.patterns[path])
                    self.tree.columns_autosize()
                except ParserError:
                    # TODO
                    pass
        
    def remove_file(self):
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG)
        dialog = gtk.Dialog(u"Remove pattern files"
            , self
            , gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_MODAL
            , (gtk.STOCK_NO, gtk.RESPONSE_NO
            , gtk.STOCK_YES, gtk.RESPONSE_YES))
        dialog.set_default_response(gtk.RESPONSE_CLOSE)
        dialog.set_title(u"Remove pattern files")

        label = gtk.Label(u"Are you sure you want to remove the selected pattern file(s)?")
        hbox = gtk.HBox(False, 0)
        hbox.pack_start(image, False, False, 0)
        hbox.pack_start(label, True, False, 10)
        dialog.vbox.pack_start(hbox, False, False, 10)
        dialog.set_resizable(False)
        dialog.set_modal(True)
        dialog.show_all()
        
        response = dialog.run()
        dialog.destroy()
        if response == gtk.RESPONSE_YES:
            while True:
                store, paths = self.tree.get_selection().get_selected_rows()
                if not paths:
                    break
                it = store.get_iter(paths.pop())
                filename = store.get_value(it, 1)
                store.remove(it)
                preferences.prefs["pattern_files"].remove(filename)
                try:
                    del self.patterns[filename]
                    self.tree.columns_autosize()
                except KeyError:
                    pass

    def on_selection_changed(self, selection):
        grid = None
        store, paths = selection.get_selected_rows()
        self.copy_pattern_button.set_sensitive(False)
        self.move_pattern_button.set_sensitive(False)
        self.remove_pattern_button.set_sensitive(False)
        self.remove_button.set_sensitive(False)
        self.info.get_buffer().set_text("")
        self.preview.clear()
        if not paths:
            return
            
        if all([self.is_file(store, p) for p in paths]):
            self.remove_button.set_sensitive(True)
        
        if len(paths) == 1:
            if not self.is_file(store, paths[0]):
                it = store.get_iter(paths[0])
                filepath = store.get_value(it, 1)
                id = store.get_value(it, 2)
                grid = self.patterns[filepath]["data"][id]
                self.preview.display(grid)
            
        only_patterns = not any([self.is_file(store, p) for p in paths])
        self.copy_pattern_button.set_sensitive(only_patterns)
        self.move_pattern_button.set_sensitive(only_patterns)
        self.remove_pattern_button.set_sensitive(only_patterns)
        
        files = list(set([self.get_file(store, p) for p in paths]))
        self.info.get_buffer().set_text("")
        if len(files) == 1:
            for g, pattern in self.patterns.items():
                if g == files[0]:
                    if grid:
                        stats = grid.determine_status()
                        info = "".join(["Blocks: ", str(stats["block_count"])
                            , " (%.2f" % stats["block_percentage"], "%)\n"
                            , "Letters: ", str(stats["char_count"]), "\n"
                            , "Words: ", str(stats["word_count"]), "\n"
                            , "Voids: ", str(stats["void_count"]), "\n"])
                    else:
                        total = str(len(self.patterns[g]["data"].keys()))
                        info = "".join(["Location: ", g, "\n"
                            , "Number of patterns: ", total, "\n"])
                    self.info.get_buffer().set_text(info)
                    break
                    
    def append_to_file(self, path, patterns):
        """Append all patterns to the specified file."""
        try:
            g, meta, data = read_pattern_file(path)
        except ParserError:
            # TODO
            return
        try:
            max_id = int(max(data.keys())) + 1
        except ValueError: # max() arg is an empty sequence
            max_id = 1
        for f, keys in patterns.items():
            for k in keys:
                data[str(max_id)] = self.patterns[f]["data"][k]
                max_id += 1
        write_pattern_file(g, meta, data)
        
    @staticmethod
    def remove_from_files(patterns):
        """Remove the patterns from their respective files."""
        for f, keys in patterns.items():
            try:
                g, meta, data = read_pattern_file(f)
                ndata = {}
                for k, v in data.items():
                    if k not in keys:
                        ndata[k] = v
                write_pattern_file(g, meta, ndata)
            except ParserError:
                # TODO
                pass
    
    def on_copy_patterns(self, button):
        """Copy the currently selected patterns to a specified file."""
        patterns = self._gather_selected_patterns()        
        path = self._get_pattern_file()
        if not path:
            return
        self.append_to_file(path, patterns)
        
    def on_move_patterns(self, button):
        """Move the currently selected patterns to a specified file."""
        patterns = self._gather_selected_patterns()        
        path = self._get_pattern_file()
        if not path:
            return
        self.append_to_file(path, patterns)
        self.remove_from_files(patterns)
        
    def on_add_pattern(self, button):
        """Add the pattern of the current puzzle to a specified file."""
        path = self._get_pattern_file()
        if not path:
            return
        # TODO ugly
        try:
            grid = self.palabra_window.puzzle_manager.current_puzzle.grid
        except AttributeError:
            # TODO
            return
        try:
            g, meta, data = read_pattern_file(path)
        except ParserError:
            # TODO
            return
        max_id = int(max(data.keys())) + 1
        data[str(max_id)] = grid
        write_pattern_file(g, meta, data)
    
    def on_remove_patterns(self, button):
        """Remove the currently selected patterns from their respective files."""
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG)
        dialog = gtk.Dialog(u"Remove patterns"
            , self
            , gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_MODAL
            , (gtk.STOCK_NO, gtk.RESPONSE_NO
            , gtk.STOCK_YES, gtk.RESPONSE_YES))
        dialog.set_default_response(gtk.RESPONSE_CLOSE)
        dialog.set_title(u"Remove patterns")

        label = gtk.Label(u"Are you sure you want to remove the selected pattern(s)?")
        hbox = gtk.HBox(False, 0)
        hbox.pack_start(image, False, False, 0)
        hbox.pack_start(label, True, False, 10)
        dialog.vbox.pack_start(hbox, False, False, 10)
        dialog.set_resizable(False)
        dialog.set_modal(True)
        dialog.show_all()
        
        response = dialog.run()
        dialog.destroy()
        if response == gtk.RESPONSE_YES:
            patterns = self._gather_selected_patterns()
            self.remove_from_files(patterns)
            while True:
                store, paths = self.tree.get_selection().get_selected_rows()
                if not paths:
                    break
                it = store.get_iter(paths.pop())
                filename = store.get_value(it, 1)
                store.remove(it)
            # currently disabled, don't automatically remove file without patterns
            if False:
                for row in self.store:
                    if not self.is_file_with_patterns(self.store, row.path):
                        filename = row[1]
                        it = store.get_iter(row.path)
                        self.store.remove(it)
                        preferences.prefs["pattern_files"].remove(filename)
                        try:
                            del self.patterns[filename]
                        except KeyError:
                            pass
            self.tree.columns_autosize()
        
    def _get_pattern_file(self):
        """Request a filepath from the user."""
        dialog = gtk.FileChooserDialog(u"Select a pattern file"
            , self
            , gtk.FILE_CHOOSER_ACTION_OPEN
            , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
            , gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        filter = gtk.FileFilter()
        filter.set_name(u"Palabra pattern files (*.xml)")
        filter.add_pattern("*.xml")
        dialog.add_filter(filter)
        dialog.show_all()
        
        path = None
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            path = dialog.get_filename()
        dialog.destroy()
        return path
        
    def _gather_selected_patterns(self):
        """Gather the currently selected patterns and the files they belong to."""
        patterns = {}
        store, paths = self.tree.get_selection().get_selected_rows()
        for path in paths:
            it = store.get_iter(path)
            parent = store.iter_parent(it)
            id = store.get_value(it, 2)
            try:
                patterns[store.get_value(parent, 1)].append(id)
            except KeyError:
                patterns[store.get_value(parent, 1)] = [id]
        return patterns

    def get_file(self, store, path):
        return store.get_value(store.get_iter(path), 1)

    def is_file(self, store, path):
        return store.iter_parent(store.get_iter(path)) is None
        
    def is_file_with_patterns(self, store, path):
        return self.is_file(store, path) and store.iter_has_child(store.get_iter(path))

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
    
def fill_with_content(width, height, content):
    full = [(p, q) for p in xrange(width) for q in xrange(height)]
    pattern = Pattern()
    if content == "block":
        pattern.blocks = full
    elif content == "void":
        pattern.voids = full
    return pattern
    
class GridEditor(PalabraDialog):
    def __init__(self, parent, size=None):
        super(GridEditor, self).__init__(parent, u"Grid editor", horizontal=True)
        self.size = size if size else (15, 15)
        
        table = gtk.Table(2, 2, False)
        
        radio = gtk.RadioButton(None, u"Tile from: ")
        radio.connect("toggled", self.on_option_toggle, "tile")
        self.tile_starts = [(p, q) for q in xrange(2) for p in xrange(2)]
        self.tile_combo = gtk.combo_box_new_text()
        self.tile_combo.append_text(u"")
        for x, y in self.tile_starts:
            content = str(''.join(["(", str(x + 1), ",", str(y + 1), ")" ]))
            self.tile_combo.append_text(content)
        self.tile_combo.connect("changed", self.on_tile_changed)
        table.attach(radio, 0, 1, 0, 1)
        table.attach(self.tile_combo, 1, 2, 0, 1)
        
        radio = gtk.RadioButton(radio, u"Fill with: ")
        radio.connect("toggled", self.on_option_toggle, "fill")
        self.fill_combo = create_combo([u"", u"Block"], f_change=self.on_fill_changed)
        table.attach(radio, 0, 1, 1, 2)
        table.attach(self.fill_combo, 1, 2, 1, 2)
        
        self.preview = GridPreview()
        self.preview.set_size_request(384, 384)

        alignment = gtk.Alignment()
        alignment.add(table)
        vbox2 = gtk.VBox(False, 6)
        vbox2.pack_start(create_label(u"<b>Options</b>"), False, False, 0)
        vbox2.pack_start(alignment, False, False, 0)
        self.pack(vbox2, False)
        self.pack(self.preview, False)
        
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.ok_button = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        self.ok_button.set_sensitive(False)
        self._select_option("tile")
        self.display_pattern(None)
        
    def on_option_toggle(self, widget, option):
        if widget.get_active() == 1:
            self._select_option(option)
    
    def _select_option(self, option):
        if option == "tile":
            self.fill_combo.set_active(0)
        elif option == "fill":
            self.tile_combo.set_active(0)
        self.tile_combo.set_sensitive(option == "tile")
        self.fill_combo.set_sensitive(option == "fill")
        
    def display_pattern(self, pattern=None):
        """
        Display a pattern in the preview. If pattern=None then 
        an empty Grid is displayed.
        """
        self.ok_button.set_sensitive(pattern is not None)
        self.grid = Grid(*self.size)
        if pattern:
            apply_pattern(self.grid, pattern)
        self.preview.display(self.grid)
        
    def on_tile_changed(self, combo):
        """Create and display a tiled pattern in the preview."""
        index = combo.get_active()
        if index == 0:
            self.display_pattern(None)
            return
        width, height = self.grid.size
        pattern = tile_from_cell(width, height, *self.tile_starts[index - 1])
        self.display_pattern(pattern)
        
    def on_fill_changed(self, combo):
        """Fill the entire grid with the specified content."""
        index = combo.get_active()
        if index == 0:
            self.display_pattern(None)
            return
        content = {1: "block", 2: "void"}[index]
        width, height = self.grid.size
        self.display_pattern(fill_with_content(width, height, content))
