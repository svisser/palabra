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

import cairo
import copy
import gtk

import grid
import view

class FillDebugDialog(gtk.Dialog):
    def __init__(self, parent, content):
        gtk.Dialog.__init__(self, "Fill debugger", parent, gtk.DIALOG_MODAL)
        self.content = content
        self.initial = content[0]
        main = gtk.HBox()
        main.set_spacing(5)
        
        self.drawing_area = gtk.DrawingArea()
        self.drawing_area.set_size_request(600, 500)
        main.pack_start(self.drawing_area, True, True, 0)
        
        self.store = gtk.ListStore(str, int)
        self.tree = gtk.TreeView(self.store)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Debug entries", cell, markup=0)
        self.tree.append_column(column)
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add(self.tree)
        scrolled_window.set_size_request(300, -1)
        self.tree.get_selection().connect("changed", self.on_tree_selection_changed)
        main.pack_start(scrolled_window, True, True, 0)
        self.a_label = gtk.Label()
        main.pack_start(self.a_label)
        self.a_label2 = gtk.Label()
        main.pack_start(self.a_label2)
        self.d_label = gtk.Label()
        main.pack_start(self.d_label)
        self.d_label2 = gtk.Label()
        main.pack_start(self.d_label2)
        
        self.offsets = {}
        prev = {}
        g = copy.deepcopy(self.initial)
        for x, y, c in content[-1]:
            g.data[y][x]["char"] = c
        for n, x, y, d in g.words(allow_duplicates=True, include_dir=True):
            prev[x, y, 0 if d == "across" else 1] = 0
        for i in xrange(len(content)):
            if i == 0:
                continue
            c = content[i]
            if isinstance(c, tuple):
                key, word, x, y, d, offset = c
                if key == "before":
                    self.store.append(["Before: ("
                        + str(x) + ", "
                        + str(y) + ", "
                        + str(d) + " at "
                        + str(offset) + "): "
                        + str(word), i])
                elif key == "after":
                    self.store.append(["After: ("
                        + str(x) + ", "
                        + str(y) + ", "
                        + str(d) + " at "
                        + str(offset) + "): "
                        + str(word), i])
                next = copy.deepcopy(prev)
                next[x, y, d] = offset
                prev = next
                self.offsets[i] = next
            elif isinstance(c, list):
                self.store.append(["Grid", i])
        
        self.vbox.pack_start(main)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        
    def on_tree_selection_changed(self, selection):
        store, it = selection.get_selected()
        if it is not None:
            index = store[it][1]
            data = self.content[index]
            if isinstance(data, list):
                g = copy.deepcopy(self.initial)
                for x, y, c in data:
                    g.data[y][x]["char"] = c
                g_view = view.GridView(g)
                width, height = g_view.properties.visual_size(True)
                surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
                pattern = cairo.SurfacePattern(surface)
                context = cairo.Context(surface)
                cs = list(g.cells())
                g_view.render_bottom(context, cs)
                g_view.render_top(context, cs)
                context = self.drawing_area.window.cairo_create()
                context.set_source(pattern)
                context.paint()
            elif isinstance(data, tuple):
                txt = []
                slots = list(self.initial.words(allow_duplicates=True, include_dir=True))
                for n, x, y, d in [item for item in slots if item[3] == "across"][0:20]:
                    if d == "across":
                        key = (x, y, 0)
                        value = self.offsets[index][key]
                        txt.append(str(key) + ": " + str(value) + "\n")
                self.a_label.set_text(''.join(txt))
                txt = []                
                for n, x, y, d in [item for item in slots if item[3] == "across"][20:]:
                    if d == "across":
                        key = (x, y, 0)
                        value = self.offsets[index][key]
                        txt.append(str(key) + ": " + str(value) + "\n")
                self.a_label2.set_text(''.join(txt))
                txt = []
                for n, x, y, d in [item for item in slots if item[3] == "down"][0:20]:
                    if d == "down":
                        key = (x, y, 1)
                        value = self.offsets[index][key]
                        txt.append(str(key) + ": " + str(value) + "\n")
                self.d_label.set_text(''.join(txt))
                txt = []
                for n, x, y, d in [item for item in slots if item[3] == "down"][20:]:
                    if d == "down":
                        key = (x, y, 1)
                        value = self.offsets[index][key]
                        txt.append(str(key) + ": " + str(value) + "\n")
                self.d_label2.set_text(''.join(txt))
