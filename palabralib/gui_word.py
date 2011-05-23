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
import pangocairo

import constants
from editor import highlight_cells
import preferences
from word import (
    create_wordlists,
    check_accidental_words,
    accidental_entries,
    search_wordlists_by_pattern,
    similar_entries,
    similar_words,
    remove_wordlist,
    rename_wordlists,
)

LOADING_TEXT = "Loading..."

class PalabraDialog(gtk.Dialog):
    def __init__(self, pwindow, title, horizontal=False):
        gtk.Dialog.__init__(self, title, pwindow, gtk.DIALOG_MODAL)
        self.pwindow = pwindow
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        if horizontal:
            self.main = gtk.HBox()
        else:
            self.main = gtk.VBox()
        self.main.set_spacing(9)
        hbox.pack_start(self.main, True, True, 0)
        self.vbox.pack_start(hbox, True, True, 0)

def create_tree(types, columns, f_sel=None):
    store = gtk.ListStore(*types)
    tree = gtk.TreeView(store)
    for title, i in columns:
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(title, cell, markup=i)
        tree.append_column(column)
    scrolled_window = gtk.ScrolledWindow()
    scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    scrolled_window.add(tree)
    if f_sel is not None:
        tree.get_selection().connect("changed", f_sel)
    return store, tree, scrolled_window

