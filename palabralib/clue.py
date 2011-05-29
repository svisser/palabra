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

from collections import namedtuple
import gobject
import gtk
import os

import constants
from gui_common import (
    create_button,
    create_tree,
    create_label,
    create_notebook,
    PalabraDialog,
)
import transform

ClueFile = namedtuple('ClueFile', ['path', 'name', 'data'])

def read_clues(path):
    if not os.path.exists(path):
        return {}
    clues = {}
    with open(path, 'r') as f:
        lower = str.lower
        for line in f:
            line = line.strip("\n")
            line = line.split(",")
            l_line = len(line)
            if not line or l_line != 2:
                continue
            word, clue = line
            if not word or not clue:
                continue
            clue = clue.strip()
            if " " in word: # for now, reject compound
                continue
            if len(word) > constants.MAX_WORD_LENGTH:
                continue
            l_word = lower(word)
            if l_word not in clues:
                clues[l_word] = [clue]
            else:
                clues[l_word].append(clue)
    return clues

def create_clues(prefs):
    files = []
    for data in prefs:
        path = data["path"]["value"]
        name = data["name"]["value"]
        files.append(ClueFile(path, name, read_clues(path)))
    return files

def lookup_clues(files, word):
    clues = []
    for c in files:
        if word in c.data:
            clues.extend(c.data[word])
    return clues

