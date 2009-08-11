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
from files import import_template, import_templates
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

class PatternComponent(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self)
        
        label = gtk.Label()
        label.set_alignment(0, 0)
        label.set_markup("<b>Pattern</b>")
        
        pattern_vbox = gtk.VBox(False, 0)
        
        pattern_vbox.pack_start(gtk.Button("TEST"), False, False, 0)
        
        align = gtk.Alignment(0, 0)
        align.set_padding(0, 0, 12, 0)
        align.add(pattern_vbox)
        
        self.pack_start(label, False, False, 6)
        self.pack_start(align, False, False, 0)

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
        
class FilterTemplateDialog(gtk.Dialog):
    def __init__(self, parent_window, current_filter):
        flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
            gtk.STOCK_APPLY, gtk.RESPONSE_ACCEPT)
        super(FilterTemplateDialog, self).__init__("Filter templates", parent_window, flags, buttons)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        main = gtk.VBox(False, 0)
        main.set_spacing(6)
        
        filter_table = gtk.Table(4, 4)
        filter_table.set_row_spacings(3)
        filter_table.set_col_spacings(12)
        
        check_min_width_hbox = gtk.HBox(False, 0)
        self.check_min_width = gtk.CheckButton("Minimum width")
        def on_width_toggled(widget):
            self.min_width_spinner.set_sensitive(widget.get_active() == 1)
        self.check_min_width.connect("toggled", on_width_toggled)
        adj = gtk.Adjustment(15
            , constants.MINIMUM_WIDTH, constants.MAXIMUM_WIDTH, 1, 0, 0)
        self.min_width_spinner = gtk.SpinButton(adj, 0.0, 0)
        filter_table.attach(self.check_min_width, 0, 1, 0, 1)
        filter_table.attach(self.min_width_spinner, 1, 2, 0, 1)
        
        if current_filter is not None:
            self.min_width_spinner.set_value(current_filter["min_width"]["value"])
            self.check_min_width.set_active(current_filter["min_width"]["status"])
            self.min_width_spinner.set_sensitive(current_filter["min_width"]["status"])
        else:
            self.check_min_width.set_active(False)
            self.min_width_spinner.set_sensitive(False)
        
        check_max_width_hbox = gtk.HBox(False, 0)
        self.check_max_width = gtk.CheckButton("Maximum width")
        def on_width_toggled(widget):
            self.max_width_spinner.set_sensitive(widget.get_active() == 1)
        self.check_max_width.connect("toggled", on_width_toggled)
        adj = gtk.Adjustment(15
            , constants.MINIMUM_WIDTH, constants.MAXIMUM_WIDTH, 1, 0, 0)
        self.max_width_spinner = gtk.SpinButton(adj, 0.0, 0)
        self.max_width_spinner.set_sensitive(False)
        filter_table.attach(self.check_max_width, 2, 3, 0, 1)
        filter_table.attach(self.max_width_spinner, 3, 4, 0, 1)
        
        if current_filter is not None:
            self.max_width_spinner.set_value(current_filter["max_width"]["value"])
            self.check_max_width.set_active(current_filter["max_width"]["status"])
            self.max_width_spinner.set_sensitive(current_filter["max_width"]["status"])
        else:
            self.check_max_width.set_active(False)
            self.max_width_spinner.set_sensitive(False)
        
        check_min_height_hbox = gtk.HBox(False, 0)
        self.check_min_height = gtk.CheckButton("Minimum height")
        def on_height_toggled(widget):
            self.min_height_spinner.set_sensitive(widget.get_active() == 1)
        self.check_min_height.connect("toggled", on_height_toggled)
        adj = gtk.Adjustment(15
            , constants.MINIMUM_WIDTH, constants.MAXIMUM_WIDTH, 1, 0, 0)
        self.min_height_spinner = gtk.SpinButton(adj, 0.0, 0)
        self.min_height_spinner.set_sensitive(False)
        filter_table.attach(self.check_min_height, 0, 1, 1, 2)
        filter_table.attach(self.min_height_spinner, 1, 2, 1, 2)
        
        if current_filter is not None:
            self.min_height_spinner.set_value(current_filter["min_height"]["value"])
            self.check_min_height.set_active(current_filter["min_height"]["status"])
            self.min_height_spinner.set_sensitive(current_filter["min_height"]["status"])
        else:
            self.check_min_height.set_active(False)
            self.min_height_spinner.set_sensitive(False)
            
        check_max_height_hbox = gtk.HBox(False, 0)
        self.check_max_height = gtk.CheckButton("Maximum height")
        def on_height_toggled(widget):
            self.max_height_spinner.set_sensitive(widget.get_active() == 1)
        self.check_max_height.connect("toggled", on_height_toggled)
        adj = gtk.Adjustment(15
            , constants.MINIMUM_WIDTH, constants.MAXIMUM_WIDTH, 1, 0, 0)
        self.max_height_spinner = gtk.SpinButton(adj, 0.0, 0)
        self.max_height_spinner.set_sensitive(False)
        filter_table.attach(self.check_max_height, 2, 3, 1, 2)
        filter_table.attach(self.max_height_spinner, 3, 4, 1, 2)
        
        if current_filter is not None:
            self.max_height_spinner.set_value(current_filter["max_height"]["value"])
            self.check_max_height.set_active(current_filter["max_height"]["status"])
            self.max_height_spinner.set_sensitive(current_filter["max_height"]["status"])
        else:
            self.check_max_height.set_active(False)
            self.max_height_spinner.set_sensitive(False)
        
        check_min_words_hbox = gtk.HBox(False, 0)
        self.check_min_words = gtk.CheckButton("Minimum word count")
        def on_words_toggled(widget):
            self.min_words_spinner.set_sensitive(widget.get_active() == 1)
        self.check_min_words.connect("toggled", on_words_toggled)
        adj = gtk.Adjustment(15
            , 1, 2 * constants.MAXIMUM_WIDTH, 1, 0, 0)
        self.min_words_spinner = gtk.SpinButton(adj, 0.0, 0)
        self.min_words_spinner.set_sensitive(False)
        filter_table.attach(self.check_min_words, 0, 1, 2, 3)
        filter_table.attach(self.min_words_spinner, 1, 2, 2, 3)
        
        if current_filter is not None:
            self.min_words_spinner.set_value(current_filter["min_words"]["value"])
            self.check_min_words.set_active(current_filter["min_words"]["status"])
            self.min_words_spinner.set_sensitive(current_filter["min_words"]["status"])
        else:
            self.check_min_words.set_active(False)
            self.min_words_spinner.set_sensitive(False)
            
        check_max_words_hbox = gtk.HBox(False, 0)
        self.check_max_words = gtk.CheckButton("Maximum word count")
        def on_words_toggled(widget):
            self.max_words_spinner.set_sensitive(widget.get_active() == 1)
        self.check_max_words.connect("toggled", on_words_toggled)
        adj = gtk.Adjustment(15
            , 1, 2 * constants.MAXIMUM_WIDTH, 1, 0, 0)
        self.max_words_spinner = gtk.SpinButton(adj, 0.0, 0)
        self.max_words_spinner.set_sensitive(False)
        filter_table.attach(self.check_max_words, 2, 3, 2, 3)
        filter_table.attach(self.max_words_spinner, 3, 4, 2, 3)
        
        if current_filter is not None:
            self.max_words_spinner.set_value(current_filter["max_words"]["value"])
            self.check_max_words.set_active(current_filter["max_words"]["status"])
            self.max_words_spinner.set_sensitive(current_filter["max_words"]["status"])
        else:
            self.check_max_words.set_active(False)
            self.max_words_spinner.set_sensitive(False)
        
        main.pack_start(filter_table, True, True, 0)
        
        hbox.pack_start(main, True, True, 0)
        
        self.vbox.pack_start(hbox, False, False, 0)
        
    def get_filter(self):
        predicates = []
        current_filter = {}
        
        min_width_value = self.min_width_spinner.get_value_as_int()
        max_width_value = self.max_width_spinner.get_value_as_int()
        min_height_value = self.min_height_spinner.get_value_as_int()
        max_height_value = self.max_height_spinner.get_value_as_int()
        min_words_value = self.min_words_spinner.get_value_as_int()
        max_words_value = self.max_words_spinner.get_value_as_int()
        
        min_width_status = self.check_min_width.get_active()
        max_width_status = self.check_max_width.get_active()
        min_height_status = self.check_min_height.get_active()
        max_height_status = self.check_max_height.get_active()
        min_words_status = self.check_min_words.get_active()
        max_words_status = self.check_max_words.get_active()
        
        current_filter["min_width"] = \
            {"status": min_width_status, "value": min_width_value}
        current_filter["max_width"] = \
            {"status": max_width_status, "value": max_width_value}
        current_filter["min_height"] = \
            {"status": min_height_status, "value": min_height_value}
        current_filter["max_height"] = \
            {"status": max_height_status, "value": max_height_value}
        current_filter["min_words"] = \
            {"status": min_words_status, "value": min_words_value}
        current_filter["max_words"] = \
            {"status": max_words_status, "value": max_words_value}
        
        if min_width_status:
            predicates.append(lambda template: template["width"] >= min_width_value)
        if max_width_status:
            predicates.append(lambda template: template["width"] <= max_width_value)
        if min_height_status:
            predicates.append(lambda template: template["height"] >= min_height_value)
        if max_height_status:
            predicates.append(lambda template: template["height"] <= max_height_value)
        if min_words_status:
            predicates.append(lambda template: template["word_count"] >= min_words_value)
        if max_words_status:
            predicates.append(lambda template: template["word_count"] <= max_words_value)
            
        return current_filter, predicates

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
        
        label = gtk.Label()
        label.set_alignment(0, 0)
        label.set_markup("<b>New puzzle</b>")
        
        options_vbox = gtk.VBox(False, 0)
        
        creation_method_vbox = gtk.VBox(False, 0)
        
        button = gtk.RadioButton(None, "Use an empty grid")
        button.set_active(True)
        button.connect("toggled", self.on_select_option, 0)
        creation_method_vbox.pack_start(button, False, False, 0)
        
        button = gtk.RadioButton(button, "Load a template")
        button.set_active(False)
        button.connect("toggled", self.on_select_option, 1)
        creation_method_vbox.pack_start(button, False, False, 0)
        
        align = gtk.Alignment(0, 0)
        align.set_padding(0, 0, 12, 0)
        align.add(creation_method_vbox)
        
        #options_vbox.pack_start(label, False, False, 6)
        #options_vbox.pack_start(align, False, False, 0)
        
        self.context_vbox = gtk.VBox(False, 0)
        options_vbox.pack_start(self.context_vbox, True, True, 0)
        
        main.pack_start(options_vbox, False, False, 0)
        main.pack_start(self.preview, True, True, 0)
        
        self.vbox.pack_start(hbox, True, True, 0)
        
        self.size_component = SizeComponent(
            #title="<b>Empty grid</b>"
            title=u"<b>New puzzle</b>"
            , callback=self.size_callback)
        
        self.template_label = gtk.Label()
        self.template_label.set_alignment(0, 0)
        self.template_label.set_markup("<b>Template</b>")
        
        self.template_button = gtk.Button("Choose template")
        self.template_button.connect("clicked", self.on_template_button_clicked)
        
        align = gtk.Alignment(0, 0)
        align.set_padding(0, 0, 12, 0)
        align.add(self.template_button)
        
        self.context_vbox.pack_start(self.size_component, False, False, 0)
        #self.context_vbox.pack_start(self.template_label, False, False, 6)
        #self.context_vbox.pack_start(align, False, False, 0)
        
        self.template_label.set_sensitive(False)
        self.template_button.set_sensitive(False)
        
    def on_select_option(self, widget, data=None):
        if widget.get_active() == 1:
            if data == 0:
                self.template_label.set_sensitive(False)
                self.template_button.set_sensitive(False)
                self.size_component.set_sensitive(True)
                width, height = self.size_component.get_size()
                self.size_callback(width, height)
            elif data == 1:
                self.template_label.set_sensitive(True)
                self.template_button.set_sensitive(True)
                self.size_component.set_sensitive(False)
            
    def size_callback(self, width, height):
        self.grid = Grid(width, height)
        self.preview.display(self.grid)
        
    def on_template_button_clicked(self, button):
        dialog = gtk.FileChooserDialog("Load template file"
            , self
            , gtk.FILE_CHOOSER_ACTION_OPEN
            , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
            , gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        filter = gtk.FileFilter()
        filter.set_name("Palabra template files (*.xml)")
        filter.add_pattern("*.xml")
        dialog.add_filter(filter)
        
        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)
        
        dialog.show_all()
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            dialog.hide()
            
            templates = import_templates(dialog.get_filename())
            if len(templates) == 0:
                message = u"This file does not appear to be a valid Palabra template file."
                mdialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL
                    , gtk.MESSAGE_INFO, gtk.BUTTONS_NONE, message)
                mdialog.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
                mdialog.set_title(u"Invalid file")
                mdialog.run()
                mdialog.destroy()
            else:
                tdialog = TemplateWindow(self, templates)
                tdialog.show_all()
                response = tdialog.run()
                if response == gtk.RESPONSE_ACCEPT:
                    grid = tdialog.get_template_grid()
                    if grid is not None:
                        self.grid = grid
                        self.preview.display(self.grid)
                tdialog.destroy()
        dialog.destroy()
        
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
            self.view.update_visual_size(self.drawing_area)
            self.drawing_area.queue_draw()
        
    def clear(self):
        self.view = None
        self.drawing_area.queue_draw()
        
    def on_expose_event(self, drawing_area, event):
        if self.view is not None:
            context = drawing_area.window.cairo_create()
            self.view.select_mode(constants.VIEW_MODE_PREVIEW)
            self.view.render_background(context)
            self.view.render(context, mode=constants.VIEW_MODE_PREVIEW)
        