class WordUsageDialog(PalabraDialog):
    def __init__(self, parent):
        PalabraDialog.__init__(self, parent
            , u"Configure word list usage", horizontal=True)
        self.wordlists = parent.wordlists
        tabs = gtk.Notebook()
        tabs.set_property("tab-hborder", 8)
        tabs.set_property("tab-vborder", 4)
        tabs.append_page(self.create_find_words(parent), gtk.Label(u"Finding words"))
        tabs.append_page(self.create_blacklist(parent), gtk.Label(u"Blacklist"))
        self.main.pack_start(tabs, True, True, 0)
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        
    def create_blacklist(self, parent):
        vbox = gtk.VBox()
        vbox.set_border_width(9)
        vbox.set_spacing(9)
        self.blacklist_combo = gtk.combo_box_new_text()
        self.blacklist_combo.append_text('')
        for wlist in self.wordlists:
            self.blacklist_combo.append_text(wlist.name)
        for i, wlist in enumerate(self.wordlists):
            if preferences.prefs[constants.PREF_BLACKLIST] == wlist.path:
                self.blacklist_combo.set_active(i + 1)
                break
        label = gtk.Label(u"Word list to be used as blacklist:")
        label.set_alignment(0, 0.5)
        vbox.pack_start(label, False, False, 0)
        vbox.pack_start(self.blacklist_combo, False, False, 0)
        return vbox
        
    def create_find_words(self, parent):
        hbox = gtk.HBox()
        hbox.set_spacing(9)
        # name path
        self.store, self.tree, s_window = create_tree((str, str)
            , [("Available word lists", 0)]
            , f_sel=self.on_tree_selection_changed)
        s_window.set_size_request(256, 196)
        hbox.pack_start(s_window, True, True, 0)
        
        button_vbox = gtk.VBox()
        self.add_wlist_button = gtk.Button(stock=gtk.STOCK_ADD)
        self.add_wlist_button.connect("clicked", self.on_add_clicked)
        button_vbox.pack_start(self.add_wlist_button, True, False, 0)
        self.remove_wlist_button = gtk.Button(stock=gtk.STOCK_REMOVE)
        self.remove_wlist_button.connect("clicked", self.on_remove_clicked)
        button_vbox.pack_start(self.remove_wlist_button, True, False, 0)
        self.add_wlist_button.set_sensitive(False)
        self.remove_wlist_button.set_sensitive(False)
        hbox.pack_start(button_vbox, True, True, 0)
        
        # name path
        self.store2, self.tree2, s_window2 = create_tree((str, str)
            , [("Word lists for finding words", 0)]
            , f_sel=self.on_tree2_selection_changed)
        s_window2.set_size_request(256, 196)
        hbox.pack_start(s_window2, True, True, 0)        
        
        # populate list stores
        c_find = preferences.prefs[constants.PREF_FIND_WORD_FILES]
        wlists1 = [w for w in parent.wordlists if w.path not in c_find]
        wlists2 = [w for w in parent.wordlists if w.path in c_find]
        for wlist in wlists1:
            self.store.append([wlist.name, wlist.path])
        for wlist in wlists2:
            self.store2.append([wlist.name, wlist.path])
        
        vbox = gtk.VBox()
        vbox.set_border_width(9)
        vbox.set_spacing(9)
        score_hbox = gtk.HBox()
        score_hbox.set_spacing(9)
        label = gtk.Label(u"Minimum word score:")
        label.set_alignment(0, 0.5)
        score_hbox.pack_start(label, False, False, 0)
        value = preferences.prefs[constants.PREF_FIND_WORD_MIN_SCORE]
        adj = gtk.Adjustment(value, 0, 100, 1, 0, 0)
        self.find_min_score_spinner = gtk.SpinButton(adj, 0.0, 0)
        score_hbox.pack_start(self.find_min_score_spinner, False, False, 0)
        vbox.pack_start(hbox)
        vbox.pack_start(score_hbox, False, False, 0)
        return vbox
        
    def on_tree_selection_changed(self, selection):
        store, it = selection.get_selected()
        self.add_wlist_button.set_sensitive(it is not None)
        
    def on_tree2_selection_changed(self, selection):
        store, it = selection.get_selected()
        self.remove_wlist_button.set_sensitive(it is not None)
        
    def on_add_clicked(self, button):
        self._move_to_store(self.tree, self.store2)
            
    def on_remove_clicked(self, button):
        self._move_to_store(self.tree2, self.store)
            
    def _move_to_store(self, tree_from, store_to):
        store, it = tree_from.get_selection().get_selected()
        if it is not None:
            name, path = store[it][0], store[it][1]
            store_to.append([name, path])
            store.remove(it)
            
    def get_configuration(self):
        # this dict gets updated to preferences.prefs
        c = {}
        c[constants.PREF_FIND_WORD_FILES] = [path for name, path in self.store2]
        b_index = self.blacklist_combo.get_active()
        if b_index >= 1:
            c[constants.PREF_BLACKLIST] = self.wordlists[b_index - 1].path
        else:
            c[constants.PREF_BLACKLIST] = ''
        c[constants.PREF_FIND_WORD_MIN_SCORE] = self.find_min_score_spinner.get_value_as_int()
        return c

class SimilarWordsDialog(PalabraDialog):
    def __init__(self, parent, puzzle):
        PalabraDialog.__init__(self, parent, u"View similar words")
        self.puzzle = puzzle
        self.store = gtk.ListStore(str, str)
        self.tree = gtk.TreeView(self.store)
        self.tree.get_selection().connect("changed", self.on_selection_changed)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Similar words", cell, markup=1)
        self.tree.append_column(column)
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add(self.tree)
        scrolled_window.set_size_request(512, 384)
        self.main.pack_start(scrolled_window, True, True, 0)
        label = gtk.Label(u"Click to highlight the words in the grid.")
        label.set_alignment(0, 0.5)
        self.main.pack_start(label, False, False, 0)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        destroy = lambda w: highlight_cells(self.pwindow, self.puzzle, clear=True)
        self.connect("destroy", destroy)
        self.entries = similar_entries(similar_words(puzzle.grid))
        self.load_entries(self.entries)
        
    def load_entries(self, entries):
        self.store.clear()
        for s, words in entries.items():
            txt = '<span font_desc="Monospace 12">'
            l_words = len(words)
            l_s = len(s)
            for i, (x, y, d, word, pos) in enumerate(words):
                txt += word[0:pos]
                txt += '<span foreground="red">'
                txt += word[pos:pos + l_s]
                txt += '</span>'
                txt += word[pos + l_s:]
                if i < l_words - 1:
                    txt += ' / '
            txt += '</span>'
            self.store.append([s, txt])
    
    def on_selection_changed(self, selection):
        """Highlight all cells associated with the selected entry."""
        store, it = selection.get_selected()
        if it is not None:
            words = self.entries[store[it][0]]
            slots = [(x, y, d) for x, y, d, word, offset in words]
            highlight_cells(self.pwindow, self.puzzle, "slots", slots)

