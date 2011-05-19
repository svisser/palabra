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
from preferences import COLORS, prefs, read_pref_color

_COLOR_BUTTONS = [(constants.COLOR_PRIMARY_SELECTION, u"Selected cell:", 'color1_button')
    , (constants.COLOR_CURRENT_WORD, u"Selected word:", 'color3_button')
    , (constants.COLOR_PRIMARY_ACTIVE, u"Cell under mouse pointer:", 'color2_button')
    , (constants.COLOR_SECONDARY_ACTIVE, u"Symmetrical cells:", 'color4_button')
    , (constants.COLOR_HIGHLIGHT, u"Highlighted cells:", 'color5_button')
]

class PreferencesWindow(gtk.Dialog):
    def __init__(self, palabra_window):
        flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
        buttons = (gtk.STOCK_CLOSE, gtk.RESPONSE_ACCEPT)
        gtk.Dialog.__init__(self, u"Palabra preferences"
            , palabra_window, flags, buttons)
        self.set_size_request(640, 420)
        self.current_item = None
        
        vbox = gtk.VBox(False, 0)
        vbox.set_spacing(15)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        hbox.pack_start(vbox, True, True, 0)
        
        main = gtk.HBox(False, 0)

        vbox.pack_start(main, True, True, 0)
        
        self.components = []
        self.components.append((u"General", self.create_general_item()))
        self.components.append((u"Editor", self.create_editor_item()))
        
        items = gtk.ListStore(str)
        for title, component in self.components:
            items.append([title])
        
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
        
        self.preference_window = gtk.VBox(False, 0)
        
        main.pack_start(tree_window, False, False, 9)
        main.pack_start(self.preference_window, True, True, 0)
        self.vbox.add(hbox)
        
        starting_index = 0
        tree.get_selection().select_path(starting_index)
        self._selection_component(starting_index)

    def on_tree_clicked(self, treeview, event):
        if event.button == 1:
            x, y = int(event.x), int(event.y)
            item = treeview.get_path_at_pos(x, y)
            if item is not None:
                path, col, cellx, celly = item
                if self.current_item is not None:
                    self.preference_window.remove(self.current_item)
                self._selection_component(path[0])
                
    def _selection_component(self, index):
        self.current_item = self.components[index][1]
        self.preference_window.pack_start(self.current_item, False, False, 0)
        self.preference_window.show_all()
    
    def create_general_item(self):
        main = gtk.VBox(False, 0)
        main.set_spacing(6)
        
        # new
        label = gtk.Label()
        label.set_alignment(0, 0)
        label.set_markup(u"<b>New puzzle</b>")
        main.pack_start(label, False, False, 6)
        
        size_table = gtk.Table(2, 2)
        size_table.set_col_spacings(6)
        main.pack_start(size_table, False, False, 0)
        
        def on_new_width_changed(spinner):
            prefs[constants.PREF_INITIAL_WIDTH] = spinner.get_value_as_int()
        adj = gtk.Adjustment(prefs[constants.PREF_INITIAL_WIDTH]
            , constants.MINIMUM_WIDTH, constants.MAXIMUM_WIDTH, 1, 0, 0)
        new_width_spinner = gtk.SpinButton(adj, 0.0, 0)
        new_width_spinner.connect("value-changed", on_new_width_changed)
        
        def on_new_height_changed(spinner):
            prefs[constants.PREF_INITIAL_HEIGHT] = spinner.get_value_as_int()
        adj = gtk.Adjustment(prefs[constants.PREF_INITIAL_HEIGHT]
            , constants.MINIMUM_WIDTH, constants.MAXIMUM_WIDTH, 1, 0, 0)
        new_height_spinner = gtk.SpinButton(adj, 0.0, 0)
        new_height_spinner.connect("value-changed", on_new_height_changed)
        
        align = gtk.Alignment(0, 0.5)
        align.set_padding(0, 0, 12, 0)
        align.add(gtk.Label(u"Default width:"))
        size_table.attach(align, 0, 1, 0, 1, gtk.FILL, gtk.FILL)
        size_table.attach(new_width_spinner, 1, 2, 0, 1, 0, 0)
        
        align = gtk.Alignment(0, 0.5)
        align.set_padding(0, 0, 12, 0)
        align.add(gtk.Label(u"Default height:"))
        size_table.attach(align, 0, 1, 1, 2, gtk.FILL, gtk.FILL)
        size_table.attach(new_height_spinner, 1, 2, 1, 2, 0, 0)
        
        label = gtk.Label()
        label.set_alignment(0, 0)
        label.set_markup(u"<b>Files</b>")
        main.pack_start(label, False, False, 6)
        
        def callback(widget, data=None):
            prefs[constants.PREF_COPY_BEFORE_SAVE] = widget.get_active()
        backup_button = gtk.CheckButton(u"Create a backup copy of files before saving")
        backup_button.set_active(prefs[constants.PREF_COPY_BEFORE_SAVE])
        backup_button.connect("toggled", callback)
        
        align = gtk.Alignment(0, 0.5)
        align.set_padding(0, 0, 12, 0)
        align.add(backup_button)
        main.pack_start(align, False, False, 0)
        
        return main
    
    def create_editor_item(self):
        main = gtk.VBox(False, 0)
        main.set_spacing(6)
        
        label = gtk.Label()
        label.set_alignment(0, 0)
        label.set_markup(u"<b>Colors</b>")
        main.pack_start(label, False, False, 6)
        
        colors_combo = gtk.combo_box_new_text()
        colors_combo.connect("changed", self.on_colors_combo_changed)
        colors_combo.append_text("")
        for key, value in COLORS:
            colors_combo.append_text(value.title)
        colors_combo.set_active(0)
        
        color_table = gtk.Table(5, 2)
        color_table.set_col_spacings(6)
        main.pack_start(color_table, False, False, 0)
        
        for i, (code, label, button) in enumerate(_COLOR_BUTTONS):
            color = gtk.gdk.Color(*read_pref_color(code, False))
            setattr(self, button, gtk.ColorButton())
            getattr(self, button).set_color(color)
            getattr(self, button).connect("color-set"
                , lambda button: self.refresh_color_preferences())
            align = gtk.Alignment(0, 0.5)
            align.set_padding(0, 0, 12, 0)
            align.add(gtk.Label(label))
            color_table.attach(align, 0, 1, i, i + 1, gtk.FILL, gtk.FILL)
            color_table.attach(getattr(self, button), 1, 2, i, i + 1, 0, 0)
        align = gtk.Alignment(0, 0.5)
        align.set_padding(0, 0, 12, 0)
        align.add(gtk.Label(u"Load color scheme:"))
        scheme_hbox = gtk.HBox(False, 0)
        scheme_hbox.pack_start(align, False, False, 0)
        align = gtk.Alignment(0, 0.5)
        align.set_padding(0, 0, 12, 0)
        align.add(colors_combo)
        scheme_hbox.pack_start(align, True, True, 0)
        main.pack_start(scheme_hbox, False, False, 0)
        
        label = gtk.Label()
        label.set_alignment(0, 0)
        label.set_markup(u"<b>Arrow keys</b>")
        main.pack_start(label, False, False, 6)
        
        def callback(widget):
            prefs[constants.PREF_ARROWS_CHANGE_DIR] = widget.get_active()
        arrows_button = gtk.CheckButton(u"Right / down arrow keys change typing direction")
        arrows_button.set_active(prefs[constants.PREF_ARROWS_CHANGE_DIR])
        arrows_button.connect("toggled", callback)
        align = gtk.Alignment(0, 0.5)
        align.set_padding(0, 0, 12, 0)
        align.add(arrows_button)
        main.pack_start(align, False, False, 0)
        
        return main
        
    def on_colors_combo_changed(self, combo, data=None):
        index = combo.get_active()
        if index > 0:
            key, scheme = COLORS[index - 1]
            self.color1_button.set_color(gtk.gdk.Color(*scheme.primary_selection))
            self.color2_button.set_color(gtk.gdk.Color(*scheme.primary_active))
            self.color4_button.set_color(gtk.gdk.Color(*scheme.secondary_active))
            self.color3_button.set_color(gtk.gdk.Color(*scheme.current_word))
            self.color5_button.set_color(gtk.gdk.Color(*scheme.highlight))
            self.refresh_color_preferences()

    def refresh_color_preferences(self):
        """Load colors of buttons into preferences."""
        for code, label, button in _COLOR_BUTTONS:
            color = getattr(self, button).get_color()
            prefs[code + "_red"] = color.red
            prefs[code + "_green"] = color.green
            prefs[code + "_blue"] = color.blue
