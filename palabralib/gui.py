# This file is part of Palabra
# coding: utf-8
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

#import pstats
#import cProfile
#cProfile.runctx('self.update_window(True)', globals(), locals(), filename='fooprof')
#p = pstats.Stats('fooprof')
#p.sort_stats('time').print_stats(20)

try:
    import pygtk
    pygtk.require("2.0")
    import gtk
    import gobject
except (ImportError, AssertionError):
    print "PyGTK 2.8 or higher is required for this application."
    raise SystemExit

import os
import webbrowser

import action
from action import State
from appearance import AppearanceDialog
import cPalabra
from clue import ClueTool
import constants
from export import ExportWindow
from editor import (
    e_settings,
    e_tools,
    Editor,
    EDITOR_EVENTS,
)
from files import (
    FILETYPES,
    ParserError,
    read_crossword,
    export_puzzle,
    read_containers,
)
from gui_editor import WordTool, FillTool
from gui_prefs import PreferencesWindow
from gui_word import (
    AccidentalWordsDialog,
    FindWordsDialog,
    WordListEditor,
    SimilarWordsDialog,
    WordUsageDialog,
)
import grid
from grid import Grid
from newpuzzle import NewWindow, SizeWindow
from pattern import PatternFileEditor
import preferences
from preferences import (
    write_config_file,
    read_config_file,
)
from properties import PropertiesWindow
from puzzle import Puzzle, PuzzleManager
import transform
import view
from word import create_wordlists

def create_splash():
    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_SPLASHSCREEN)
    window.set_decorated(False)
    window.set_position(gtk.WIN_POS_CENTER)
    hbox = gtk.HBox()
    window.add(hbox)
    image = gtk.Image()
    image.set_from_file(os.path.join('resources', 'splash.png'))
    hbox.pack_start(image)
    image.show()
    hbox.show()
    return window

