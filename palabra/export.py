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

class ExportWindow(gtk.Dialog):
    def __init__(self, palabra_window):
        flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
            gtk.STOCK_OK, gtk.RESPONSE_OK)
        super(ExportWindow, self).__init__("Export puzzle", palabra_window, flags, buttons)
        self.set_size_request(480, 420)
        self.current_item = None
        
        self.options = {"format": ""
            , "output": {"grid": False, "solution": False, "clues": False}
            , "settings": {}}
        
        self.default_settings = {}
        self.default_settings["csv"] = {"separator": ","}
        self.default_settings["png"] = {}
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        
        main = gtk.HBox(False, 0)
        main.set_spacing(18)
        hbox.pack_start(main, True, True, 0)
        
        self.components = []
        self.components.append(("csv", "CSV (csv)", self.create_csv_item()))
        self.components.append(("png", "PNG (png)", self.create_png_item()))
        
        items = gtk.ListStore(str)
        for key, title, component in self.components:
            items.append([title])
        
        tree = gtk.TreeView(items)
        tree.set_headers_visible(False)
        tree.connect("button_press_event", self.on_tree_clicked)
        
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("")
        column.pack_start(cell, True)
        column.set_attributes(cell, text=0)
        tree.append_column(column)
        
        tree_window = gtk.ScrolledWindow(None, None)
        tree_window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        tree_window.add(tree)
        
        self.options_window = gtk.VBox(False, 0)
        
        main.pack_start(tree_window, False, False, 9)
        main.pack_start(self.options_window, True, True, 0)
        self.vbox.pack_start(hbox, True, True, 0)
        
        starting_index = 0
        tree.get_selection().select_path(starting_index)
        self._selection_component(starting_index)
        
    def on_tree_clicked(self, treeview, event):
        if event.button == 1:
            x = int(event.x)
            y = int(event.y)
            
            item = treeview.get_path_at_pos(x, y)
            if item is not None:
                path, col, cellx, celly = item
                
                if self.current_item is not None:
                    self.options_window.remove(self.current_item)
                
                self._selection_component(path[0])
                
    def _selection_component(self, index):
        format = self.components[index][0]
        self.options["format"] = format
        self.options["settings"] = self.default_settings[format]
        
        self.current_item = self.components[index][2]
        self.options_window.pack_start(self.current_item, False, False, 0)
        self.options_window.show_all()
        
    def create_csv_item(self):
        main = gtk.VBox(False, 0)
        main.set_spacing(6)
        
        label = gtk.Label()
        label.set_alignment(0, 0)
        label.set_markup("<b>Output</b>")
        main.pack_start(label, False, False, 6)
        
        def on_select_output(widget, data=None):
            self.options["output"][data] = widget.get_active()

        grid_button = gtk.CheckButton("Grid")
        grid_button.connect("toggled", on_select_output, "grid")
        align = gtk.Alignment(0, 0.5)
        align.set_padding(0, 0, 12, 0)
        align.add(grid_button)
        main.pack_start(align, False, False, 0)
        
        solution_button = gtk.CheckButton("Solution")
        solution_button.connect("toggled", on_select_output, "solution")
        align = gtk.Alignment(0, 0.5)
        align.set_padding(0, 0, 12, 0)
        align.add(solution_button)
        main.pack_start(align, False, False, 0)
        
        clues_button = gtk.CheckButton("Clues")
        clues_button.connect("toggled", on_select_output, "clues")
        align = gtk.Alignment(0, 0.5)
        align.set_padding(0, 0, 12, 0)
        align.add(clues_button)
        main.pack_start(align, False, False, 0)
        
        label = gtk.Label()
        label.set_alignment(0, 0)
        label.set_markup("<b>Settings</b>")
        main.pack_start(label, False, False, 6)
        
        settings_table = gtk.Table(1, 2)
        settings_table.set_col_spacings(6)
        main.pack_start(settings_table, False, False, 0)
        
        def on_separator_combo_changed(combo):
            try:
                index = combo.get_active()
                separator = separators[index][1]
                self.options["settings"]["separator"] = separator
            except KeyError:
                pass
        
        separators = [("Comma", ","), ("Tab", "\t")]
        separator_combo = gtk.combo_box_new_text()
        for title, separator in separators:
            separator_combo.append_text(title)
        separator_combo.connect("changed", on_separator_combo_changed)
        
        for i, (title, separator) in enumerate(separators):
            if separator == self.default_settings["csv"]["separator"]:
                separator_combo.set_active(i)
                break
        
        align = gtk.Alignment(0, 0.5)
        align.set_padding(0, 0, 12, 0)
        align.add(gtk.Label("Separator:"))
        settings_table.attach(align, 0, 1, 0, 1, gtk.FILL, gtk.FILL)
        settings_table.attach(separator_combo, 1, 2, 0, 1)
        
        return main
        
    def create_png_item(self):
        main = gtk.VBox(False, 0)
        main.set_spacing(6)
        
        return main
