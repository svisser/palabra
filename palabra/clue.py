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

class ClueEditor(gtk.Dialog):
    def __init__(self, palabra_window, puzzle):
        gtk.Dialog.__init__(self, "Palabra Clue Editor"
            , palabra_window, gtk.DIALOG_MODAL)
        self.puzzle = puzzle
        self.set_size_request(640, 480)
        
        tabs = gtk.Notebook()
        tabs.append_page(self.create_clue_editor(), gtk.Label("Clue"))
        tabs.append_page(self.create_overview(), gtk.Label("Overview"))
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
        
    def on_tab_change(self, notebook, page, index):
        if index == 0:
            self.update_current_word()
        elif index == 1:
            counter = 0
            for row in self.gather_words(self.puzzle.grid, "across"):
                it = self.across_store.get_iter(counter)
                self.across_store.set(it, 4, row[4])
                counter += 1
                
            counter = 0
            for row in self.gather_words(self.puzzle.grid, "down"):
                it = self.down_store.get_iter(counter)
                self.down_store.set(it, 4, row[4])
                counter += 1
            
            self.across_tree.queue_draw()
            self.down_tree.queue_draw()
    
    def on_clue_changed(self, widget):
        n, x, y, direction = self.words[self.current_index]
        value = widget.get_text().strip()
        self._store_property(x, y, direction, "text", value)

    def on_explanation_changed(self, widget):
        n, x, y, direction = self.words[self.current_index]
        value = widget.get_text().strip()
        self._store_property(x, y, direction, "explanation", value)
        
    def _store_property(self, x, y, direction, key, value):
        self.puzzle.grid.store_clue(x, y, direction, key, value)
        
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
        
        display_dir = {"across": "Across", "down": "Down"}[direction]
        self.update_clue_label(n, display_dir)
        
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
        
    def update_clue_label(self, number, direction):
        text = ''.join(
            ["<b>Currently editing</b>: "
            , str(number)
            , ", "
            , direction
            ])
        self.clue_label.set_markup(text)
        
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
        label.set_markup("<b>Grid entry</b>")
        label.set_alignment(0, 0.5)
        label.set_padding(3, 3)
        self.grid_entry = gtk.Entry(512)
        self.grid_entry.set_editable(False)
        main.pack_start(label, False, False, 3)
        main.pack_start(self.grid_entry, False, False, 0)
        
        label = gtk.Label()
        label.set_markup("<b>Clue</b>")
        label.set_alignment(0, 0.5)
        self.clue_entry = gtk.Entry(512)
        self.clue_entry.connect("changed", self.on_clue_changed)
        main.pack_start(label, False, False, 3)
        main.pack_start(self.clue_entry, False, False, 0)
        
        label = gtk.Label()
        label.set_markup("<b>Explanation</b>")
        label.set_alignment(0, 0.5)
        self.explanation_entry = gtk.Entry(512)
        self.explanation_entry.connect("changed", self.on_explanation_changed)
        main.pack_start(label, False, False, 3)
        main.pack_start(self.explanation_entry, False, False, 0)
        
        buttons = gtk.HButtonBox()
        buttons.set_layout(gtk.BUTTONBOX_END)
        
        button = gtk.Button(stock=gtk.STOCK_GO_BACK)
        button.connect("clicked", lambda widget: self.to_previous_word())
        align = button.get_children()[0]
        hbox = align.get_children()[0]
        image, label = hbox.get_children()
        label.set_text("Previous")
        buttons.pack_start(button, False, False, 0)
        
        button = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        button.connect("clicked", lambda widget: self.to_next_word())
        align = button.get_children()[0]
        hbox = align.get_children()[0]
        image, label = hbox.get_children()
        label.set_text("Next")
        buttons.pack_start(button, False, False, 0)
        
        main.pack_start(buttons, False, False, 7)
        
        return main
        
    def create_overview(self):
        # number x y word clue
        self.across_store = gtk.ListStore(int, int, int, str, str)
        self.down_store = gtk.ListStore(int, int, int, str, str)
        
        for row in self.gather_words(self.puzzle.grid, "across"):
            self.across_store.append(row)
        for row in self.gather_words(self.puzzle.grid, "down"):
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
        column = gtk.TreeViewColumn("Word")
        column.pack_start(cell, True)
        column.set_attributes(cell, text=3)
        self.across_tree.append_column(column)
        
        cell = gtk.CellRendererText()
        cell.set_property("editable", True)
        cell.connect("edited", self.on_across_clue_editted)
        column = gtk.TreeViewColumn("Clue")
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
        column = gtk.TreeViewColumn("Word")
        column.pack_start(cell, True)
        column.set_attributes(cell, text=3)
        self.down_tree.append_column(column)
        
        cell = gtk.CellRendererText()
        cell.set_property("editable", True)
        cell.connect("edited", self.on_down_clue_editted)
        column = gtk.TreeViewColumn("Clue")
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
        across_label.set_markup("<b>Across words</b>")
        across_label.set_alignment(0, 0.5)
        across_label.set_padding(3, 3)
        main.pack_start(across_label, False, False, 0)
        main.pack_start(across_window, True, True, 0)
        
        down_label = gtk.Label()
        down_label.set_markup("<b>Down words</b>")
        down_label.set_alignment(0, 0.5)
        down_label.set_padding(3, 3)
        main.pack_start(down_label, False, False, 0)
        main.pack_start(down_window, True, True, 0)
        main.set_border_width(7)
        
        return main
        
    def on_across_clue_editted(self, cell, path, new_text):
        it = self.across_store.get_iter_from_string(path)
        self.across_store.set_value(it, 4, new_text.strip())
        
        x = self.across_store.get_value(it, 1)
        y = self.across_store.get_value(it, 2)
        self._store_property(x, y, "across", "text", new_text.strip())
        
    def on_down_clue_editted(self, cell, path, new_text):
        it = self.down_store.get_iter_from_string(path)
        self.down_store.set_value(it, 4, new_text.strip())
        
        x = self.down_store.get_value(it, 1)
        y = self.down_store.get_value(it, 2)
        self._store_property(x, y, "down", "text", new_text.strip())
        
    def gather_words(self, grid, direction):
        if direction == "across":
            iter_words = grid.horizontal_words()
        elif direction == "down":
            iter_words = grid.vertical_words()
            
        words = []
        for n, x, y in iter_words:
            try:
                clue = grid.cell(x, y)["clues"][direction]["text"]
            except KeyError:
                clue = ""
                
            word = grid.gather_word(x, y, direction)
            words.append([n, x, y, word, clue])
        return words
