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

import constants
import grid
from grid import Grid
import preferences
from view import GridView

class SizeComponent(gtk.VBox):
    def __init__(self, title=None, callback=None):
        gtk.VBox.__init__(self)
        
        self.callback = callback
        
        size_vbox = gtk.VBox(False, 0)
        
        initial_width = preferences.prefs["new_initial_width"]
        initial_height = preferences.prefs["new_initial_height"]
        
        adj = gtk.Adjustment(initial_width
            , constants.MINIMUM_WIDTH, constants.MAXIMUM_WIDTH, 1, 0, 0)
        self.width_spinner = gtk.SpinButton(adj, 0.0, 0)
        self.width_spinner.connect("output", self.on_spinner_changed)
        
        adj = gtk.Adjustment(initial_height
            , constants.MINIMUM_WIDTH, constants.MAXIMUM_WIDTH, 1, 0, 0)
        self.height_spinner = gtk.SpinButton(adj, 0.0, 0)
        self.height_spinner.connect("output", self.on_spinner_changed)
        
        spinners = gtk.HBox(False, 0)
        
        spinners.pack_start(gtk.Label("Width:"), False, False, 6)
        spinners.pack_start(self.width_spinner, False, False, 6)
        spinners.pack_start(gtk.Label("Height:"), False, False, 6)
        spinners.pack_start(self.height_spinner, False, False, 6)
        size_vbox.pack_start(spinners, True, True, 0)
        
        size_table = gtk.Table(3, 4)
        size_table.set_row_spacings(3)
        size_table.set_col_spacings(12)
        
        button = gtk.RadioButton(None, "9 x 9")
        button.set_active(initial_width == 9 and initial_height == 9)
        button.connect("toggled", self.on_size_change, 9)
        size_table.attach(button, 0, 1, 0, 1)
        
        button = gtk.RadioButton(button, "11 x 11")
        button.set_active(initial_width == 11 and initial_height == 11)
        button.connect("toggled", self.on_size_change, 11)
        size_table.attach(button, 0, 1, 1, 2)
        
        button = gtk.RadioButton(button, "13 x 13")
        button.set_active(initial_width == 13 and initial_height == 13)
        button.connect("toggled", self.on_size_change, 13)
        size_table.attach(button, 0, 1, 2, 3)
        
        button = gtk.RadioButton(button, "15 x 15")
        button.set_active(initial_width == 15 and initial_height == 15)
        button.connect("toggled", self.on_size_change, 15)
        size_table.attach(button, 1, 2, 0, 1)
        
        button = gtk.RadioButton(button, "17 x 17")
        button.set_active(initial_width == 17 and initial_height == 17)
        button.connect("toggled", self.on_size_change, 17)
        size_table.attach(button, 1, 2, 1, 2)
        
        button = gtk.RadioButton(button, "19 x 19")
        button.set_active(initial_width == 19 and initial_height == 19)
        button.connect("toggled", self.on_size_change, 19)
        size_table.attach(button, 1, 2, 2, 3)
        
        button = gtk.RadioButton(button, "21 x 21")
        button.set_active(initial_width == 21 and initial_height == 21)
        button.connect("toggled", self.on_size_change, 21)
        size_table.attach(button, 2, 3, 0, 1)
        
        button = gtk.RadioButton(button, "23 x 23")
        button.set_active(initial_width == 23 and initial_height == 23)
        button.connect("toggled", self.on_size_change, 23)
        size_table.attach(button, 2, 3, 1, 2)
        
        button = gtk.RadioButton(button, "25 x 25")
        button.set_active(initial_width == 25 and initial_height == 25)
        button.connect("toggled", self.on_size_change, 25)
        size_table.attach(button, 2, 3, 2, 3)
        
        button = gtk.RadioButton(button, "27 x 27")
        button.set_active(initial_width == 27 and initial_height == 27)
        button.connect("toggled", self.on_size_change, 27)
        size_table.attach(button, 3, 4, 0, 1)
        
        button = gtk.RadioButton(button, "29 x 29")
        button.set_active(initial_width == 29 and initial_height == 29)
        button.connect("toggled", self.on_size_change, 29)
        size_table.attach(button, 3, 4, 1, 2)
        
        button = gtk.RadioButton(button, "31 x 31")
        button.set_active(initial_width == 31 and initial_height == 31)
        button.connect("toggled", self.on_size_change, 31)
        size_table.attach(button, 3, 4, 2, 3)
        
        size_vbox.pack_start(size_table, False, False, 6)
        
        align = gtk.Alignment(0, 0)
        align.set_padding(0, 0, 12, 0)
        align.add(size_vbox)
        
        if title is not None:
            label = gtk.Label()
            label.set_alignment(0, 0)
            label.set_markup(title)
            self.pack_start(label, False, False, 6)
        self.pack_start(align, False, False, 0)
        
    def on_spinner_changed(self, widget, data=None):
        self.perform_callback()
        
    def on_size_change(self, widget, data=None):
        if widget.get_active() == 1:
            self.width_spinner.set_value(data)
            self.height_spinner.set_value(data)
            
            self.perform_callback()
                
    def perform_callback(self):
        if self.callback is not None:
            width = self.width_spinner.get_value_as_int()
            height = self.height_spinner.get_value_as_int()
            self.callback(width, height)
            
    def get_size(self):
        width = self.width_spinner.get_value_as_int()
        height = self.height_spinner.get_value_as_int()
        return (width, height)

