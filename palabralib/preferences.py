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
import os
from collections import namedtuple

from lxml import etree

import action
import constants
import grid

import ConfigParser

ColorScheme = namedtuple('ColorScheme', ['title'
    , 'primary_selection'
    , 'primary_active'
    , 'secondary_active'
    , 'current_word'
])
_SCHEME_YELLOW = ColorScheme("Yellow"
    , (65535, 65535, 16383)
    , (65535, 65535, 16383)
    , (65535, 65535, 49152)
    , (65535, 65535, 49152)
)
_SCHEME_RED = ColorScheme("Red"
    , (65535, 16383, 16383)
    , (65535, 16383, 16383)
    , (65535, 49152, 49152)
    , (65535, 49152, 49152)
)
_SCHEME_GREEN = ColorScheme("Green"
    , (16383, 65535, 16383)
    , (16383, 65535, 16383)
    , (49152, 65535, 49152)
    , (49152, 65535, 49152)
)
_SCHEME_BLUE = ColorScheme("Blue"
    , (16383, 16383, 65535)
    , (16383, 16383, 65535)
    , (49152, 49152, 65535)
    , (49152, 49152, 65535)
)
_SCHEME_PURPLE = ColorScheme("Purple"
    , (65535, 16383, 65535)
    , (65535, 16383, 65535)
    , (65535, 49152, 65535)
    , (65535, 49152, 65535)
)
_SCHEME_CYAN = ColorScheme("Cyan"
    , (16383, 65535, 65535)
    , (16383, 65535, 65535)
    , (49152, 65535, 65535)
    , (49152, 65535, 65535)
)

COLORS = [('yellow', _SCHEME_YELLOW)
    , ('red', _SCHEME_RED)
    , ('green', _SCHEME_GREEN)
    , ('blue', _SCHEME_BLUE)
    , ('purple', _SCHEME_PURPLE)
    , ('cyan', _SCHEME_CYAN)
]
D_COLORS = dict(COLORS)

prefs = {}

Preference = namedtuple('Preference', ['value', 'eval', 'type', 'itemtype'])

_COLOR_ATTRS = [
    (constants.COLOR_PRIMARY_SELECTION, 'primary_selection')
    , (constants.COLOR_PRIMARY_ACTIVE, 'primary_active')
    , (constants.COLOR_SECONDARY_ACTIVE, 'secondary_active')
    , (constants.COLOR_CURRENT_WORD, 'current_word')
]
_INT_PREFS = [
    (constants.PREF_INITIAL_HEIGHT, 15)
    , (constants.PREF_INITIAL_WIDTH, 15)
#    , (constants.PREF_UNDO_STACK_SIZE, 50)    
]
_BOOL_PREFS = [
    (constants.PREF_COPY_BEFORE_SAVE, False)
#    , (constants.PREF_UNDO_FINITE_STACK, True)
]
_OTHER_COLOR_PREFS = [
    (constants.COLOR_WARNING, (65535, 49152, 49152))
]

DEFAULTS = {}
for code, b in _BOOL_PREFS:
    DEFAULTS[code] = Preference(b, lambda s: "True" in s, "bool", None)
for code, n in _INT_PREFS:
    DEFAULTS[code] = Preference(n, int, "int", None)
for code, attr in _COLOR_ATTRS:
    DEFAULTS[code + "_red"] = Preference(getattr(D_COLORS["yellow"], attr)[0], int, "int", None)
    DEFAULTS[code + "_green"] = Preference(getattr(D_COLORS["yellow"], attr)[1], int, "int", None)
    DEFAULTS[code + "_blue"] = Preference(getattr(D_COLORS["yellow"], attr)[2], int, "int", None)
#DEFAULTS["color_secondary_selection_red"] = (65535, int)
#DEFAULTS["color_secondary_selection_green"] = (65535, int)
#DEFAULTS["color_secondary_selection_blue"] = (49152, int)
for code, color in _OTHER_COLOR_PREFS:
    DEFAULTS[code + "_red"] = Preference(color[0], int, "int", None)
    DEFAULTS[code + "_green"] = Preference(color[1], int, "int", None)
    DEFAULTS[code + "_blue"] = Preference(color[2], int, "int", None)
