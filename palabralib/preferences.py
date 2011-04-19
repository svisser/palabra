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

from lxml import etree

import action
import constants
import grid

import ConfigParser

color_schemes_order = ["yellow", "red", "green", "blue", "purple", "cyan"]
color_schemes = {}
color_schemes["yellow"] = {"title": "Yellow"
    ,"primary_selection": (65535, 65535, 16383)
    ,"primary_active":    (65535, 65535, 16383)
    ,"secondary_active":  (65535, 65535, 49152)
    ,"current_word":      (65535, 65535, 49152)
    }
color_schemes["red"] = {"title": "Red"
    ,"primary_selection": (65535, 16383, 16383)
    ,"primary_active":    (65535, 16383, 16383)
    ,"secondary_active":  (65535, 49152, 49152)
    ,"current_word":      (65535, 49152, 49152)
    }
color_schemes["green"] = {"title": "Green"
    ,"primary_selection": (16383, 65535, 16383)
    ,"primary_active":    (16383, 65535, 16383)
    ,"secondary_active":  (49152, 65535, 49152)
    ,"current_word":      (49152, 65535, 49152)
    }
color_schemes["blue"] = {"title": "Blue"
    ,"primary_selection": (16383, 16383, 65535)
    ,"primary_active":    (16383, 16383, 65535)
    ,"secondary_active":  (49152, 49152, 65535)
    ,"current_word":      (49152, 49152, 65535)
    }
color_schemes["purple"] = {"title": "Purple"
    ,"primary_selection": (65535, 16383, 65535)
    ,"primary_active":    (65535, 16383, 65535)
    ,"secondary_active":  (65535, 49152, 65535)
    ,"current_word":      (65535, 49152, 65535)
    }
color_schemes["cyan"] = {"title": "Cyan"
    ,"primary_selection": (16383, 65535, 65535)
    ,"primary_active":    (16383, 65535, 65535)
    ,"secondary_active":  (49152, 65535, 65535)
    ,"current_word":      (49152, 65535, 65535)
    }   

prefs = {}

defaults = {}
defaults["backup_copy_before_save"] = (False, lambda s: "True" in s, "bool")
defaults["new_initial_height"] = (15, int, "int")
defaults["new_initial_width"] = (15, int, "int")
defaults["undo_stack_size"] = (50, int, "int")
defaults["undo_use_finite_stack"] = (True, lambda s: "True" in s, "bool")
defaults["color_primary_selection_red"] = (color_schemes["yellow"]["primary_selection"][0], int, "int")
defaults["color_primary_selection_green"] = (color_schemes["yellow"]["primary_selection"][1], int, "int")
defaults["color_primary_selection_blue"] = (color_schemes["yellow"]["primary_selection"][2], int, "int")
#defaults["color_secondary_selection_red"] = (65535, int)
#defaults["color_secondary_selection_green"] = (65535, int)
#defaults["color_secondary_selection_blue"] = (49152, int)
defaults["color_primary_active_red"] = (color_schemes["yellow"]["primary_active"][0], int, "int")
defaults["color_primary_active_green"] = (color_schemes["yellow"]["primary_active"][1], int, "int")
defaults["color_primary_active_blue"] = (color_schemes["yellow"]["primary_active"][2], int, "int")
defaults["color_secondary_active_red"] = (color_schemes["yellow"]["secondary_active"][0], int, "int")
defaults["color_secondary_active_green"] = (color_schemes["yellow"]["secondary_active"][1], int, "int")
defaults["color_secondary_active_blue"] = (color_schemes["yellow"]["secondary_active"][2], int, "int")
defaults["color_current_word_red"] = (color_schemes["yellow"]["current_word"][0], int, "int")
defaults["color_current_word_green"] = (color_schemes["yellow"]["current_word"][1], int, "int")
defaults["color_current_word_blue"] = (color_schemes["yellow"]["current_word"][2], int, "int")
defaults["color_warning_red"] = (65535, int, "int")
defaults["color_warning_green"] = (49152, int, "int")
defaults["color_warning_blue"] = (49152, int, "int")
defaults["pattern_files"] = ([], list, "list", "str")
defaults["word_files"] = ([{"name": {"type": "str", "value": "default"}
    , "path": {"type": "str", "value": "/usr/share/dict/words"}}], list, "list", "file")

