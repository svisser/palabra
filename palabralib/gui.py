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
from clue import ClueTool, create_clues, ManageCluesDialog
import constants
from export import ExportWindow
from editor import (
    compute_words,
    e_settings,
    e_tools,
    Editor,
    EDITOR_EVENTS,
    set_overlay,
    set_selection,
)
from files import (
    FILETYPES,
    ParserError,
    read_crossword,
    export_puzzle,
    read_containers,
)
from gui_common import (
    create_label,
    create_notebook,
    create_scroll,
    create_menubar,
    launch_dialog,
    launch_file_dialog,
    PalabraMessageDialog,
)
from gui_editor import WordTool, FillTool
from gui_prefs import PreferencesWindow
from gui_word import (
    AccidentalWordsDialog,
    FindWordsDialog,
    WordListManager,
    SimilarWordsDialog,
    WordUsageDialog,
    WordListEditor,
    WordListUnableToStoreDialog,
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
from word import create_wordlists, write_wordlists

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

def determine_status_message(grid):
    status = grid.determine_status(False)
    return ''.join(
        ["Blocks: ", str(status["block_count"]), " ("
        ,"%.2f" % status["block_percentage"], "%), "
        ,"words: ", str(status["word_count"]), ", "
        ,"letters: ", str(status["actual_char_count"]), " / ", str(status["char_count"])
        ])

class ClosePuzzleDialog(gtk.Dialog):
    def __init__(self, parent):
        super(ClosePuzzleDialog, self).__init__(u"Close without saving"
            , parent
            , gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_MODAL
            , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
            , gtk.STOCK_NO, gtk.RESPONSE_NO
            , gtk.STOCK_YES, gtk.RESPONSE_YES))
        self.set_default_response(gtk.RESPONSE_CLOSE)
        self.set_resizable(False)
        label = create_label(u"Save the changes to the current puzzle before closing?")
        hbox = gtk.HBox()
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG)
        hbox.pack_start(image, False, False, 0)
        hbox.pack_start(label, True, False, 10)
        self.vbox.pack_start(hbox, False, False, 10)

class PalabraAboutDialog(gtk.AboutDialog):
    def __init__(self, parent):
        super(PalabraAboutDialog, self).__init__()
        self.set_title(u"About " + constants.TITLE)
        self.set_program_name(constants.TITLE)
        self.set_comments(u"Crossword creation software")
        self.set_version(constants.VERSION)
        self.set_authors([u"Simeon Visser <simeonvisser@gmail.com>"])
        self.set_copyright(u"Copyright © 2009 - 2011 Simeon Visser")
        def on_click_website(dialog, link):
            webbrowser.open(link)
        gtk.about_dialog_set_url_hook(on_click_website)
        self.set_website(constants.WEBSITE)
        self.set_license(u"""This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
                
    This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses/>.""")
        self.set_wrap_license(True)
        self.set_transient_for(parent)
        self.connect("response", lambda dialog, response: dialog.destroy())

def compute_title(path=None):
    title = u"Unsaved puzzle - " + constants.TITLE
    if path is not None:
        filename_start = path.rfind(os.sep) + 1
        filename = path[filename_start:]
        title = ''.join([filename, u" - ", constants.TITLE])
    return title