DEFAULTS[constants.PREF_PATTERN_FILES] = Preference([], list, "list", "str")
DEFAULTS["word_files"] = Preference([{"name": {"type": "str", "value": "Default"}
    , "path": {"type": "str", "value": "/usr/share/dict/words"}}], list, "list", "file")

def read_config_file(filename=constants.CONFIG_FILE_LOCATION):
    props = {}
    try:
        doc = etree.parse(filename)
        root = doc.getroot()
        version = root.get("version")
        for p in root:
            t = p.get("type")
            name = p.get("name")
            if t in ["int", "bool"]:
                props[name] = p.text
            elif t == "list":
                values = []
                for child in p:
                    ts = child.get("type")
                    if ts == "file":
                        value = {}
                        for child2 in child:
                            value[child2.get("name")] = {"type": child2.get("type"), "value": child2.text}
                    else:
                        value = child.text
                    values.append(value)
                props[name] = values
    except (etree.XMLSyntaxError, IOError):
        print "Warning: No configuration file found, using defaults instead."
    for key, pref in DEFAULTS.items():
        prefs[key] = pref.eval(props[key]) if key in props else value[0]

def write_config_file(filename=constants.CONFIG_FILE_LOCATION):
    root = etree.Element("palabra-preferences")
    root.set("version", constants.VERSION)
    keys = DEFAULTS.keys()
    keys.sort()
    for key in keys:
        pref = DEFAULTS[key]
        e = etree.SubElement(root, "preference")
        e.set("type", pref.type)
        e.set("name", key)
        data = prefs[key] if key in prefs else pref.value
        if pref.type in ["int", "bool"]:
            e.text = str(data)
        elif pref.type == "list":
            for v in data:
                f = etree.SubElement(e, "preference-item")
                f.set("type", pref.itemtype)
                if pref.itemtype == "str":
                    f.text = str(v)
                elif pref.itemtype == "file":
                    for k0, v0 in v.items():
                        g = etree.SubElement(f, "preference-item")
                        g.set("name", k0)
                        g.set("type", v0["type"])
                        g.text = v0["value"]
    if not os.path.isdir(constants.APPLICATION_DIRECTORY):
        os.mkdir(constants.APPLICATION_DIRECTORY)
    contents = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
    with open(filename, "w") as f:
        f.write(contents)

def read_pref_color(key):
    r = prefs[key + "_red"] / 65535.0
    g = prefs[key + "_green"] / 65535.0
    b = prefs[key + "_blue"] / 65535.0
    return r, g, b