def read_config_file():
    props = {}
    try:
        doc = etree.parse(constants.CONFIG_FILE_LOCATION)
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
    for key, value in defaults.items():
        prefs[key] = value[1](props[key]) if key in props else value[0]

def write_config_file():
    root = etree.Element("palabra-preferences")
    root.set("version", constants.VERSION)
    
    keys = defaults.keys()
    keys.sort()
    for key in keys:
        e = etree.SubElement(root, "preference")
        
        t = defaults[key][2]
        e.set("type", t)
        e.set("name", key)
        
        data = prefs[key] if key in prefs else defaults[key][0]
        if t in ["int", "bool"]:
            e.text = str(data)
        elif t == "list":
            for v in data:
                f = etree.SubElement(e, "preference-item")
                f.set("type", defaults[key][3])
                if defaults[key][3] == "str":
                    f.text = str(v)
                elif defaults[key][3] == "file":
                    for k0, v0 in v.items():
                        g = etree.SubElement(f, "preference-item")
                        g.set("name", k0)
                        g.set("type", v0["type"])
                        g.text = v0["value"]
    
    if not os.path.isdir(constants.APPLICATION_DIRECTORY):
        os.mkdir(constants.APPLICATION_DIRECTORY)
    
    contents = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
    f = open(constants.CONFIG_FILE_LOCATION, "w")
    f.write(contents)
    f.close()

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
            prefs["new_initial_width"] = spinner.get_value_as_int()
        adj = gtk.Adjustment(prefs["new_initial_width"]
            , constants.MINIMUM_WIDTH, constants.MAXIMUM_WIDTH, 1, 0, 0)
        new_width_spinner = gtk.SpinButton(adj, 0.0, 0)
        new_width_spinner.connect("value-changed", on_new_width_changed)
        
        def on_new_height_changed(spinner):
            prefs["new_initial_height"] = spinner.get_value_as_int()
        adj = gtk.Adjustment(prefs["new_initial_height"]
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
            prefs["backup_copy_before_save"] = widget.get_active()
        backup_button = gtk.CheckButton(u"Create a backup copy of files before saving")
        backup_button.set_active(prefs["backup_copy_before_save"])
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
        for key in color_schemes_order:
            colors_combo.append_text(color_schemes[key]["title"])
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
            scheme = color_schemes[color_schemes_order[index - 1]]
            for key, value in scheme.items():
                if key == "primary_selection":
                    self.color1_button.set_color(gtk.gdk.Color(*value))
                elif key == "primary_active":
                    self.color2_button.set_color(gtk.gdk.Color(*value))
                elif key == "secondary_active":
                    self.color4_button.set_color(gtk.gdk.Color(*value))
                elif key == "current_word":
                    self.color3_button.set_color(gtk.gdk.Color(*value))
            self.refresh_color_preferences()

    def refresh_color_preferences(self):
        color = self.color1_button.get_color()
        prefs["color_primary_selection_red"] = color.red
        prefs["color_primary_selection_green"] = color.green
        prefs["color_primary_selection_blue"] = color.blue
        
        color = self.color2_button.get_color()
        prefs["color_primary_active_red"] = color.red
        prefs["color_primary_active_green"] = color.green
        prefs["color_primary_active_blue"] = color.blue
        
        color = self.color4_button.get_color()
        prefs["color_secondary_active_red"] = color.red
        prefs["color_secondary_active_green"] = color.green
        prefs["color_secondary_active_blue"] = color.blue
        
        color = self.color3_button.get_color()
        prefs["color_current_word_red"] = color.red
        prefs["color_current_word_green"] = color.green
        prefs["color_current_word_blue"] = color.blue
