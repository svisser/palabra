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
import sys

import constants
from editor import highlight_cells
from gui_common import (
    create_button,
    create_tree,
    create_scroll,
    create_label,
    create_notebook,
    create_entry,
    PalabraDialog,
    PalabraMessageDialog,
    NameFileDialog,
    obtain_file,
    create_combo,
    create_stock_button,
)
import preferences
from word import (
    create_wordlists,
    check_accidental_words,
    accidental_entries,
    search_wordlists,
    search_wordlists_by_pattern,
    similar_entries,
    similar_words,
    remove_wordlist,
    rename_wordlists,
)

LOADING_TEXT = "Loading..."

class WordListUnableToStoreDialog(PalabraDialog):
    def __init__(self, parent, unable):
        super(WordListUnableToStoreDialog, self).__init__(parent, u"Unable to store word list(s)")
        self.main.pack_start(create_label(constants.TITLE + " was unable to store the following word lists:"))
        self.store, self.tree, window = create_tree(str, [(u"Word list", 0)])
        for name, error in unable:
            self.store.append([name + " (" + error + ")"])
        window.set_size_request(200, 300)
        self.main.pack_start(window, True, True, 0)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)

class WordListEditor(PalabraDialog):
    def __init__(self, parent):
        PalabraDialog.__init__(self, parent, u"Edit word lists", horizontal=True)
        self.wordlists = parent.wordlists
        # name path
        self.store, self.tree, s_window = create_tree((str, str)
            , [("Available word lists", 0)]
            , f_sel=self.on_tree_selection_changed
            , window_size=(256, 196))
        for wlist in self.wordlists:
            self.store.append([wlist.name, wlist.path])
        self.main.pack_start(s_window, True, True, 0)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        
    def on_tree_selection_changed(self, selection):
        store, it = selection.get_selected()

class WordUsageDialog(PalabraDialog):
    def __init__(self, parent):
        super(WordUsageDialog, self).__init__(parent
            , u"Configure word list usage", horizontal=True)
        self.wordlists = parent.wordlists
        pages = [(self.create_find_words(parent), u"Finding words")
            #, (self.create_blacklist(parent), u"Blacklist")
        ]
        self.main.pack_start(create_notebook(pages, border=(8, 4)))
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        
    def create_blacklist(self, parent):
        vbox = gtk.VBox()
        vbox.set_border_width(9)
        vbox.set_spacing(9)
        self.blacklist_combo = create_combo([''] + [w.name for w in self.wordlists])
        for i, wlist in enumerate(self.wordlists):
            if preferences.prefs[constants.PREF_BLACKLIST] == wlist.path:
                self.blacklist_combo.set_active(i + 1)
                break
        vbox.pack_start(create_label(u"Word list to be used as blacklist:"), False, False, 0)
        vbox.pack_start(self.blacklist_combo, False, False, 0)
        return vbox
        
    def create_find_words(self, parent):
        hbox = gtk.HBox()
        hbox.set_spacing(9)
        # name path
        self.store, self.tree, s_window = create_tree((str, str)
            , [("Available word lists", 0)]
            , f_sel=self.on_tree_selection_changed
            , window_size=(256, 196))
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
            , f_sel=self.on_tree2_selection_changed
            , window_size=(256, 196))
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
        score_hbox.pack_start(create_label(u"Minimum word score:"), False, False, 0)
        value = preferences.prefs[constants.PREF_FIND_WORD_MIN_SCORE]
        adj = gtk.Adjustment(value, 0, 100, 1, 0, 0)
        self.find_min_score_spinner = gtk.SpinButton(adj, 0.0, 0)
        score_hbox.pack_start(self.find_min_score_spinner, False, False, 0)
        vbox.pack_start(hbox)
        vbox.pack_start(score_hbox, False, False, 0)
        label = create_label(u"These settings are loaded when you start " + constants.TITLE + ".")
        vbox.pack_start(label, False, False, 0)
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
        #b_index = self.blacklist_combo.get_active()
        #if b_index >= 1:
        #    c[constants.PREF_BLACKLIST] = self.wordlists[b_index - 1].path
        #else:
        #    c[constants.PREF_BLACKLIST] = ''
        c[constants.PREF_FIND_WORD_MIN_SCORE] = self.find_min_score_spinner.get_value_as_int()
        return c

