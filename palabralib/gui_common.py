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
        hbox.pack_start(self.main)
        self.vbox.pack_start(hbox)
        
    def pack(self, widget, expand=True):
        args = (True, True) if expand else (False, False)
        self.main.pack_start(widget, *args)

class PalabraMessageDialog(gtk.MessageDialog):
    def __init__(self, parent, title, message):
        gtk.MessageDialog.__init__(self, parent, gtk.DIALOG_MODAL
            , gtk.MESSAGE_INFO, gtk.BUTTONS_NONE, message)
        self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        self.set_title(title)

class NameFileDialog(PalabraDialog):
    def __init__(self, parent, path, name=None):
        PalabraDialog.__init__(self, parent, self.p_title)
        self.main.pack_start(create_label(self.p_message), False, False, 0)
        self.main.pack_start(create_label(self.p_message2), False, False, 0)
        self.entry = gtk.Entry()
        def on_entry_changed(widget):
            self.store_name(widget.get_text().strip())
        self.entry.connect("changed", on_entry_changed)
        self.main.pack_start(self.entry, True, True, 0)
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.ok_button = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        if name is not None:
            self.entry.set_text(name)
        self.store_name(name)
    
    def store_name(self, name=None):
        self.given_name = name
        self.ok_button.set_sensitive(False if name is None else len(name) > 0)

def obtain_file(parent, file_dialog_title, paths, msg_duplicate, dialog_name):
    d = gtk.FileChooserDialog(file_dialog_title
        , parent
        , gtk.FILE_CHOOSER_ACTION_OPEN
        , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
        , gtk.STOCK_OPEN, gtk.RESPONSE_OK))
    d.show_all() 
    if d.run() != gtk.RESPONSE_OK:
        d.destroy()
        return
    path = d.get_filename()
    d.destroy()
    if path in paths:
        m = PalabraMessageDialog(parent, u"Duplicate found", msg_duplicate)
        m.show_all()
        m.run()
        m.destroy()
        return
    value = None
    d = dialog_name(parent, path)
    d.show_all()
    if d.run() == gtk.RESPONSE_OK:
        value = {"name": {"type": "str", "value": d.given_name}
            , "path": {"type": "str", "value": path}
        }
    d.destroy()
    return value

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
    
def create_button(text, align=None, f_click=None):
    button = gtk.Button(text)
    if f_click is not None:
        button.connect("clicked", f_click)
    if align is not None:
        a = gtk.Alignment(*align)
        a.add(button)
        return a
    return button

def create_stock_button(stock, f_click=None):
    button = gtk.Button(stock=stock)
    if f_click is not None:
        button.connect("clicked", f_click)
    return button

def create_check_button(label, active=None, f_toggle=None):
    button = gtk.CheckButton(label)
    if active is not None:
        button.set_active(active)
    if f_toggle is not None:
        button.connect("toggled", f_toggle)
    return button

def create_notebook(pages, border=None, f_switch=None):
    tabs = gtk.Notebook()
    for widget, title in pages:
        tabs.append_page(widget, gtk.Label(title))
    if border is not None:
        tabs.set_property("tab-hborder", border[0])
        tabs.set_property("tab-vborder", border[1])
    if f_switch is not None:
        tabs.connect("switch-page", f_switch)
    return tabs
    
def create_color_button(color, f=None):
    color = gtk.gdk.Color(*color)
    button = gtk.ColorButton()
    button.set_color(color)
    if f is not None:
        button.connect("color-set", f)
    return button
    
def create_combo(options, active=None, f_change=None):
    combo = gtk.combo_box_new_text()
    for o in options:
        combo.append_text(o)
    if active is not None:
        combo.set_active(active)
    if f_change is not None:
        combo.connect("changed", f_change)
    return combo

def create_entry(f_change=None):
    entry = gtk.Entry()
    if f_change is not None:
        entry.connect("changed", f_change)
    return entry

def create_menubar(funcs):
    m = gtk.MenuBar()
    for f in funcs:
        m.append(f())
    return m

def create_drawing_area(f_expose):
    drawing_area = gtk.DrawingArea()
    drawing_area.connect("expose_event", f_expose)
    return drawing_area
    
def launch_dialog(dialog, arg0, arg1=None, arg2=None, f_done=None):
    if arg1 is None:
        w = dialog(arg0)
    elif arg2 is None:
        w = dialog(arg0, arg1)
    else:
        w = dialog(arg0, arg1, arg2)
    w.show_all()
    response = w.run()
    if f_done is not None:
        result = f_done(w)
    w.destroy()
    if f_done is not None:
        return response, result
    return response
    
def launch_file_dialog(dialog, parent):
    w = dialog(parent)
    w.show_all()
    w.run()
    filename = w.get_filename()
    w.destroy()
    return filename
