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
    create_tree,
    create_label,
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

class EditClueDialog(PalabraDialog):
    def __init__(self, parent):
        PalabraDialog.__init__(self, parent, "Edit clue")
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)

class ClueTool:
    def __init__(self, parent):
        self.parent = parent
        self.settings = {"use_scrolling": True}
        
    def create(self, puzzle):
        vbox = gtk.VBox(False, 0)
        vbox.set_spacing(6)
        vbox.set_border_width(6)
        def create_entry(key, title):
            entry = gtk.Entry()
            c_id = entry.connect("changed", lambda w: self.on_clue_changed(w, key))
            entry.set_sensitive(False)
            vbox.pack_start(create_label(title), False, False, 3)
            vbox.pack_start(entry, False, False, 0)
            return entry, c_id
        self.clue_entry, self.c_changed_id = create_entry("text", u"<b>Clue</b>")
        self.explanation_entry, self.e_changed_id = create_entry("explanation", u"<b>Explanation</b>")
        
        def on_edit_clue(button):
            w = EditClueDialog(self.parent)
            w.show_all()
            w.run()
            w.destroy()
        edit_button = gtk.Button(stock=gtk.STOCK_EDIT)
        edit_button.connect("clicked", on_edit_clue)
        align = gtk.Alignment(1, 0.5)
        align.add(edit_button)
        vbox.pack_start(align, False, False, 0)
        
        # number x y direction word clue explanation displayed_string
        types = (int, int, int, str, str, str, str, str)
        self.store, self.tree, window, self.selection_id = create_tree(types
            , [(u"", 7)]
            , f_sel=self.on_selection_changed
            , return_id=True)
        self.tree.set_headers_visible(False)
        self.load_items(puzzle.grid)
        vbox.pack_start(gtk.HSeparator(), False, False, 0)
        vbox.pack_start(create_label(u"<b>Words and clues</b>", padding=(3, 3)), False, False, 0)
        vbox.pack_start(window, True, True, 0)
        return vbox
        
    def on_clue_changed(self, widget, key):
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
            value = widget.get_text()
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