class SimilarWordsDialog(PalabraDialog):
    def __init__(self, parent, puzzle):
        super(SimilarWordsDialog, self).__init__(parent, u"View similar words")
        self.puzzle = puzzle
        self.store, self.tree, scrolled_window = create_tree((str, str)
            , [(u"Similar words", 1)]
            , f_sel=self.on_selection_changed
            , window_size=(512, 384))
        self.main.pack_start(scrolled_window, True, True, 0)
        self.main.pack_start(create_label(u"Click to highlight the words in the grid."), False, False, 0)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        destroy = lambda w: highlight_cells(self.pwindow, self.puzzle, clear=True)
        self.connect("destroy", destroy)
        self.entries = similar_entries(similar_words(puzzle.grid))
        self.load_entries(self.entries)
        
    def load_entries(self, entries):
        self.store.clear()
        items = entries.items()
        items.sort(key=operator.itemgetter(0))
        for key, words in iterate_similars(items):
            txt = '<span font_desc="Monospace 12">' + key.lower() + ": "
            for pre, middle, post, comma in words:
                txt += pre + '<span foreground="red">' + middle + '</span>' + post
                if comma:
                    txt += ', '
            txt += '</span>'
            self.store.append([key, txt])
    
    def on_selection_changed(self, selection):
        """Highlight all cells associated with the selected entry."""
        store, it = selection.get_selected()
        if it is not None:
            slots = [(x, y, d) for x, y, d, word, o in self.entries[store[it][0]]]
            highlight_cells(self.pwindow, self.puzzle, "slots", slots)

def iterate_similars(items):
    """Iterate over all items for the similar words dialog."""
    for s, words in items:
        l_words = len(words)
        l_s = len(s)
        values = []
        for i, (x, y, d, word, pos) in enumerate(words):
            o1 = word[0:pos]
            o2 = word[pos:pos + l_s]
            o3 = word[pos + l_s:]
            values.append((o1, o2, o3, i < l_words - 1))
        yield s, values

def merge_highlights(data, indices):
    """Merge the cells in the data corresponding to the given indices."""
    cells = []
    for index in indices.split(','):
        cells.extend([(x, y) for x, y, c in data[int(index)][1]])
    return cells

class AccidentalWordsDialog(PalabraDialog):
    def __init__(self, parent, puzzle):
        super(AccidentalWordsDialog, self).__init__(parent, u"View accidental words")
        self.puzzle = puzzle
        self.wordlists = parent.wordlists
        self.index = 0
        self.collapse = True
        self.timer = None
        wlist_hbox = gtk.HBox(False, 0)
        wlist_hbox.pack_start(create_label(u"Check for words in list:"), True, True, 0)
        def on_wordlist_changed(widget):
            self.index = widget.get_active()
            self.launch_accidental(self.puzzle.grid)
        combo = create_combo([w.name for w in self.wordlists]
            , active=self.index, f_change=on_wordlist_changed)
        wlist_hbox.pack_start(combo, False, False, 0)
        self.main.pack_start(wlist_hbox, False, False, 0)
        self.store, self.tree, s_window = create_tree((str, str)
            , [(u"Word", 0)], window_size=(300, 300))
        self.tree.get_selection().connect("changed", self.on_selection_changed)
        self.main.pack_start(s_window, True, True, 0)
        self.main.pack_start(create_label(u"Click to highlight the word(s) in the grid."), False, False, 0)
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
        if self.timer is not None:
            glib.source_remove(self.timer)
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
            cells = merge_highlights(self.results, self.store[it][1])
            highlight_cells(self.pwindow, self.puzzle, "cells", cells)

