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

import gtk
import glib
import operator

import constants

class FindWordsDialog(gtk.Dialog):
    def __init__(self, parent):
        gtk.Dialog.__init__(self, u"Find word", parent, gtk.DIALOG_MODAL)
        self.wordlists = parent.wordlists
        self.sort_option = 0
        self.pattern = None
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        main = gtk.VBox(False, 0)
        main.set_spacing(18)
        label = gtk.Label("Use ? for an unknown letter and * for zero or more unknown letters.")
        label.set_alignment(0, 0.5)
        main.pack_start(label, False, False, 0)
        entry = gtk.Entry()
        entry.connect("changed", self.on_entry_changed)
        main.pack_start(entry, False, False, 0)
        self.store = gtk.ListStore(str, str)
        self.tree = gtk.TreeView(self.store)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Word", cell, markup=0)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        column.set_fixed_width(250)
        self.tree.append_column(column)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Wordlist", cell, markup=1)
        self.tree.append_column(column)
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add(self.tree)
        scrolled_window.set_size_request(-1, 300)
        main.pack_start(scrolled_window, True, True, 0)
        
        sort_hbox = gtk.HBox(False, 6)
        label = gtk.Label("Sort by:")
        label.set_alignment(0, 0.5)
        sort_hbox.pack_start(label, False, False, 0)
        def on_sort_changed(combo):
            self.sort_option = combo.get_active()
            self.launch_pattern(self.pattern)
        combo = gtk.combo_box_new_text()
        for t in ["Alphabet", "Length"]:
            combo.append_text(t)
        combo.set_active(self.sort_option)
        combo.connect("changed", on_sort_changed)
        sort_hbox.pack_start(combo, True, True, 0)
        
        main.pack_start(sort_hbox, False, False, 0)
        hbox.pack_start(main, True, True, 0)
        self.vbox.pack_start(hbox, True, True, 0)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        self.launch_pattern(None)
        
    def on_entry_changed(self, widget):
        glib.source_remove(self.timer)
        self.launch_pattern(widget.get_text().strip())
        
    def launch_pattern(self, pattern=None):
        self.store.clear()
        if pattern is not None:
            self.store.append(["Loading...", ''])
        self.timer = glib.timeout_add(constants.INPUT_DELAY, self.find_words, pattern)
        
    def find_words(self, pattern=None):
        if pattern is None:
            return False
        result = []
        for wlist in self.wordlists:
            name = wlist.name if wlist.name is not None else wlist.path
            result.extend([(name, w) for w in wlist.find_by_pattern(pattern)])
        if self.sort_option == 0:
            result.sort(key=operator.itemgetter(1))
        self.pattern = pattern
        self.store.clear()
        for name, s in result:
            t1 = '<span font_desc="Monospace 12">' + s + '</span>'
            t2 = '<span foreground="gray">' + name + '</span>'
            self.store.append([t1, t2])
        return False

class AnagramDialog(gtk.Dialog):
    def __init__(self, parent):
        gtk.Dialog.__init__(self, u"Find anagrams", parent, gtk.DIALOG_MODAL)
        self.wordlists = parent.wordlists
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        main = gtk.VBox(False, 0)
        main.set_spacing(18)
        
        entry = gtk.Entry()
        entry.connect("changed", self.on_buffer_changed)
        main.pack_start(entry, False, False, 0)
        
        self.store = gtk.ListStore(str)
        self.tree = gtk.TreeView(self.store)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(u"Contained words", cell, text=0)
        self.tree.append_column(column)
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add(self.tree)
        scrolled_window.set_size_request(300, 300)
        main.pack_start(scrolled_window, True, True, 0)
        hbox.pack_start(main, True, True, 0)
        
        self.vbox.pack_start(hbox, True, True, 0)
        
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        
        self.timer = glib.timeout_add(INPUT_DELAY, self.find_words)
        
    def on_buffer_changed(self, widget):
        glib.source_remove(self.timer)
        self.store.clear()
        self.store.append(["Loading..."])
        word = widget.get_text().strip()
        self.timer = glib.timeout_add(INPUT_DELAY, self.find_words, word)
        
    def load_contained_words(self, word=None):
        if word is None:
            return
        self.store.clear()
        counts, strings = get_contained_words(self.wordlists, word)
        counts = dict(counts)
        result = [extract(counts, s) for s in strings]
        pairs = [(w1, ''.join(w2)) for w1, w2 in result if len(w2) > 1]
        f_result = verify_contained_words(self.wordlists, pairs)
        self._display([s1 + " (" + s2 + ")" for s1, s2 in f_result])
        return False
        
    def find_words(self, pattern=None):
        if pattern is not None:
            result = []
            for p, wlist in self.wordlists.items():
                result.extend(wlist.find_by_pattern(pattern))
            self._display(result)
        return False
        
    def _display(self, strings):
        self.store.clear()
        for s in strings:
            self.store.append([s])