class AccidentalWordsDialog(PalabraDialog):
    def __init__(self, parent, puzzle):
        PalabraDialog.__init__(self, parent, u"View accidental words")
        self.puzzle = puzzle
        self.wordlists = parent.wordlists
        self.index = 0
        self.collapse = True
        wlist_hbox = gtk.HBox(False, 0)
        label = gtk.Label(u"Check for words in list:")
        label.set_alignment(0, 0.5)
        wlist_hbox.pack_start(label, True, True, 0)
        combo = gtk.combo_box_new_text()
        for wlist in self.wordlists:
            combo.append_text(wlist.name)
        combo.set_active(self.index)    
        def on_wordlist_changed(widget):
            self.index = widget.get_active()
        combo.connect("changed", on_wordlist_changed)
        wlist_hbox.pack_start(combo, False, False, 0)
        self.main.pack_start(wlist_hbox, False, False, 0)
        self.store = gtk.ListStore(str, str)
        self.tree = gtk.TreeView(self.store)
        self.tree.get_selection().connect("changed", self.on_selection_changed)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Word", cell, markup=0)
        self.tree.append_column(column)
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add(self.tree)
        scrolled_window.set_size_request(300, 300)
        self.main.pack_start(scrolled_window, True, True, 0)
        label = gtk.Label(u"Click to highlight the word(s) in the grid.")
        label.set_alignment(0, 0.5)
        self.main.pack_start(label, False, False, 0)
        def collapse_callback(button):
            self.collapse = button.get_active()
            self.launch_accidental(self.puzzle.grid)
        button = gtk.CheckButton("Collapse multiple occurrences into one item.")
        button.connect("toggled", collapse_callback)
        button.set_active(self.collapse)
        self.main.pack_start(button, False, False, 0)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        destroy = lambda w: highlight_cells(self.pwindow, self.puzzle, clear=True)
        self.connect("destroy", destroy)
        self.launch_accidental(puzzle.grid)
        
    def launch_accidental(self, grid):
        highlight_cells(self.pwindow, self.puzzle, clear=True)
        self.store.clear()
        self.store.append([LOADING_TEXT, ''])
        self.timer = glib.timeout_add(constants.INPUT_DELAY_SHORT
            , self.load_words, grid, self.wordlists[self.index])
        
    def load_words(self, grid, wlist):
        """Compute and display the words of the grid found in the word list."""
        self.results = [(d, cells) for d, cells in
            check_accidental_words([wlist], grid) if len(cells) > 1]
        self.store.clear()
        for s, count, str_indices in accidental_entries(self.results, self.collapse, True):
            text = s.lower()
            if count > 1:
                text += " (" + str(count) + "x)"
            t1 = '<span font_desc="Monospace 12">' + text + '</span>'
            self.store.append([t1, str_indices])
        return False
    
    def on_selection_changed(self, selection):
        """Highlight all cells associated with the selected entry."""
        store, it = selection.get_selected()
        if it is not None:
            index = self.store[it][1]
            highlight = []
            for index in index.split(','):
                d, cells = self.results[int(index)]
                highlight.extend(cells)
            h_cells = [(x, y) for x, y, c in highlight]
            highlight_cells(self.pwindow, self.puzzle, "cells", h_cells)

MATCHING_TEXT = u"Number of matching words:"