class FindWordsDialog(PalabraDialog):
    def __init__(self, parent):
        super(FindWordsDialog, self).__init__(parent, u"Find words")
        self.wordlists = parent.wordlists
        self.sort_option = 0
        self.pattern = None
        self.pack(create_label(u"Use ? for an unknown letter and * for zero or more unknown letters."))
        def on_entry_changed(widget):
            glib.source_remove(self.timer)
            self.launch_pattern(widget.get_text().strip())
        self.pack(create_entry(f_change=on_entry_changed), False)
        # word path score
        self.store, self.tree, s_window = create_tree((str, str, int)
            , [(u"Word", 0), (u"Word list", 1), (u"Score", 2)]
            , window_size=(-1, 300)
        )
        self.tree.get_column(0).set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.tree.get_column(0).set_fixed_width(250)
        self.pack(s_window)
        self.n_label = create_label("")
        self.set_n_label(0)
        self.pack(self.n_label, False)
        sort_hbox = gtk.HBox(False, 6)
        sort_hbox.pack_start(create_label(u"Sort by:"), False, False, 0)
        def on_sort_changed(combo):
            self.sort_option = combo.get_active()
            self.launch_pattern(self.pattern)
        sort_hbox.pack_start(create_combo(["Alphabet", "Length", "Score"]
            , active=self.sort_option, f_change=on_sort_changed))
        self.pack(sort_hbox, False)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        self.launch_pattern(None)
        
    def set_n_label(self, n):
        """Display the number of words that match the user's pattern."""
        self.n_label.set_text(u"Number of matching words: " + str(n))
        
    def launch_pattern(self, pattern=None):
        """Start a timer and display the words when the timer has expired."""
        self.store.clear()
        if pattern is not None and len(pattern) > 0:
            self.store.append([LOADING_TEXT, '', 0])
        def find_words(pattern=None):
            if pattern is None:
                return False
            result = search_wordlists_by_pattern(self.wordlists, pattern, sort=self.sort_option)
            self.pattern = pattern
            self.store.clear()
            self.set_n_label(len(result))
            for name, word, score in result:
                t1 = '<span font_desc="Monospace 12">' + word + '</span>'
                self.store.append([t1, name, score])
            return False
        self.timer = glib.timeout_add(constants.INPUT_DELAY, find_words, pattern)

class AnagramDialog(gtk.Dialog):
    def __init__(self, parent):
        gtk.Dialog.__init__(self, u"Find anagrams", parent, gtk.DIALOG_MODAL)
        self.wordlists = parent.wordlists
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        main = gtk.VBox(False, 0)
        main.set_spacing(18)
        
        main.pack_start(create_entry(f_change=self.on_buffer_changed), False, False, 0)
        
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

class NewWordListDialog(NameFileDialog):
    def __init__(self, parent, path, name=None):
        self.p_title = u"New word list" if name is None else u"Rename word list"
        self.p_message = u"Word list: <b>" + path + "</b>"
        self.p_message2 = u"Please give the new word list a name:"
        if name is not None:
            self.p_message2 = u"Please give the word list a new name:"
        super(NewWordListDialog, self).__init__(parent, path, name)

class WordListPropertiesDialog(PalabraDialog):
    def __init__(self, parent, wlist):
        super(WordListPropertiesDialog, self).__init__(parent, u"Word list properties")
        table = gtk.Table(4, 2)
        table.set_col_spacings(6)
        table.set_row_spacings(6)
        def create_row(y, title, info):
            table.attach(create_label(title), 0, 1, y, y + 1)
            info_label = create_label(info, align=(1, 0))
            table.attach(info_label, 1, 2, y, y + 1)
            return info_label
        create_row(0, u"Word list:", wlist.name)
        self.n_words_label = create_row(1, u"Number of words:", u"0")
        self.avg_word_label = create_row(2, u"Average word length:", u"0")
        self.avg_score_label = create_row(3, u"Average word score:", u"0")
        self.counts_store, tree, l_window = create_tree((int, int)
            , [(u"Length", 0), (u"Count", 1)], window_size=(300, 300))
        self.score_store, score_tree, s_window = create_tree((int, int)
            , [(u"Score", 0), (u"Count", 1)], window_size=(300, 300))
        self.main.pack_start(table)
        pages = [(l_window, u"Words by length"), (s_window, u"Words by score")]
        self.main.pack_start(create_notebook(pages))
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        self.n_words_label.set_text(str(wlist.count_words()))
        counts = wlist.get_word_counts()
        scores = wlist.get_score_counts()
        for l in sorted(wlist.words.keys()):
            if counts[l] == 0:
                continue
            self.counts_store.append([l, counts[l]])
        for k in sorted(scores.keys()):
            self.score_store.append([k, scores[k]])
        self.avg_word_label.set_text("%.2f" % wlist.average_word_length())
        self.avg_score_label.set_text("%.2f" % wlist.average_word_score())

class DuplicateWordListDialog(PalabraMessageDialog):
    def __init__(self, parent):
        super(DuplicateWordListDialog, self).__init__(parent
            , u"Duplicate found"
            , u"The word list has not been added because it's already in the list."
        )

