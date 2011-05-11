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

import copy
import gobject
import gtk
import os
import time
from operator import itemgetter

import cPalabra
import constants
import preferences

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
        entry.connect("changed", self.on_input_changed)
        main.pack_start(entry, False, False, 0)
        
        self.store = gtk.ListStore(str)
        self.tree = gtk.TreeView(self.store)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(u"Partial words", cell, text=0)
        self.tree.append_column(column)
        self.tree.set_size_request(300, 300)
        scrolled_window = gtk.ScrolledWindow(None, None)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add_with_viewport(self.tree)
        main.pack_start(scrolled_window, True, True, 0)
        hbox.pack_start(main, True, True, 0)
        
        self.vbox.pack_start(hbox, True, True, 0)
        
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        
    def on_input_changed(self, widget):
        word = widget.get_text().strip()
        if len(word) >= 3:
            import pstats
            import cProfile
            cProfile.runctx('self.load_partial_words(word)', globals(), locals(), filename='fooprof')
            p = pstats.Stats('fooprof')
            p.sort_stats('time').print_stats(20)
            p.print_callers()
        
    def load_partial_words(self, word):
        self.store.clear()
        self.store.append(["Loading..."])
        counts, strings = get_partial_words(self.wordlists, word)
        counts = dict(counts)
        self.store.clear()
        for s in strings:
            chars = []
            s_counts = {}
            for c in s:
                if c not in s_counts:
                    s_counts[c] = 1
                else:
                    s_counts[c] += 1
                if c not in counts or s_counts[c] > counts[c]:
                    chars.append(c)
            self.store.append([s + " (" + ''.join(chars) + ")"])

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

def read_wordlist(path):
    """Yield all words found in the specified file."""
    if not os.path.exists(path):
        return []
    words = set()
    with open(path, "r") as f:
        ord_A = ord("A")
        ord_Z = ord("Z")
        ord_a = ord("a")
        ord_z = ord("z")
        ords = {}
        lower = str.lower
        for line in f:
            line = line.strip("\n")
            line = line.split(",")
            l_line = len(line)
            if not line or l_line > 2:
                continue
            if l_line == 1:
                word = line[0]
            elif l_line == 2:
                word, r = line
            word = word.strip()
            if " " in word:
                continue # for now, reject compound
            if len(word) > constants.MAX_WORD_LENGTH:
                continue    
            for c in word:
                if c not in ords:
                    ord_c = ords[c] = ord(c)
                else:
                    ord_c = ords[c]                
                if not (ord_A <= ord_c <= ord_Z
                    or ord_a <= ord_c <= ord_z):
                    break
            else:
                words.add(lower(word))
    return words
    
def check_accidental_words(grid):
    accidentals = []
    slots = grid.generate_all_slots()
    for s in slots:
        for offset, length in check_accidental_word(s):
            accidentals.append(s[offset:offset + length])
    return accidentals
        
def check_accidental_word(seq):
    # return (offset, length) pairs
    seqs = [(c if c[2] != constants.MISSING_CHAR else None) for c in seq]
    if False not in [(i is None) for i in seqs]:
        return []
    p = []
    p_r = []
    for item in seqs:
        if item is None:
            p.append(p_r)
            p_r = []
        else:
            p_r.append(item)
    if p_r:
        p.append(p_r)
    check = [i for i in p if len(i) >= 2]
    result = []
    for s in check:
        r = _check_seq_for_words(s)
        if r is not None:
            result.append(r)
    return result
    
def _check_seq_for_words(seq):
    print seq
    return None

def produce_word_counts(word):
    counts = {}
    for i, c in enumerate(word):
        if c not in counts:
            counts[c] = 1
        else:
            counts[c] += 1
    return counts
    
def get_partial_words(wordlists, word):
    c_items = produce_word_counts(word).items()
    result = []
    for p, wlist in wordlists.items():
        for l in xrange(len(word) + 1, constants.MAX_WORD_LENGTH):
            result.extend(cPalabra.get_partial_words(wlist.index, l, c_items, len(c_items)))
    return c_items, result

def create_wordlists(word_files):
    wordlists = {}
    for i, data in enumerate(word_files):
        if i >= constants.MAX_WORD_LISTS:
            break
        name = data["name"]["value"]
        path = data["path"]["value"]
        wordlists[path] = CWordList(path, index=i)
    return wordlists

def cs_to_str(l, cs):
    result = ['.' for i in xrange(l)]
    for (i, c) in cs:
        result[i] = c
    return ''.join(result)

def css_to_strs(css=None):
    return None if css is None else [(i, cs_to_str(l, cs)) for (i, l, cs) in css]

def search_wordlists(wordlists, length, constraints, more=None):
    indices = [item.index for p, item in wordlists.items()]
    result = cPalabra.search(length
        , cs_to_str(length, constraints)
        , css_to_strs(more), indices)
    if len(indices) > 1:
        result.sort()
    return result
    
def analyze_words(grid, g_words, g_cs, g_lengths, words):
    cs = {}
    for n, x, y, d in g_words:
        cs[x, y, d] = grid.gather_all_constraints(x, y, d, g_cs, g_lengths)
    counts = cPalabra.compute_counts(words)
    for l in words:
        for i in xrange(l):
            counts[l][i] = sorted(counts[l][i].items(), key=itemgetter(1), reverse=True)
    result = {}
    for n, x, y, d in g_words:
        data = cPalabra.compute_distances(words[g_lengths[x, y, d]], cs, counts, (x, y, d))
        result[x, y, d] = [t[0] for t in sorted(data, key=itemgetter(1))]
    return result

class CWordList:
    def __init__(self, content, index=0):
        """Accepts either a filepath or a list of words, possibly with ranks."""
        if isinstance(content, str):
            words = [(w, 0) for w in list(read_wordlist(content))]
        else:
            words = [(w if isinstance(w, tuple) else (w, 0)) for w in content]
            # for now, reject compound
            words = [item for item in words if " " not in item[0]]
        self.words = cPalabra.preprocess(words, index)
        self.index = index
        
    def has_matches(self, length, constraints, words=None):
        """
        Return True when a word exists that matches the constraints and the length.
        """
        ws = self.words[length] if words is None else words
        return cPalabra.has_matches(ws, length, constraints)
        
    def search(self, length, constraints, more=None):
        """
        Search for words that match the given criteria.
        
        This function returns a list with tuples, (str, bool).
        The first value is the word, the second value is whether all
        positions of the word have a matching word, when the
        more_constraints (more) argument is specified.
        If more is not specified, the second value
        in a tuple is True.
        
        If more is specified, then constraints must be
        specified for ALL intersecting words.
        
        constraints and more must match with each other
        (i.e., if intersecting word at position 0 starts with 'a' then
        main word must also have a constraint 'a' at position 0).
        
        Words are returned in alphabetical order.
        """
        return cPalabra.search(length
            , cs_to_str(length, constraints)
            , css_to_strs(more), [self.index])
