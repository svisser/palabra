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

class PalabraDialog(gtk.Dialog):
    def __init__(self, pwindow, title, horizontal=False):
        gtk.Dialog.__init__(self, title, pwindow, gtk.DIALOG_MODAL)
        self.pwindow = pwindow
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        if horizontal:
            self.main = gtk.HBox()
        else:
            self.main = gtk.VBox()
        self.main.set_spacing(9)
        hbox.pack_start(self.main, True, True, 0)
        self.vbox.pack_start(hbox, True, True, 0)

def create_tree(types, columns, f_sel=None, window_size=None, return_id=False):
    store = gtk.ListStore(*types if isinstance(types, tuple) else [types])
    tree = gtk.TreeView(store)
    for item in columns:
        title = item[0]
        i = item[1]
        if len(item) > 2:
            f_edit = item[2]
        else:
            f_edit = None
        cell = gtk.CellRendererText()
        if f_edit is not None:
            cell.set_property('editable', True)
            cell.connect("edited", f_edit)
        column = gtk.TreeViewColumn(title, cell, markup=i)
        tree.append_column(column)
    scroll = create_scroll(tree, size=window_size)
    if f_sel is not None:
        selection_id = tree.get_selection().connect("changed", f_sel)
    if return_id:
        return store, tree, scroll, selection_id
    return store, tree, scroll

def create_scroll(widget, viewport=False, size=None):
    w = gtk.ScrolledWindow()
    w.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    if viewport:
        w.add_with_viewport(widget)
    else:
        w.add(widget)
    if size is not None:
        w.set_size_request(*size)
    return w
    
def create_label(text, align=None, padding=None):
    label = gtk.Label()
    label.set_markup(text)
    if align is None:
        label.set_alignment(0, 0.5)
    else:
        label.set_alignment(*align)
    if padding is not None:
        label.set_padding(*padding)
    return label
    
def create_notebook(pages):
    tabs = gtk.Notebook()
    for widget, title in pages:
        tabs.append_page(widget, gtk.Label(title))
    return tabs
