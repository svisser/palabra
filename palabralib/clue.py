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

import gtk

import transform

class ClueTool:
    def __init__(self, callbacks, puzzle):
        self.callbacks = callbacks
        self.puzzle = puzzle
        self.last = None
        
        self.settings = {}
        self.settings["use_scrolling"] = True
        
    def create(self):
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
        vbox.pack_start(label, False, False, 3)
        vbox.pack_start(self.explanation_entry, False, False, 0)
        
        # number x y direction word clue explanation displayed_string
        self.store = gtk.ListStore(int, int, int, str, str, str, str, str)
        
        self.tree = gtk.TreeView(self.store)
        self.selection_changed_id = self.tree.get_selection().connect("changed"
            , self.on_selection_changed)
        self.tree.set_headers_visible(False)
        
        self.load_items()
        
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(u"Word", cell, markup=7)
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
        store, it = self.tree.get_selection().get_selected()
        if it is not None:
            n = store.get_value(it, 0)
            x = store.get_value(it, 1)
            y = store.get_value(it, 2)
            direction = store.get_value(it, 3)
            word = store.get_value(it, 4)
            clue = store.get_value(it, 5)
            explanation = store.get_value(it, 6)
            
            value = widget.get_text().strip()
            if key == "text":
                clue = value
                store.set_value(it, 5, value)
            elif key == "explanation":
                explanation = value
                store.set_value(it, 6, value)

            display = self.create_display_string(n, direction, word, clue)
            store.set_value(it, 7, display)
            
            self.callbacks["clue"](x, y, direction, key, value)
            
            self.tree.columns_autosize()
            self.tree.queue_draw()
        
    def create_display_string(self, n, direction, word, clue):
        """Construct the displayed string for a word/clue item."""
        c = clue if len(clue) > 0 else "<span foreground=\"red\">No clue yet.</span>"
        d = {"across": "Across", "down": "Down"}[direction]
        return ''.join(["<b>", d, ", ", str(n), "</b>:\n<i>", word, "</i>\n", c])

    def load_items(self):
        """Load all word/clue items and put them in the ListStore."""
        def process_row(direction, row):
            n = row[0]
            x = row[1]
            y = row[2]
            word = row[3]
            clue = row[4]
            display = self.create_display_string(n, direction, word, clue)
            return (n, x, y, direction, word, clue, "TODO", display)
        self.store.clear()
        for d in ["across", "down"]:
            for row in self.puzzle.grid.gather_words(d):
                self.store.append(process_row(d, row))
        
    def update_current_word(self, x, y, direction):
        """Put the clue data of the word at (x, y, direction) in the text entries."""
        self.set_clue_editor_status(True)
        
        clues = self.puzzle.grid.cell(x, y)["clues"]
        try:
            text = clues[direction]["text"] 
            self.clue_entry.set_text(text)
        except KeyError:
            self.clue_entry.set_text("")
        try:
            explanation = clues[direction]["explanation"]
            self.explanation_entry.set_text(explanation)
        except KeyError:
            self.explanation_entry.set_text("") 
            
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
        x = store.get_value(it, 1)
        y = store.get_value(it, 2)
        direction = store.get_value(it, 3)
        
        def locked():
            self.update_current_word(x, y, direction)
            self.callbacks["select"](x, y, direction)
        self.perform_while_locked(selection, locked)
        
    def select(self, x, y, direction):
        """Select the word starting at the given (x, y, direction)."""
        if x < 0 or y < 0:
            return
        
        selection = self.tree.get_selection()            
        def locked():
            selection.select_path(row.path)
            if self.settings["use_scrolling"]:
                self.tree.scroll_to_cell(row.path)
            self.update_current_word(x, y, direction)
        
        for row in self.store:
            if (row[1], row[2], row[3]) == (x, y, direction):
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

# ########################################################

