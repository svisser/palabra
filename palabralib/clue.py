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

import gobject
import gtk

import transform

class ClueTool:
    def __init__(self, editor):
        self.editor = editor
        self.last = None
        
        self.settings = {}
        self.settings["use_scrolling"] = True
        
    def create(self, puzzle):
        vbox = gtk.VBox(False, 0)
        vbox.set_spacing(6)
        vbox.set_border_width(6)
        
        changed = lambda widget: self.on_clue_changed(widget, "text")
        label = gtk.Label()
        label.set_markup(u"<b>Clue</b>")
        label.set_alignment(0, 0.5)
        self.clue_entry = gtk.Entry()
        self.clue_changed_id = self.clue_entry.connect("changed", changed)
        self.clue_entry.set_sensitive(False)
        vbox.pack_start(label, False, False, 3)
        vbox.pack_start(self.clue_entry, False, False, 0)
        
        changed = lambda widget: self.on_clue_changed(widget, "explanation")
        label = gtk.Label()
        label.set_markup(u"<b>Explanation</b>")
        label.set_alignment(0, 0.5)
        self.explanation_entry = gtk.Entry()
        self.explanation_changed_id = self.explanation_entry.connect("changed", changed)
        self.explanation_entry.set_sensitive(False)
        # disable for release
        vbox.pack_start(label, False, False, 3)
        vbox.pack_start(self.explanation_entry, False, False, 0)
        
        # number x y direction word clue explanation displayed_string
        self.store = gtk.ListStore(int, int, int, str, str, str, str, str)
        
        self.tree = gtk.TreeView(self.store)
        self.selection_changed_id = self.tree.get_selection().connect("changed"
            , self.on_selection_changed)
        self.tree.set_headers_visible(False)
        
        self.load_items(puzzle)
        
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("", cell, markup=7)
        self.tree.append_column(column)
        
        window = gtk.ScrolledWindow(None, None)
        window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        window.add(self.tree)

        label = gtk.Label()
        label.set_markup(u"<b>Words and clues</b>")
        label.set_alignment(0, 0.5)
        label.set_padding(3, 3)
        
        vbox.pack_start(gtk.HSeparator(), False, False, 0)
        vbox.pack_start(label, False, False, 0)
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
            explanation = store[it][6]
            
            value = widget.get_text()
            if key == "text":
                clue = value
                store[it][5] = value
            elif key == "explanation":
                explanation = value
                store[it][6] = value

            display = self.create_display_string(n, direction, word, clue)
            store[it][7] = display
            
            self.editor.clue(x, y, direction, key, value)
            
            self.tree.columns_autosize()
            self.tree.queue_draw()
        
    def create_display_string(self, n, direction, word, clue):
        """Construct the displayed string for a word/clue item."""
        c = gobject.markup_escape_text(clue) if len(clue) > 0 else "<span foreground=\"red\">No clue yet.</span>"
        d = {"across": "Across", "down": "Down"}[direction]
        return ''.join(["<b>", d, ", ", str(n), "</b>:\n<i>", word, "</i>\n", c])

    def load_items(self, puzzle):
        """Load all word/clue items and put them in the ListStore."""
        def locked():
            self.store.clear()
            for row in puzzle.grid.gather_words():
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
            self.editor.set_selection(x, y, direction, full_update=False)
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
        selection.handler_block(self.selection_changed_id)
        self.clue_entry.handler_block(self.clue_changed_id)
        self.explanation_entry.handler_block(self.explanation_changed_id)
        code()
        selection.handler_unblock(self.selection_changed_id)
        self.clue_entry.handler_unblock(self.clue_changed_id)
        self.explanation_entry.handler_unblock(self.explanation_changed_id)
