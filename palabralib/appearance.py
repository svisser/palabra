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

MAX_LINE_WIDTH = 32

class AppearanceDialog(gtk.Dialog):
    def __init__(self, palabra_window, properties):
        gtk.Dialog.__init__(self, u"Appearance"
            , palabra_window, gtk.DIALOG_MODAL)
        self.palabra_window = palabra_window
        self.set_size_request(480, 240)
        
        main = gtk.VBox(False, 0)
        main.set_spacing(18)
        main.pack_start(self.create_content(properties), True, True, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        hbox.pack_start(main, True, True, 0)
        
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.add_button(gtk.STOCK_APPLY, gtk.RESPONSE_OK)
        self.vbox.add(hbox)
        
    def create_content(self, properties):
        main = gtk.VBox(False, 0)
        main.set_spacing(6)
        
        table = gtk.Table(9, 6)
        table.set_col_spacings(6)
        table.set_row_spacings(3)
        main.pack_start(table, False, False, 0)
        
        def create_label(label):
            align = gtk.Alignment(0, 0.5)
            align.set_padding(0, 0, 12, 0)
            align.add(gtk.Label(label))
            return align
            
        def create_color_button(color):
            color = gtk.gdk.Color(*color)
            button = gtk.ColorButton()
            button.set_color(color)
            return button
            
        def create_width_spinner(current):
            adj = gtk.Adjustment(current, 1, MAX_LINE_WIDTH, 1, 0, 0)
            return gtk.SpinButton(adj, 0.0, 0)
            
        def create_row(table, y, label, c1, c2=None):
            table.attach(label, 0, 1, y, y + 1, gtk.FILL, gtk.FILL)
            table.attach(c1, 1, 2, y, y + 1, 0, 0)
            if c2 is not None:
                table.attach(c2, 2, 3, y, y + 1, 0, 0)
        def create_row_two(table, y, label, c1, c2=None):
            table.attach(label, 3, 4, y, y + 1, gtk.FILL, gtk.FILL)
            table.attach(c1, 4, 5, y, y + 1, 0, 0)
            if c2 is not None:
                table.attach(c2, 5, 6, y, y + 1, 0, 0)
        
        label = create_label(u"Color")
        table.attach(label, 1, 2, 0, 1, gtk.FILL, gtk.FILL)
        label = create_label(u"Thickness")
        table.attach(label, 2, 3, 0, 1, gtk.FILL, gtk.FILL)
        
        # border
        label = create_label(u"Border:")
        self.border_color_button = create_color_button(properties.border["color"])
        self.border_width_spinner = create_width_spinner(properties.border["width"])
        create_row(table, 1, label, self.border_color_button, self.border_width_spinner)
        
        # lines
        label = create_label(u"Line:")
        self.line_color_button = create_color_button(properties.line["color"])
        self.line_width_spinner = create_width_spinner(properties.line["width"])
        create_row(table, 2, label, self.line_color_button, self.line_width_spinner)
        
        # cells
        label = create_label(u"Color")
        table.attach(label, 4, 5, 0, 1, gtk.FILL, gtk.FILL)
        label = create_label(u"Size")
        table.attach(label, 5, 6, 0, 1, gtk.FILL, gtk.FILL)
        
        label = create_label(u"Cell:")
        self.cell_color_button = create_color_button(properties.default.cell["color"])
        adj = gtk.Adjustment(properties.cell["size"], 32, 128, 1, 0, 0)
        self.cell_size_spinner = gtk.SpinButton(adj, 0.0, 0)
        create_row_two(table, 1, label, self.cell_color_button, self.cell_size_spinner)
        
        # blocks
        label = create_label(u"Color")
        table.attach(label, 4, 5, 2, 3, gtk.FILL, gtk.FILL)
        label = create_label(u"Margin (%)")
        table.attach(label, 5, 6, 2, 3, gtk.FILL, gtk.FILL)
        
        current = properties.default.block["margin"]
        label = create_label(u"Block:")
        self.block_color_button = create_color_button(properties.default.block["color"])
        adj = gtk.Adjustment(current, 0, 49, 1, 0, 0)
        self.block_margin_spinner = gtk.SpinButton(adj, 0.0, 0)
        create_row_two(table, 3, label, self.block_color_button, self.block_margin_spinner)
        
        # letters
        label = create_label(u"Letter:")
        self.char_color_button = create_color_button(properties.default.char["color"])
        create_row(table, 3, label, self.char_color_button)
        
        # numbers
        label = create_label(u"Number:")
        self.number_color_button = create_color_button(properties.default.number["color"])
        create_row(table, 4, label, self.number_color_button)
        
        return main
        
    def gather_appearance(self):
        appearance = {}
        appearance["block"] = {}
        appearance["block"]["margin"] = self.block_margin_spinner.get_value_as_int()
        appearance["border"] = {}
        appearance["border"]["width"] = self.border_width_spinner.get_value_as_int()
        appearance["char"] = {}
        appearance["cell"] = {}
        appearance["cell"]["size"] = self.cell_size_spinner.get_value_as_int()
        appearance["line"] = {}
        appearance["line"]["width"] = self.line_width_spinner.get_value_as_int()
        appearance["number"] = {}
        
        color = self.cell_color_button.get_color()
        appearance["cell"]["color"] = (color.red, color.green, color.blue)
        color = self.line_color_button.get_color()
        appearance["line"]["color"] = (color.red, color.green, color.blue)
        color = self.border_color_button.get_color()
        appearance["border"]["color"] = (color.red, color.green, color.blue)
        color = self.block_color_button.get_color()
        appearance["block"]["color"] = (color.red, color.green, color.blue)
        color = self.char_color_button.get_color()
        appearance["char"]["color"] = (color.red, color.green, color.blue)
        color = self.number_color_button.get_color()
        appearance["number"]["color"] = (color.red, color.green, color.blue)
        
        return appearance