def get_words_by_length(wlist):
    words = []
    for l in wlist.words.keys():
        words.extend([(w, score, True) for w, score in wlist.words[l]])
    words.sort(key=operator.itemgetter(0))
    return words

def iterate_word_lists():
    data = preferences.prefs[constants.PREF_WORD_FILES]
    wlists = [(p["name"]["value"], p["path"]["value"]) for p in data]
    for wlist in sorted(wlists, key=operator.itemgetter(0)):
        yield wlist

class WordListManager(PalabraDialog):
    def __init__(self, parent):
        super(WordListManager, self).__init__(parent, u"Manage word lists")
        self.palabra_window = parent
        self.modifications = set()
        # name path
        self.store, self.tree, s_window = create_tree((str, str)
            , [(u"Name", 0), (u"Path", 1)]
            , f_sel=self.on_selection_changed
            , window_size=(400, 400))
        self.current_wlist = None
        self.add_wlist_button = create_stock_button(gtk.STOCK_ADD, lambda b: self.add_word_list())
        self.rename_button = create_button(u"Rename", f_click=lambda b: self.rename_word_list())
        def show_word_list_props():
            w = WordListPropertiesDialog(self, self.current_wlist)
            w.show_all()
            w.run()
            w.destroy()
        self.props_button = create_stock_button(gtk.STOCK_PROPERTIES, lambda b: show_word_list_props())
        self.remove_button = create_stock_button(gtk.STOCK_REMOVE, lambda b: self.remove_word_list())
        buttonbox = gtk.HButtonBox()
        buttonbox.set_layout(gtk.BUTTONBOX_START)
        buttonbox.pack_start(self.add_wlist_button)
        buttonbox.pack_start(self.rename_button)
        buttonbox.pack_start(self.props_button)
        buttonbox.pack_start(self.remove_button)
        self.wlist_sensitives = [self.rename_button, self.props_button, self.remove_button]
        for b in self.wlist_sensitives:
            b.set_sensitive(False)
        wlist_vbox = gtk.VBox()
        wlist_vbox.set_spacing(12)
        wlist_vbox.pack_start(create_label("<b>Word lists</b>"), False, False, 0)
        wlist_vbox.pack_start(s_window)
        wlist_vbox.pack_start(buttonbox, False, False, 0)
        main = gtk.HBox()
        main.set_spacing(18)
        main.pack_start(wlist_vbox, False, False, 0)
        main.pack_start(self.create_contents_tab())
        self.main.pack_start(main)
        label = create_label(u"These word lists are loaded when you start " + constants.TITLE + ".")
        self.main.pack_start(label, False, False, 0)
        self.display_wordlists()
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        
    def create_contents_tab(self):
        self.word_widget = EditWordWidget()
        vbox = gtk.VBox()
        vbox.set_border_width(6)
        vbox.set_spacing(6)
        vbox.pack_start(create_scroll(self.word_widget, True, size=(300, -1)))
        hbox = gtk.HBox()
        hbox.set_spacing(6)
        vbox.pack_start(hbox, False, False, 0)
        return vbox
        
    # TODO not in use
    def on_edit_score(self, cell, path, value):
        it = self.w_store.get_iter(path)
        try:
            value = int(value)
            if constants.MIN_WORD_SCORE <= value <= constants.MAX_WORD_SCORE:
                word = self.w_store[it][0]
                self.w_store.set(it, 2, value)
                self.current_wlist.update_score(word, value)
                self.modifications.add(self.current_wlist)
        except ValueError:
            pass
        
    def add_word_list(self):
        paths = [p["path"]["value"] for p in preferences.prefs[constants.PREF_WORD_FILES]]
        value = obtain_file(self, u"Add word list", paths
            , u"The word list has not been added because it's already in the list."
            , NewWordListDialog)
        if value is not None:
            preferences.prefs[constants.PREF_WORD_FILES].append(value)
            self.palabra_window.wordlists = create_wordlists(preferences.prefs[constants.PREF_WORD_FILES]
                , previous=self.palabra_window.wordlists)
            self.display_wordlists()
        
    def on_selection_changed(self, selection):
        store, it = selection.get_selected()
        for b in self.wlist_sensitives:
            b.set_sensitive(it is not None)
        if it is not None:
            path = store[it][1]
            for wlist in self.palabra_window.wordlists:
                if wlist.path == path:
                    self.current_wlist = wlist
                    self.word_widget.set_words(get_words_by_length(wlist))
        
    def rename_word_list(self):
        store, it = self.tree.get_selection().get_selected()
        name, path = self.store[it][0], self.store[it][1]
        d = NewWordListDialog(self, path, name=name)
        d.show_all()
        response = d.run()
        if response == gtk.RESPONSE_OK:
            rename_wordlists(preferences.prefs[constants.PREF_WORD_FILES]
                , self.palabra_window.wordlists
                , path, d.given_name)
            self.store[it][0] = d.given_name
            self.tree.columns_autosize()
        d.destroy()
        
    def remove_word_list(self):
        store, it = self.tree.get_selection().get_selected()
        path = self.store[it][1]
        n_prefs, n_wlists = remove_wordlist(preferences.prefs[constants.PREF_WORD_FILES]
            , self.palabra_window.wordlists, path)
        preferences.prefs[constants.PREF_WORD_FILES] = n_prefs
        self.palabra_window.wordlists = n_wlists
        if preferences.prefs[constants.PREF_BLACKLIST] == path:
            self.palabra_window.blacklist = None
            preferences.prefs[constants.PREF_BLACKLIST] = ''
        if path in preferences.prefs[constants.PREF_FIND_WORD_FILES]:
            preferences.prefs[constants.PREF_FIND_WORD_FILES].remove(path)
        self.palabra_window.refresh_words(True)
        self.display_wordlists()
        
    def display_wordlists(self):
        self.store.clear()
        wlists = list(iterate_word_lists())
        for wlist in wlists:
            self.store.append(wlist)
        self.add_wlist_button.set_sensitive(len(wlists) < constants.MAX_WORD_LISTS)
        self.word_widget.set_words([])