def prefs_to_word_files(prefs):
    files = []
    for i, data in enumerate(prefs):
        if i >= constants.MAX_WORD_LISTS:
            break
        name = data["name"]["value"]
        path = data["path"]["value"]
        files.append((i, path, name))
    return files

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
            x = int(event.x)
            y = int(event.y)
            
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
        
        color_table = gtk.Table(5, 2)
        color_table.set_col_spacings(6)
        main.pack_start(color_table, False, False, 0)
        
        color1 = gtk.gdk.Color(prefs["color_primary_selection_red"]
            , prefs["color_primary_selection_green"]
            , prefs["color_primary_selection_blue"])
        self.color1_button = gtk.ColorButton()
        self.color1_button.set_color(color1)
        self.color1_button.connect("color-set"
            , lambda button: self.refresh_color_preferences())
        align = gtk.Alignment(0, 0.5)
        align.set_padding(0, 0, 12, 0)
        align.add(gtk.Label(u"Selected cell:"))
        color_table.attach(align, 0, 1, 0, 1, gtk.FILL, gtk.FILL)
        color_table.attach(self.color1_button, 1, 2, 0, 1, 0, 0)
        
        color3 = gtk.gdk.Color(prefs["color_current_word_red"]
            , prefs["color_current_word_green"]
            , prefs["color_current_word_blue"])
        self.color3_button = gtk.ColorButton()
        self.color3_button.set_color(color3)
        self.color3_button.connect("color-set"
            , lambda button: self.refresh_color_preferences())
        align = gtk.Alignment(0, 0.5)
        align.set_padding(0, 0, 12, 0)
        align.add(gtk.Label(u"Selected word:"))
        color_table.attach(align, 0, 1, 1, 2, gtk.FILL, gtk.FILL)
        color_table.attach(self.color3_button, 1, 2, 1, 2, 0, 0)
        
        color2 = gtk.gdk.Color(prefs["color_primary_active_red"]
            , prefs["color_primary_active_green"]
            , prefs["color_primary_active_blue"])
        self.color2_button = gtk.ColorButton()
        self.color2_button.set_color(color2)
        self.color2_button.connect("color-set"
            , lambda button: self.refresh_color_preferences())
        align = gtk.Alignment(0, 0.5)
        align.set_padding(0, 0, 12, 0)
        align.add(gtk.Label(u"Cell under mouse pointer:"))
        color_table.attach(align, 0, 1, 2, 3, gtk.FILL, gtk.FILL)
        color_table.attach(self.color2_button, 1, 2, 2, 3, 0, 0)
        
        color4 = gtk.gdk.Color(prefs["color_secondary_active_red"]
            , prefs["color_secondary_active_green"]
            , prefs["color_secondary_active_blue"])
        self.color4_button = gtk.ColorButton()
        self.color4_button.set_color(color4)
        self.color4_button.connect("color-set"
            , lambda button: self.refresh_color_preferences())
        align = gtk.Alignment(0, 0.5)
        align.set_padding(0, 0, 12, 0)
        align.add(gtk.Label(u"Symmetrical cells:"))
        color_table.attach(align, 0, 1, 3, 4, gtk.FILL, gtk.FILL)
        color_table.attach(self.color4_button, 1, 2, 3, 4, 0, 0)
        
        label = gtk.Label()
        label.set_alignment(0, 0)
        label.set_markup(u"<b>Color schemes</b>")
        main.pack_start(label, False, False, 6)
        
        scheme_table = gtk.Table(1, 2)
        scheme_table.set_col_spacings(6)
        main.pack_start(scheme_table, False, False, 0)
        
        colors_combo = gtk.combo_box_new_text()
        colors_combo.connect("changed", self.on_colors_combo_changed)
        colors_combo.append_text("")
        for key, value in COLORS:
            colors_combo.append_text(value.title)
        colors_combo.set_active(0)
        
        align = gtk.Alignment(0, 0.5)
        align.set_padding(0, 0, 12, 0)
        align.add(gtk.Label(u"Load color scheme:"))
        scheme_table.attach(align, 0, 1, 0, 1, gtk.FILL, gtk.FILL)
        scheme_table.attach(colors_combo, 1, 2, 0, 1)
        return main
        
    def on_colors_combo_changed(self, combo, data=None):
        index = combo.get_active()
        if index > 0:
            key, scheme = COLORS[index - 1]
            self.color1_button.set_color(gtk.gdk.Color(*scheme.primary_selection))
            self.color2_button.set_color(gtk.gdk.Color(*scheme.primary_active))
            self.color4_button.set_color(gtk.gdk.Color(*scheme.secondary_active))
            self.color3_button.set_color(gtk.gdk.Color(*scheme.current_word))
            self.refresh_color_preferences()

    def refresh_color_preferences(self):
        """Load colors of buttons into preferences."""
        BUTTONS = [(constants.COLOR_PRIMARY_SELECTION, self.color1_button)
            , (constants.COLOR_PRIMARY_ACTIVE, self.color2_button)
            , (constants.COLOR_SECONDARY_ACTIVE, self.color4_button)
            , (constants.COLOR_CURRENT_WORD, self.color3_button)]
        for code, button in BUTTONS:
            color = button.get_color()
            prefs[code + "_red"] = color.red
            prefs[code + "_green"] = color.green
            prefs[code + "_blue"] = color.blue
