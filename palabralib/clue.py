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
import glib
import gobject
import gtk
import operator
import os

import constants
from gui_common import (
    create_button,
    create_tree,
    create_label,
    create_notebook,
    PalabraDialog,
    NameFileDialog,
    obtain_file,
    create_stock_button,
)
import preferences
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
            c_index = line.find(",")
            if c_index < 0:
                continue
            word, clue = line[:c_index], line[c_index + 1:]
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
    l_word = word.lower()
    clues = []
    for c in files:
        if l_word in c.data:
            clues.extend(c.data[l_word])
    return clues

class ClueFileDialog(NameFileDialog):
    def __init__(self, parent, path, name=None):
        self.p_title = u"New clue database" if name is None else u"Rename clue database"
        self.p_message = u"Clue database: <b>" + path + "</b>"
        self.p_message2 = u"Please give the new clue database a name:"
        if name is not None:
            self.p_message2 = u"Please give the clue database a new name:"
        NameFileDialog.__init__(self, parent, path, name)
    
class ManageCluesDialog(PalabraDialog):
    def __init__(self, parent):
        PalabraDialog.__init__(self, parent, u"Manage clue databases")
        self.pwindow = parent
        self.store, self.tree, window = create_tree((str, str)
            , [(u"Name", 0), (u"Path", 1)]
            , f_sel=self.on_file_selected
            , window_size=(300, 300))
        self.pack(window)
        buttonbox = gtk.HButtonBox()
        buttonbox.set_layout(gtk.BUTTONBOX_START)
        self.add_file_button = create_stock_button(gtk.STOCK_ADD
            , f_click=lambda b: self.on_add_clue_db())
        buttonbox.pack_start(self.add_file_button, False, False, 0)
        self.remove_button = create_stock_button(gtk.STOCK_REMOVE
            , f_click=lambda b: self.on_remove_db())
        buttonbox.pack_start(self.remove_button, False, False, 0)
        self.remove_button.set_sensitive(False)
        self.pack(buttonbox)
        label = create_label(u"These clue databases are loaded when you start " + constants.TITLE + ".")
        self.pack(label, False)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        self.load_clue_files(parent.clues)
    
    def on_add_clue_db(self):
        paths = [p["path"]["value"] for p in preferences.prefs[constants.PREF_CLUE_FILES]]
        value = obtain_file(self, u"Add clue database", paths
            , u"The clue database has not been added because it's already in the list."
            , ClueFileDialog)
        if value is not None:
            preferences.prefs[constants.PREF_CLUE_FILES].append(value)
            self.pwindow.clues = create_clues(preferences.prefs[constants.PREF_CLUE_FILES])
            self.load_clue_files(self.pwindow.clues)
    
    def on_remove_db(self):
        store, it = self.tree.get_selection().get_selected()
        path = self.store[it][1]
        n_prefs = [p for p in preferences.prefs[constants.PREF_CLUE_FILES] if p["path"]["value"] != path]
        preferences.prefs[constants.PREF_CLUE_FILES] = n_prefs
        n_clues = [f for f in self.pwindow.clues if f.path != path]
        self.pwindow.clues = n_clues
        self.load_clue_files(n_clues)
        
    def on_file_selected(self, selection):
        store, it = selection.get_selected()
        self.remove_button.set_sensitive(it is not None)
        
    def load_clue_files(self, clues):
        self.store.clear()
        for f in sorted(clues, key=operator.attrgetter('name')):
            self.store.append([f.name, f.path])

def create_display_string(n, direction, word, clue):
    """Construct the displayed string for a word/clue item."""
    c = gobject.markup_escape_text(clue) if len(clue) > 0 else '<span foreground="red">No clue yet.</span>'
    d = constants.DIRECTION_NAMES[direction]
    return ''.join(["<b>", d, ", ", str(n), "</b>: <i>", word, "</i>\n", c])

def compute_clue_items(grid):
    """
    Compute a list of clue items that are displayed in the main clue control.
    """
    items = []
    for row in grid.gather_words():
        n, x, y, d, word, clue, explanation = row
        display = create_display_string(n, d, word, clue)
        items.append((n, x, y, d, word, clue, explanation, display))
    return items

