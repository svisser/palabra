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

class AppearanceDialog(gtk.Dialog):
    def __init__(self, palabra_window, properties):
        gtk.Dialog.__init__(self, "Appearance"
            , palabra_window, gtk.DIALOG_MODAL)
        self.palabra_window = palabra_window
        self.properties = properties
        self.set_size_request(640, 480)
        
        tabs = gtk.Notebook()
        tabs.append_page(self.create_cell_page(), gtk.Label("Cell"))
        tabs.append_page(self.create_line_page(), gtk.Label("Line"))
        tabs.append_page(self.create_border_page(), gtk.Label("Border"))
        
        main = gtk.VBox(False, 0)
        main.set_spacing(18)
        main.pack_start(tabs, True, True, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        hbox.pack_start(main, True, True, 0)
        
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.add_button(gtk.STOCK_APPLY, gtk.RESPONSE_OK)
        self.vbox.add(hbox)
        
    def create_cell_page(self):
        main = gtk.VBox(False, 0)
        main.set_spacing(6)
        
        table = gtk.Table(1, 2)
        table.set_col_spacings(6)
        main.pack_start(table, False, False, 0)
        
        color = gtk.gdk.Color(*self.properties.cell["color"])
        self.cell_color_button = gtk.ColorButton()
        self.cell_color_button.set_color(color)
        
        align = gtk.Alignment(0, 0.5)
        align.set_padding(0, 0, 12, 0)
        align.add(gtk.Label("Color:"))
        table.attach(align, 0, 1, 0, 1, gtk.FILL, gtk.FILL)
        table.attach(self.cell_color_button, 1, 2, 0, 1, 0, 0)
        
        return main
        
    def create_line_page(self):
        return gtk.VBox(False, 0)
        
    def create_border_page(self):
        return gtk.VBox(False, 0)
        
    def gather_appearance(self):
        appearance = {}
        appearance["cell"] = {}
        appearance["cell"]["color"] = self.cell_color_button.get_color()
        
        return appearance
