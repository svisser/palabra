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
from gui_common import (
    create_label,
    create_button,
    create_color_button,
    create_check_button,
    PalabraDialog,
)
from grid import Grid
from view import GridPreview, _relative_to, DEFAULTS_CELL

def color_tuple(button):
    color = button.get_color()
    return color.red, color.green, color.blue

class AppearanceDialog(PalabraDialog):
    def __init__(self, palabra_window, properties):
        PalabraDialog.__init__(self, palabra_window, u"Appearance")
        self.palabra_window = palabra_window
        hbox = gtk.HBox()
        hbox.set_spacing(18)
        hbox.pack_start(self.create_content(properties))
        mode = constants.VIEW_MODE_PREVIEW_SOLUTION
        self.preview = GridPreview(mode=mode, cell_size=None)
        self.preview.set_size_request(200, 200)
        hbox.pack_start(self.preview, False, False, 0)
        self.pack(hbox)
        g = Grid(3, 3)
        g.set_block(0, 2, True)
        g.set_void(2, 0, True)
        g.set_char(0, 0, 'A')
        g.assign_numbers()
        self.preview.display(g)
        self.on_update()
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.add_button(gtk.STOCK_APPLY, gtk.RESPONSE_OK)
        
    def create_content(self, properties):
        main = gtk.VBox()
        main.set_spacing(6)
        
        table = gtk.Table(10, 3)
        table.set_col_spacings(6)
        table.set_row_spacings(6)
        main.pack_start(table)
        
        def create_label(label):
            align = gtk.Alignment(0, 0.5)
            align.set_padding(0, 0, 12, 0)
            align.add(gtk.Label(label))
            return align
            
        def create_width_spinner(current):
            adj = gtk.Adjustment(current, 1, constants.MAX_LINE_WIDTH, 1, 0, 0)
            button = gtk.SpinButton(adj, 0.0, 0)
            return button
            
        def create_row(table, y, label, c1, c2=None):
            table.attach(label, 0, 1, y, y + 1, gtk.FILL, gtk.FILL)
            table.attach(c1, 1, 2, y, y + 1, 0, 0)
            if c2 is not None:
                table.attach(c2, 2, 3, y, y + 1, 0, 0)
        
        table.attach(create_label(u"Color"), 1, 2, 0, 1, gtk.FILL, gtk.FILL)
        table.attach(create_label(u"Width (px)"), 2, 3, 0, 1, gtk.FILL, gtk.FILL)
        
        def create_line_controls(title, key_color, key_width):
            label = create_label(title)
            button = create_color_button(properties[key_color], self.on_update)
            spinner = create_width_spinner(properties[key_width])
            return label, button, spinner
        
        # borders and lines
        widgets = create_line_controls(u"Border:", ("border", "color"), ("border", "width"))
        self.border_color_button = widgets[1]
        self.border_width_spinner = widgets[2]
        create_row(table, 1, *widgets)
        widgets = create_line_controls(u"Line:", ("line", "color"), ("line", "width"))
        self.line_color_button = widgets[1]
        self.line_width_spinner = widgets[2]
        create_row(table, 2, *widgets)

        def cap_line_width_at(bound):
            s = self.line_width_spinner
            adj = s.get_adjustment()
            adj.set_upper(bound)
            if s.get_value_as_int() > bound:
                s.set_value(bound)
        def on_border_width_update(widget):
            cap_line_width_at(widget.get_value_as_int())
            self.on_update()
        self.border_width_spinner.connect("value-changed", on_border_width_update)
        self.line_width_spinner.connect("value_changed", self.on_update)
        cap_line_width_at(properties["border", "width"])
        
        table.attach(create_label(u"Color"), 1, 2, 3, 4, gtk.FILL, gtk.FILL)
        table.attach(create_label(u"Size (%)"), 2, 3, 3, 4, gtk.FILL, gtk.FILL)
        
        def create_font_controls(title, key_color, key_size):
            label = create_label(title)
            button = create_color_button(properties[key_color], self.on_update)
            adj = gtk.Adjustment(properties[key_size][0], 10, 100, 1, 0, 0)
            spinner = gtk.SpinButton(adj)
            spinner.connect("value-changed", self.on_update)
            return label, button, spinner
        
        # letters and numbers
        widgets = create_font_controls(u"Letter:", ("char", "color"), ("char", "size"))
        self.char_color_button = widgets[1]
        self.char_size_spinner = widgets[2]
        create_row(table, 4, *widgets)
        widgets = create_font_controls(u"Number:", ("number", "color"), ("number", "size"))
        self.number_color_button = widgets[1]
        self.number_size_spinner = widgets[2]
        create_row(table, 5, *widgets)
        
        # cells
        table.attach(create_label(u"Color"), 1, 2, 6, 7, gtk.FILL, gtk.FILL)
        table.attach(create_label(u"Size (px)"), 2, 3, 6, 7, gtk.FILL, gtk.FILL)
        
        label = create_label(u"Cell:")
        self.cell_color_button = create_color_button(properties["cell", "color"], self.on_update)
        adj = gtk.Adjustment(properties["cell", "size"], 32, 128, 1, 0, 0)
        self.cell_size_spinner = gtk.SpinButton(adj, 0.0, 0)
        self.cell_size_spinner.connect("value-changed", self.on_update)
        create_row(table, 7, label, self.cell_color_button, self.cell_size_spinner)
        
        # blocks
        table.attach(create_label(u"Color"), 1, 2, 8, 9, gtk.FILL, gtk.FILL)
        table.attach(create_label(u"Margin (%)"), 2, 3, 8, 9, gtk.FILL, gtk.FILL)
        
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
        a["cell", "color"] = color_tuple(self.cell_color_button)
        a["line", "color"] = color_tuple(self.line_color_button)
        a["border", "color"] = color_tuple(self.border_color_button)
        a["block", "color"] = color_tuple(self.block_color_button)
        a["char", "color"] = color_tuple(self.char_color_button)
        a["number", "color"] = color_tuple(self.number_color_button)
        p = self.char_size_spinner.get_value_as_int()
        key = ("cell", "size")
        a["char", "size"] = (p, _relative_to(key, p / 100.0, d=a))
        p = self.number_size_spinner.get_value_as_int()
        a["number", "size"] = (p, _relative_to(key, p / 100.0, d=a))
        return a