class TemplateWindow(gtk.Dialog):
    def __init__(self, palabra_window, templates):
        flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
        gtk.Dialog.__init__(self, "Template selection", palabra_window, flags, buttons)
        self.palabra_window = palabra_window
        
        self.template_index = None
        
        self.templates = templates
        
        self.current_filter = None
        self.predicates = []
        
        self.set_size_request(640, 480)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        
        main = gtk.HBox(False, 0)
        main.set_spacing(18)
        
        hbox.pack_start(main, True, True, 0)
        
        grid_vbox = gtk.VBox(False, 0)
        
        self.store = gtk.ListStore(str)
        
        tree = gtk.TreeView(self.store)
        tree.set_headers_visible(False)
        
        selection = tree.get_selection()
        selection.connect("changed", self.on_template_selection_change)
        
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("")
        column.pack_start(cell, True)
        column.set_attributes(cell, text=0)
        tree.append_column(column)
        
        label = gtk.Label()
        label.set_alignment(0, 0)
        label.set_markup("<b>Templates</b>")
        
        across_window = gtk.ScrolledWindow(None, None)
        across_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        across_window.add(tree)
        
        filter_button = gtk.Button("Filter...")
        filter_button.connect("clicked", self.on_filter_clicked)
        
        grid_vbox.pack_start(label, False, False, 6)
        grid_vbox.pack_start(across_window, True, True, 0)
        grid_vbox.pack_start(filter_button, False, False, 0)
        
        align = gtk.Alignment(0, 0, 1, 1)
        align.set_padding(0, 0, 12, 0)
        align.add(grid_vbox)
        
        settings_vbox = gtk.VBox(False, 0)
        settings_vbox.pack_start(align, True, True, 0)
        
        main.pack_start(settings_vbox, True, True, 0)
        
        template_info_vbox = gtk.VBox(False, 0)
        
        self.preview = GridPreview()
        
        self.template_file_entry = gtk.Entry(512)
        self.template_file_entry.set_editable(False)

        template_info_vbox.pack_start(self.preview, True, True, 0)
        template_info_vbox.pack_start(self.template_file_entry, False, False, 0)
        
        main.pack_start(template_info_vbox, True, True, 0)
        
        self.reset()
        
        self.refresh_template_list()
        
        self.vbox.pack_start(hbox, True, True, 0)
        
    def display_template(self, grid, location):
        self.preview.display(grid)
        
        self.template_file_entry.set_text(location)
        
    def reset(self):
        self.template_index = None
        self.preview.clear()
        
        self.template_file_entry.set_text("")
        
    def refresh_template_list(self):
        self.store.clear()
        for template, location in self.templates:
            include_template = True
            for predicate in self.predicates:
                if not predicate(template):
                    include_template = False
                    break
            if not include_template:
                continue
            self.store.append([''.join(
                [str(template["word_count"])
                ," words, "
                ,str(template["letter_count"])
                , " letters ("
                ,str(template["width"])
                ," x "
                ,str(template["height"])
                ,")"
                ])])
        self.reset()
        
    def on_filter_clicked(self, button):
        dialog = FilterTemplateDialog(self, self.current_filter)
        dialog.show_all()
        
        response = dialog.run()
        if response == gtk.RESPONSE_ACCEPT:
            self.current_filter, self.predicates = dialog.get_filter()
            self.refresh_template_list()
        dialog.destroy()

    def on_template_selection_change(self, selection):
        model, model_iter = selection.get_selected()
        if model_iter is None:
            self.reset()
            return
        self.template_index = model.get_path(model_iter)[0]
        
        grid = self.get_template_grid()
        if grid is not None:
            template_stats, location = self.templates[self.template_index]
            self.display_template(grid, location)
        else:
            self.reset()
        
    def get_template_grid(self):
        if self.template_index is None:
            return None
        template_stats, location = self.templates[self.template_index]
        return import_template(location, self.template_index)