class FindWordsDialog(PalabraDialog):
    def __init__(self, parent):
        PalabraDialog.__init__(self, parent, u"Find words")
        self.wordlists = parent.wordlists
        self.sort_option = 0
        self.pattern = None
        label = gtk.Label(u"Use ? for an unknown letter and * for zero or more unknown letters.")
        label.set_alignment(0, 0.5)
        self.main.pack_start(label, False, False, 0)
        entry = gtk.Entry()
        entry.connect("changed", self.on_entry_changed)
        self.main.pack_start(entry, False, False, 0)
        # word path score
        self.store = gtk.ListStore(str, str, int)
        self.tree = gtk.TreeView(self.store)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Word", cell, markup=0)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        column.set_fixed_width(250)
        self.tree.append_column(column)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Wordlist", cell, markup=1)
        self.tree.append_column(column)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Score", cell, text=2)
        self.tree.append_column(column)
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add(self.tree)
        scrolled_window.set_size_request(-1, 300)
        self.main.pack_start(scrolled_window, True, True, 0)
        self.n_label = gtk.Label("")
        self.n_label.set_alignment(0, 0.5)
        self.set_n_label(0)
        self.main.pack_start(self.n_label, False, False, 0)
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
        self.main.pack_start(sort_hbox, False, False, 0)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        self.launch_pattern(None)
        
    def set_n_label(self, n):
        self.n_label.set_text(MATCHING_TEXT + " " + str(n))
        
    def on_entry_changed(self, widget):
        glib.source_remove(self.timer)
        self.launch_pattern(widget.get_text().strip())
        
    def launch_pattern(self, pattern=None):
        self.store.clear()
        if pattern is not None and len(pattern) > 0:
            self.store.append([LOADING_TEXT, '', 0])
        self.timer = glib.timeout_add(constants.INPUT_DELAY, self.find_words, pattern)
        
    def find_words(self, pattern=None):
        if pattern is None:
            return False
        result = search_wordlists_by_pattern(self.wordlists, pattern)
        if self.sort_option == 0:
            result.sort(key=operator.itemgetter(1))
        self.pattern = pattern
        self.store.clear()
        self.set_n_label(len(result))
        for name, word, score in result:
            t1 = '<span font_desc="Monospace 12">' + word + '</span>'
            self.store.append([t1, name, score])
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
        self.store.append([LOADING_TEXT])
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

class NewWordListDialog(PalabraDialog):
    def __init__(self, parent, path, name=None):
        title = u"New word list"
        if name is not None:
            title = u"Rename word list"
        PalabraDialog.__init__(self, parent, title)
        label = gtk.Label()
        label.set_markup(u"Word list: <b>" + path + "</b>")
        label.set_alignment(0, 0.5)
        self.main.pack_start(label, False, False, 0)
        text = u"Please give the new word list a name:"
        if name is not None:
            text = u"Please give the word list a new name:"
        label = gtk.Label(text)
        label.set_alignment(0, 0.5)
        self.main.pack_start(label, False, False, 0)
        self.entry = gtk.Entry()
        def on_entry_changed(widget):
            self.store_name(widget.get_text().strip())
        self.entry.connect("changed", on_entry_changed)
        self.main.pack_start(self.entry, True, True, 0)
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.ok_button = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        if name is not None:
            self.entry.set_text(name)
        self.store_name(name)
        
    def store_name(self, name=None):
        self.wlist_name = name
        self.ok_button.set_sensitive(False if name is None else len(name) > 0)

