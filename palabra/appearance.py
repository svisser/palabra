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

MAX_LINE_WIDTH = 32

def apply_appearance(properties, appearance):
    cell_color = appearance["cell"]["color"]
    cell_red = cell_color.red
    cell_green = cell_color.green
    cell_blue = cell_color.blue
    
    line_color = appearance["line"]["color"]
    line_red = line_color.red
    line_green = line_color.green
    line_blue = line_color.blue
    
    border_color = appearance["border"]["color"]
    border_red = border_color.red
    border_green = border_color.green
    border_blue = border_color.blue
    
    block_color = appearance["block"]["color"]
    block_red = block_color.red
    block_green = block_color.green
    block_blue = block_color.blue
    
    char_color = appearance["char"]["color"]
    char_red = char_color.red
    char_green = char_color.green
    char_blue = char_color.blue
    
    number_color = appearance["number"]["color"]
    number_red = number_color.red
    number_green = number_color.green
    number_blue = number_color.blue
    
    properties.block["color"] = (block_red, block_green, block_blue)
    properties.border["color"] = (border_red, border_green, border_blue)
    properties.char["color"] = (char_red, char_green, char_blue)
    properties.cell["color"] = (cell_red, cell_green, cell_blue)
    properties.line["color"] = (line_red, line_green, line_blue)
    properties.number["color"] = (number_red, number_green, number_blue)
    
    properties.border["width"] = appearance["border"]["width"]
    properties.line["width"] = appearance["line"]["width"]
    properties.block["margin"] = appearance["block"]["margin"]

class AppearanceDialog(gtk.Dialog):
    def __init__(self, palabra_window, properties):
        gtk.Dialog.__init__(self, "Appearance"
            , palabra_window, gtk.DIALOG_MODAL)
        self.palabra_window = palabra_window
        self.properties = properties
        self.set_size_request(480, 320)
        
        main = gtk.VBox(False, 0)
        main.set_spacing(18)
        main.pack_start(self.create_content(), True, True, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        hbox.pack_start(main, True, True, 0)
        
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.add_button(gtk.STOCK_APPLY, gtk.RESPONSE_OK)
        self.vbox.add(hbox)
        
    def create_content(self):
        main = gtk.VBox(False, 0)
        main.set_spacing(6)
        
        table = gtk.Table(8, 3)
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
        
        label = create_label("Color")
        table.attach(label, 1, 2, 0, 1, gtk.FILL, gtk.FILL)
        label = create_label("Thickness")
        table.attach(label, 2, 3, 0, 1, gtk.FILL, gtk.FILL)
        
        # lines
        label = create_label(u"Line:")
        self.line_color_button = create_color_button(self.properties.line["color"])
        self.line_width_spinner = create_width_spinner(self.properties.line["width"])
        create_row(table, 1, label, self.line_color_button, self.line_width_spinner)
        
        # border
        label = create_label(u"Border:")
        self.border_color_button = create_color_button(self.properties.border["color"])
        self.border_width_spinner = create_width_spinner(self.properties.border["width"])
        create_row(table, 2, label, self.border_color_button, self.border_width_spinner)
        
        # cells
        label = create_label(u"Cell:")
        self.cell_color_button = create_color_button(self.properties.cell["color"])
        create_row(table, 3, label, self.cell_color_button)
        
        # blocks
        label = create_label(u"Color")
        table.attach(label, 1, 2, 4, 5, gtk.FILL, gtk.FILL)
        label = create_label(u"Margin (%)")
        table.attach(label, 2, 3, 4, 5, gtk.FILL, gtk.FILL)
        
        current = self.properties.block["margin"]
        label = create_label(u"Blocks:")
        self.block_color_button = create_color_button(self.properties.block["color"])
        adj = gtk.Adjustment(current, 0, 49, 1, 0, 0)
        self.block_margin_spinner = gtk.SpinButton(adj, 0.0, 0)
        create_row(table, 5, label, self.block_color_button, self.block_margin_spinner)
        
        # letters
        label = create_label(u"Letter:")
        self.char_color_button = create_color_button(self.properties.char["color"])
        create_row(table, 6, label, self.char_color_button)
        
        # numbers
        label = create_label(u"Number:")
        self.number_color_button = create_color_button(self.properties.number["color"])
        create_row(table, 7, label, self.number_color_button)
        
        return main
        
    def gather_appearance(self):
        appearance = {}
        appearance["block"] = {}
        appearance["block"]["color"] = self.block_color_button.get_color()
        appearance["block"]["margin"] = self.block_margin_spinner.get_value_as_int()
        
        appearance["border"] = {}
        appearance["border"]["color"] = self.border_color_button.get_color()
        appearance["border"]["width"] = self.border_width_spinner.get_value_as_int()
        
        appearance["char"] = {}
        appearance["char"]["color"] = self.char_color_button.get_color()
        
        appearance["cell"] = {}
        appearance["cell"]["color"] = self.cell_color_button.get_color()
        
        appearance["line"] = {}
        appearance["line"]["color"] = self.line_color_button.get_color()
        appearance["line"]["width"] = self.line_width_spinner.get_value_as_int()
        
        appearance["number"] = {}
        appearance["number"]["color"] = self.number_color_button.get_color()
        
        return appearance
