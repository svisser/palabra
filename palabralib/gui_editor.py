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
from editor import DEFAULT_FILL_OPTIONS
from files import get_real_filename
from gui_word import WordWidget

class WordTool:
    def __init__(self, editor):
        self.editor = editor
        self.show_intersect = False
        self.show_used = True
    
    def create(self):
        img = gtk.Image()
        img.set_from_file(get_real_filename("resources/icon1.png"))
        def on_button_toggled(self, button):
            self.show_intersect = button.get_active()
            self.display_words()
        toggle_button = gtk.ToggleButton()
        toggle_button.set_property("image", img)
        toggle_button.set_tooltip_text(u"Show only words with intersecting words")
        toggle_button.connect("toggled", lambda b: on_button_toggled(self, b))
        
        img = gtk.Image()
        img.set_from_file(get_real_filename("resources/icon2.png"))
        def on_button2_toggled(self, button):
            self.show_used = not button.get_active()
            self.display_words()
        toggle_button2 = gtk.ToggleButton()
        toggle_button2.set_property("image", img)
        toggle_button2.set_tooltip_text(u"Show only unused words")
        toggle_button2.connect("toggled", lambda b: on_button2_toggled(self, b))
        
        buttons = gtk.HButtonBox()
        buttons.set_layout(gtk.BUTTONBOX_START)
        buttons.add(toggle_button)
        buttons.add(toggle_button2)
        
        self.main = gtk.VBox(False, 0)
        self.main.set_spacing(9)
        self.main.pack_start(buttons, False, False, 0)
        
        self.view = WordWidget(self.editor)
        sw = gtk.ScrolledWindow(None, None)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add_with_viewport(self.view)
        self.main.pack_start(sw, True, True, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(6)
        hbox.set_spacing(6)
        hbox.pack_start(self.main, True, True, 0)
        return hbox
        
    def display_words(self, words=None):
        if words is not None:
            self.words = words
        entries = []
        if not self.show_used:
            entries = [e.lower() for e in self.editor.puzzle.grid.entries() if constants.MISSING_CHAR not in e]
        shown = [row for row in self.words if 
            not ( (self.show_intersect and not row[1]) or (not self.show_used and row[0] in entries) ) ]
        self.view.set_words(shown)
        
    def get_selected_word(self):
        return self.view.get_selected_word()
        
    def deselect(self):
        self.view.selection = None

class FillTool:
    def __init__(self, editor):
        self.editor = editor
        self.starts = [
            (constants.FILL_START_AT_ZERO, "First slot")
            , (constants.FILL_START_AT_AUTO, "Suitably chosen slot")
        ]
        self.editor.fill_options.update(DEFAULT_FILL_OPTIONS)
        
    def create(self):
        main = gtk.VBox(False, 0)
        main.set_spacing(9)
        
        button = gtk.Button("Fill")
        button.connect("pressed", self.on_button_pressed)
        main.pack_start(button, False, False, 0)
        
        start_combo = gtk.combo_box_new_text()
        for i, (c, txt) in enumerate(self.starts):
            start_combo.append_text(txt)
            if c == self.editor.fill_options[constants.FILL_OPTION_START]:
                start_combo.set_active(i)
        def on_start_changed(combo):
            self.editor.fill_options[constants.FILL_OPTION_START] = self.starts[combo.get_active()][0]
        start_combo.connect("changed", on_start_changed)
        
        label = gtk.Label(u"Start filling from:")
        label.set_alignment(0, 0.5)
        main.pack_start(label, False, False, 0)
        main.pack_start(start_combo, False, False, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(6)
        hbox.set_spacing(6)
        hbox.pack_start(main, True, True, 0)
        return hbox
        
    def on_button_pressed(self, button):
        self.editor.fill()
