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
import os
import time

import constants
import preferences

try:
    import sqlite3 as sqlite
except ImportError:
    try:
        from pysqlite2 import dbapi2 as sqlite
    except ImportError:
        pass # should not occur, see main palabra file

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
        name = self.store.get_value(it, 0)
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

class WordList:
    def __init__(self):
        self.lengths = {}
        self.combinations = {}
        self.size = 0
        
    def add_word(self, word):
        length = len(word)
        try:
            self.lengths[length].append(word)
        except KeyError:
            self.lengths[length] = [word]
        if length not in self.combinations:
            self.combinations[length] = {}
        for x in xrange(length):
            if x not in self.combinations[length]:
                self.combinations[length][x] = {}
        for i, c in enumerate(word):
            try:
                self.combinations[length][i][c].add(self.size)
            except KeyError:
                self.combinations[length][i][c] = set([self.size])
        self.size += 1
        
    def get_substring_matches(self, word):
        result = []
        for length in self.lengths.keys():
            result += [x for x in self.lengths[length] if x in word]
        return result
            
    def has_matches(self, length, constraints):
        # check whether for each constraint at least one word exists
        for i, c in constraints:
            try:
                if not self.combinations[length][i][c]:
                    return False
            except KeyError:
                return False
                
        # check whether all constraints are satisfied for at least one word
        words = [self.combinations[length][i][c] for i, c in constraints]
        return len(reduce(set.intersection, words)) > 0
    
    # yields word and whether all positions of the word have a matching word
    def search(self, length, constraints, more_constraints=None):
        if length in self.lengths.keys():
            for word in self.lengths[length]:
                if self._predicate(constraints, word):
                    if more_constraints is not None:
                        filled_constraints = [(l, cs + [(i, word[j])]) for j, (i, l, cs) in enumerate(more_constraints)]
                        
                        for args in filled_constraints:
                            if not self.has_matches(*args):
                                yield word, False
                                break
                        else:
                            yield word, True
                    else:
                        yield word, True
        
    @staticmethod
    def _predicate(constraints, word):
        for position, letter in constraints:
            if not word[position] == letter:
                return False
        return True

def _process_word(word):
    word = word.strip("\n")
    if not word:
        return None
    ord_A = ord("A")
    ord_Z = ord("Z")
    ord_a = ord("a")
    ord_z = ord("z")
    for c in word:
        if not (ord_A <= ord(c) <= ord_Z or ord_a <= ord(c) <= ord_z):
            return None
    return word

def read_wordlist(path):
    if not os.path.exists(path):
        print "Error: The file", path, "does not exist."
        return
    f = open(path, "r")
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

def read_wordlists(paths):
    wordlists = {}
    for path in paths:
        wordlist = WordList()
        for word in read_wordlist(path):
            wordlist.add_word(word.lower())
        wordlists[path] = {"list": wordlist, "status": "ready"}
    return wordlists

def search_wordlists(wordlists, length, constraints, more_constraints=None):
    result = []
    for path, item in wordlists.items():
        wordlist = item["list"]
        if wordlist is not None:
            result += wordlist.search(length, constraints, more_constraints)
    result.sort()
    return result
    
#####

MAX_WORD_LENGTH = 64

def create_tables(word_files):
    if not os.path.isdir(constants.WORDLIST_DIRECTORY):
        os.mkdir(constants.WORDLIST_DIRECTORY)

    for data in word_files:
        name = data["name"]["value"]
        path = data["path"]["value"]

        con = sqlite.connect(''.join([constants.WORDLIST_DIRECTORY, os.sep, name, '.pdb']))
        cur = con.cursor()
        cur.execute('PRAGMA table_info(words)')
        if not cur.fetchall():
            print "Creating words table for", path
            cur.execute('CREATE TABLE words (id INTEGER PRIMARY KEY, word VARCHAR(64), length INTEGER)')
            for word in read_wordlist(path):
                cur.execute('INSERT INTO words VALUES (null, ?, ?)', (word.lower(), len(word)))
            con.commit()
            
        cur.execute('PRAGMA table_info(search)')
        if not cur.fetchall():
            print "Creating search table for", path
            query = ''.join(['c' + str(i) + ' VARCHAR(1)' + (', ' if i < MAX_WORD_LENGTH - 1 else '') for i in xrange(MAX_WORD_LENGTH)])
            query = 'CREATE TABLE search (id INTEGER PRIMARY KEY, length INTEGER, ' + query + ')'
            cur.execute(query)
            con.commit()
            
            cur2 = con.cursor()
            cur.execute('SELECT id, word FROM words')
            for id, word in cur:
                v = ' (' + str(id) + ', ' + str(len(word)) + ', '
                for i in xrange(MAX_WORD_LENGTH):
                    try:
                        v += "'" + word[i] + "'"
                    except IndexError:
                        v += 'null'
                    if i < MAX_WORD_LENGTH - 1:
                        v += ', '
                v += ')'
                cur2.execute('INSERT INTO search VALUES' + v)
            con.commit()
        con.close()

def create_wordlists(word_files):
    wordlists = {}
    for data in word_files:
        name = data["name"]["value"]
        path = data["path"]["value"]
        wordlist = SQLWordList(name)
        wordlists[path] = {"list": wordlist}
    return wordlists
    
class SQLWordList:
    def __init__(self, name):
        print "Loading", name
        self.path = ''.join([constants.WORDLIST_DIRECTORY, os.sep, name, '.pdb'])
        self.combinations = {}
        
        con = sqlite.connect(self.path)
        cur = con.cursor()
        cur.execute('SELECT * FROM search')
        for row in cur:
            id = row[0]
            length = row[1]
            if length not in self.combinations:
                self.combinations[length] = {}
            for x in xrange(length):
                if x not in self.combinations[length]:
                    self.combinations[length][x] = {}
            for i, c in enumerate(row[2:]):
                if c:
                    try:
                        self.combinations[length][i][c].add(id)
                    except KeyError:
                        self.combinations[length][i][c] = set([id])
        con.close()
        
    def has_matches(self, length, constraints):
        """
        Return True when a word exists that matches the constraints and the length.
        """
        # check whether for each constraint at least one word exists
        for i, c in constraints:
            try:
                if not self.combinations[length][i][c]:
                    return False
            except KeyError:
                return False
                
        # check whether all constraints are satisfied for at least one word
        words = [self.combinations[length][i][c] for i, c in constraints]
        return len(reduce(set.intersection, words)) > 0
        
    def search(self, length, constraints, more_constraints=None):
        """
        Search for words that match the given criteria.
        
        This function yields the word and whether all positions of the word
        have a matching word, when the more_constraints argument is specified.
        If more_constraints is not specified, it yields the word and the
        value True.
        """
        con = sqlite.connect(self.path)
        cursor = con.cursor()
        cursor.execute('SELECT word FROM words WHERE length=?', [length])
        for row in cursor:
            word = row[0]
            if not all([word[i] == c for i, c in constraints]):
                continue
            intersecting = True
            if more_constraints:
                for j, (i, l, cs) in enumerate(more_constraints):
                    if not self.has_matches(l, cs + [(i, word[j])]):
                        intersecting = False
                        break
            yield word, intersecting
        con.close()