class WordListEditor(gtk.Dialog):
    def __init__(self, palabra_window):
        gtk.Dialog.__init__(self, u"Manage word lists"
            , palabra_window, gtk.DIALOG_MODAL)
        self.palabra_window = palabra_window
        
        # name path
        self.store = gtk.ListStore(str, str)
        self.current_wlist = None
        
        self.tree = gtk.TreeView(self.store)
        self.tree.get_selection().connect("changed", self.on_selection_changed)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(u"Name")
        column.pack_start(cell, True)
        column.set_attributes(cell, text=0)
        self.tree.append_column(column)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(u"Path")
        column.pack_start(cell, True)
        column.set_attributes(cell, text=1)
        self.tree.append_column(column)
        
        buttonbox = gtk.HButtonBox()
        buttonbox.set_layout(gtk.BUTTONBOX_START)
        
        self.add_wlist_button = gtk.Button(stock=gtk.STOCK_ADD)
        buttonbox.pack_start(self.add_wlist_button, False, False, 0)
        self.add_wlist_button.connect("clicked", lambda button: self.add_word_list())
        self.rename_button = gtk.Button("Rename")
        buttonbox.pack_start(self.rename_button, False, False, 0)
        self.rename_button.connect("clicked", lambda button: self.rename_word_list())
        self.rename_button.set_sensitive(False)        
        self.remove_button = gtk.Button(stock=gtk.STOCK_REMOVE)
        buttonbox.pack_start(self.remove_button, False, False, 0)
        self.remove_button.connect("clicked", lambda button: self.remove_word_list())
        self.remove_button.set_sensitive(False)
        
        main = gtk.HBox(False, 0)
        main.set_spacing(18)
        
        wlist_vbox = gtk.VBox(False, 0)
        wlist_vbox.set_spacing(12)
        label = gtk.Label()
        label.set_markup("<b>Word lists</b>")
        label.set_alignment(0, 0)
        wlist_vbox.pack_start(label, False, False, 0)
        label = gtk.Label(u"Select a word list for more information:")
        label.set_alignment(0, 0.5)
        wlist_vbox.pack_start(label, False, False, 0)
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add(self.tree)
        scrolled_window.set_size_request(400, -1)
        wlist_vbox.pack_start(scrolled_window, True, True, 0)
        wlist_vbox.pack_start(buttonbox, False, False, 0)
        main.pack_start(wlist_vbox, False, False, 0)
        
        table = gtk.Table(4, 2)
        table.set_col_spacings(6)
        table.set_row_spacings(6)
        table.set_row_spacing(0, 18)
        label = gtk.Label()
        label.set_markup("<b>Properties of selected word list</b>")
        label.set_alignment(0, 0)
        table.attach(label, 0, 2, 0, 1, gtk.FILL, gtk.FILL)        
        
        label = gtk.Label("Number of words:")
        label.set_alignment(0, 0)
        table.attach(label, 0, 1, 1, 2)
        self.n_words_label = gtk.Label("0")
        self.n_words_label.set_alignment(1, 0)
        table.attach(self.n_words_label, 1, 2, 1, 2, gtk.FILL, gtk.FILL)
        
        label = gtk.Label("Average word length:")
        label.set_alignment(0, 0)
        table.attach(label, 0, 1, 2, 3)
        self.avg_word_label = gtk.Label("0")
        self.avg_word_label.set_alignment(1, 0)
        table.attach(self.avg_word_label, 1, 2, 2, 3, gtk.FILL, gtk.FILL)
        
        label = gtk.Label("Average word score:")
        label.set_alignment(0, 0)
        table.attach(label, 0, 1, 3, 4)
        self.avg_score_label = gtk.Label("0")
        self.avg_score_label.set_alignment(1, 0)
        table.attach(self.avg_score_label, 1, 2, 3, 4, gtk.FILL, gtk.FILL)
        
        self.counts_store = gtk.ListStore(int, int)
        tree = gtk.TreeView(self.counts_store)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(u"Length", cell, text=0)
        tree.append_column(column)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(u"Count", cell, text=1)
        tree.append_column(column)
        tree.get_selection().set_mode(gtk.SELECTION_NONE)
        
        self.score_store = gtk.ListStore(int, int)
        score_tree = gtk.TreeView(self.score_store)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(u"Score", cell, text=0)
        score_tree.append_column(column)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(u"Count", cell, text=1)
        score_tree.append_column(column)
        score_tree.get_selection().set_mode(gtk.SELECTION_NONE)
        
        length_window = gtk.ScrolledWindow()
        length_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        length_window.add(tree)
        length_window.set_size_request(300, 300)
        score_window = gtk.ScrolledWindow()
        score_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        score_window.add(score_tree)
        score_window.set_size_request(300, 300)
        
        props_vbox = gtk.VBox(False, 0)
        props_vbox.set_spacing(6)
        props_vbox.pack_start(table)
        tabs = gtk.Notebook()
        tabs.append_page(length_window, gtk.Label(u"Words by length"))
        tabs.append_page(score_window, gtk.Label(u"Words by score"))
        props_vbox.pack_start(tabs)
        
        main.pack_start(props_vbox, True, True, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        hbox.pack_start(main, True, True, 0)
        
        # select a word list by default
        self.display_wordlists()
        it = self.store.get_iter_first()
        if it is not None:
            sel = self.tree.get_selection()
            sel.select_iter(it)
        
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
                message = u"The word list has not been added because it's already in the list."
                mdialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL
                    , gtk.MESSAGE_INFO, gtk.BUTTONS_NONE, message)
                mdialog.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
                mdialog.set_title(u"Duplicate found")
                mdialog.run()
                mdialog.destroy()
                return
            dialog.destroy()
            d = NewWordListDialog(self, path)
            d.show_all()
            if d.run() == gtk.RESPONSE_OK:
                value = {"name": {"type": "str", "value": d.wlist_name}
                    , "path": {"type": "str", "value": path}
                }
                preferences.prefs["word_files"].append(value)
                self.palabra_window.wordlists = create_wordlists(preferences.prefs["word_files"]
                    , previous=self.palabra_window.wordlists)
                self.display_wordlists()
            d.destroy()
        else:
            dialog.destroy()
        
    def on_selection_changed(self, selection):
        store, it = selection.get_selected()
        self.remove_button.set_sensitive(it is not None)
        self.rename_button.set_sensitive(it is not None)
        if it is not None:
            path = store[it][1]
            for wlist in self.palabra_window.wordlists:
                if wlist.path == path:
                    self.current_wlist = wlist
                    self.load_word_counts(wlist.words)

    def load_word_counts(self, words):
        total_n_words = sum([len(words[i]) for i in words.keys()])
        self.n_words_label.set_text(str(total_n_words))
        counts = []
        self.counts_store.clear()
        for k, k_words in words.items():
            n_words = len(k_words)
            if k < 2 or n_words == 0:
                continue
            counts.append((k, n_words))
            self.counts_store.append([k, n_words])
        self.score_store.clear()
        scores = {}
        for k, k_words in words.items():
            for w, s in k_words:
                if s in scores:
                    scores[s] += 1
                else:
                    scores[s] = 1
        s_keys = scores.keys()
        s_keys.sort()
        for k in s_keys:
            self.score_store.append([k, scores[k]])
        total = 0.0
        for l, count in counts:
            total += (l * count)
        total /= total_n_words
        self.avg_word_label.set_text("%.2f" % total)
        total = 0.0
        for s, count in scores.items():
            total += (s * count)
        total /= total_n_words
        self.avg_score_label.set_text("%.2f" % total)
        
    def rename_word_list(self):
        store, it = self.tree.get_selection().get_selected()
        name, path = self.store[it][0], self.store[it][1]
        d = NewWordListDialog(self, path, name=name)
        d.show_all()
        response = d.run()
        if response == gtk.RESPONSE_OK:
            rename_wordlists(preferences.prefs["word_files"]
                , self.palabra_window.wordlists
                , path, d.wlist_name)
            self.store[it][0] = d.wlist_name
            self.tree.columns_autosize()
        d.destroy()
        
    def remove_word_list(self):
        store, it = self.tree.get_selection().get_selected()
        path = self.store[it][1]
        n_prefs, n_wlists = remove_wordlist(preferences.prefs["word_files"]
            , self.palabra_window.wordlists, path)
        preferences.prefs["word_files"] = n_prefs
        self.palabra_window.wordlists = n_wlists
        try:
            self.palabra_window.editor.refresh_words(True)
        except AttributeError:
            pass
        self.display_wordlists()
        
    def display_wordlists(self):
        self.store.clear()
        for p in preferences.prefs["word_files"]:
            self.store.append([p["name"]["value"], p["path"]["value"]])
        n_prefs = len(preferences.prefs["word_files"])
        self.add_wlist_button.set_sensitive(n_prefs < constants.MAX_WORD_LISTS)
        self.counts_store.clear()
        self.score_store.clear()
        self.n_words_label.set_text("0")
        self.avg_word_label.set_text("0")
        self.avg_score_label.set_text("0")
            
