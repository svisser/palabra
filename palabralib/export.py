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
        
    def add(self, s):
        self.settings.append(s)
        
class Setting:
    def __init__(self, type, title, key, default, properties=None):
        self.type = type
        self.title = title
        self.key = key
        self.default = default
        self.properties = properties
        self.callback = None

class ExportWindow(gtk.Dialog):
    def __init__(self, palabra_window):
        flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
            gtk.STOCK_SAVE, gtk.RESPONSE_OK)
        super(ExportWindow, self).__init__(u"Export puzzle", palabra_window, flags, buttons)
        self.set_size_request(640, 480)
        
        pdf = Format("pdf", u"PDF (pdf)", ["grid", "solution"])
        pdf.add(Setting("bool", u"Include header", "page_header_include", True))
        pdf.add(Setting("bool", u"Include header on each page", "page_header_include_all", False))
        pdf.add(Setting("text", u"Header:", "page_header_text", "%T / %F / %P"))
        pdf.add(Setting("combo", u"Align grid:", "align", "right"
            , [(u"Left", "left"), (u"Center", "center"), (u"Right", "right")]))
        pdf.add(Setting("spin", u"Columns", "n_columns", 3, (3, 5)))
        pdf.add(Setting("spin", u"Margin left (mm)", "margin_left", 20, (0, 50)))
        pdf.add(Setting("spin", u"Margin right (mm)", "margin_right", 20, (0, 50)))
        pdf.add(Setting("spin", u"Margin top (mm)", "margin_top", 20, (0, 50)))
        pdf.add(Setting("spin", u"Margin bottom (mm)", "margin_bottom", 20, (0, 50)))
        png = Format("png", u"PNG (png)", ["grid", "solution"], False)
        self.formats = [pdf, png]
        self.format = None
        
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
        
        def _text_callback(entry, key):
            self.options["settings"][key] = entry.get_text()
        def _bool_callback(button, key):
            self.options["settings"][key] = button.get_active()
        def _combo_callback(combo, key, props):
            self.options["settings"][key] = props[combo.get_active()][1]
        def _spin_callback(spinner, key):
            self.options["settings"][key] = spinner.get_value_as_int()
        for f in self.formats:
            for s in f.settings:
                s.callback = {"text": _text_callback
                    , "bool": _bool_callback
                    , "combo": _combo_callback
                    , "spin": _spin_callback
                }[s.type]
        self.reset_options()
        
        starting_index = 0
        tree.get_selection().select_path(starting_index)
        self.select_format(starting_index)
        
    def reset_options(self):
        self.options = {}
        self.options["format"] = None
        self.options["output"] = {"grid": False, "solution": False, "clues": False}
        self.options["settings"] = {}
        for f in self.formats:
            for s in f.settings:
                self.options["settings"][s.key] = s.default
        
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
        options = [("grid", u"Puzzle"), ("solution", u"Solution"), ("clues", u"Clues")]
        for i, (key, title) in enumerate(options):
            if key in format.outputs:
                if format.allow_multiple:
                    button = gtk.CheckButton(title)
                    button.connect("toggled", callback, key)
                    if i == 0:
                        button.set_active(True)
                        callback(button, key)
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
        if not format.settings:
            return
        label = gtk.Label()
        label.set_alignment(0, 0)
        label.set_markup(u"<b>Settings</b>")
        main.pack_start(label, False, False, 6)
        table = gtk.Table(len(format.settings), 2)
        table.set_col_spacings(6)
        table.set_row_spacings(3)
        main.pack_start(table, False, False, 0)
        for row, s in enumerate(format.settings):
            if s.type == "combo":
                widget = gtk.combo_box_new_text()
                index = 0
                for i, (title, value) in enumerate(s.properties):
                    widget.append_text(title)
                    if value == s.default:
                        index = i
                widget.set_active(index)
                widget.connect("changed", s.callback, s.key, s.properties)
            elif s.type == "text":
                widget = gtk.Entry()
                widget.set_text(s.default)
                widget.connect("changed", s.callback, s.key)
            elif s.type == "bool":
                widget = gtk.CheckButton(s.title)
                widget.set_active(s.default)
                widget.connect("toggled", s.callback, s.key)
            elif s.type == "spin":
                minn, maxx = s.properties
                adj = gtk.Adjustment(s.default, minn, maxx, 1, 0, 0)
                widget = gtk.SpinButton(adj, 0.0, 0)
                widget.connect("value-changed", s.callback, s.key)
            if s.type in ["combo", "text"]:
                align = gtk.Alignment(0, 0.5)
                align.set_padding(0, 0, 12, 0)
                align.add(gtk.Label(s.title))
                table.attach(align, 0, 1, row, row + 1, gtk.FILL, gtk.FILL)
                table.attach(widget, 1, 2, row, row + 1)
            elif s.type == "spin":
                align = gtk.Alignment(0, 0.5)
                align.set_padding(0, 0, 12, 0)
                align.add(gtk.Label(s.title))
                table.attach(align, 0, 1, row, row + 1, gtk.FILL, gtk.FILL)
                align = gtk.Alignment(0, 0.5)
                align.add(widget)
                table.attach(align, 1, 2, row, row + 1)
            elif s.type == "bool":
                align = gtk.Alignment(0, 0.5)
                align.set_padding(0, 0, 12, 0)
                align.add(widget)
                table.attach(align, 0, 2, row, row + 1, gtk.FILL, gtk.FILL)