class PalabraWindow(gtk.Window):
    def __init__(self):
        super(PalabraWindow, self).__init__()
        self.set_title(constants.TITLE)
        self.set_size_request(800, 600)
        self.puzzle_toggle_items = []
        self.selection_toggle_items = []
        self.puzzle_manager = PuzzleManager()
        self.menubar = gtk.MenuBar()
        self.menubar.append(self.create_file_menu())
        self.menubar.append(self.create_edit_menu())
        self.menubar.append(self.create_view_menu())
        self.menubar.append(self.create_grid_menu())
        #self.menubar.append(self.create_clue_menu())
        self.menubar.append(self.create_word_menu())
        self.menubar.append(self.create_help_menu())
        self.toolbar = self.create_toolbar()
        self.panel = gtk.VBox(False, 0)
        self.statusbar = gtk.Statusbar()
        self.main = gtk.VBox(False, 0)
        self.main.pack_start(self.menubar, False, False, 0)
        self.main.pack_start(self.toolbar, False, False, 0)
        self.main.pack_start(self.panel, True, True, 0)
        self.main.pack_start(self.statusbar, False, False, 0)
        self.add(self.main)
        self.connect("delete-event", self.on_delete)
        self.connect("destroy", lambda widget: quit())
        self.wordlists = []
        self.patterns = None
        self.blacklist = None
        
    def on_delete(self, window, event):
        self.close_puzzle()
        return self.puzzle_manager.has_puzzle()
        
    def on_quit(self):
        self.close_puzzle()
        if not self.puzzle_manager.has_puzzle():
            quit()
        
    def to_empty_panel(self):
        for widget in self.panel.get_children():
            self.panel.remove(widget)
        self.drawing_area.unset_flags(gtk.CAN_FOCUS)
        for i in self.ids:
            self.drawing_area.disconnect(i)
    
    def to_edit_panel(self):
        self.drawing_area = gtk.DrawingArea()
        self.drawing_area.set_flags(gtk.CAN_FOCUS)
        self.drawing_area.add_events(
            gtk.gdk.BUTTON_PRESS_MASK
            | gtk.gdk.BUTTON_RELEASE_MASK
            | gtk.gdk.POINTER_MOTION_MASK
            | gtk.gdk.KEY_PRESS_MASK
            | gtk.gdk.KEY_RELEASE_MASK
            | gtk.gdk.POINTER_MOTION_HINT_MASK
            )
        puzzle = self.puzzle_manager.current_puzzle
        puzzle.view.refresh_visual_size(self.drawing_area)
        self.drawing_area.queue_draw()
        self.editor = Editor(self)
        self.ids = []
        for k, e in EDITOR_EVENTS.items():
            self.ids.append(self.drawing_area.connect(k, e, self, puzzle, e_settings))
        e_tools["clue"] = ClueTool(self.editor)
        e_tools["fill"] = FillTool(self.editor)
        e_tools["word"] = WordTool(self.editor)
        
        options_hbox = gtk.HBox(False, 0)
        options_hbox.set_border_width(12)
        options_hbox.set_spacing(18)
        
        options_vbox = gtk.VBox(False, 0)
        options_vbox.set_spacing(15)
        options_hbox.pack_start(options_vbox, True, True, 0)
        
        options = gtk.VBox(False, 0)
        options_vbox.pack_start(options, True, True, 0)
        
        scrolled_window = gtk.ScrolledWindow(None, None)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add_with_viewport(self.drawing_area)
        main = gtk.VBox(False, 0)
        main.pack_start(scrolled_window, True, True, 0)
        
        tabs = gtk.Notebook()
        tabs.set_border_width(8)
        tabs.set_size_request(300, -1)
        tabs.set_show_border(False)
        tabs.set_property("tab-hborder", 16)
        tabs.set_property("tab-vborder", 8)
        tool = e_tools["word"].create()
        tabs.append_page(tool, gtk.Label(u"Word"))
        #tool = e_tools["fill"].create()
        #tabs.append_page(tool, gtk.Label(u"Fill"))
        tool = e_tools["clue"].create(puzzle)
        tabs.append_page(tool, gtk.Label(u"Clue"))
        def on_switch_page(tabs, do_not_use, num):
            if num == 0:
                word = e_tools["word"].get_selected_word()
                self.editor.set_overlay(word)
                self.update_window()
            else:
                self.editor.set_overlay(None)
                e_tools["word"].deselect()
        tabs.connect("switch-page", on_switch_page)
        
        paned = gtk.HPaned()
        paned.pack1(main, True, False)
        paned.pack2(tabs, True, False)
        w, h = self.get_size()
        paned.set_position(w - 300)
        self.panel.pack_start(paned, True, True, 0)
        self.panel.show_all()
        
    def get_selection(self, slot=False):
        x, y, d = e_settings.selection
        if slot:
            puzzle = self.puzzle_manager.current_puzzle
            sx, sy = puzzle.grid.get_start_word(x, y, d)
            return (x, y, d, puzzle.grid.word_length(sx, sy, d))
        return (x, y)
            
    def set_selection(self, x, y, direction=None, selection_changed=True):
        try:
            self.editor.set_selection(x=x
                , y=y
                , direction=direction
                , selection_changed=selection_changed)
        except AttributeError:
            pass
        
    def update_status(self, context_string, message):
        context_id = self.statusbar.get_context_id(context_string)
        self.statusbar.pop(context_id)
        self.statusbar.push(context_id, message)

    def pop_status(self, context_string):
        context_id = self.statusbar.get_context_id(context_string)
        self.statusbar.pop(context_id)
        return context_id
        
    def new_puzzle(self):
        self.close_puzzle()
        if not self.puzzle_manager.has_puzzle():
            window = NewWindow(self)
            window.show_all()
            
            response = window.run()
            if response == gtk.RESPONSE_ACCEPT:
                self.update_title(None)
                configuration = window.get_configuration()
                self.puzzle_manager.new_puzzle(configuration)
                e_settings.reset_controls()
                self.load_puzzle()
            window.destroy()
    
    def open_puzzle(self):
        self.close_puzzle()
        if not self.puzzle_manager.has_puzzle():
            if False: # TODO
                preview = gtk.DrawingArea()
                from view import GridView
                view = GridView(Grid(15, 15))
                def on_expose_event(preview, event):
                    context = preview.window.cairo_create()
                    view.render(context, constants.VIEW_MODE_PREVIEW)
                preview.connect("expose_event", on_expose_event)
                def on_selection_changed(filechooser):
                    path = filechooser.get_preview_filename() 
                    if path and os.path.isfile(path):
                        puzzle = read_crossword(path)
                        view.grid = puzzle.grid
                        view.properties.cell["size"] = 12
                        view.properties.default.char["font"] = "Sans 7"
                        view.refresh_visual_size(preview)
                        preview.queue_draw()

            dialog = gtk.FileChooserDialog(u"Open puzzle"
                , self
                , gtk.FILE_CHOOSER_ACTION_OPEN
                , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
                , gtk.STOCK_OPEN, gtk.RESPONSE_OK))
            #dialog.set_preview_widget(preview)
            #dialog.connect("selection-changed", on_selection_changed)
            for key in FILETYPES['keys']:
                description = FILETYPES[key]['description']
                pattern = FILETYPES[key]['pattern']
                f = gtk.FileFilter()
                f.set_name(description + ' (*' + pattern + ')')
                f.add_pattern('*' + pattern)
                dialog.add_filter(f)
            f = gtk.FileFilter()
            f.set_name(u"All files")
            f.add_pattern("*")
            dialog.add_filter(f)
            
            dialog.show_all()
            response = dialog.run()
            if response == gtk.RESPONSE_OK:
                dialog.hide()
                
                def show_error(title, message):
                    mdialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL
                        , gtk.MESSAGE_INFO, gtk.BUTTONS_NONE, message)
                    mdialog.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
                    mdialog.set_title(title)
                    mdialog.run()
                    mdialog.destroy()
                    
                filename = dialog.get_filename()
                try:
                    puzzle = read_crossword(filename)
                except ParserError, e:
                    title = u"Error when opening file"
                    show_error(title, e.message)
                else:
                    puzzle.filename = filename
                    self.update_title(filename)
                    
                    self.puzzle_manager.current_puzzle = puzzle
                    self.load_puzzle()
            dialog.destroy()
            
    def update_title(self, path=None):
        title = u"Unsaved puzzle - " + constants.TITLE
        if path is not None:
            filename_start = path.rfind(os.sep) + 1
            filename = path[filename_start:]
            title = ''.join([filename, u" - ", constants.TITLE])
        self.set_title(title)
    
    def save_puzzle(self, save_as=False):
        puzzle = self.puzzle_manager.current_puzzle
        backup = preferences.prefs[constants.PREF_COPY_BEFORE_SAVE]
        if save_as or self.puzzle_manager.current_puzzle.filename is None:
            title = u"Save puzzle"
            if save_as:
                title = u"Save puzzle as"
            dialog = gtk.FileChooserDialog(title
                , self
                , gtk.FILE_CHOOSER_ACTION_SAVE
                , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
                , gtk.STOCK_SAVE, gtk.RESPONSE_OK))
            dialog.set_do_overwrite_confirmation(True)
            
            filters = {}
            for key in FILETYPES['keys']:
                description = FILETYPES[key]['description']
                pattern = FILETYPES[key]['pattern']
                f = gtk.FileFilter()
                f.set_name(description + ' (*' + pattern + ')')
                f.add_pattern('*' + pattern)
                dialog.add_filter(f)
                filters[f] = key

            dialog.show_all()
            response = dialog.run()
            if response == gtk.RESPONSE_OK:
                filetype = filters[dialog.get_filter()]
                filename = dialog.get_filename()
                extension = FILETYPES[filetype]['pattern']
                if not filename.endswith(extension):
                    filename = filename + extension
                puzzle.filename = filename
                puzzle.type = filetype
                FILETYPES[filetype]['writer'](puzzle, backup)
                self.update_title(filename)
            dialog.destroy()
        else:
            FILETYPES[puzzle.type]['writer'](puzzle, backup)
        action.stack.distance_from_saved = 0
        
    def export_puzzle(self):
        w = ExportWindow(self)
        w.show_all() 
        if w.run() == gtk.RESPONSE_OK:
            w.hide()
            d = gtk.FileChooserDialog(u"Export location", self
                , gtk.FILE_CHOOSER_ACTION_SAVE
                , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
                , gtk.STOCK_SAVE, gtk.RESPONSE_OK))
            d.set_do_overwrite_confirmation(True)
            d.show_all() 
            if d.run() == gtk.RESPONSE_OK:
                export_puzzle(self.puzzle_manager.current_puzzle
                    , d.get_filename(), w.options)
            d.destroy()
        w.destroy()
    
    def load_puzzle(self):
        action.stack.push(State(self.puzzle_manager.current_puzzle.grid), initial=True)
        self.to_edit_panel()
        self.update_window(True)
        
    def close_puzzle(self):
        need_to_close, need_to_save = self.check_close_puzzle()
        if need_to_close:
            if need_to_save:
                self.save_puzzle(False)
            self.puzzle_manager.current_puzzle = None
            action.stack.clear()
            self.to_empty_panel()
            self.update_window(True)

    def check_close_puzzle(self):
        if not self.puzzle_manager.has_puzzle():
            return False, False

        need_to_close = True
        need_to_save = False
        if action.stack.distance_from_saved != 0:
            image = gtk.Image()
            image.set_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG)
            dialog = gtk.Dialog(u"Close puzzle"
                , self
                , gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_MODAL
                , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
                , gtk.STOCK_NO, gtk.RESPONSE_NO
                , gtk.STOCK_YES, gtk.RESPONSE_YES))
            dialog.set_default_response(gtk.RESPONSE_CLOSE)
            dialog.set_title(u"Close without saving")

            label = gtk.Label(u"Save the changes to the current puzzle before closing?")
            hbox = gtk.HBox(False, 0)
            hbox.pack_start(image, False, False, 0)
            hbox.pack_start(label, True, False, 10)
            dialog.vbox.pack_start(hbox, False, False, 10)
            dialog.set_resizable(False)
            dialog.set_modal(True)
            dialog.show_all()
            
            response = dialog.run()
            if response == gtk.RESPONSE_YES:
                need_to_close = True
                need_to_save = True
            elif response == gtk.RESPONSE_CANCEL:
                need_to_close = False
                need_to_save = False
            else:
                need_to_close = True
                need_to_save = False
            dialog.destroy()
        return need_to_close, need_to_save
    
    def export_clues(self, export_title, export_function, **args):
        dialog = gtk.FileChooserDialog(export_title
            , self
            , gtk.FILE_CHOOSER_ACTION_SAVE
            , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
            , gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        dialog.set_do_overwrite_confirmation(True)
        dialog.show_all()
        
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            filename = dialog.get_filename()
            export_function(self.puzzle_manager.current_puzzle, filename, **args)
        dialog.destroy()
        
    def view_puzzle_properties(self):
        dialog = PropertiesWindow(self, self.puzzle_manager.current_puzzle)
        dialog.show_all()
        dialog.run()
        dialog.destroy()
        
    def create_toolbar(self):
        toolbar = gtk.Toolbar()
        toolbar.set_orientation(gtk.ORIENTATION_HORIZONTAL)
        
        item = gtk.ToolButton()
        item.set_stock_id(gtk.STOCK_NEW)
        item.connect("clicked", lambda item: self.new_puzzle())
        item.show()
        toolbar.insert(item, -1)
        
        item = gtk.ToolButton()
        item.set_stock_id(gtk.STOCK_OPEN)
        item.connect("clicked", lambda item: self.open_puzzle())
        item.show()
        toolbar.insert(item, -1)
        
        item = gtk.ToolButton()
        item.set_stock_id(gtk.STOCK_SAVE)
        item.connect("clicked", lambda item: self.save_puzzle(False))
        item.show()
        item.set_sensitive(False)
        toolbar.insert(item, -1)
        self.puzzle_toggle_items += [item]
        
        toolbar.insert(gtk.SeparatorToolItem(), -1)
        
        self.undo_tool_item = gtk.ToolButton()
        self.undo_tool_item.set_stock_id(gtk.STOCK_UNDO)
        self.undo_tool_item.connect("clicked", lambda item: self.undo_action())
        self.undo_tool_item.show()
        toolbar.insert(self.undo_tool_item, -1)
        self.undo_tool_item.set_sensitive(False)
        
        self.redo_tool_item = gtk.ToolButton()
        self.redo_tool_item.set_stock_id(gtk.STOCK_REDO)
        self.redo_tool_item.connect("clicked", lambda item: self.redo_action())
        self.redo_tool_item.show()
        toolbar.insert(self.redo_tool_item, -1)
        self.redo_tool_item.set_sensitive(False)
        
        toolbar.insert(gtk.SeparatorToolItem(), -1)
        
        item = gtk.ToolButton()
        item.set_stock_id(gtk.STOCK_PROPERTIES)
        item.connect("clicked", lambda item: self.view_puzzle_properties())
        item.show()
        item.set_sensitive(False)
        toolbar.insert(item, -1)
        self.puzzle_toggle_items += [item]
        
        return toolbar
        
    def _create_menu_item(self, activate, tooltip
        , title=None
        , image=None
        , accelerator=None
        , accel_group=None
        , condition=None
        , is_puzzle_sensitive=False
        , is_selection_sensitive=False):
        select = lambda item: self.update_status(constants.STATUS_MENU, tooltip)
        deselect = lambda item: self.pop_status(constants.STATUS_MENU)
        if title is not None:
            item = gtk.MenuItem(title, True)
        elif image is not None:
            item = gtk.ImageMenuItem(image, None)
        if accelerator is not None and accel_group is not None:
            key, mod = gtk.accelerator_parse(accelerator)
            item.add_accelerator("activate", accel_group, key, mod, gtk.ACCEL_VISIBLE)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        
        if is_puzzle_sensitive:
            item.set_sensitive(False)
            self.puzzle_toggle_items += [item]
        if is_selection_sensitive:
            item.set_sensitive(False)
            if condition is None:
                condition = lambda puzzle: True
            self.selection_toggle_items.append((item, condition))
        return item
    
    def create_file_menu(self):
        menu = gtk.Menu()
        
        accel_group = gtk.AccelGroup()
        self.add_accel_group(accel_group)
        
        menu.append(self._create_menu_item(
            lambda item: self.new_puzzle()
            , u"Create a new puzzle"
            , image=gtk.STOCK_NEW
            , accelerator="<Ctrl>N"
            , accel_group=accel_group))
        menu.append(self._create_menu_item(
            lambda item: self.open_puzzle()
            , u"Open a puzzle"
            , image=gtk.STOCK_OPEN
            , accelerator="<Ctrl>O"
            , accel_group=accel_group))
        
        menu.append(gtk.SeparatorMenuItem())
        
        menu.append(self._create_menu_item(
            lambda item: self.save_puzzle(False)
            , u"Save the current puzzle"
            , image=gtk.STOCK_SAVE
            , accelerator="<Ctrl>S"
            , accel_group=accel_group
            , is_puzzle_sensitive=True))
        menu.append(self._create_menu_item(
            lambda item: self.save_puzzle(True)
            , u"Save the current puzzle with a different name"
            , image=gtk.STOCK_SAVE_AS
            , accelerator="<Shift><Ctrl>S"
            , accel_group=accel_group
            , is_puzzle_sensitive=True))
        
        menu.append(gtk.SeparatorMenuItem())
        
        menu.append(self._create_menu_item(
            lambda item: self.export_puzzle()
            , u"Export the puzzle to various file formats"
            , title=u"_Export..."
            , is_puzzle_sensitive=True))
        
        menu.append(gtk.SeparatorMenuItem())
        
        menu.append(self._create_menu_item(
            lambda item: self.view_puzzle_properties()
            , u"View the properties of the current puzzle"
            , image=gtk.STOCK_PROPERTIES
            , is_puzzle_sensitive=True))
        
        menu.append(gtk.SeparatorMenuItem())
        
        menu.append(self._create_menu_item(
            lambda item: self.close_puzzle()
            , u"Close the current puzzle"
            , image=gtk.STOCK_CLOSE
            , accelerator="<Ctrl>W"
            , accel_group=accel_group
            , is_puzzle_sensitive=True))
        menu.append(self._create_menu_item(
            lambda item: self.on_quit()
            , u"Quit the program"
            , image=gtk.STOCK_QUIT
            , accelerator="<Ctrl>Q"
            , accel_group=accel_group))
        
        file_menu = gtk.MenuItem(u"_File", True)
        file_menu.set_submenu(menu)
        return file_menu
        
    def resize_grid(self):
        window = SizeWindow(self, self.puzzle_manager.current_puzzle)
        window.show_all()
        response = window.run()
        if response == gtk.RESPONSE_ACCEPT:
            width, height = window.get_size()
            if (self.puzzle_manager.current_puzzle.grid.size != (width, height)):
                self.transform_grid(transform.resize_grid, width=width, height=height)
        window.destroy()
        
    def view_preferences(self):
        preferences = PreferencesWindow(self)
        preferences.show_all()
        preferences.run()
        preferences.destroy()
        self.update_window()
        
    def undo_action(self):
        s = action.stack.undo(self.puzzle_manager.current_puzzle)
        self.update_window(True)
        if s.clue_slot:
            self.set_selection(*s.clue_slot)
        
    def redo_action(self):
        s = action.stack.redo(self.puzzle_manager.current_puzzle)
        self.update_window(True)
        if s.clue_slot:
            self.set_selection(*s.clue_slot)
        
    def create_edit_menu(self):
        menu = gtk.Menu()
        
        accel_group = gtk.AccelGroup()
        self.add_accel_group(accel_group)
        
        self.undo_menu_item = self._create_menu_item(
            lambda item: self.undo_action()
            , u"Undo the last action"
            , image=gtk.STOCK_UNDO
            , accelerator="<Ctrl>Z"
            , accel_group=accel_group)
        self.undo_menu_item.set_sensitive(False)
        menu.append(self.undo_menu_item)
        
        self.redo_menu_item = self._create_menu_item(
            lambda item: self.redo_action()
            , u"Redo the last undone action"
            , image=gtk.STOCK_REDO
            , accelerator="<Shift><Ctrl>Z"
            , accel_group=accel_group)
        self.redo_menu_item.set_sensitive(False)
        menu.append(self.redo_menu_item)
        
        menu.append(gtk.SeparatorMenuItem())

        item = self.create_edit_symmetry_menu()
        item.set_sensitive(False)
        self.puzzle_toggle_items += [item]
        menu.append(item)
        
        menu.append(gtk.SeparatorMenuItem())
        
        menu.append(self._create_menu_item(
            lambda item: self.view_preferences()
            , u"Configure the program"
            , image=gtk.STOCK_PREFERENCES))
                
        edit_menu = gtk.MenuItem(u"_Edit", True)
        edit_menu.set_submenu(menu)
        return edit_menu
        
    def create_edit_symmetry_menu(self):
        menu = gtk.Menu()
        def set_symmetry(item, options):
            try:
                e_settings.settings["symmetries"] = options
            except AttributeError:
                pass
        def create_symmetry_option(symmetries, txt_select, txt_item, prev, active):
            select = lambda i: self.update_status(constants.STATUS_MENU, txt_select)
            deselect = lambda i: self.pop_status(constants.STATUS_MENU)
            item = gtk.RadioMenuItem(prev, txt_item, True)
            item.connect("activate", set_symmetry, symmetries)
            item.connect("select", select)
            item.connect("deselect", deselect)
            if active:
                item.set_active(True)
            menu.append(item)
            return item
        item = None
        options = [
            ([], u"Use no symmetry rules when modifying the grid", u"_No symmetry", False)
            , (None, None, None, None)
            , ([constants.SYM_HORIZONTAL]
                , u"Use a horizontal symmetry axis when modifying the grid"
                , u"_Horizontal symmetry axis", False)
            , ([constants.SYM_VERTICAL]
                , u"Use a vertical symmetry axis when modifying the grid"
                , u"_Vertical symmetry axis", False)
            , ([constants.SYM_HORIZONTAL, constants.SYM_VERTICAL]
                , u"Use horizontal and vertical symmetry axes when modifying the grid"
                , u"_Horizontal and vertical axes", False)
            , ([constants.SYM_DIAGONALS]
                , u"Use diagonal symmetry axes when modifying the grid"
                , u"_Diagonal symmetry axes", False)
            , (None, None, None, None)
            , ([constants.SYM_90]
                , u"Use 90 degree rotational symmetry when modifying the grid"
                , u"_90 degree rotational symmetry", False)
            , ([constants.SYM_180]
                , u"Use 180 degree rotational symmetry when modifying the grid"
                , u"_180 degree rotational symmetry", True)
        ]
        for o_s, o_sel, o_item, o_active in options:
            if o_s is None:
                menu.append(gtk.SeparatorMenuItem())
            else:
                item = create_symmetry_option(o_s, o_sel, o_item, item, o_active)
        symmetry_menu = gtk.MenuItem(u"_Symmetry", True)
        symmetry_menu.set_submenu(menu)
        return symmetry_menu
        
    def perform_selection_based_transform(self, transform):
        selection = self.get_selection()
        if selection is not None:
            sel_x, sel_y = selection
            self.transform_grid(transform, x=sel_x, y=sel_y)
    
    def transform_grid(self, transform, **args):
        pre_slot = self.get_selection(slot=True)
        puzzle = self.puzzle_manager.current_puzzle
        transform(puzzle, **args)
        selection_changed = pre_slot != self.get_selection(slot=True)
        action.stack.push(State(self.puzzle_manager.current_puzzle.grid))
        # TODO catch all, should not be needed
        if puzzle.grid.lines:
            puzzle.grid.lines = None
        
        # a transform function optionally has an attribute type to
        # indicate whether it changed the structure or just the contennt
        # of the puzzle
        try:
            t = transform.type
        except AttributeError:
            t = constants.TRANSFORM_STRUCTURE
        self.update_window(True, transform=t, selection_changed=selection_changed)
        
    def transform_clues(self, transform, **args):
        puzzle = self.puzzle_manager.current_puzzle
        transform(puzzle, **args)
        s = State(puzzle.grid, clue_slot=(args['x'], args['y'], args['direction']))
        action.stack.push(s)
        self.update_undo_redo()
    
    def update_undo_redo(self):
        has_undo = action.stack.has_undo()
        has_redo = action.stack.has_redo()
        self.undo_menu_item.set_sensitive(has_undo)
        self.redo_menu_item.set_sensitive(has_redo)
        self.undo_tool_item.set_sensitive(has_undo)
        self.redo_tool_item.set_sensitive(has_redo)
        
    def update_window(self
        , content_changed=False
        , transform=constants.TRANSFORM_STRUCTURE
        , selection_changed=True):
        puzzle = self.puzzle_manager.current_puzzle
        if puzzle is None:
            self.set_title(constants.TITLE)
            self.pop_status(constants.STATUS_GRID)
        else:
            selection = self.get_selection()
            if content_changed and transform >= constants.TRANSFORM_STRUCTURE:
                status = puzzle.grid.determine_status(False)
                message = self.determine_status_message(status)
                self.update_status(constants.STATUS_GRID, message)
                # if grid structure changes, set selection again
                # (it may have changed)
                if selection is not None:
                    sel_x, sel_y = selection
                    self.set_selection(x=sel_x, y=sel_y, selection_changed=selection_changed)
            if selection is not None:
                sel_x, sel_y = selection
                valid = puzzle.grid.is_valid(sel_x, sel_y)
                for item, predicate in self.selection_toggle_items:
                    item.set_sensitive(valid and predicate(puzzle))
                if valid and not puzzle.grid.is_available(sel_x, sel_y):
                    self.set_selection(-1, -1)
                
        for item in self.puzzle_toggle_items:
            item.set_sensitive(puzzle is not None)
        if content_changed and transform >= constants.TRANSFORM_CONTENT:
            self.update_undo_redo()
        
        try:
            # TODO refactor content_changed away
            if content_changed:
                if transform >= constants.TRANSFORM_STRUCTURE:
                    # TODO modify when arbitrary number schemes are implemented
                    self.editor.puzzle.grid.assign_numbers()
                if transform >= constants.TRANSFORM_CONTENT:
                    # reload all word/clue items and select current word
                    grid = self.puzzle_manager.current_puzzle.grid
                    selection = e_settings.selection
                    p, q = grid.get_start_word(*selection)
                    e_tools["clue"].load_items(grid)
                    e_tools["clue"].select(p, q, selection[2])
            e_settings.force_redraw = True
            self.editor.refresh_words()
            self.editor.refresh_visual_size()
        except AttributeError:
            pass
        self.panel.queue_draw()
        
    @staticmethod
    def determine_status_message(status):
        return ''.join(
            ["Blocks: ", str(status["block_count"]), " ("
            ,"%.2f" % status["block_percentage"], "%), "
            ,"words: ", str(status["word_count"]), ", "
            ,"letters: ", str(status["actual_char_count"]), " / ", str(status["char_count"])
            ])
        
    def create_view_menu(self):
        menu = gtk.Menu()
        
        def toggle_toolbar(widget):
            if widget.active:
                self.toolbar.show()
            else:
                self.toolbar.hide() 
        
        activate = lambda item: toggle_toolbar(item)
        select = lambda item: self.update_status(constants.STATUS_MENU
            , u"Show or hide the toolbar")
        deselect = lambda item: self.pop_status(constants.STATUS_MENU)
        item = gtk.CheckMenuItem(u"_Toolbar", True)
        item.set_active(True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        menu.append(item)
        
        def toggle_statusbar(widget):
            if widget.active:
                self.statusbar.show()
            else:
                self.statusbar.hide()
        
        activate = lambda item: toggle_statusbar(item)
        select = lambda item: self.update_status(constants.STATUS_MENU
            , u"Show or hide the statusbar")
        deselect = lambda item: self.pop_status(constants.STATUS_MENU)
        item = gtk.CheckMenuItem(u"_Statusbar", True)
        item.set_active(True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        menu.append(item)
        
        menu.append(gtk.SeparatorMenuItem())
        
        def toggle_predicate(predicate, status):
            view.custom_settings[predicate] = status
            try:
                e_settings.force_redraw = True
                self.panel.queue_draw()
            except AttributeError:
                pass
                
        def toggle_warning(predicate, status):
            e_settings.warnings[predicate] = status
            try:
                e_settings.force_redraw = True
                self.panel.queue_draw()
            except AttributeError:
                pass
        
        activate = lambda item: toggle_predicate("show_numbers", item.active)
        select = lambda item: self.update_status(constants.STATUS_MENU
            , u"Show or hide the word numbers in the editor")
        deselect = lambda item: self.pop_status(constants.STATUS_MENU)
        item = gtk.CheckMenuItem(u"_Word numbers", True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        menu.append(item)
        item.set_active(True)
        toggle_predicate("show_numbers", True)
        
        menu.append(gtk.SeparatorMenuItem())
        
        warnings = [(constants.WARN_UNCHECKED
            , u"Warn visually when cells that belong to one word exist in the grid"
            , u"Warn for _unchecked cells")
            , (constants.WARN_CONSECUTIVE
            , u"Warn visually when consecutive unchecked cells exist in the grid"
            , u"Warn for _consecutive unchecked cells")
            , (constants.WARN_TWO_LETTER
            , u"Warn visually when two-letter words exist in the grid"
            , u"Warn for tw_o-letter words")
            #, (constants.WARN_BLACKLIST
            #, u"Warn visually when blacklisted words exist in the grid"
            #, u"Warn for blacklisted words")
        ]
        for code, status, txt in warnings:
            activate = lambda i, code: toggle_warning(code, i.active)
            select = lambda i, status: self.update_status(constants.STATUS_MENU, status)
            deselect = lambda i: self.pop_status(constants.STATUS_MENU)
            item = gtk.CheckMenuItem(txt, True)
            item.connect("activate", activate, code)
            item.connect("select", select, status)
            item.connect("deselect", deselect)
            menu.append(item)
            item.set_active(True)
            toggle_warning(code, True)
        view_menu = gtk.MenuItem(u"_View", True)
        view_menu.set_submenu(menu)
        return view_menu
        
    def edit_appearance(self):
        puzzle = self.puzzle_manager.current_puzzle
        editor = AppearanceDialog(self, puzzle.view.properties)
        editor.show_all()
        if editor.run() == gtk.RESPONSE_OK:
            app = editor.gather_appearance()
            for key, value in app.items():
                puzzle.view.properties[key] = value
            try:
                e_settings.force_redraw = True
                self.editor.refresh_visual_size()
            except AttributeError:
                pass
            self.panel.queue_draw()
        editor.destroy()
        
    def create_patterns(self):
        size = self.puzzle_manager.current_puzzle.grid.size
        editor = PatternEditor(self, size=size)
        editor.show_all()
        if editor.run() == gtk.RESPONSE_OK:
            self.transform_grid(transform.replace_grid, grid=editor.grid)
        editor.destroy()

    def create_grid_menu(self):
        menu = gtk.Menu()
        
        menu.append(self._create_menu_item(
            lambda item: self.edit_appearance()
            , u"Edit the appearance of the puzzle"
            , title=u"Edit _appearance..."
            , is_puzzle_sensitive=True))
            
        menu.append(gtk.SeparatorMenuItem())
        
        item = self.create_grid_transform_menu()
        item.set_sensitive(False)
        self.puzzle_toggle_items += [item]
        menu.append(item)
        
        item = self.create_grid_clear_menu()
        item.set_sensitive(False)
        self.puzzle_toggle_items += [item]
        menu.append(item)
        
        menu.append(gtk.SeparatorMenuItem())
        
        menu.append(self._create_menu_item(
            lambda item: self.resize_grid()
            , u"Change the dimensions of the grid"
            , title=u"_Resize grid..."
            , is_puzzle_sensitive=True))
            
        menu.append(gtk.SeparatorMenuItem())
        
        #menu.append(self._create_menu_item(
        #    lambda item: self.manage_patterns()
        #    , u"Manage the pattern files available to the program"
        #    , title="_Manage pattern files..."))
            
        #menu.append(self._create_menu_item(
        #    lambda item: self.create_patterns()
        #    , u"Generate a pattern using the pattern editor"
        #    , title="_Create pattern..."
        #    , is_puzzle_sensitive=True))
        
        grid_menu = gtk.MenuItem(u"_Grid", True)
        grid_menu.set_submenu(menu)
        return grid_menu
        
    def create_grid_transform_menu(self):
        menu = gtk.Menu()
        
        menu.append(self._create_menu_item(
            lambda item: self.transform_grid(transform.shift_grid_up)
            , u"Move the content of the grid up by one square"
            , title=u"Move content _up"
            , is_puzzle_sensitive=True))
        menu.append(self._create_menu_item(
            lambda item: self.transform_grid(transform.shift_grid_down)
            , u"Move the content of the grid down by one square"
            , title=u"Move content _down"
            , is_puzzle_sensitive=True))
        menu.append(self._create_menu_item(
            lambda item: self.transform_grid(transform.shift_grid_left)
            , u"Move the content of the grid left by one square"
            , title=u"Move content _left"
            , is_puzzle_sensitive=True))
        menu.append(self._create_menu_item(
            lambda item: self.transform_grid(transform.shift_grid_right)
            , u"Move the content of the grid right by one square"
            , title=u"Move content _right"
            , is_puzzle_sensitive=True))
        
        menu.append(gtk.SeparatorMenuItem())
        
        menu.append(self._create_menu_item(
            lambda item: self.perform_selection_based_transform(transform.insert_row_above)
            , u"Insert an empty row above the selected cell"
            , title=u"Insert row (above)"
            , is_selection_sensitive=True))
        menu.append(self._create_menu_item(
            lambda item: self.perform_selection_based_transform(transform.insert_row_below)
            , u"Insert an empty row below the selected cell"
            , title=u"Insert row (below)"
            , is_selection_sensitive=True))
        menu.append(self._create_menu_item(
            lambda item: self.perform_selection_based_transform(transform.insert_column_left)
            , u"Insert an empty column to the left of the selected cell"
            , title=u"Insert column (left)"
            , is_selection_sensitive=True))
        menu.append(self._create_menu_item(
            lambda item: self.perform_selection_based_transform(transform.insert_column_right)
            , u"Insert an empty column to the right of the selected cell"
            , title=u"Insert column (right)"
            , is_selection_sensitive=True))
        
        menu.append(gtk.SeparatorMenuItem())
        
        menu.append(self._create_menu_item(
            lambda item: self.perform_selection_based_transform(transform.remove_row)
            , u"Remove the row containing the selected cell"
            , title=u"Remove row"
            , is_selection_sensitive=True
            , condition=lambda puzzle: puzzle.grid.height > 3))
        menu.append(self._create_menu_item(
            lambda item: self.perform_selection_based_transform(transform.remove_column)
            , u"Remove the column containing the selected cell"
            , title=u"Remove column"
            , is_selection_sensitive=True
            , condition=lambda puzzle: puzzle.grid.width > 3))
            
        menu.append(gtk.SeparatorMenuItem())
        
        menu.append(self._create_menu_item(
            lambda item: self.transform_grid(transform.horizontal_flip)
            , u"Flip the content of the grid horizontally and clear the clues"
            , title=u"Flip _horizontally"
            , is_puzzle_sensitive=True))
        menu.append(self._create_menu_item(
            lambda item: self.transform_grid(transform.vertical_flip)
            , u"Flip the content of the grid vertically and clear the clues"
            , title=u"Flip _vertically"
            , is_puzzle_sensitive=True))
        #menu.append(self._create_menu_item(
        #    lambda item: self.transform_grid(transform.diagonal_flip)
        #    , u"Flip the content of the grid diagonally"
        #    , title=u"Flip _diagonally"
        #    , is_puzzle_sensitive=True))
        
        flip_menu = gtk.MenuItem(u"_Transform", True)
        flip_menu.set_submenu(menu)
        return flip_menu
        
    def create_grid_clear_menu(self):
        menu = gtk.Menu()
        
        menu.append(self._create_menu_item(
            lambda item: self.transform_grid(transform.clear_all)
            , u"Clear all the content of the puzzle"
            , title=u"_All"
            , is_puzzle_sensitive=True))
        #menu.append(self._create_menu_item(
        #    lambda item: self.transform_grid(transform.clear_bars)
        #    , u"Clear the bars and the involved clues of the puzzle"
        #    , title=u"_Bars"
        #    , is_puzzle_sensitive=True))
        menu.append(self._create_menu_item(
            lambda item: self.transform_grid(transform.clear_blocks)
            , u"Clear the blocks and the involved clues of the puzzle"
            , title=u"Bl_ocks"
            , is_puzzle_sensitive=True))
        #menu.append(self._create_menu_item(
        #    lambda item: self.transform_grid(transform.clear_voids)
        #    , u"Clear the void cells and the involved clues of the puzzle"
        #    , title=u"_Voids"
        #    , is_puzzle_sensitive=True))
        menu.append(self._create_menu_item(
            lambda item: self.transform_grid(transform.clear_chars)
            , u"Clear the letters and the involved clues of the puzzle"
            , title=u"_Letters"
            , is_puzzle_sensitive=True))
        menu.append(self._create_menu_item(
            lambda item: self.transform_grid(transform.clear_clues)
            , u"Clear the clues of the puzzle"
            , title=u"_Clues"
            , is_puzzle_sensitive=True))
        
        clear_menu = gtk.MenuItem(u"_Clear", True)
        clear_menu.set_submenu(menu)
        return clear_menu
        
    def create_word_menu(self):
        menu = gtk.Menu()
        
        def activate(item):
            w = WordListEditor(self)
            w.show_all()
            w.run()
            w.destroy()
        menu.append(self._create_menu_item(activate
            , u"Manage the word lists available to the program"
            , title=u"_Manage word lists..."))
        def activate(item):
            w = WordUsageDialog(self)
            w.show_all()
            w.run()
            w.destroy()
        menu.append(self._create_menu_item(activate
            , u"Configure how word lists are used in the program"
            , title=u"Configure word list _usage..."))
        
        menu.append(gtk.SeparatorMenuItem())
        
        def activate(item):
            w = FindWordsDialog(self)
            w.show_all()
            w.run()
            w.destroy()        
        menu.append(self._create_menu_item(activate
            , u"Find words in word lists according to a pattern"
            , title=u"_Find words..."))
        
        def activate(item):
            w = AccidentalWordsDialog(self, self.puzzle_manager.current_puzzle)
            w.show_all()
            w.run()
            w.destroy()
        menu.append(self._create_menu_item(activate
            , u"View words that may have accidentally appeared in the grid"
            , title=u"View _accidental words..."
            , is_puzzle_sensitive=True))
        
        def activate(item):
            w = SimilarWordsDialog(self, self.puzzle_manager.current_puzzle)
            w.show_all()
            w.run()
            w.destroy()
        menu.append(self._create_menu_item(activate
            , u"View words that have a part in common"
            , title=u"View _similar words..."
            , is_puzzle_sensitive=True))
            
        tool_menu = gtk.MenuItem(u"_Word", True)
        tool_menu.set_submenu(menu)
        return tool_menu
    
    def create_clue_menu(self):
        menu = gtk.Menu()
        
        menu.append(self._create_menu_item(
            lambda item: self.edit_clues()
            , u"Edit the clues of the puzzle"
            , title=u"Edit _clues..."
            , is_puzzle_sensitive=True))
        
        word_menu = gtk.MenuItem(u"_Clue", True)
        word_menu.set_submenu(menu)
        return word_menu
        
    def manage_patterns(self):
        editor = PatternFileEditor(self)
        editor.show_all()
        editor.run()
        editor.destroy()

    def create_help_menu(self):
        menu = gtk.Menu()
        
        menu.append(self._create_menu_item(
            self.on_help_about_activate
            , u"About this program"
            , image=gtk.STOCK_ABOUT))
        
        help_menu = gtk.MenuItem(u"_Help", True)
        help_menu.set_submenu(menu)
        return help_menu
        
    def on_help_about_activate(self, widget, data=None):
        dialog = gtk.AboutDialog()
        dialog.set_title(u"About " + constants.TITLE)
        dialog.set_program_name(constants.TITLE)
        dialog.set_comments(u"Crossword creation software")
        dialog.set_version(constants.VERSION)
        dialog.set_authors([u"Simeon Visser <simeonvisser@gmail.com>"])
        dialog.set_copyright(u"Copyright © 2009 - 2011 Simeon Visser")
        def on_click_website(dialog, link):
            webbrowser.open(link)
        gtk.about_dialog_set_url_hook(on_click_website)
        dialog.set_website(constants.WEBSITE)
        dialog.set_license(u"""This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
                
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses/>.""")
        dialog.set_wrap_license(True)
        dialog.set_transient_for(self)
        dialog.connect("response", lambda dialog, response: dialog.destroy())
        dialog.show_all()

def quit():
    gtk.main_quit()
    cPalabra.postprocess()
    write_config_file()
    
def main(argv=None):
    try:
        has_splash = False
        if has_splash:
            splash = create_splash()
            splash.show()
            while gtk.events_pending():
                gtk.main_iteration()
        print "Reading configuration file..."
        read_config_file()
        print "Loading word lists..."
        cPalabra.preprocess_all()
        wordlists = create_wordlists(preferences.prefs["word_files"])
        print "Loading grid files..."
        fs = constants.STANDARD_PATTERN_FILES + preferences.prefs[constants.PREF_PATTERN_FILES]
        patterns = read_containers(fs)
        
        palabra = PalabraWindow()
        palabra.wordlists = wordlists
        palabra.patterns = patterns
        palabra.show_all()
        if has_splash:
            splash.destroy()
        gtk.main()
    except KeyboardInterrupt:
        import sys
        sys.exit("ERROR: Interrupted by user")
