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

import copy
import gobject
import gtk
import time

class WordListEditor(gtk.Dialog):
    def __init__(self, palabra_window):
        gtk.Dialog.__init__(self, u"Word list manager"
            , palabra_window, gtk.DIALOG_MODAL)
        self.palabra_window = palabra_window
        self.set_size_request(640, 480)
        
        self.data = self.palabra_window.wordlists.keys()
        self.modifications = {}
        
        self.store = gtk.ListStore(str)
        self._display_wordlists()
        
        self.tree = gtk.TreeView(self.store)
        self.tree.get_selection().connect("changed", self.on_selection_changed)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(u"Word lists")
        column.pack_start(cell, True)
        column.set_attributes(cell, text=0)
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
        
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
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
            if path in self.data:
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
            self.data.append(path)
            self.modifications[path] = "add"
            self._display_wordlists()
        dialog.destroy()
        
    def on_selection_changed(self, selection):
        store, it = selection.get_selected()
        self.remove_button.set_sensitive(it is not None)
        
    def remove_word_list(self):
        store, it = self.tree.get_selection().get_selected()
        path = self.store.get_value(it, 0)
        self.data.remove(path)
        self.modifications[path] = "remove"
        self._display_wordlists()
        
    def _display_wordlists(self):
        self.store.clear()
        for path in self.data:
            self.store.append([path])

class WordList:
    def __init__(self):
        self.lengths = {}
        self.combinations = {}
        self.size = 0
        
    def add_word(self, word):
        try:
            self.lengths[len(word)].append(word)
        except KeyError:
            self.lengths[len(word)] = [word]
        if len(word) not in self.combinations:
            self.combinations[len(word)] = {}
        for x in xrange(len(word)):
            if x not in self.combinations[len(word)]:
                self.combinations[len(word)][x] = {}
        for i, c in enumerate(word):
            try:
                self.combinations[len(word)][i][c].append(self.size)
            except KeyError:
                self.combinations[len(word)][i][c] = [self.size]
        self.size += 1
        
    # TODO
    def has_substring_matches(self, length, constraints):
        return self.has_matches(length, constraints)
            
    def has_matches(self, length, constraints):
        if length not in self.lengths:
            return False

        # preprocess constraints
        for i, c in constraints:
            if i not in self.combinations[length]:
                return False
            if c not in self.combinations[length][i]:
                return False
            if len(self.combinations[length][i][c]) == 0:
                return False
                
        # store the words available per constraint and sort
        counts = [(i, c, self.combinations[length][i][c]) for i, c in constraints]
        counts.sort(key=lambda x: len(x[2]))
        
        # use each constraint to reduce the number of words available
        # if it reaches zero at any time, there are no matches
        result = None
        for i, c, words in counts:
            if result is None:
                result = words
                continue
            else:
                reduced = filter(lambda w: w in result, words)
                if len(reduced) == 0:
                    return False
                result = reduced
        return True
    
    def search(self, length, constraints, more_constraints=None):
        if length not in self.lengths:
            return []
        result = []
        for word in self.lengths[length]:
            if self._predicate(constraints, word):
                if more_constraints is not None:
                    filled_constraints = []
                    for j, (i, l, cs) in enumerate(more_constraints):
                        filled_constraints.append((l, cs + [(i, word[j])]))
                    
                    for l, cs in filled_constraints:
                        if not self.has_matches(l, cs):
                            break
                    else:
                        result.append(word)
                else:
                    result.append(word)
        return result
        
    @staticmethod
    def _predicate(constraints, word):
        for position, letter in constraints:
            if not word[position] == letter:
                return False
        return True

def _process_word(word):
    word = word.strip("\n")
    if len(word) == 0:
        return None
    for c in word:
        if not (ord("A") <= ord(c) <= ord("Z") or ord("a") <= ord(c) <= ord("z")):
            return None
    return word

def read_wordlist(filename):
    f = open(filename, "r")
    for line in f:
        word = _process_word(line)
        if word is not None:
            yield word

def read_wordlist_from_iter(callback, words):
    wordlist = WordList()
    for word in words:
        wordlist.add_word(word.lower())
        yield True
    callback(wordlist)
    yield False

def read_wordlists(window, paths):
    for path in paths:
        window.wordlists[path] = {"list": None, "status": "loading"}
    wordlists = {}
    for path in paths:
        wordlist = WordList()
        for word in read_wordlist(path):
            wordlist.add_word(word.lower())
            yield True
        wordlists[path] = {"list": wordlist, "status": "ready"}
    window.wordlists.update(wordlists)
    try:
        window.editor.refresh_words(True)
    except AttributeError:
        pass
    yield False

def search_wordlists(wordlists, length, constraints, more_constraints=None):
    result = []
    for path, item in wordlists.items():
        wordlist = item["list"]
        if wordlist is not None:
            result += wordlist.search(length, constraints, more_constraints)
    result.sort()
    return result
