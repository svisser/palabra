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
        for p, wlist in self.wordlists.items():
            result.extend([(p, w) for w in wlist.find_by_pattern(pattern)])
        if self.sort_option == 0:
            result.sort(key=operator.itemgetter(1))
        self.pattern = pattern
        self.store.clear()
        for p, s in result:
            t1 = '<span font_desc="Monospace 12">' + s + '</span>'
            t2 = '<span foreground="gray">' + p + '</span>'
            self.store.append([t1, t2])
        return False