class WordWidget(gtk.DrawingArea):
    def __init__(self):
        super(WordWidget, self).__init__()
        self.STEP = 24
        self.set_words([])
        self.connect('expose_event', self.expose)

    def set_words(self, words):
        self.words = words
        self.selection = None
        self.set_size_request(-1, self.STEP * len(self.words))
        self.queue_draw()

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
        for n, w, score, h in self.visible_words(y):
            color = (0, 0, 0) if h else (65535.0 / 2, 65535.0 / 2, 65535.0 / 2)
            ctx.set_source_rgb(*[c / 65535.0 for c in color])
            markup = ['<span font_desc="Monospace 12"']
            if n == self.selection:
                ctx.set_source_rgb(65535, 0, 0)
                markup += [' underline="single"']
            markup += [">", w, "</span>"]
            pcr_layout.set_markup(''.join(markup))
            ctx.move_to(5, n * self.STEP)
            pcr.show_layout(pcr_layout)
            
    def visible_words(self, y):
        offset = self.get_word_offset(y)
        n_rows = 30 #(height / self.STEP) + 1
        for i, (w, score, h) in enumerate(self.words[offset:offset + n_rows]):
            yield offset + i, w, score, h

    def get_selected_word(self):
        if self.selection is None:
            return None
        return self.words[self.selection][0]

class EditWordWidget(WordWidget):
    def __init__(self):
        super(EditWordWidget, self).__init__()
        self.set_flags(gtk.CAN_FOCUS)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.connect("button_press_event", self.on_button_press)
        
    def on_button_press(self, widget, event):
        offset = self.get_word_offset(event.y)
        if offset >= len(self.words):
            self.selection = None
            self.queue_draw()
            return True
        word = self.words[offset][0]
        if event.button == 1:
            self.selection = offset
        self.queue_draw()
        return True

class EditorWordWidget(WordWidget):
    def __init__(self, parent):
        super(EditorWordWidget, self).__init__()
        self.editor = parent.editor
        self.set_flags(gtk.CAN_FOCUS)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.connect("button_press_event", self.on_button_press)
        
    def on_button_press(self, widget, event):
        offset = self.get_word_offset(event.y)
        if offset >= len(self.words):
            self.selection = None
            self.editor.set_overlay(None)
            return True
        word = self.words[offset][0]
        if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
            self.editor.insert(word)
            self.selection = None
            self.editor.set_overlay(None)
        elif event.button == 1:
            self.selection = offset
            self.editor.set_overlay(word)
        self.queue_draw()
        return True
            
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
