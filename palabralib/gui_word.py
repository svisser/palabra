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

import constants

class FindWordsDialog(gtk.Dialog):
    def __init__(self, parent):
        gtk.Dialog.__init__(self, u"Find word", parent, gtk.DIALOG_MODAL)
        self.wordlists = parent.wordlists
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        main = gtk.VBox(False, 0)
        main.set_spacing(18)
        entry = gtk.Entry()
        entry.connect("changed", self.on_entry_changed)
        main.pack_start(entry, False, False, 0)
        self.store = gtk.ListStore(str)
        self.tree = gtk.TreeView(self.store)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("", cell, text=0)
        self.tree.append_column(column)
        self.tree.set_headers_visible(False)
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add(self.tree)
        scrolled_window.set_size_request(300, 300)
        main.pack_start(scrolled_window, True, True, 0)
        hbox.pack_start(main, True, True, 0)
        self.vbox.pack_start(hbox, True, True, 0)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        self.timer = glib.timeout_add(constants.INPUT_DELAY, self.find_words)
        
    def on_entry_changed(self, widget):
        glib.source_remove(self.timer)
        self.store.clear()
        self.store.append(["Loading..."])
        word = widget.get_text().strip()
        self.timer = glib.timeout_add(constants.INPUT_DELAY, self.find_words, word)
        
    def find_words(self, pattern=None):
        if pattern is None:
            return False
        result = []
        for p, wlist in self.wordlists.items():
            result.extend(wlist.find_by_pattern(pattern))
        result.sort()
        self.store.clear()
        for s in result:
            self.store.append([s])
        return False
