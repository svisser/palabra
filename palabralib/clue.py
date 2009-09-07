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

def create_clue_editor(puzzle):
    vbox = gtk.VBox(False, 0)
    vbox.set_spacing(6)
    vbox.set_border_width(6)
    #changed = lambda widget: self.on_clue_changed(widget, "text")
    label = gtk.Label()
    label.set_markup(u"<b>Clue</b>")
    label.set_alignment(0, 0.5)
    clue_entry = gtk.Entry(512)
    #self.clue_entry.connect("changed", changed)
    vbox.pack_start(label, False, False, 3)
    vbox.pack_start(clue_entry, False, False, 0)
    
    #changed = lambda widget: self.on_clue_changed(widget, "explanation")
    label = gtk.Label()
    label.set_markup(u"<b>Explanation</b>")
    label.set_alignment(0, 0.5)
    explanation_entry = gtk.Entry(512)
    #self.explanation_entry.connect("changed", changed)
    vbox.pack_start(label, False, False, 3)
    vbox.pack_start(explanation_entry, False, False, 0)
    
    # number x y word clue
    across_store = gtk.ListStore(int, int, int, str)
    down_store = gtk.ListStore(int, int, int, str)
    
    def process_row(row):
        c = row[4] if len(row[4]) > 0 else "No clue yet."
        return (row[0], row[1], row[2], ''.join(["<i>", row[3], "</i>\n", c]))
    
    for row in puzzle.grid.gather_words("across"):
        across_store.append(process_row(row))
    for row in puzzle.grid.gather_words("down"):
        down_store.append(process_row(row))
    
    across_tree = gtk.TreeView(across_store)
    across_tree.set_headers_visible(False)
    down_tree = gtk.TreeView(down_store)
    down_tree.set_headers_visible(False)
    
    cell = gtk.CellRendererText()
    cell.set_property("xalign", 1)
    column = gtk.TreeViewColumn("")
    column.pack_start(cell, True)
    column.set_attributes(cell, text=0)
    across_tree.append_column(column)
    
    cell = gtk.CellRendererText()
    column = gtk.TreeViewColumn(u"Word", cell, markup=3)
    #column.pack_start(cell, True)
    #column.set_attributes(cell, text=3)
    across_tree.append_column(column)
    
    #def on_across_clue_editted(cell, path, new_text):
    #    self.on_clue_editted(cell, path, new_text, "across", self.across_store)
    
    cell = gtk.CellRendererText()
    cell.set_property("xalign", 1)
    column = gtk.TreeViewColumn("")
    column.pack_start(cell, True)
    column.set_attributes(cell, text=0)
    down_tree.append_column(column)
    
    cell = gtk.CellRendererText()
    column = gtk.TreeViewColumn(u"Word", cell, markup=3)
    #column.pack_start(cell, True)
    #column.set_attributes(cell, text=3)
    down_tree.append_column(column)
    
    #def on_down_clue_editted(cell, path, new_text):
    #    self.on_clue_editted(cell, path, new_text, "down", self.down_store)
    
    across_window = gtk.ScrolledWindow(None, None)
    across_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    #across_window.set_size_request(-1, 192)
    across_window.add(across_tree)
    
    down_window = gtk.ScrolledWindow(None, None)
    down_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    #down_window.set_size_request(-1, 192)
    down_window.add(down_tree)
    
    across_label = gtk.Label()
    across_label.set_markup(u"<b>Across words</b>")
    across_label.set_alignment(0, 0.5)
    across_label.set_padding(3, 3)
    
    vbox.pack_start(across_label, False, False, 0)
    vbox.pack_start(across_window, True, True, 0)
    
    down_label = gtk.Label()
    down_label.set_markup(u"<b>Down words</b>")
    down_label.set_alignment(0, 0.5)
    down_label.set_padding(3, 3)
    
    vbox.pack_start(down_label, False, False, 0)
    vbox.pack_start(down_window, True, True, 0)
    
    return vbox

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