class PalabraOpenPuzzleDialog(gtk.FileChooserDialog):
    def __init__(self, parent):
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
        super(PalabraOpenPuzzleDialog, self).__init__(u"Open puzzle"
            , parent
            , gtk.FILE_CHOOSER_ACTION_OPEN
            , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
            , gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        #self.set_preview_widget(preview)
        #self.connect("selection-changed", on_selection_changed)
        for key, f in compute_filters(include_all=True):
            self.add_filter(f)

def compute_filters(include_all=False):
    filters = []
    for key in FILETYPES['keys']:
        description = FILETYPES[key]['description']
        pattern = '*' + FILETYPES[key]['pattern']
        f = gtk.FileFilter()
        f.set_name(description + ' (' + pattern + ')')
        f.add_pattern(pattern)
        filters.append((key, f))
    if include_all:
        f = gtk.FileFilter()
        f.set_name(u"All files")
        f.add_pattern("*")
        filters.append(("all", f))
    return filters

class PalabraSavePuzzleDialog(gtk.FileChooserDialog):
    def __init__(self, parent, save_as=False):
        title = u"Save puzzle"
        if save_as:
            title = u"Save puzzle as..."
        super(PalabraSavePuzzleDialog, self).__init__(title
            , parent
            , gtk.FILE_CHOOSER_ACTION_SAVE
            , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
            , gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        self.set_do_overwrite_confirmation(True)
        self.filters = {}
        for key, f in compute_filters():
            self.add_filter(f)
            self.filters[f] = key
    
    def get_filetype(self):
        return self.filters[self.get_filter()]

class PalabraExportPuzzleDialog(gtk.FileChooserDialog):
    def __init__(self, parent):
        super(PalabraExportPuzzleDialog, self).__init__(u"Export location"
            , parent
            , gtk.FILE_CHOOSER_ACTION_SAVE
            , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
            , gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        self.set_do_overwrite_confirmation(True)

class PalabraOpenPuzzleErrorDialog(PalabraMessageDialog):
    def __init__(self, parent, message):
        super(PalabraOpenPuzzleErrorDialog, self).__init__(parent
            , u"Error when opening file", message
        )

class PalabraWindow(gtk.Window):
    def __init__(self):
        super(PalabraWindow, self).__init__()
        self.update_title(clear=True)
        self.set_size_request(800, 600)
        self.puzzle_toggle_items = []
        self.selection_toggle_items = []
        self.puzzle_manager = PuzzleManager()
        MENUBAR = [self.create_file_menu
            , self.create_edit_menu
            , self.create_view_menu
            , self.create_grid_menu
            , self.create_word_menu
            , self.create_clue_menu
            , self.create_help_menu
        ]
        self.toolbar = self.create_toolbar()
        self.panel = gtk.VBox()
        self.statusbar = gtk.Statusbar()
        self.main = gtk.VBox()
        self.main.pack_start(create_menubar(MENUBAR), False, False, 0)
        self.main.pack_start(self.toolbar, False, False, 0)
        self.main.pack_start(self.panel)
        self.main.pack_start(self.statusbar, False, False, 0)
        self.add(self.main)
        self.connect("delete-event", self.on_delete)
        self.connect("destroy", lambda widget: quit())
        self.wordlists = []
        self.clues = []
        self.patterns = None
        self.blacklist = None
    
    def _get_puzzle(self):
        return self.puzzle_manager.current_puzzle
        
    puzzle = property(_get_puzzle)
        
    def on_delete(self, window, event):
        self.close_puzzle()
        return self.puzzle_manager.has_puzzle()
        
    def on_quit(self):
        self.close_puzzle()
        if not self.puzzle_manager.has_puzzle():
            quit()
        
    def get_selection(self, slot=False):
        """
        Return the currently selected cell. If slot=True then return
        the currently selected slot. (-1, -1) is returned if the currently
        'selected' cell is not valid anymore.
        """
        x, y, d = e_settings.selection
        if slot:
            sx, sy = self.puzzle.grid.get_start_word(x, y, d)
            # check for validness because selection may have become invalid
            # to due grid transform
            if not self.puzzle.grid.is_valid(sx, sy):
                return (-1, -1, "across", -1)
            return (x, y, d, self.puzzle.grid.word_length(sx, sy, d))
        if not self.puzzle.grid.is_valid(x, y):
            return (-1, -1)
        return (x, y)
            
    def set_selection(self, x, y, direction=None, selection_changed=True, full_update=True):
        set_selection(self, self.puzzle, e_settings, x=x, y=y
            , direction=direction, selection_changed=selection_changed
            , full_update=full_update)
        
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
            f_done = lambda w: w.get_configuration()
            response, configuration = launch_dialog(NewWindow, self, f_done=f_done)
            if response == gtk.RESPONSE_ACCEPT:
                self.update_title(None)
                self.puzzle_manager.new_puzzle(configuration)
                e_settings.reset_controls()
                self.load_puzzle()
    
    def open_puzzle(self):
        self.close_puzzle()
        if self.puzzle_manager.has_puzzle():
            return
        filename = launch_file_dialog(PalabraOpenPuzzleDialog, self)
        if filename is None:
            return
        try:
            puzzle = read_crossword(filename)
        except ParserError, e:
            launch_dialog(PalabraOpenPuzzleErrorDialog, self, e.message)
        puzzle.filename = filename
        self.update_title(filename)
        self.puzzle_manager.current_puzzle = puzzle
        self.load_puzzle()
            
    def update_title(self, path=None, clear=False):
        """Update the title of the window, possibly including a filename."""
        self.set_title(constants.TITLE if clear else compute_title(path))
    
    def save_puzzle(self, save_as=False):
        backup = preferences.prefs[constants.PREF_COPY_BEFORE_SAVE]
        if save_as or self.puzzle.filename is None:
            d = PalabraSavePuzzleDialog(self, save_as)
            d.show_all() 
            if d.run() == gtk.RESPONSE_OK:
                filetype = d.get_filetype()
                filename = d.get_filename()
                extension = FILETYPES[filetype]['pattern']
                self.puzzle.update_type(filetype, filename, extension)
                FILETYPES[filetype]['writer'](self.puzzle, backup)
                self.update_title(filename)
            d.destroy()
        else:
            FILETYPES[self.puzzle.type]['writer'](self.puzzle, backup)
        action.stack.distance_from_saved = 0
        
    def export_puzzle(self):
        f_done = lambda w: w.options
        response, options = launch_dialog(ExportWindow, self, self.puzzle, f_done=f_done)
        if response == gtk.RESPONSE_OK:
            filename = launch_file_dialog(PalabraExportPuzzleDialog, self)
            if filename is not None:
                export_puzzle(self.puzzle, filename, options)
    
    def load_puzzle(self):
        action.stack.push(State(self.puzzle_manager.current_puzzle.grid), initial=True)
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
        self.puzzle.view.refresh_visual_size(self.drawing_area)
        self.drawing_area.queue_draw()
        self.editor = Editor(self)
        self.ids = []
        for k, e in EDITOR_EVENTS.items():
            self.ids.append(self.drawing_area.connect(k, e, self, self.puzzle, e_settings))
        e_tools["clue"] = ClueTool(self)
        e_tools["fill"] = FillTool(self.editor)
        e_tools["word"] = WordTool(self)
        
        options_hbox = gtk.HBox()
        options_hbox.set_border_width(12)
        options_hbox.set_spacing(18)
        
        options_vbox = gtk.VBox()
        options_vbox.set_spacing(15)
        options_hbox.pack_start(options_vbox)
        
        options = gtk.VBox()
        options_vbox.pack_start(options)
        
        main = gtk.VBox()
        main.pack_start(create_scroll(self.drawing_area, viewport=True))
        
        tab_word = (e_tools["word"].create(), u"Word")
        tab_clue = (e_tools["clue"].create(self.puzzle), u"Clue")
        #tab_fill = (e_tools["fill"].create(), u"Fill")
        e_tools["clue"].set_clue_editor_status(False)
        def on_switch_page(tabs, do_not_use, num):
            if num == 0:
                word = e_tools["word"].get_selected_word()
                self.editor.set_overlay(word)
                self.update_window()
            else:
                self.editor.set_overlay(None)
                e_tools["word"].deselect()
        pages = [tab_word, tab_clue]#, tab_fill]
        tabs = create_notebook(pages, border=(16, 8), f_switch=on_switch_page)
        tabs.set_border_width(8)
        tabs.set_size_request(375, -1)
        tabs.set_show_border(False)
        
        paned = gtk.HPaned()
        paned.pack1(main, True, False)
        paned.pack2(tabs, True, False)
        w, h = self.get_size()
        paned.set_position(w - 375)
        self.panel.pack_start(paned, True, True, 0)
        self.panel.show_all()
        self.update_window()
        
    def close_puzzle(self):
        """
        Ask the user if the puzzle needs to be closed and/or saved
        and perform these actions if desired.
        """
        need_to_close, need_to_save = self.check_close_puzzle()
        if need_to_close:
            if need_to_save:
                self.save_puzzle()
            self.puzzle_manager.current_puzzle = None
            action.stack.clear()
            for widget in self.panel.get_children():
                self.panel.remove(widget)
            self.drawing_area.unset_flags(gtk.CAN_FOCUS)
            for i in self.ids:
                self.drawing_area.disconnect(i)
            self.update_window()

    def check_close_puzzle(self):
        """
        Return a tuple with two booleans: (need_to_close, need_to_save).
        need_to_close = whether the puzzle needs to be closed
        need_to_save = whether the puzzle needs to be saved before closing
        """
        if not self.puzzle_manager.has_puzzle():
            return False, False 
        if action.stack.distance_from_saved == 0:
            return True, False
        response = launch_dialog(ClosePuzzleDialog, self)
        if response == gtk.RESPONSE_YES:
            return True, True
        elif response == gtk.RESPONSE_CANCEL:
            return False, False
        return True, False
    
    def create_toolbar(self):
        """Create the buttons in the toolbar."""
        toolbar = gtk.Toolbar()
        toolbar.set_orientation(gtk.ORIENTATION_HORIZONTAL)
        def create_tool_button(stock, f_click, p_sensitive=False):
            item = gtk.ToolButton()
            item.set_stock_id(stock)
            item.connect("clicked", f_click)
            item.show()
            toolbar.insert(item, -1)
            if p_sensitive:
                item.set_sensitive(False)
                self.puzzle_toggle_items += [item]
            return item
        create_tool_button(gtk.STOCK_NEW, lambda i: self.new_puzzle())
        create_tool_button(gtk.STOCK_OPEN, lambda i: self.open_puzzle())
        create_tool_button(gtk.STOCK_SAVE, lambda i: self.save_puzzle(), True)
        toolbar.insert(gtk.SeparatorToolItem(), -1)
        self.undo_tool_item = create_tool_button(gtk.STOCK_UNDO, lambda i: self.do_action("undo"))
        self.undo_tool_item.set_sensitive(False)
        self.redo_tool_item = create_tool_button(gtk.STOCK_REDO, lambda i: self.do_action("redo"))
        self.redo_tool_item.set_sensitive(False)
        toolbar.insert(gtk.SeparatorToolItem(), -1)
        activate = lambda i: launch_dialog(PropertiesWindow, self, self.puzzle)
        create_tool_button(gtk.STOCK_PROPERTIES, activate, True)
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
            lambda item: self.save_puzzle()
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
            lambda item: launch_dialog(PropertiesWindow, self, self.puzzle)
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
        w = SizeWindow(self, self.puzzle)
        w.show_all() 
        if w.run() == gtk.RESPONSE_ACCEPT:
            width, height = w.get_size()
            if (self.puzzle.grid.size != (width, height)):
                self.transform_grid(transform.resize_grid
                    , width=width, height=height)
        w.destroy()
        
    def do_action(self, task):
        if task == "undo":
            s = action.stack.undo(self.puzzle)
        elif task == "redo":
            s = action.stack.redo(self.puzzle)
        self.update_window()
        if s.clue_slot:
            self.set_selection(*s.clue_slot)
        
    def create_edit_menu(self):
        menu = gtk.Menu()
        
        accel_group = gtk.AccelGroup()
        self.add_accel_group(accel_group)
        
        self.undo_menu_item = self._create_menu_item(
            lambda item: self.do_action("undo")
            , u"Undo the last action"
            , image=gtk.STOCK_UNDO
            , accelerator="<Ctrl>Z"
            , accel_group=accel_group)
        self.undo_menu_item.set_sensitive(False)
        menu.append(self.undo_menu_item)
        
        self.redo_menu_item = self._create_menu_item(
            lambda item: self.do_action("redo")
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
        
        def view_preferences():
            w = PreferencesWindow(self)
            w.show_all()
            w.run()
            w.destroy()
            self.update_window()
        menu.append(self._create_menu_item(
            lambda item: view_preferences()
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
        self.update_window(transform=t, selection_changed=selection_changed)
        
    def transform_clues(self, transform, **args):
        puzzle = self.puzzle_manager.current_puzzle
        transform(puzzle, **args)
        s = State(puzzle.grid, clue_slot=(args['x'], args['y'], args['direction']))
        action.stack.push(s)
        self.update_undo_redo()
    
    def refresh_words(self, force_refresh=False):
        """
        Update the list of words according to active constraints of letters
        and the current settings (e.g., show only words with intersections).
        """
        if self.puzzle is None:
            return
        f_wlists = preferences.prefs[constants.PREF_FIND_WORD_FILES]
        wordlists = [wlist for wlist in self.wordlists if wlist.path in f_wlists]
        min_score = preferences.prefs[constants.PREF_FIND_WORD_MIN_SCORE]
        options = {
            constants.SEARCH_OPTION_MIN_SCORE: min_score
        }
        words = compute_words(self.puzzle.grid
            , wordlists, e_settings.selection, force_refresh, options)
        e_tools["word"].display_words(words)
    
    def update_undo_redo(self):
        """Update the controls for undo and redo."""
        for i in [self.undo_menu_item, self.undo_tool_item]:
            i.set_sensitive(action.stack.has_undo())
        for i in [self.redo_menu_item, self.redo_tool_item]:
            i.set_sensitive(action.stack.has_redo())
        
    def update_window(self
        , transform=constants.TRANSFORM_STRUCTURE
        , selection_changed=True):
        puzzle = self.puzzle
        if puzzle is None:
            self.update_title(clear=True)
            self.pop_status(constants.STATUS_GRID)
        else:
            if transform >= constants.TRANSFORM_STRUCTURE:
                message = determine_status_message(puzzle.grid)
                self.update_status(constants.STATUS_GRID, message)
                selection = self.get_selection()
                if selection is not None:
                    # if grid structure changes, set selection again
                    # (it may have changed)
                    x, y = selection
                    self.set_selection(x=x, y=y
                        , selection_changed=selection_changed
                        , full_update=False)
            selection = self.get_selection()
            if selection is not None:
                valid = puzzle.grid.is_valid(*selection)
                for item, predicate in self.selection_toggle_items:
                    item.set_sensitive(valid and predicate(puzzle))
                if valid and not puzzle.grid.is_available(*selection):
                    self.set_selection(-1, -1)
        for item in self.puzzle_toggle_items:
            item.set_sensitive(puzzle is not None)
        self.update_undo_redo()
        if self.puzzle is not None:
            if transform >= constants.TRANSFORM_STRUCTURE:
                # TODO modify when arbitrary number schemes are implemented
                self.puzzle.grid.assign_numbers()
            if transform >= constants.TRANSFORM_CONTENT:
                # reload all word/clue items and select current word
                grid = self.puzzle.grid
                selection = e_settings.selection
                p, q = grid.get_start_word(*selection)
                e_tools["clue"].load_items(grid)
                e_tools["clue"].select(p, q, selection[2])
        e_settings.force_redraw = True
        self.refresh_words()
        self.refresh_editor()
        self.panel.queue_draw()
        
    def refresh_editor(self):
        if self.puzzle is None:
            return
        self.puzzle.view.grid = self.puzzle.grid
        self.puzzle.view.properties.grid = self.puzzle.grid
        size = self.puzzle.view.properties.visual_size()
        self.drawing_area.set_size_request(*size)
        
    def create_view_menu(self):
        menu = gtk.Menu()
        
        def toggle_widget(widget, active):
            if active:
                widget.show()
            else:
                widget.hide()

        activate = lambda item: toggle_widget(self.toolbar, item.active)
        select = lambda item: self.update_status(constants.STATUS_MENU
            , u"Show or hide the toolbar")
        deselect = lambda item: self.pop_status(constants.STATUS_MENU)
        item = gtk.CheckMenuItem(u"_Toolbar", True)
        item.set_active(True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        menu.append(item)
        
        activate = lambda item: toggle_widget(self.statusbar, item.active)
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
        d = AppearanceDialog(self, puzzle.view.properties)
        d.show_all()
        if d.run() == gtk.RESPONSE_OK:
            for key, value in d.gather_appearance().items():
                puzzle.view.properties[key] = value
            e_settings.force_redraw = True
            self.refresh_editor()
            self.panel.queue_draw()
        d.destroy()
        
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
            w = WordListManager(self)
            w.show_all()
            if w.run() == gtk.RESPONSE_OK:
                w.destroy()
                unable = write_wordlists(w.modifications)
                if unable:
                    w2 = WordListUnableToStoreDialog(self, unable)
                    w2.show_all()
                    w2.run()
                    w2.destroy()
            else:
                w.destroy()
        menu.append(self._create_menu_item(activate
            , u"Manage the word lists available to the program"
            , title=u"_Manage word lists..."))
        def activate(item):
            w = WordUsageDialog(self)
            w.show_all()
            if w.run() == gtk.RESPONSE_OK:
                preferences.prefs.update(w.get_configuration())
                self.update_window()
            w.destroy()
        menu.append(self._create_menu_item(activate
            , u"Configure how word lists are used in the program"
            , title=u"Configure word list _usage..."))
        activate = lambda i: launch_dialog(FindWordsDialog, self)
        menu.append(self._create_menu_item(activate
            , u"Find words in word lists according to a pattern"
            , title=u"_Find words..."))
        #def activate(item):
        #    w = WordListEditor(self)
        #    w.show_all()
        #    w.run()
        #    w.destroy()
        #menu.append(self._create_menu_item(activate
        #    , u"Create new word lists and edit existing word lists"
        #    , title=u"_Edit word lists..."))
        
        menu.append(gtk.SeparatorMenuItem())

        activate = lambda i: launch_dialog(AccidentalWordsDialog, self, self.puzzle)
        menu.append(self._create_menu_item(activate
            , u"View words that may have accidentally appeared in the grid"
            , title=u"View _accidental words..."
            , is_puzzle_sensitive=True))
        activate = lambda i: launch_dialog(SimilarWordsDialog, self, self.puzzle)
        menu.append(self._create_menu_item(activate
            , u"View words that have a part in common"
            , title=u"View _similar words..."
            , is_puzzle_sensitive=True))
            
        tool_menu = gtk.MenuItem(u"_Word", True)
        tool_menu.set_submenu(menu)
        return tool_menu
    
    def create_clue_menu(self):
        menu = gtk.Menu()
        
        activate = lambda i: launch_dialog(ManageCluesDialog, self)
        menu.append(self._create_menu_item(activate
            , u"Manage the clue databases available to the program"
            , title=u"_Manage clue databases..."))
        
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
            lambda w: launch_dialog(PalabraAboutDialog, self)
            , u"About this program"
            , image=gtk.STOCK_ABOUT))
        
        help_menu = gtk.MenuItem(u"_Help", True)
        help_menu.set_submenu(menu)
        return help_menu

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
        WORD_FILES = preferences.prefs[constants.PREF_WORD_FILES]
        cPalabra.preprocess_all()
        wordlists = create_wordlists(WORD_FILES)
        print "Loading grid files..."
        fs = constants.STANDARD_PATTERN_FILES + preferences.prefs[constants.PREF_PATTERN_FILES]
        patterns = read_containers(fs)
        print "Loading clue databases..."
        clues = create_clues(preferences.prefs[constants.PREF_CLUE_FILES])
        
        palabra = PalabraWindow()
        palabra.wordlists = wordlists
        palabra.clues = clues
        palabra.patterns = patterns
        palabra.show_all()
        if has_splash:
            splash.destroy()
        gtk.main()
    except KeyboardInterrupt:
        import sys
        sys.exit("ERROR: Interrupted by user")
