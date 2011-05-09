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
from grid import Grid
from view import GridPreview, _relative_to

MAX_LINE_WIDTH = 32

def create_color_button(color, f=None):
    color = gtk.gdk.Color(*color)
    button = gtk.ColorButton()
    button.set_color(color)
    if f:
        button.connect("color-set", f)
    return button

class AppearanceDialog(gtk.Dialog):
    def __init__(self, palabra_window, properties):
        gtk.Dialog.__init__(self, u"Appearance"
            , palabra_window, gtk.DIALOG_MODAL)
        self.palabra_window = palabra_window
        
        main = gtk.VBox(False, 0)
        main.set_spacing(18)
        main.pack_start(self.create_content(properties), True, True, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        hbox.pack_start(main, True, True, 0)
        mode = constants.VIEW_MODE_PREVIEW_SOLUTION
        self.preview = GridPreview(mode=mode, cell_size=None)
        self.preview.set_size_request(200, 200)
        hbox.pack_start(self.preview, False, False, 0)
        g = Grid(3, 3)
        g.set_block(0, 2, True)
        g.set_void(2, 0, True)
        g.set_char(0, 0, 'A')
        g.assign_numbers()
        self.preview.display(g)
        self.on_update()
        
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.add_button(gtk.STOCK_APPLY, gtk.RESPONSE_OK)
        self.vbox.add(hbox)
        
    def create_content(self, properties):
        main = gtk.VBox(False, 0)
        main.set_spacing(6)
        
        table = gtk.Table(10, 3)
        table.set_col_spacings(6)
        table.set_row_spacings(6)
        main.pack_start(table, True, True, 0)
        
        def create_label(label):
            align = gtk.Alignment(0, 0.5)
            align.set_padding(0, 0, 12, 0)
            align.add(gtk.Label(label))
            return align
            
        def create_width_spinner(current):
            adj = gtk.Adjustment(current, 1, MAX_LINE_WIDTH, 1, 0, 0)
            button = gtk.SpinButton(adj, 0.0, 0)
            button.connect("value-changed", self.on_update)
            return button
            
        def create_row(table, y, label, c1, c2=None):
            table.attach(label, 0, 1, y, y + 1, gtk.FILL, gtk.FILL)
            table.attach(c1, 1, 2, y, y + 1, 0, 0)
            if c2 is not None:
                table.attach(c2, 2, 3, y, y + 1, 0, 0)
        
        label = create_label(u"Color")
        table.attach(label, 1, 2, 0, 1, gtk.FILL, gtk.FILL)
        label = create_label(u"Width (px)")
        table.attach(label, 2, 3, 0, 1, gtk.FILL, gtk.FILL)
        
        # border
        label = create_label(u"Border:")
        self.border_color_button = create_color_button(properties["border", "color"], self.on_update)
        self.border_width_spinner = create_width_spinner(properties["border", "width"])
        create_row(table, 1, label, self.border_color_button, self.border_width_spinner)
        
        # lines
        label = create_label(u"Line:")
        self.line_color_button = create_color_button(properties["line", "color"], self.on_update)
        self.line_width_spinner = create_width_spinner(properties["line", "width"])
        create_row(table, 2, label, self.line_color_button, self.line_width_spinner)
        
        # letters
        label = create_label(u"Size (%)")
        table.attach(label, 2, 3, 3, 4, gtk.FILL, gtk.FILL)
        
        label = create_label(u"Letter:")
        self.char_color_button = create_color_button(properties["char", "color"], self.on_update)
        adj = gtk.Adjustment(properties["char", "size"][0], 10, 100, 1, 0, 0)
        self.char_size_spinner = gtk.SpinButton(adj)
        self.char_size_spinner.connect("value-changed", self.on_update)
        create_row(table, 4, label, self.char_color_button, self.char_size_spinner)
        
        # numbers
        label = create_label(u"Number:")
        self.number_color_button = create_color_button(properties["number", "color"], self.on_update)
        adj = gtk.Adjustment(properties["number", "size"][0], 10, 100, 1, 0, 0)
        self.number_size_spinner = gtk.SpinButton(adj)
        self.number_size_spinner.connect("value-changed", self.on_update)
        create_row(table, 5, label, self.number_color_button, self.number_size_spinner)
        
        # cells
        label = create_label(u"Color")
        table.attach(label, 1, 2, 6, 7, gtk.FILL, gtk.FILL)
        label = create_label(u"Size (px)")
        table.attach(label, 2, 3, 6, 7, gtk.FILL, gtk.FILL)
        
        label = create_label(u"Cell:")
        self.cell_color_button = create_color_button(properties["cell", "color"], self.on_update)
        adj = gtk.Adjustment(properties["cell", "size"], 32, 128, 1, 0, 0)
        self.cell_size_spinner = gtk.SpinButton(adj, 0.0, 0)
        self.cell_size_spinner.connect("value-changed", self.on_update)
        create_row(table, 7, label, self.cell_color_button, self.cell_size_spinner)
        
        # blocks
        label = create_label(u"Color")
        table.attach(label, 1, 2, 8, 9, gtk.FILL, gtk.FILL)
        label = create_label(u"Margin (%)")
        table.attach(label, 2, 3, 8, 9, gtk.FILL, gtk.FILL)
        
        current = properties["block", "margin"]
        label = create_label(u"Block:")
        self.block_color_button = create_color_button(properties["block", "color"], self.on_update)
        adj = gtk.Adjustment(current, 0, 49, 1, 0, 0)
        self.block_margin_spinner = gtk.SpinButton(adj, 0.0, 0)
        self.block_margin_spinner.connect("value-changed", self.on_update)
        create_row(table, 9, label, self.block_color_button, self.block_margin_spinner)
        return main
        
    def on_update(self, widget=None):
        for k, v in self.gather_appearance().items():
            self.preview.view.properties[k] = v
        self.preview.refresh(force=True)
        
    def gather_appearance(self):
        a = {}
        a["block", "margin"] = self.block_margin_spinner.get_value_as_int()
        a["border", "width"] = self.border_width_spinner.get_value_as_int()
        a["cell", "size"] = self.cell_size_spinner.get_value_as_int()
        a["line", "width"] = self.line_width_spinner.get_value_as_int()
        color = self.cell_color_button.get_color()
        a["cell", "color"] = (color.red, color.green, color.blue)
        color = self.line_color_button.get_color()
        a["line", "color"] = (color.red, color.green, color.blue)
        color = self.border_color_button.get_color()
        a["border", "color"] = (color.red, color.green, color.blue)
        color = self.block_color_button.get_color()
        a["block", "color"] = (color.red, color.green, color.blue)
        color = self.char_color_button.get_color()
        a["char", "color"] = (color.red, color.green, color.blue)
        color = self.number_color_button.get_color()
        a["number", "color"] = (color.red, color.green, color.blue)
        p = self.char_size_spinner.get_value_as_int()
        key = ("cell", "size")
        a["char", "size"] = (p, _relative_to(key, p / 100.0, d=a))
        p = self.number_size_spinner.get_value_as_int()
        a["number", "size"] = (p, _relative_to(key, p / 100.0, d=a))
        return a
