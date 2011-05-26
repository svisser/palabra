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

import constants
import files

SETTING_TABS = [("page", u"Page")
    , ("grid", u"Grid")
    , ("clue", u"Clue")
    , ("clueh", u"Clue header")
    , ("answers", u"Answers")
]
OUTPUT_OPTIONS = [("puzzle", u"Puzzle")
    , ("grid", u"Grid")
    , ("solution", u"Solution")
    , ("clues", u"Clues")
    , ("answers", u"Clues with answers")
]

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
    def __init__(self, tab, type, title, key, default, properties=None, editable=None):
        self.tab = tab
        self.type = type
        self.title = title
        self.key = key
        self.default = default
        self.properties = properties
        self.callback = None
        self.editable = editable

class HeaderEditor(gtk.Dialog):
    def __init__(self, parent, puzzle, header):
        flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
        super(HeaderEditor, self).__init__(u"Page header editor", parent, flags)
        self.puzzle = puzzle
        self.header = header
        main = gtk.VBox()
        main.set_border_width(12)
        main.set_spacing(18)
        label = gtk.Label()
        label.set_markup(u"<b>Header text</b>:")
        label.set_alignment(0, 0.5)
        main.pack_start(label, False, False, 0)
        self.text = gtk.TextView()
        self.text.set_size_request(512, 320)
        self.text.get_buffer().connect("changed", self.on_header_changed)
        main.pack_start(self.text, True, True, 0)
        label = gtk.Label()
        label.set_markup(u"<b>Header preview</b>:")
        label.set_alignment(0, 0.5)
        main.pack_start(label, False, False, 0)
        self.preview = gtk.Label()
        s_window = gtk.ScrolledWindow()
        s_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        s_window.add_with_viewport(self.preview)
        main.pack_start(s_window, False, False, 0)
        self.text.get_buffer().set_text(self.header)
        labels_vbox = gtk.VBox()
        labels_vbox.set_border_width(12)
        labels_vbox.set_spacing(6)
        label = gtk.Label()
        label.set_markup(u"<b>Click to insert</b>:")
        label.set_alignment(0, 0.5)
        labels_vbox.pack_start(label, False, False, 0)
        for code, title in constants.META_CAPTIONS:
            label = gtk.Label(title + " (" + code + ")")
            label.set_alignment(0, 0.5)
            eventbox = gtk.EventBox()
            eventbox.add(label)
            eventbox.connect("button-press-event", self.on_code_clicked, code)
            labels_vbox.pack_start(eventbox, False, False, 0)
        content_box = gtk.HBox()
        content_box.pack_start(main, True, True, 0)
        content_box.pack_start(labels_vbox, False, False, 0)
        self.vbox.pack_start(content_box, True, True, 0)
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        
    def on_code_clicked(self, widget, event, code):
        buff = self.text.get_buffer()
        start, end = buff.get_bounds()
        header = buff.get_text(start, end)
        insert_it = buff.get_iter_at_mark(buff.get_insert())
        if insert_it.get_char() == buff.get_end_iter().get_char():
            if header.endswith(" "):
                buff.set_text(header + code)
            else:
                buff.set_text(header + " " + code)
        else:
            buff.insert_at_cursor(code)
        
    def on_header_changed(self, buff):
        start, end = buff.get_bounds()
        self.header = buff.get_text(start, end).strip()
        preview_txt = files.compute_header(self.puzzle, self.header)
        preview_txt = files.compute_header(self.puzzle, preview_txt, page_n=0)
        self.preview.set_text(preview_txt)