class SizeWindow(gtk.Dialog):
    def __init__(self, parent, puzzle):
        flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                   gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
        super(SizeWindow, self).__init__("Resize grid", parent, flags, buttons)
        
        self.set_size_request(360, -1)
        self.puzzle = puzzle
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        
        main = gtk.VBox(False, 0)
        main.set_spacing(18)
        
        hbox.pack_start(main, True, True, 0)
        
        self.size_component = SizeComponent()
        
        main.pack_start(self.size_component, False, False, 0)
        
        self.vbox.pack_start(hbox, False, False, 0)
        
    def get_size(self):
        return self.size_component.get_size()

class NewWindow(gtk.Dialog):
    def __init__(self, palabra_window):
        flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
        super(NewWindow, self).__init__("New puzzle", palabra_window, flags, buttons)
        
        self.set_size_request(640, 480)
        
        self.grid = None
        
        self.preview = GridPreview()
        self.preview.display(Grid(15, 15))
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        
        main = gtk.HBox(False, 0)
        main.set_spacing(18)
        
        hbox.pack_start(main, True, True, 0)
        
        options_vbox = gtk.VBox(False, 0)
        
        self.context_vbox = gtk.VBox(False, 0)
        options_vbox.pack_start(self.context_vbox, True, True, 0)
        
        main.pack_start(options_vbox, False, False, 0)
        main.pack_start(self.preview, True, True, 0)
        
        self.vbox.pack_start(hbox, True, True, 0)
        
        self.size_component = SizeComponent(
            title=u"<b>New puzzle</b>"
            , callback=self.size_callback)
        self.context_vbox.pack_start(self.size_component, False, False, 0)
            
    def size_callback(self, width, height):
        self.grid = Grid(width, height)
        self.preview.display(self.grid)
        
    def get_configuration(self):
        width, height = self.size_component.get_size()
    
        configuration = {}
        configuration["type"] = "crossword"
        
        if self.grid is not None:
            configuration["grid"] = self.grid
        return configuration
        
class GridPreview(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self)
        
        self.view = None
        
        label = gtk.Label()
        label.set_alignment(0, 0)
        label.set_markup("<b>Preview</b>")
        
        self.drawing_area = gtk.DrawingArea()
        self.drawing_area.connect("expose_event", self.on_expose_event)
        
        self.scrolled_window = gtk.ScrolledWindow(None, None)
        self.scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scrolled_window.add_with_viewport(self.drawing_area)
        
        self.pack_start(label, False, False, 6)
        self.pack_start(self.scrolled_window, True, True, 0)
        
    def display(self, grid):
        self.view = GridView(grid)
        self.refresh()
        
    def refresh(self):
        if self.view is not None:
            self.view.properties.cell["size"] = 12
            self.view.refresh_visual_size(self.drawing_area)
            self.drawing_area.queue_draw()
        
    def clear(self):
        self.view = None
        self.drawing_area.queue_draw()
        
    def on_expose_event(self, drawing_area, event):
        if self.view is not None:
            context = drawing_area.window.cairo_create()
            self.view.select_mode(constants.VIEW_MODE_PREVIEW)
            self.view.render_background(context, event.area)
            self.view.render(context, event.area, mode=constants.VIEW_MODE_PREVIEW)
