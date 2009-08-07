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

class AppearanceDialog(gtk.Dialog):
    def __init__(self, palabra_window, properties):
        gtk.Dialog.__init__(self, "Appearance"
            , palabra_window, gtk.DIALOG_MODAL)
        self.palabra_window = palabra_window
        self.properties = properties
        self.set_size_request(640, 480)
        
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
        
        table = gtk.Table(6, 2)
        table.set_col_spacings(6)
        main.pack_start(table, False, False, 0)
        
        color = gtk.gdk.Color(*self.properties.cell["color"])
        self.cell_color_button = gtk.ColorButton()
        self.cell_color_button.set_color(color)
        
        align = gtk.Alignment(0, 0.5)
        align.set_padding(0, 0, 12, 0)
        align.add(gtk.Label("Cell:"))
        table.attach(align, 0, 1, 0, 1, gtk.FILL, gtk.FILL)
        table.attach(self.cell_color_button, 1, 2, 0, 1, 0, 0)
        
        color = gtk.gdk.Color(*self.properties.line["color"])
        self.line_color_button = gtk.ColorButton()
        self.line_color_button.set_color(color)
        
        align = gtk.Alignment(0, 0.5)
        align.set_padding(0, 0, 12, 0)
        align.add(gtk.Label("Line:"))
        table.attach(align, 0, 1, 1, 2, gtk.FILL, gtk.FILL)
        table.attach(self.line_color_button, 1, 2, 1, 2, 0, 0)
        
        color = gtk.gdk.Color(*self.properties.border["color"])
        self.border_color_button = gtk.ColorButton()
        self.border_color_button.set_color(color)
        
        align = gtk.Alignment(0, 0.5)
        align.set_padding(0, 0, 12, 0)
        align.add(gtk.Label("Border:"))
        table.attach(align, 0, 1, 2, 3, gtk.FILL, gtk.FILL)
        table.attach(self.border_color_button, 1, 2, 2, 3, 0, 0)
        
        color = gtk.gdk.Color(*self.properties.block["color"])
        self.block_color_button = gtk.ColorButton()
        self.block_color_button.set_color(color)
        
        align = gtk.Alignment(0, 0.5)
        align.set_padding(0, 0, 12, 0)
        align.add(gtk.Label("Block:"))
        table.attach(align, 0, 1, 3, 4, gtk.FILL, gtk.FILL)
        table.attach(self.block_color_button, 1, 2, 3, 4, 0, 0)
        
        color = gtk.gdk.Color(*self.properties.char["color"])
        self.char_color_button = gtk.ColorButton()
        self.char_color_button.set_color(color)
        
        align = gtk.Alignment(0, 0.5)
        align.set_padding(0, 0, 12, 0)
        align.add(gtk.Label("Letter:"))
        table.attach(align, 0, 1, 4, 5, gtk.FILL, gtk.FILL)
        table.attach(self.char_color_button, 1, 2, 4, 5, 0, 0)
        
        color = gtk.gdk.Color(*self.properties.number["color"])
        self.number_color_button = gtk.ColorButton()
        self.number_color_button.set_color(color)
        
        align = gtk.Alignment(0, 0.5)
        align.set_padding(0, 0, 12, 0)
        align.add(gtk.Label("Number:"))
        table.attach(align, 0, 1, 5, 6, gtk.FILL, gtk.FILL)
        table.attach(self.number_color_button, 1, 2, 5, 6, 0, 0)
        
        return main
        
    def gather_appearance(self):
        appearance = {}
        appearance["block"] = {}
        appearance["block"]["color"] = self.block_color_button.get_color()
        
        appearance["border"] = {}
        appearance["border"]["color"] = self.border_color_button.get_color()
        
        appearance["char"] = {}
        appearance["char"]["color"] = self.char_color_button.get_color()
        
        appearance["cell"] = {}
        appearance["cell"]["color"] = self.cell_color_button.get_color()
        
        appearance["line"] = {}
        appearance["line"]["color"] = self.line_color_button.get_color()
        
        appearance["number"] = {}
        appearance["number"]["color"] = self.number_color_button.get_color()
        
        return appearance
