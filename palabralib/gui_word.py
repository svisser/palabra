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
from word import (
    check_accidental_words,
    accidental_entries,
    search_wordlists_by_pattern,
)

LOADING_TEXT = "Loading..."

class PalabraDialog(gtk.Dialog):
    def __init__(self, pwindow, title):
        gtk.Dialog.__init__(self, title, pwindow, gtk.DIALOG_MODAL)
        self.pwindow = pwindow
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        self.main = gtk.VBox(False, 0)
        self.main.set_spacing(9)
        hbox.pack_start(self.main, True, True, 0)
        self.vbox.pack_start(hbox, True, True, 0)

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
        combo.connect("changed",on_wordlist_changed)
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
        """Compute and display the words of the grid found in the wordlist."""
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
            self.store.append([LOADING_TEXT, ''])
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
        for name, s in result:
            t1 = '<span font_desc="Monospace 12">' + s + '</span>'
            self.store.append([t1, name])
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
        for i, (w, h) in enumerate(self.words[offset:offset + n_rows]):
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