class CellPropertiesDialog(PalabraDialog):
    def __init__(self, palabra_window, properties):
        super(CellPropertiesDialog, self).__init__(palabra_window, u"Cell properties")
        self.palabra_window = palabra_window
        self.properties = properties
        x, y = properties["cell"]
        c1 = (u"Background color", ("cell", "color"))
        c2 = (u"Block color", ("block", "color"))
        c3 = (u"Letter color", ("char", "color"))
        c4 = (u"Number color", ("number", "color"))
        self.colors = [c1, c2, c3, c4]
        
        self.grid = Grid(1, 1)
        self.grid.data[0][0].update(properties["grid"].data[y][x])
        
        table = gtk.Table(3, 3, False)
        table.set_col_spacings(6)
        table.set_row_spacings(6)
        def create_row(table, title, value, x, y):
            table.attach(create_label(title), x, x + 1, y, y + 1, gtk.FILL, gtk.FILL)
            table.attach(create_label(value, align=(0, 0)), x + 1, x + 2, y, y + 1)
        def create_color_row(table, title, b_align, r_align, x, y):
            table.attach(create_label(title), x, x + 1, y, y + 1, gtk.FILL, gtk.FILL)
            table.attach(b_align, x + 1, x + 2, y, y + 1)
            table.attach(r_align, x + 2, x + 3, y, y + 1)
        on_color_set = lambda button, key: self._on_update(key, color_tuple(button))    
        for i, (title, key) in enumerate(self.colors):
            attr = '_'.join(list(key) + ["button"])
            setattr(self, attr, create_color_button(properties[key]))
            getattr(self, attr).connect("color-set", on_color_set, key)
            attr2 = '_'.join(list(key) + ["reset", "button"])
            setattr(self, attr2, gtk.Button(u"Reset"))
            getattr(self, attr2).connect("clicked", self.on_color_reset, key)
            b_align = gtk.Alignment(0, 0.5)
            b_align.add(getattr(self, attr))
            r_align = gtk.Alignment(0, 0.5)
            r_align.add(getattr(self, attr2))
            create_color_row(table, title, b_align, r_align, 0, i)
        
        table.attach(create_label(u"Other options"), 0, 1, 4, 5, gtk.FILL, gtk.FILL)
        on_circle = lambda b: self._on_update("circle", b.get_active())
        self.circle_button = create_check_button(u"Display circle"
            , active=properties["circle"], f_toggle=on_circle)
        table.attach(self.circle_button, 1, 3, 4, 5)

        main = gtk.VBox()
        main.set_spacing(6)
        main.pack_start(create_label(u"<b>Properties</b>"), False, False, 0)
        main.pack_start(table, False, False, 0)
        content = gtk.HBox()
        content.set_border_width(6)
        content.set_spacing(6)
        content.pack_start(main)
        
        self.previews = []
        prevs = gtk.VBox()
        p1 = (constants.VIEW_MODE_PREVIEW_CELL, "Puzzle")
        p2 = (constants.VIEW_MODE_PREVIEW_SOLUTION, "Solution")
        for m, h in [p1, p2]:
            p = GridPreview(mode=m, header=h, cell_size=96)
            p.set_size_request(164, 164)
            align = gtk.Alignment()
            align.add(p)
            self.previews.append(p)
            p.display(self.grid)
            for k in DEFAULTS_CELL:
                p.view.properties[k] = properties[k]
            p.refresh()
            prevs.pack_start(align, False, False, 0)
        content.pack_start(prevs, False, False, 0)
        self.pack(content)
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.add_button(gtk.STOCK_APPLY, gtk.RESPONSE_OK)
        
    def on_color_reset(self, button, key):
        color = self.properties["defaults"][key]
        button = getattr(self, '_'.join(list(key) + ["button"]))
        c = button.get_color()
        c.red, c.green, c.blue = color
        button.set_color(c)
        self._on_update(key, color)
            
    def _on_update(self, key, value):
        for p in self.previews:
            p.view.properties[key] = value
            p.refresh(force=True)
    
    def gather_appearance(self):
        a = {}
        for title, key in self.colors:
            attr = '_'.join(list(key) + ["button"])
            a[key] = color_tuple(getattr(self, attr))
        a["circle"] = self.circle_button.get_active()
        return a