def store_get_item(target, store, it):
    """
    Return the next/previous item in the store, based on the given iter.
    Return the first/last item when the end/beginning of the store has been reached.
    """
    if target == "next":
        it_n = store.iter_next(it)
        if it_n is None:
            it_n = store.get_iter_first()
        return it_n
    elif target == "previous":
        n = store.iter_n_children(None)
        index = store.get_path(it)[0] - 1
        if index < 0:
            index = store.iter_n_children(None) - 1
        return store.iter_nth_child(None, index)

class ClueTool:
    def __init__(self, parent):
        self.parent = parent
        self.settings = {"use_scrolling": True}
        self.timer = None
    
    def create_entry(self, vbox, key, title):
        entry = gtk.Entry()
        def changed(widget):
            if self.timer is not None:
                glib.source_remove(self.timer)
            self.timer = glib.timeout_add(constants.INPUT_DELAY_VERY_SHORT
            , self.on_clue_changed, key, widget.get_text())
        c_id = entry.connect("changed", changed)
        entry.set_sensitive(False)
        vbox.pack_start(create_label(title), False, False, 3)
        vbox.pack_start(entry, False, False, 0)
        return entry, c_id
        
    def create(self, puzzle):
        vbox = gtk.VBox()
        vbox.set_spacing(6)
        vbox.set_border_width(6)
        result = self.create_entry(vbox, "text", u"<b>Clue</b>")
        self.clue_entry, self.c_changed_id = result
        
        def on_cycle_clue(target):
            it = store_get_item(target, *self.tree.get_selection().get_selected())
            self.select_iter(self.tree.get_model(), it)
        f_next = lambda b: on_cycle_clue("next")
        f_prev = lambda b: on_cycle_clue("previous")
        np_box = gtk.HButtonBox()
        self.prev_button = create_button(u"Previous", f_click=f_prev)
        self.next_button = create_button(u"Next", f_click=f_next)
        np_box.pack_start(self.prev_button)
        np_box.pack_start(self.next_button)
        align = gtk.Alignment(1, 0.5)
        align.add(np_box)
        vbox.pack_start(align, False, False, 0)
        
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
        
        l_vbox = gtk.VBox()
        l_vbox.set_spacing(6)
        l_vbox.set_border_width(6)
        
        l_vbox.pack_start(create_label(u"<b>Lookup clues</b>"), False, False, 0)
        l_vbox.pack_start(w_hbox, False, False, 0)
        self.c_store, self.c_tree, c_window = create_tree(str
            , [(u"Clues", 0)]
            , f_sel=self.on_clue_selected)
        l_vbox.pack_start(c_window, True, True, 0)
        self.use_clue_button = create_button(u"Use clue"
            , align=(0, 0.5), f_click=self.on_use_clicked)
        self.use_clue_button.set_sensitive(False)
        l_vbox.pack_start(self.use_clue_button, False, False, 0)
                
        pages = [(window, u"Words and clues")
            , (l_vbox, u"Lookup")
            , (o_vbox, u"Advanced")
        ]
        vbox.pack_start(create_notebook(pages, border=(4, 2)))
        self.tree.set_headers_visible(False)
        self.load_items(puzzle.grid)
        return vbox
        
    def select_iter(self, store, it):
        x, y, d = store[it][1], store[it][2], store[it][3]
        self.parent.set_selection(x=x, y=y, direction=d)
        
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
            display = create_display_string(n, direction, word, clue)
            store[it][7] = display
            self.parent.transform_clues(transform.modify_clue
                    , x=x
                    , y=y
                    , direction=direction
                    , key=key
                    , value=value)
            self.tree.columns_autosize()
            self.tree.queue_draw()

    def load_items(self, grid):
        """Load all word/clue items and put them in the ListStore."""
        def locked():
            self.store.clear()
            for item in compute_clue_items(grid):
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
        self.next_button.set_sensitive(status)
        self.prev_button.set_sensitive(status)
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
            self.parent.set_selection(x, y, direction, full_update=False)
            self.settings["use_scrolling"] = True
        self.perform_while_locked(selection, locked)
        
    def select(self, x, y, direction):
        """Select the word starting at the given (x, y, direction)."""
        if x < 0 or y < 0:
            return
        for row in self.store:
            if (row[1], row[2], row[3]) == (x, y, direction):
                selection = self.tree.get_selection()
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