class ExportWindow(gtk.Dialog):
    def __init__(self, palabra_window, puzzle):
        flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
        super(ExportWindow, self).__init__(u"Export puzzle", palabra_window, flags)
        self.palabra_window = palabra_window
        self.puzzle = puzzle
        pdf = Format("pdf", u"PDF (pdf)", ["puzzle", "grid", "solution", "answers"])
        pdf.add(Setting("page", "bool", u"Include header", "page_header_include", True))
        pdf.add(Setting("page", "bool", u"Include header on each page", "page_header_include_all", False))
        pdf.add(Setting("page", "text", u"Header:", "page_header_text", u"%T / %A", editable=self.on_edit_header))
        pdf.add(Setting("grid", "spin", u"Cell size in puzzle (mm)", "cell_size_puzzle", 7, (5, 10)))
        pdf.add(Setting("grid", "spin", u"Cell size in solution (mm)", "cell_size_solution", 6, (5, 10)))
        pdf.add(Setting("grid", "combo", u"Align grid:", "align", "right"
            , [(u"Left", "left"), (u"Center", "center"), (u"Right", "right")]))
        pdf.add(Setting("clue", "combo", u"Clues:", "clue_placement", "wrap"
            , [(u"Wrapped around grid", "wrap"), (u"Below grid", "below")]))
        pdf.add(Setting("clue", "spin", u"Columns", "n_columns", 3, (3, 5)))
        pdf.add(Setting("clue", "spin", u"Spacing between columns\n\t(% of available width)", "column_spacing", 5, (0, 20)))
        pdf.add(Setting("page", "spin", u"Margin left (mm)", "margin_left", 20, (0, 50)))
        pdf.add(Setting("page", "spin", u"Margin right (mm)", "margin_right", 20, (0, 50)))
        pdf.add(Setting("page", "spin", u"Margin top (mm)", "margin_top", 20, (0, 50)))
        pdf.add(Setting("page", "spin", u"Margin bottom (mm)", "margin_bottom", 20, (0, 50)))
        pdf.add(Setting("clue", "bool", u"Bold clue number", "clue_number_bold", True))
        pdf.add(Setting("clue", "bool", u"Add period after clue number", "clue_number_period", False))
        pdf.add(Setting("clue", "bool", u"Add length of solution after clue", "clue_length", False))
        pdf.add(Setting("clueh", "text", u"Across header:", "clue_header_across", u"Across"))
        pdf.add(Setting("clueh", "text", u"Down header:", "clue_header_down", u"Down"))
        pdf.add(Setting("clueh", "bool", u"Bold clue header", "clue_header_bold", True))
        pdf.add(Setting("clueh", "bool", u"Italic clue header", "clue_header_italic", False))
        pdf.add(Setting("clueh", "bool", u"Underline clue header", "clue_header_underline", False))
        pdf.add(Setting("answers", "spin", u"Width of clue column\n\t(% of available width)", "answers_clue_width", 50, (10, 90)))
        pdf.add(Setting("answers", "spin", u"Width of spacing between clues / answers\n\t(% of available width)", "answers_clue_sep", 5, (0, 20)))
        png = Format("png", u"PNG (png)", ["grid", "solution"], False)
        self.formats = [pdf, png]
        self.outputs = {}
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
        
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.ok_button = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        
    def reset_options(self):
        self.options = {}
        self.options["format"] = None
        self.options["output"] = dict([(k, False) for k, v in OUTPUT_OPTIONS])
        self.options["settings"] = {}
        for f in self.formats:
            for s in f.settings:
                self.options["settings"][s.key] = s.default
        
    def select_format(self, index):
        if self.format is not None:
            for w in self.removes:
                self.options_window.remove(w)
        self.format = self.formats[index]
        self.reset_options()
        self.options["format"] = self.format.key
        self.tabs = gtk.Notebook()
        self.tabs.set_property("tab-hborder", 8)
        self.tabs.set_property("tab-vborder", 4)
        n_tabs = 0
        for k, t in SETTING_TABS:
            key_setts = [v for v in self.format.settings if v.tab == k]
            if not key_setts:
                continue
            n_tabs += 1
            tab = gtk.HBox(False, 0)
            tab.set_border_width(6)
            tab.set_spacing(6)
            tab_c = gtk.VBox(False, 0)
            self._create_settings(tab_c, key_setts, self.puzzle)
            tab.pack_start(tab_c, True, True, 0)
            self.tabs.append_page(tab, gtk.Label(t))
        self.option = gtk.VBox(False, 0)
        def callback(widget, data=None):
            self.options["output"][data] = widget.get_active()
            self.check_ok_button(check=self.format.allow_multiple)
        self._create_output_options(self.option, self.format, callback)
        self.removes = []        
        label = gtk.Label()
        label.set_alignment(0, 0)
        label.set_markup(u"<b>Settings:</b>")
        self.options_window.pack_start(label, False, False, 6)
        self.removes.append(label)
        if n_tabs > 0:
            self.options_window.pack_start(self.tabs, True, True, 0)
            self.removes.append(self.tabs)
        else:
            label = gtk.Label()
            label.set_alignment(0, 0)
            label.set_markup(u"No settings available.")
            self.options_window.pack_start(label, False, False, 6)
            self.removes.append(label)
        self.options_window.pack_start(self.option, False, False, 0)
        self.removes.append(self.option)
        self.options_window.show_all()
        
    def on_tree_clicked(self, treeview, event):
        if event.button != 1:
            return True
        if event.button == 1:
            pos = int(event.x), int(event.y)
            item = treeview.get_path_at_pos(*pos)
            if item is not None:
                self.select_format(item[0][0])
                
    def check_ok_button(self, check=True):
        try:
            sensitive = True
            if check:
                outputs = self.outputs[self.options["format"]]
                sensitive = True in [w.get_active() for w in outputs]
            self.ok_button.set_sensitive(sensitive)
        except AttributeError:
            pass
            
    def on_edit_header(self, item, puzzle):
        cur_header = self.options["settings"]["page_header_text"]
        w = HeaderEditor(self, puzzle, cur_header)
        w.show_all()
        if w.run() == gtk.RESPONSE_OK:
            self.options["settings"]["page_header_text"] = w.header
        w.destroy()
            
    def _create_output_options(self, main, format, callback):
        label = gtk.Label()
        label.set_alignment(0, 0)
        label.set_markup(u"<b>Output</b>")
        main.pack_start(label, False, False, 6)
        prev_option = None
        self.outputs[format.key] = []
        for i, (key, title) in enumerate(OUTPUT_OPTIONS):
            if key in format.outputs:
                if format.allow_multiple:
                    button = gtk.CheckButton(title)
                    button.connect("toggled", callback, key)
                    if i == 0:
                        button.set_active(True)
                        callback(button, key)
                    self.outputs[format.key].append(button)
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
        self.check_ok_button(check=format.allow_multiple)
        
    @staticmethod
    def _create_settings(main, settings, puzzle):
        if not settings:
            return
        table = gtk.Table(len(settings), 2)
        table.set_col_spacings(6)
        table.set_row_spacings(6)
        main.pack_start(table, False, False, 0)
        for row, s in enumerate(settings):
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
            if s.type == "text":
                align = gtk.Alignment(0, 0.5)
                align.set_padding(0, 0, 12, 0)
                align.add(gtk.Label(s.title))
                table.attach(align, 0, 1, row, row + 1, gtk.FILL, gtk.FILL)
                if s.editable:
                    button = gtk.ToolButton() # TODO check
                    button.set_stock_id(gtk.STOCK_EDIT)
                    button.connect("clicked", s.editable, puzzle)
                    table.attach(button, 1, 2, row, row + 1)
                else:
                    table.attach(widget, 1, 2, row, row + 1)
            elif s.type in ["combo", "spin"]:
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