class NewWordListDialog(gtk.Dialog):
    def __init__(self, parent):
        gtk.Dialog.__init__(self, u"New word list", parent, gtk.DIALOG_MODAL)
        self.set_size_request(320, 240)
        
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)

class WordListEditor(gtk.Dialog):
    def __init__(self, palabra_window):
        gtk.Dialog.__init__(self, u"Word list manager"
            , palabra_window, gtk.DIALOG_MODAL)
        self.palabra_window = palabra_window
        self.set_size_request(640, 480)
        
        # name path
        self.store = gtk.ListStore(str, str)
        self._load_wordlists()
        
        self.tree = gtk.TreeView(self.store)
        self.tree.get_selection().connect("changed", self.on_selection_changed)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(u"Identifier")
        column.pack_start(cell, True)
        column.set_attributes(cell, text=0)
        self.tree.append_column(column)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(u"Word lists")
        column.pack_start(cell, True)
        column.set_attributes(cell, text=1)
        self.tree.append_column(column)
        
        buttonbox = gtk.HButtonBox()
        buttonbox.set_layout(gtk.BUTTONBOX_START)
        
        add_button = gtk.Button(stock=gtk.STOCK_ADD)
        buttonbox.pack_start(add_button, False, False, 0)
        add_button.connect("clicked", lambda button: self.add_word_list())
        
        self.remove_button = gtk.Button(stock=gtk.STOCK_REMOVE)
        buttonbox.pack_start(self.remove_button, False, False, 0)
        self.remove_button.connect("clicked", lambda button: self.remove_word_list())
        self.remove_button.set_sensitive(False)
        
        main = gtk.VBox(False, 0)
        main.set_spacing(18)
        main.pack_start(self.tree, True, True, 0)
        main.pack_start(buttonbox, False, False, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        hbox.pack_start(main, True, True, 0)
        
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        self.vbox.add(hbox)
        
    def add_word_list(self):
        dialog = gtk.FileChooserDialog(u"Add word list"
            , self
            , gtk.FILE_CHOOSER_ACTION_OPEN
            , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
            , gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.show_all()
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            path = dialog.get_filename()
            if path in [p["path"]["value"] for p in preferences.prefs["word_files"]]:
                dialog.destroy()
                
                title = u"Duplicate found"
                message = u"The word list has not been added because it's already in the list."
                mdialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL
                    , gtk.MESSAGE_INFO, gtk.BUTTONS_NONE, message)
                mdialog.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
                mdialog.set_title(title)
                mdialog.run()
                mdialog.destroy()
                return
            
            d = NewWordListDialog(self)
            d.show_all()
            d.run()
            d.destroy()
            
            # TODO
            value = {"name": {"type": "str", "value": "TODO"}, "path": {"type": "str", "value": path}}
            preferences.prefs["word_files"].append(value)
            
            self._load_wordlists()
        dialog.destroy()
        
    def on_selection_changed(self, selection):
        store, it = selection.get_selected()
        self.remove_button.set_sensitive(it is not None)
        
    def remove_word_list(self):
        store, it = self.tree.get_selection().get_selected()
        name = self.store[it][0]
        nextprefs = [p for p in preferences.prefs["word_files"] if p["name"]["value"] != name]
        preferences.prefs["word_files"] = nextprefs
        
        self.palabra_window.wordlists = create_wordlists(preferences.prefs["word_files"])
        try:
            self.palabra_window.editor.refresh_words(True)
        except AttributeError:
            pass
        self._load_wordlists()
        
    def _load_wordlists(self):
        self.store.clear()
        for p in preferences.prefs["word_files"]:
            name = p["name"]["value"]
            path = p["path"]["value"]
            self.store.append([name, path])
