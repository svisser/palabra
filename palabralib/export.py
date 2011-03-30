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

def verify_output_options(options):
    for key, value in options["output"].items():
        if value:
            break
    else:
        return u"No output options are selected."
    return None

class Format:
    def __init__(self, key, title, outputs, allow_multiple=True):
        self.key = key
        self.title = title
        self.outputs = outputs
        self.allow_multiple = allow_multiple
        self.settings = []
        
    def register_setting(self, setting):
        self.settings.append(setting)
        
class FormatSetting:
    def __init__(self, type, title, name, default, properties):
        self.type = type
        self.title = title
        self.name = name
        self.default = default
        self.properties = properties
        
        self.callback = None
        self.initialize = None

class ExportWindow(gtk.Dialog):
    def __init__(self, palabra_window):
        flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
            gtk.STOCK_SAVE, gtk.RESPONSE_OK)
        super(ExportWindow, self).__init__(u"Export puzzle", palabra_window, flags, buttons)
        self.set_size_request(480, 420)
        
        self.reset_options()
        
        self.format = None
        self.formats = []

        csv = Format("csv", u"CSV (csv)", ["grid", "solution", "clues"])
        #self.formats.append(csv)
        pdf = Format("pdf", u"PDF (pdf)", ["grid", "solution"], False)
        self.formats.append(pdf)
        png = Format("png", u"PNG (png)", ["grid", "solution"], False)
        self.formats.append(png)

        setting = FormatSetting("combo", u"Separator:", "separator", ","
            , [(u"Comma", ","), (u"Tab", "\t")])
        def initialize(combo):
            combo.set_active(0)
        def callback(combo):
            separator = setting.properties[combo.get_active()][1]
            self.options["settings"]["separator"] = separator
        setting.initialize = initialize
        setting.callback = callback        
        csv.register_setting(setting)
        
        items = gtk.ListStore(str)
        for format in self.formats:
            items.append([format.title])
        
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
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        
        main = gtk.HBox(False, 0)
        main.set_spacing(18)
        hbox.pack_start(main, True, True, 0)
        
        label = gtk.Label()
        label.set_alignment(0, 0)
        label.set_markup(u"<b>Export to:</b>")
        format_vbox = gtk.VBox(False, 0)
        format_vbox.pack_start(label, False, False, 6)
        format_vbox.pack_start(tree_window, True, True, 6)
        
        main.pack_start(format_vbox, False, False, 0)
        main.pack_start(self.options_window, True, True, 0)
        self.vbox.pack_start(hbox, True, True, 0)
        
        starting_index = 0
        tree.get_selection().select_path(starting_index)
        self.select_format(starting_index)
        
    def reset_options(self):
        self.options = {}
        self.options["format"] = None
        self.options["output"] = {"grid": False, "solution": False, "clues": False}
        self.options["settings"] = {}
        
    def select_format(self, index):
        if self.format is not None:
            self.options_window.remove(self.option)
        self.format = self.formats[index]
        
        self.reset_options()
        self.options["format"] = self.format.key
        
        def callback(widget, data=None):
            self.options["output"][data] = widget.get_active()
        
        self.option = gtk.VBox(False, 0)
        self._create_output_options(self.option, self.format, callback)
        self._create_settings(self.option, self.format)
        
        self.options_window.pack_start(self.option, False, False, 0)
        self.options_window.show_all()
        
    def on_tree_clicked(self, treeview, event):
        if event.button == 1:
            x = int(event.x)
            y = int(event.y)
            
            item = treeview.get_path_at_pos(x, y)
            if item is not None:
                path, col, cellx, celly = item
                self.select_format(path[0])
            
    @staticmethod    
    def _create_output_options(main, format, callback):
        label = gtk.Label()
        label.set_alignment(0, 0)
        label.set_markup(u"<b>Output</b>")
        main.pack_start(label, False, False, 6)

        prev_option = None
        options = {"grid": u"Grid", "solution": u"Solution", "clues": u"Clues"}
        for key, title in options.items():
            if key in format.outputs:
                if format.allow_multiple:
                    button = gtk.CheckButton(title)
                    button.connect("toggled", callback, key)
                else:
                    button = gtk.RadioButton(prev_option, title)
                    button.connect("toggled", callback, key)
                    if prev_option is None:
                        button.set_active(True)
                        callback(button, key)
                    prev_option = button
                
                align = gtk.Alignment(0, 0.5)
                align.set_padding(0, 0, 12, 0)
                align.add(button)
                main.pack_start(align, False, False, 0)
        
    @staticmethod
    def _create_settings(main, format):
        if len(format.settings) == 0:
            return
            
        label = gtk.Label()
        label.set_alignment(0, 0)
        label.set_markup(u"<b>Settings</b>")
        main.pack_start(label, False, False, 6)
        
        table = gtk.Table(len(format.settings), 2)
        table.set_col_spacings(6)
        main.pack_start(table, False, False, 0)
        
        row = 0
        for setting in format.settings:
            if setting.type == "combo":
                widget = gtk.combo_box_new_text()
                for title, value in setting.properties:
                    widget.append_text(title)
                widget.connect("changed", setting.callback)
                
                align = gtk.Alignment(0, 0.5)
                align.set_padding(0, 0, 12, 0)
                align.add(gtk.Label(setting.title))
                table.attach(align, 0, 1, row, row + 1, gtk.FILL, gtk.FILL)
                table.attach(widget, 1, 2, row, row + 1)
                
            if setting.initialize is not None:
                setting.initialize(widget)
            row += 1