class ClueEditor(gtk.Dialog):
    def __init__(self, palabra_window, puzzle):
        gtk.Dialog.__init__(self, u"Palabra clue editor"
            , palabra_window, gtk.DIALOG_MODAL)
        self.palabra_window = palabra_window
        self.puzzle = puzzle
        self.set_size_request(640, 480)
        
        self.modifications = []
        
        tabs = gtk.Notebook()
        tabs.append_page(self.create_clue_editor(), gtk.Label(u"Clue"))
        tabs.append_page(self.create_overview(), gtk.Label(u"Overview"))
        tabs.connect("switch-page", self.on_tab_change)
        
        main = gtk.VBox(False, 0)
        main.set_spacing(18)
        main.pack_start(tabs, True, True, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        hbox.pack_start(main, True, True, 0)
        
        self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_ACCEPT)
        self.vbox.add(hbox)
        
        def quit():
            for x, y, direction, key, value in self.modifications:
                self.palabra_window.transform_grid(transform.modify_clue
                    , x=x
                    , y=y
                    , direction=direction
                    , key=key
                    , value=value)
        
        self.connect("destroy", lambda widget: quit())
    
    def _store_property(self, x, y, direction, key, value):
        try:
            clue = self.puzzle.grid.cell(x, y)["clues"]
        except KeyError:
            clue = self.puzzle.grid.cell(x, y)["clues"] = {}
        try:
            current = clue[direction][key]
        except KeyError:
            current = None
        
        # nothing is currently saved and nothing was entered
        # so do not store this modification (this occurs when
        # the program resets the text entry, which triggers
        # the changed functions)
        if current is None and len(value) == 0:
            return
            
        if current != value:
            if len(self.modifications) > 0:
                tx, ty, tdirection, tkey, tvalue = self.modifications[-1]
                if (tx, ty, tdirection, tkey) == (x, y, direction, key):
                    self.modifications[-1] = (x, y, direction, key, value)
                else:
                    self.modifications.append((x, y, direction, key, value))
            else:
                self.modifications.append((x, y, direction, key, value))
        
    def update_current_word(self):
        n, x, y, direction = self.words[self.current_index]
        
        word = self.puzzle.grid.gather_word(x, y, direction)
        self.grid_entry.set_text(word)

        clues = self.puzzle.grid.cell(x, y)["clues"]
        try:
            text = clues[direction]["text"] 
            self.clue_entry.set_text(text)
        except KeyError:
            self.clue_entry.set_text("")
        try:
            explanation = clues[direction]["explanation"]
            self.explanation_entry.set_text(explanation)
        except KeyError:
            self.explanation_entry.set_text("")    
            
        # override stored values when the user has entered something
        # that is not yet committed to the clues data structure
        d = [("text", self.clue_entry), ("explanation", self.explanation_entry)]
        for key, widget in d:
            value = self._check_against_user_modifications(x, y, direction, key)
            if value is not None:
                widget.set_text(value)
        
        display_dir = {"across": u"Across", "down": u"Down"}[direction]
        content = [u"<b>Currently editing</b>: ", str(n), u", ", display_dir]
        self.clue_label.set_markup(''.join(content))
        
    def _check_against_user_modifications(self, x, y, direction, key):
        result = None
        for mx, my, mdirection, mkey, mvalue in self.modifications:
            if (x, y, direction, key) == (mx, my, mdirection, mkey):
                result = mvalue
        return result
        
    def to_next_word(self):
        self.current_index += 1
        if self.current_index >= len(self.words):
            self.current_index = 0
        self.update_current_word()
    
    def to_previous_word(self):
        self.current_index -= 1
        if self.current_index < 0:
            self.current_index = len(self.words) - 1
        self.update_current_word()
        
    def create_clue_editor(self):
        main = gtk.VBox(False, 0)
        main.set_border_width(7)
        
        self.words = []
        for n, x, y in self.puzzle.grid.horizontal_words():
            self.words.append((n, x, y, "across"))
        for n, x, y in self.puzzle.grid.vertical_words():
            self.words.append((n, x, y, "down"))
        self.current_index = 0
        
        self.clue_label = gtk.Label()
        self.clue_label.set_alignment(0, 0.5)
        self.clue_label.set_padding(3, 3)
        main.pack_start(self.clue_label, False, False, 0)
        
        label = gtk.Label()
        label.set_markup(u"<b>Grid entry</b>")
        label.set_alignment(0, 0.5)
        label.set_padding(3, 3)
        self.grid_entry = gtk.Entry(512)
        self.grid_entry.set_editable(False)
        main.pack_start(label, False, False, 3)
        main.pack_start(self.grid_entry, False, False, 0)
        
        changed = lambda widget: self.on_clue_changed(widget, "text")
        label = gtk.Label()
        label.set_markup(u"<b>Clue</b>")
        label.set_alignment(0, 0.5)
        self.clue_entry = gtk.Entry(512)
        self.clue_entry.connect("changed", changed)
        main.pack_start(label, False, False, 3)
        main.pack_start(self.clue_entry, False, False, 0)
        
        changed = lambda widget: self.on_clue_changed(widget, "explanation")
        label = gtk.Label()
        label.set_markup(u"<b>Explanation</b>")
        label.set_alignment(0, 0.5)
        self.explanation_entry = gtk.Entry(512)
        self.explanation_entry.connect("changed", changed)
        main.pack_start(label, False, False, 3)
        main.pack_start(self.explanation_entry, False, False, 0)
        
        buttons = gtk.HButtonBox()
        buttons.set_layout(gtk.BUTTONBOX_END)
        
        button = gtk.Button(stock=gtk.STOCK_GO_BACK)
        button.connect("clicked", lambda widget: self.to_previous_word())
        align = button.get_children()[0]
        hbox = align.get_children()[0]
        image, label = hbox.get_children()
        label.set_text(u"Previous")
        buttons.pack_start(button, False, False, 0)
        
        def to_next_word(self):
            self.current_index += 1
            if self.current_index >= len(self.words):
                self.current_index = 0
            self.update_current_word()
        
        button = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        button.connect("clicked", lambda widget: self.to_next_word())
        align = button.get_children()[0]
        hbox = align.get_children()[0]
        image, label = hbox.get_children()
        label.set_text(u"Next")
        buttons.pack_start(button, False, False, 0)
        
        main.pack_start(buttons, False, False, 7)
        return main
        
    def create_overview(self):
        # number x y word clue
        self.across_store = gtk.ListStore(int, int, int, str, str)
        self.down_store = gtk.ListStore(int, int, int, str, str)
        
        for row in self.puzzle.grid.gather_words("across"):
            self.across_store.append(row)
        for row in self.puzzle.grid.gather_words("down"):
            self.down_store.append(row)
        
        self.across_tree = gtk.TreeView(self.across_store)
        self.down_tree = gtk.TreeView(self.down_store)
        
        cell = gtk.CellRendererText()
        cell.set_property("xalign", 1)
        column = gtk.TreeViewColumn("")
        column.pack_start(cell, True)
        column.set_attributes(cell, text=0)
        self.across_tree.append_column(column)
        
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(u"Word")
        column.pack_start(cell, True)
        column.set_attributes(cell, text=3)
        self.across_tree.append_column(column)
        
        def on_across_clue_editted(cell, path, new_text):
            self.on_clue_editted(cell, path, new_text, "across", self.across_store)
        
        cell = gtk.CellRendererText()
        cell.set_property("editable", True)
        cell.connect("edited", on_across_clue_editted)
        column = gtk.TreeViewColumn(u"Clue")
        column.pack_start(cell, True)
        column.set_attributes(cell, text=4)
        self.across_tree.append_column(column)
        
        cell = gtk.CellRendererText()
        cell.set_property("xalign", 1)
        column = gtk.TreeViewColumn("")
        column.pack_start(cell, True)
        column.set_attributes(cell, text=0)
        self.down_tree.append_column(column)
        
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(u"Word")
        column.pack_start(cell, True)
        column.set_attributes(cell, text=3)
        self.down_tree.append_column(column)
        
        def on_down_clue_editted(cell, path, new_text):
            self.on_clue_editted(cell, path, new_text, "down", self.down_store)
        
        cell = gtk.CellRendererText()
        cell.set_property("editable", True)
        cell.connect("edited", on_down_clue_editted)
        column = gtk.TreeViewColumn(u"Clue")
        column.pack_start(cell, True)
        column.set_attributes(cell, text=4)
        self.down_tree.append_column(column)
        
        across_window = gtk.ScrolledWindow(None, None)
        across_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        across_window.add(self.across_tree)
        
        down_window = gtk.ScrolledWindow(None, None)
        down_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        down_window.add(self.down_tree)
        
        main = gtk.VBox(False, 0)
        across_label = gtk.Label()
        across_label.set_markup(u"<b>Across words</b>")
        across_label.set_alignment(0, 0.5)
        across_label.set_padding(3, 3)
        main.pack_start(across_label, False, False, 0)
        main.pack_start(across_window, True, True, 0)
        
        down_label = gtk.Label()
        down_label.set_markup(u"<b>Down words</b>")
        down_label.set_alignment(0, 0.5)
        down_label.set_padding(3, 3)
        main.pack_start(down_label, False, False, 0)
        main.pack_start(down_window, True, True, 0)
        main.set_border_width(7)
        return main
        
    def on_tab_change(self, notebook, page, index):
        if index == 0:
            self.update_current_word()
        elif index == 1:
            l = [("across", self.across_store), ("down", self.down_store)]
            for direction, store in l:
                counter = 0
                for n, x, y, word, clue in self.puzzle.grid.gather_words(direction):
                    it = store.get_iter(counter)
                    
                    # override stored values when the user has entered something
                    # that is not yet committed to the clues data structure
                    value = self._check_against_user_modifications(x, y, direction, "text")
                    if value is not None:
                        clue = value
                    
                    store.set(it, 4, clue)
                    counter += 1
            
            self.across_tree.queue_draw()
            self.down_tree.queue_draw()
            
    def on_clue_changed(self, widget, key):
        n, x, y, direction = self.words[self.current_index]
        value = widget.get_text().strip()
        self._store_property(x, y, direction, key, value)
        
    def on_clue_editted(self, cell, path, new_text, direction, store):
        it = store.get_iter_from_string(path)
        store.set_value(it, 4, new_text.strip())
        
        x = store.get_value(it, 1)
        y = store.get_value(it, 2)
        self._store_property(x, y, direction, "text", new_text.strip())
