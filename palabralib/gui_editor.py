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
import operator

import constants
from editor import DEFAULT_FILL_OPTIONS
from files import get_real_filename
from gui_common import (
    create_label,
    create_button,
    create_combo,
)
from gui_word import EditorWordWidget
from word import visible_entries

WORD_DISPLAY_OPTIONS = [u"Alphabet", u"Score"]

class WordTool:
    def __init__(self, parent):
        self.parent = parent
        self.show_intersect = False
        self.show_used = True
        self.show_order = 0
    
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
        
        self.view = EditorWordWidget(self.parent)
        sw = gtk.ScrolledWindow(None, None)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add_with_viewport(self.view)
        self.main.pack_start(sw, True, True, 0)
        
        show_hbox = gtk.HBox()
        show_hbox.pack_start(create_label(u"Sort words by:"))
        def on_show_changed(widget):
            self.show_order = widget.get_active()
            self.display_words()
        show_combo = create_combo(WORD_DISPLAY_OPTIONS
            , active=self.show_order
            , f_change=on_show_changed)
        show_hbox.pack_start(show_combo)
        self.main.pack_start(show_hbox, False, False, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(6)
        hbox.set_spacing(6)
        hbox.pack_start(self.main, True, True, 0)
        return hbox
        
    def display_words(self, words=None):
        if words is not None:
            self.words = words
        shown = visible_entries(self.words, self.parent.puzzle.grid
            , show_used=self.show_used
            , show_intersect=self.show_intersect
            , show_order=self.show_order)
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
        
        def on_fill_button_clicked(button):
            self.editor.fill()
        button = create_button(u"Fill", f_click=on_fill_button_clicked)
        main.pack_start(button, False, False, 0)
        
        start_combo = gtk.combo_box_new_text()
        for i, (c, txt) in enumerate(self.starts):
            start_combo.append_text(txt)
            if c == self.editor.fill_options[constants.FILL_OPTION_START]:
                start_combo.set_active(i)
        def on_start_changed(combo):
            self.editor.fill_options[constants.FILL_OPTION_START] = self.starts[combo.get_active()][0]
        start_combo.connect("changed", on_start_changed)
        
        main.pack_start(create_label(u"Start filling from:"), False, False, 0)
        main.pack_start(start_combo, False, False, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(6)
        hbox.set_spacing(6)
        hbox.pack_start(main, True, True, 0)
        return hbox