class WordWidget(gtk.DrawingArea):
    def __init__(self, editor):
        super(WordWidget, self).__init__()
        self.STEP = 24
        self.selection = None
        self.editor = editor
        self.set_words([])
        self.set_flags(gtk.CAN_FOCUS)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.connect('expose_event', self.expose)
        self.connect("button_press_event", self.on_button_press)
        
    def set_words(self, words):
        self.words = words
        self.selection = None
        self.set_size_request(-1, self.STEP * len(self.words))
        self.queue_draw()
        
    def on_button_press(self, widget, event):
        offset = self.get_word_offset(event.y)
        if offset >= len(self.words):
            self.selection = None
            self.editor.set_overlay(None)
            return
        word = self.words[offset][0]
        if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
            self.editor.insert(word)
            self.selection = None
            self.editor.set_overlay(None)
        else:
            self.selection = offset
            self.editor.set_overlay(word)
        self.queue_draw()
        return True
            
    def get_selected_word(self):
        if self.selection is None:
            return None
        return self.words[self.selection][0]
        
    def get_word_offset(self, y):
        return max(0, int(y / self.STEP)) 
        
    def expose(self, widget, event):
        ctx = widget.window.cairo_create()
        pcr = pangocairo.CairoContext(ctx)
        pcr_layout = pcr.create_layout()
        x, y, width, height = event.area
        ctx.set_source_rgb(65535, 65535, 65535)
        ctx.rectangle(*event.area)
        ctx.fill()
        ctx.set_source_rgb(0, 0, 0)
        offset = self.get_word_offset(y)
        n_rows = 30 #(height / self.STEP) + 1
        for i, (w, score, h) in enumerate(self.words[offset:offset + n_rows]):
            n = offset + i
            color = (0, 0, 0) if h else (65535.0 / 2, 65535.0 / 2, 65535.0 / 2)
            ctx.set_source_rgb(*[c / 65535.0 for c in color])
            markup = ['''<span font_desc="Monospace 12"''']
            if n == self.selection:
                ctx.set_source_rgb(65535, 0, 0)
                markup += [''' underline="double"''']
            markup += [">", w, "</span>"]
            pcr_layout.set_markup(''.join(markup))
            ctx.move_to(5, n * self.STEP)
            pcr.show_layout(pcr_layout)
            
class WordPropertiesDialog(gtk.Dialog):
    def __init__(self, palabra_window, properties):
        gtk.Dialog.__init__(self, u"Word properties", palabra_window
            , gtk.DIALOG_MODAL)
        self.palabra_window = palabra_window
        self.set_size_request(384, 256)
        
        label = gtk.Label()
        label.set_markup(''.join(['<b>', properties["word"], '</b>']))
        
        main = gtk.VBox(False, 0)
        main.set_spacing(18)
        main.pack_start(label, True, True, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        hbox.pack_start(main, True, True, 0)
        
        self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_ACCEPT)
        self.vbox.add(hbox)