class ClueTool:
    def __init__(self, parent):
        self.parent = parent
        self.settings = {"use_scrolling": True}
    
    def create_entry(self, vbox, key, title):
        entry = gtk.Entry()
        changed = lambda w: self.on_clue_changed(key, w.get_text())
        c_id = entry.connect("changed", changed)
        entry.set_sensitive(False)
        vbox.pack_start(create_label(title), False, False, 3)
        vbox.pack_start(entry, False, False, 0)
        return entry, c_id
        
    def create(self, puzzle):
        vbox = gtk.VBox(False, 0)
        vbox.set_spacing(6)
        vbox.set_border_width(6)
        result = self.create_entry(vbox, "text", u"<b>Clue</b>")
        self.clue_entry, self.c_changed_id = result
        
        # number x y direction word clue explanation displayed_string
        types = (int, int, int, str, str, str, str, str)
        self.store, self.tree, window, self.selection_id = create_tree(types
            , [(u"", 7)]
            , f_sel=self.on_selection_changed
            , return_id=True)
        vbox.pack_start(gtk.HSeparator(), False, False, 0)
        
        o_vbox = gtk.VBox()
        o_vbox.set_spacing(6)
        o_vbox.set_border_width(6)
        result = self.create_entry(o_vbox, "explanation", u"<b>Explanation</b>")
        self.explanation_entry, self.e_changed_id = result
        
        w_hbox = gtk.HBox()
        w_hbox.set_spacing(6)
        w_hbox.pack_start(create_label(u"Word:"), False, False, 0)
        w_entry = gtk.Entry()
        def on_word_changed(widget):
            self.load_clues_for_word(widget.get_text().strip())
        w_entry.connect("changed", on_word_changed)
        w_hbox.pack_start(w_entry)
        o_vbox.pack_start(create_label(u"<b>Lookup clues</b>"), False, False, 0)
        o_vbox.pack_start(w_hbox, False, False, 0)
        self.c_store, self.c_tree, c_window = create_tree(str
            , [(u"Clues", 0)]
            , f_sel=self.on_clue_selected)
        o_vbox.pack_start(c_window, True, True, 0)
        self.use_clue_button = create_button(u"Use clue"
            , align=(0, 0.5), f_click=self.on_use_clicked)
        self.use_clue_button.set_sensitive(False)
        o_vbox.pack_start(self.use_clue_button, False, False, 0)
                
        pages = [(window, u"Words and clues"), (o_vbox, u"Advanced")]
        tabs = create_notebook(pages)
        tabs.set_property("tab-hborder", 4)
        tabs.set_property("tab-vborder", 2)
        vbox.pack_start(tabs)
        self.tree.set_headers_visible(False)
        self.load_items(puzzle.grid)
        return vbox
        
    def on_clue_selected(self, selection):
        store, it = selection.get_selected()
        store, it_main = self.tree.get_selection().get_selected()
        self.use_clue_button.set_sensitive(it is not None and it_main is not None)
    
    def on_use_clicked(self, button):
        store, it = self.c_tree.get_selection().get_selected()
        self.clue_entry.set_text(store[it][0])
        
    def load_clues_for_word(self, word):
        self.c_store.clear()
        for c in sorted(lookup_clues(self.parent.clues, word)):
            self.c_store.append([gobject.markup_escape_text(c)])
        
    def on_clue_changed(self, key, value):
        """
        Update the ListStore/tree and create or update an undoable action.
        """
        store, it = self.tree.get_selection().get_selected()
        if it is not None:
            n = store[it][0]
            x = store[it][1]
            y = store[it][2]
            direction = store[it][3]
            word = store[it][4]
            clue = store[it][5]
            if key == "text":
                clue = value
                store[it][5] = value
            elif key == "explanation":
                store[it][6] = value
            display = self.create_display_string(n, direction, word, clue)
            store[it][7] = display
            self.parent.editor.clue(x, y, direction, key, value)
            self.tree.columns_autosize()
            self.tree.queue_draw()
        
    def create_display_string(self, n, direction, word, clue):
        """Construct the displayed string for a word/clue item."""
        c = gobject.markup_escape_text(clue) if len(clue) > 0 else '<span foreground="red">No clue yet.</span>'
        d = constants.DIRECTION_NAMES[direction]
        return ''.join(["<b>", d, ", ", str(n), "</b>:\n<i>", word, "</i>\n", c])

    def load_items(self, grid):
        """Load all word/clue items and put them in the ListStore."""
        def locked():
            self.store.clear()
            for row in grid.gather_words():
                n, x, y, d, word, clue, explanation = row
                display = self.create_display_string(n, d, word, clue)
                item = (n, x, y, d, word, clue, explanation, display)
                self.store.append(item)
        selection = self.tree.get_selection()
        self.perform_while_locked(selection, locked)
        
    def update_current_word(self, clue, explanation):
        """Put the clue data of the word at (x, y, direction) in the text entries."""
        self.set_clue_editor_status(True)
        self.clue_entry.set_text(clue)
        self.explanation_entry.set_text(explanation)
            
    def set_clue_editor_status(self, status):
        """Enable or disable the text entries for editing clue data."""
        self.clue_entry.set_sensitive(status)
        self.explanation_entry.set_sensitive(status)
        store, it = self.c_tree.get_selection().get_selected()
        self.use_clue_button.set_sensitive(status and it is not None)
        if not status:
            self.clue_entry.set_text("")
            self.explanation_entry.set_text("")
            self.deselect()

    def on_selection_changed(self, selection):
        """When the selection changes, update the state of the edit controls."""
        store, it = selection.get_selected()
        if it is None:
            def locked():
                self.set_clue_editor_status(False)
            self.perform_while_locked(selection, locked)
            return
        x = store[it][1]
        y = store[it][2]
        direction = store[it][3]
        clue = store[it][5]
        explanation = store[it][6]
        def locked():
            self.update_current_word(clue, explanation)
            self.settings["use_scrolling"] = False
            self.parent.editor.set_selection(x, y, direction, full_update=False)
            self.settings["use_scrolling"] = True
        self.perform_while_locked(selection, locked)
        
    def select(self, x, y, direction):
        """Select the word starting at the given (x, y, direction)."""
        if x < 0 or y < 0:
            return
        selection = self.tree.get_selection()            
        for row in self.store:
            if (row[1], row[2], row[3]) == (x, y, direction):
                def locked():
                    selection.select_path(row.path)
                    if self.settings["use_scrolling"]:
                        self.tree.scroll_to_cell(row.path)
                    self.update_current_word(row[5], row[6])
                self.perform_while_locked(selection, locked)
        
    def deselect(self):
        """Deselect all word/clue items in the list."""
        self.tree.get_selection().unselect_all()
        
    def perform_while_locked(self, selection, code):
        """
        Execute the given code while preventing GTK callbacks from running.
        """
        ITEMS = [(selection, self.selection_id)
            , (self.clue_entry, self.c_changed_id)
            , (self.explanation_entry, self.e_changed_id)]
        for w, i in ITEMS:
            w.handler_block(i)
        code()
        for w, i in ITEMS:
            w.handler_unblock(i)
