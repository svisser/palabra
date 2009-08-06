# This file is part of Palabra
#
# Copyright (C) 2009 Simeon Visser
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

import action
from appearance import AppearanceDialog
from clue import ClueEditor
import constants
from export import (
    verify_output_options,
    ExportWindow,
)
from editor import Editor
from files import (
    import_puzzle,
    export_puzzle,
    export_puzzle_to_xml,
    export_template,
)
import grid
from grid import Grid
from newpuzzle import NewWindow, SizeWindow
import preferences
from preferences import (
    PreferencesWindow,
    write_config_file,
)
from properties import PropertiesWindow
from puzzle import Puzzle, PuzzleManager
import transform
import view

class PalabraWindow(gtk.Window):
    def __init__(self):
        super(PalabraWindow, self).__init__()
        self.set_title("Palabra")
        self.set_size_request(800, 600)
        
        self.puzzle_toggle_items = []
        self.selection_toggle_items = []
        
        self.puzzle_manager = PuzzleManager()
        
        self.menubar = gtk.MenuBar()
        self.menubar.append(self.create_file_menu())
        self.menubar.append(self.create_edit_menu())
        self.menubar.append(self.create_view_menu())
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
        
        self.connect("destroy", lambda widget: quit())
        
    def to_empty_panel(self):
        for widget in self.panel.get_children():
            self.panel.remove(widget)
        self.editor.cleanup()
    
    def to_edit_panel(self):
        drawing_area = gtk.DrawingArea()
        drawing_area.add_events(
            gtk.gdk.BUTTON_PRESS_MASK
            | gtk.gdk.BUTTON_RELEASE_MASK
            | gtk.gdk.POINTER_MOTION_MASK
            | gtk.gdk.KEY_PRESS_MASK
            | gtk.gdk.KEY_RELEASE_MASK
            )
        scrolled_window = gtk.ScrolledWindow(None, None)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add_with_viewport(drawing_area)
        
        self.puzzle_manager.current_puzzle.view.update_visual_size(drawing_area)
        drawing_area.queue_draw()
        
        self.editor = Editor(self, drawing_area, self.puzzle_manager.current_puzzle)
        
        options_hbox = gtk.HBox(False, 0)
        options_hbox.set_border_width(12)
        options_hbox.set_spacing(18)
        
        options_vbox = gtk.VBox(False, 0)
        options_vbox.set_spacing(15)
        options_hbox.pack_start(options_vbox, True, True, 0)
        
        options = gtk.VBox(False, 0)
        options_vbox.pack_start(options, True, True, 0)
        
        main = gtk.HBox(False, 0)
        main.pack_start(scrolled_window, True, True, 0)
        
        all_vbox = gtk.VBox(False, 0)
        all_vbox.pack_start(main, True, True, 0)
        self.panel.pack_start(all_vbox, True, True, 0)
        self.panel.show_all()
        
    def get_selection(self):
        try:
            return self.editor.get_selection()
        except AttributeError:
            return None
        
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
                
                self.load_puzzle()
            window.destroy()
    
    def open_puzzle(self):
        self.close_puzzle()
        if not self.puzzle_manager.has_puzzle():
            dialog = gtk.FileChooserDialog("Open puzzle"
                , self
                , gtk.FILE_CHOOSER_ACTION_OPEN
                , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
                , gtk.STOCK_OPEN, gtk.RESPONSE_OK))
            filter = gtk.FileFilter()
            filter.set_name("Palabra puzzle files (*.xml)")
            filter.add_pattern("*.xml")
            dialog.add_filter(filter)
            
            filter = gtk.FileFilter()
            filter.set_name("All files")
            filter.add_pattern("*")
            dialog.add_filter(filter)
            
            dialog.show_all()
            response = dialog.run()
            if response == gtk.RESPONSE_OK:
                dialog.hide()

                filename = dialog.get_filename()
                puzzle = import_puzzle(filename)
                if puzzle is None:
                    message = u"This file does not appear to be a valid Palabra puzzle file."
                    mdialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL
                        , gtk.MESSAGE_INFO, gtk.BUTTONS_NONE, message)
                    mdialog.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
                    mdialog.set_title(u"Invalid file")
                    mdialog.run()
                    mdialog.destroy()
                else:
                    puzzle.filename = filename
                    self.update_title(filename)
                    
                    self.puzzle_manager.current_puzzle = puzzle
                    self.load_puzzle()
            dialog.destroy()
            
    def update_title(self, path=None):
        title = "Unsaved puzzle - Palabra"
        if path is not None:
            filename_start = path.rfind(os.sep) + 1
            filename = path[filename_start:]
            title = ''.join([filename, " - Palabra"])
        self.set_title(title)
    
    def save_puzzle(self, save_as=False):
        if save_as or self.puzzle_manager.current_puzzle.filename is None:
            title = "Save puzzle"
            if save_as:
                title="Save puzzle as"
            dialog = gtk.FileChooserDialog(title
                , self
                , gtk.FILE_CHOOSER_ACTION_SAVE
                , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
                , gtk.STOCK_SAVE, gtk.RESPONSE_OK))
            dialog.set_do_overwrite_confirmation(True)
            filter = gtk.FileFilter()
            filter.set_name("Palabra puzzle files (*.xml)")
            filter.add_pattern("*.xml")
            dialog.add_filter(filter)
            
            dialog.show_all()
            response = dialog.run()
            if response == gtk.RESPONSE_OK:
                filename = dialog.get_filename()
                self.puzzle_manager.current_puzzle.filename = filename
                export_puzzle_to_xml(self.puzzle_manager.current_puzzle)
                self.update_title(self.puzzle_manager.current_puzzle.filename)
            dialog.destroy()
        else:
            export_puzzle_to_xml(self.puzzle_manager.current_puzzle)
        action.stack.distance_from_saved_puzzle = 0
        
    def export_puzzle(self):
        window = ExportWindow(self)
        window.show_all()
        
        response = window.run()
        if response == gtk.RESPONSE_OK:
            window.hide()
            
            options = window.options
            message = verify_output_options(options)
            if message is not None:
                mdialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL
                    , gtk.MESSAGE_INFO, gtk.BUTTONS_NONE, message)
                mdialog.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
                mdialog.run()
                mdialog.destroy()
            else:
                dialog = gtk.FileChooserDialog("Export location"
                    , self
                    , gtk.FILE_CHOOSER_ACTION_SAVE
                    , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
                    , gtk.STOCK_SAVE, gtk.RESPONSE_OK))
                dialog.set_do_overwrite_confirmation(True)
                
                dialog.show_all()
                response = dialog.run()
                if response == gtk.RESPONSE_OK:
                    export_puzzle(self.puzzle_manager.current_puzzle
                        , dialog.get_filename(), options)
                dialog.destroy()
        window.destroy()
    
    def export_as_template(self):
        dialog = gtk.FileChooserDialog("Export as template"
            , self
            , gtk.FILE_CHOOSER_ACTION_SAVE
            , (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
            , gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        dialog.set_do_overwrite_confirmation(True)
        filter = gtk.FileFilter()
        filter.set_name("Palabra template files (*.xml)")
        filter.add_pattern("*.xml")
        dialog.add_filter(filter)
        
        dialog.show_all()
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            grid = self.puzzle_manager.current_puzzle.grid
            filename = dialog.get_filename()
            export_template(grid, filename)
        dialog.destroy()
    
    def load_puzzle(self):
        self.to_edit_panel()
        self.update_window()
    
    def close_puzzle(self):
        need_to_close, need_to_save = self.check_close_puzzle()
        if need_to_close:
            if need_to_save:
                self.save_puzzle(False)
            
            self.puzzle_manager.current_puzzle = None
            action.stack.clear()
            
            self.to_empty_panel()
            self.update_window()

    def check_close_puzzle(self):
        if not self.puzzle_manager.has_puzzle():
            return False, False

        need_to_close = True
        need_to_save = False
        if action.stack.distance_from_saved_puzzle != 0:
            image = gtk.Image()
            image.set_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG)
            dialog = gtk.Dialog("Close puzzle"
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
        item.set_stock_id(gtk.STOCK_EDIT)
        item.set_label("Edit clues")
        item.connect("clicked", lambda item: self.edit_clues())
        item.show()
        item.set_sensitive(False)
        toolbar.insert(item, -1)
        self.puzzle_toggle_items += [item]
        
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
            , "Create a new puzzle"
            , image=gtk.STOCK_NEW
            , accelerator="<Ctrl>N"
            , accel_group=accel_group))
        menu.append(self._create_menu_item(
            lambda item: self.open_puzzle()
            , "Open a puzzle"
            , image=gtk.STOCK_OPEN
            , accelerator="<Ctrl>O"
            , accel_group=accel_group))
        
        menu.append(gtk.SeparatorMenuItem())
        
        menu.append(self._create_menu_item(
            lambda item: self.save_puzzle(False)
            , "Save the current puzzle"
            , image=gtk.STOCK_SAVE
            , accelerator="<Ctrl>S"
            , accel_group=accel_group
            , is_puzzle_sensitive=True))
        menu.append(self._create_menu_item(
            lambda item: self.save_puzzle(True)
            , "Save the current puzzle with a different name"
            , image=gtk.STOCK_SAVE_AS
            , accelerator="<Shift><Ctrl>S"
            , accel_group=accel_group
            , is_puzzle_sensitive=True))
        
        menu.append(gtk.SeparatorMenuItem())
        
        menu.append(self._create_menu_item(
            lambda item: self.export_puzzle()
            , "Export the puzzle to various file formats"
            , title="_Export..."
            , is_puzzle_sensitive=True))
        menu.append(self._create_menu_item(
            lambda item: self.export_as_template()
            , "Save the grid as a template without the words and clues"
            , title="Export as _template..."
            , is_puzzle_sensitive=True))
        
        menu.append(gtk.SeparatorMenuItem())
        
        menu.append(self._create_menu_item(
            lambda item: self.view_puzzle_properties()
            , "View the properties of the current puzzle"
            , image=gtk.STOCK_PROPERTIES
            , is_puzzle_sensitive=True))
        
        menu.append(gtk.SeparatorMenuItem())
        
        menu.append(self._create_menu_item(
            lambda item: self.close_puzzle()
            , "Close the current puzzle"
            , image=gtk.STOCK_CLOSE
            , accelerator="<Ctrl>W"
            , accel_group=accel_group
            , is_puzzle_sensitive=True))
        menu.append(self._create_menu_item(
            lambda item: quit()
            , "Quit the application"
            , image=gtk.STOCK_QUIT
            , accelerator="<Ctrl>Q"
            , accel_group=accel_group))
        
        file_menu = gtk.MenuItem("_File", True)
        file_menu.set_submenu(menu)
        return file_menu
        
    def edit_clues(self):
        editor = ClueEditor(self, self.puzzle_manager.current_puzzle)
        editor.show_all()
        editor.run()
        editor.destroy()

    def resize_grid(self):
        window = SizeWindow(self, self.puzzle_manager.current_puzzle)
        window.show_all()
        response = window.run()
        if response == gtk.RESPONSE_ACCEPT:
            width, height = window.get_size()
            if (self.puzzle_manager.current_puzzle.grid.width != width or
                self.puzzle_manager.current_puzzle.grid.height != height):
                self.transform_grid(transform.resize_grid, width=width, height=height)
                self.editor.refresh_visual_size()
        window.destroy()
        
    def view_preferences(self):
        preferences = PreferencesWindow(self)
        preferences.show_all()
        preferences.run()
        preferences.destroy()
        
    def undo_action(self):
        action.stack.undo_action(self.puzzle_manager.current_puzzle)
        self.update_window()
        
    def redo_action(self):
        action.stack.redo_action(self.puzzle_manager.current_puzzle)
        self.update_window()
        
    def create_edit_menu(self):
        menu = gtk.Menu()
        
        accel_group = gtk.AccelGroup()
        self.add_accel_group(accel_group)
        
        self.undo_menu_item = self._create_menu_item(
            lambda item: self.undo_action()
            , "Undo the last action"
            , image=gtk.STOCK_UNDO
            , accelerator="<Ctrl>Z"
            , accel_group=accel_group)
        self.undo_menu_item.set_sensitive(False)
        menu.append(self.undo_menu_item)
        
        self.redo_menu_item = self._create_menu_item(
            lambda item: self.redo_action()
            , "Redo the last undone action"
            , image=gtk.STOCK_REDO
            , accelerator="<Shift><Ctrl>Z"
            , accel_group=accel_group)
        self.redo_menu_item.set_sensitive(False)
        menu.append(self.redo_menu_item)
        
        menu.append(gtk.SeparatorMenuItem())
        
        menu.append(self._create_menu_item(
            lambda item: self.edit_clues()
            , "Edit clues"
            , title="Edit _clues"
            , is_puzzle_sensitive=True))
        
        menu.append(gtk.SeparatorMenuItem())

        item = self.create_edit_symmetry_menu()
        item.set_sensitive(False)
        self.puzzle_toggle_items += [item]
        menu.append(item)
        
        menu.append(gtk.SeparatorMenuItem())
        
        menu.append(self._create_menu_item(
            lambda item: self.transform_grid(transform.shift_grid_up)
            , "Move the content of the grid up by one square"
            , title="Move content _up"
            , is_puzzle_sensitive=True))
        menu.append(self._create_menu_item(
            lambda item: self.transform_grid(transform.shift_grid_down)
            , "Move the content of the grid down by one square"
            , title="Move content _down"
            , is_puzzle_sensitive=True))
        menu.append(self._create_menu_item(
            lambda item: self.transform_grid(transform.shift_grid_left)
            , "Move the content of the grid left by one square"
            , title="Move content _left"
            , is_puzzle_sensitive=True))
        menu.append(self._create_menu_item(
            lambda item: self.transform_grid(transform.shift_grid_right)
            , "Move the content of the grid right by one square"
            , title="Move content _right"
            , is_puzzle_sensitive=True))
        
        menu.append(gtk.SeparatorMenuItem())
        
        menu.append(self._create_menu_item(
            lambda item: self.resize_grid()
            , "Change the size of the grid"
            , title="_Resize grid"
            , is_puzzle_sensitive=True))
        
        menu.append(gtk.SeparatorMenuItem())
        
        menu.append(self._create_menu_item(
            lambda item: self.perform_selection_based_transform(transform.insert_row_above)
            , "Insert an empty row above this cell"
            , title="Insert row (above)"
            , is_selection_sensitive=True))
        menu.append(self._create_menu_item(
            lambda item: self.perform_selection_based_transform(transform.insert_row_below)
            , "Insert an empty row below this cell"
            , title="Insert row (below)"
            , is_selection_sensitive=True))
        menu.append(self._create_menu_item(
            lambda item: self.perform_selection_based_transform(transform.insert_column_left)
            , "Insert an empty column to the left of this cell"
            , title="Insert column (left)"
            , is_selection_sensitive=True))
        menu.append(self._create_menu_item(
            lambda item: self.perform_selection_based_transform(transform.insert_column_right)
            , "Insert an empty column to the right of this cell"
            , title="Insert column (right)"
            , is_selection_sensitive=True))
        
        menu.append(gtk.SeparatorMenuItem())
        
        menu.append(self._create_menu_item(
            lambda item: self.perform_selection_based_transform(transform.remove_row)
            , "Remove the row containing this cell"
            , title="Remove row"
            , is_selection_sensitive=True
            , condition=lambda puzzle: puzzle.grid.height > 3))
        menu.append(self._create_menu_item(
            lambda item: self.perform_selection_based_transform(transform.remove_column)
            , "Remove the column containing this cell"
            , title="Remove column"
            , is_selection_sensitive=True
            , condition=lambda puzzle: puzzle.grid.width > 3))
        
        menu.append(gtk.SeparatorMenuItem())
        
        menu.append(self._create_menu_item(
            lambda item: self.transform_grid(transform.horizontal_flip)
            , "Flip the content of the grid horizontally and clear the clues"
            , title="Flip _horizontally"
            , is_puzzle_sensitive=True))
        menu.append(self._create_menu_item(
            lambda item: self.transform_grid(transform.vertical_flip)
            , "Flip the content of the grid vertically and clear the clues"
            , title="Flip _vertically"
            , is_puzzle_sensitive=True))
        menu.append(self._create_menu_item(
            lambda item: self.transform_grid(transform.diagonal_flip)
            , "Flip the content of the grid diagonally"
            , title="Flip _diagonally"
            , is_puzzle_sensitive=True))
        
        menu.append(gtk.SeparatorMenuItem())
        
        menu.append(self._create_menu_item(
            lambda item: self.transform_grid(transform.clear_all)
            , "Clear the blocks, the letters and the clues of the puzzle"
            , title="Clear _all"
            , is_puzzle_sensitive=True))
        menu.append(self._create_menu_item(
            lambda item: self.transform_grid(transform.clear_chars)
            , "Clear the letters and the clues of the puzzle"
            , title="Clear _letters"
            , is_puzzle_sensitive=True))
        menu.append(self._create_menu_item(
            lambda item: self.transform_grid(transform.clear_clues)
            , "Clear the clues of the puzzle"
            , title="Clear clu_es"
            , is_puzzle_sensitive=True))
        
        menu.append(gtk.SeparatorMenuItem())
        
        menu.append(self._create_menu_item(
            lambda item: self.view_preferences()
            , "Configure the application"
            , image=gtk.STOCK_PREFERENCES))
                
        edit_menu = gtk.MenuItem("_Edit", True)
        edit_menu.set_submenu(menu)
        return edit_menu
        
    def create_edit_symmetry_menu(self):
        menu = gtk.Menu()
        
        def set_symmetry(options):
            try:
                self.editor.set_symmetry(options)
            except AttributeError:
                pass
        
        activate = lambda item: set_symmetry([])
        select = lambda item: self.update_status(constants.STATUS_MENU
            , "Use no symmetry rules when modifying the grid")
        deselect = lambda item: self.pop_status(constants.STATUS_MENU)
        item = gtk.RadioMenuItem(None, "_None", True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        menu.append(item)
        
        horizontal = ["keep_horizontal_symmetry"]
        activate = lambda item: set_symmetry(horizontal)
        select = lambda item: self.update_status(constants.STATUS_MENU
            , "Use horizontal symmetry when modifying the grid")
        deselect = lambda item: self.pop_status(constants.STATUS_MENU)
        item = gtk.RadioMenuItem(item, "_Horizontal axis", True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        menu.append(item)
        
        vertical = ["keep_vertical_symmetry"]
        activate = lambda item: set_symmetry(vertical)
        select = lambda item: self.update_status(constants.STATUS_MENU
            , "Use vertical symmetry when modifying the grid")
        deselect = lambda item: self.pop_status(constants.STATUS_MENU)
        item = gtk.RadioMenuItem(item, "_Vertical axis", True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        menu.append(item)
        
        both = ["keep_horizontal_symmetry", "keep_vertical_symmetry"]
        activate = lambda item: set_symmetry(both)
        select = lambda item: self.update_status(constants.STATUS_MENU
            , "Use horizontal and vertical symmetry when modifying the grid")
        deselect = lambda item: self.pop_status(constants.STATUS_MENU)
        item = gtk.RadioMenuItem(item, "_Horizontal and vertical", True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        menu.append(item)

        point = ["keep_point_symmetry"]
        activate = lambda item: set_symmetry(point)
        select = lambda item: self.update_status(constants.STATUS_MENU
            , "Use point symmetry when modifying the grid")
        deselect = lambda item: self.pop_status(constants.STATUS_MENU)
        item = gtk.RadioMenuItem(item, "_Point symmetry", True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        item.set_active(True)
        menu.append(item)
        
        symmetry_menu = gtk.MenuItem("_Symmetry", True)
        symmetry_menu.set_submenu(menu)
        return symmetry_menu
        
    def perform_selection_based_transform(self, transform):
        selection = self.get_selection()
        if selection is not None:
            sel_x, sel_y = selection
            self.transform_grid(transform, x=sel_x, y=sel_y)
        
    def transform_grid(self, transform, **args):
        a = transform(self.puzzle_manager.current_puzzle, **args)
        action.stack.push_action(a)
        self.update_window()
        
    def update_window(self):
        puzzle = self.puzzle_manager.current_puzzle
        if puzzle is None:
            self.set_title("Palabra")
            self.pop_status(constants.STATUS_GRID)
        else:
            status = puzzle.grid.determine_status(False)
            message = self.determine_status_message(status)
            self.update_status(constants.STATUS_GRID, message)
            
            selection = self.get_selection()
            if selection is not None:
                sel_x, sel_y = selection
                valid = puzzle.grid.is_valid(sel_x, sel_y)
                
                for item, predicate in self.selection_toggle_items:
                    item.set_sensitive(valid and predicate(puzzle))
                
        for item in self.puzzle_toggle_items:
            item.set_sensitive(puzzle is not None)
                
        self.undo_menu_item.set_sensitive(len(action.stack.undo_stack) > 0)
        self.redo_menu_item.set_sensitive(len(action.stack.redo_stack) > 0)
        self.undo_tool_item.set_sensitive(len(action.stack.undo_stack) > 0)
        self.redo_tool_item.set_sensitive(len(action.stack.redo_stack) > 0)
        
        self.panel.queue_draw()
        
    @staticmethod
    def determine_status_message(status):
        return ''.join(
            ["Words: ", str(status["word_count"]), ", "
            ,"Blocks: ", str(status["block_count"]), " ("
            ,"%.2f" % status["block_percentage"]
            , "%), Letters: ", str(status["char_count"])
            ])
        
    def create_view_menu(self):
        menu = gtk.Menu()
        
        activate = lambda item: self.toggle_toolbar(item)
        select = lambda item: self.update_status(constants.STATUS_MENU
            , "Show or hide the toolbar")
        deselect = lambda item: self.pop_status(constants.STATUS_MENU)
        item = gtk.CheckMenuItem("_Toolbar", True)
        item.set_active(True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        menu.append(item)
        
        activate = lambda item: self.toggle_statusbar(item)
        select = lambda item: self.update_status(constants.STATUS_MENU
            , "Show or hide the statusbar")
        deselect = lambda item: self.pop_status(constants.STATUS_MENU)
        item = gtk.CheckMenuItem("_Statusbar", True)
        item.set_active(True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        menu.append(item)
        
        menu.append(gtk.SeparatorMenuItem())
        
        def toggle_numbers(status):
            view.custom_settings["show_numbers"] = status
            try:
                self.panel.queue_draw()
            except AttributeError:
                pass
        
        activate = lambda item: toggle_numbers(item.active)
        select = lambda item: self.update_status(constants.STATUS_MENU
            , "Show or hide the word numbers in the editor")
        deselect = lambda item: self.pop_status(constants.STATUS_MENU)
        item = gtk.CheckMenuItem("Show _word numbers", True)
        item.connect("activate", activate)
        item.connect("select", select)
        item.connect("deselect", deselect)
        menu.append(item)
        item.set_active(True)
        toggle_numbers(True)
        
        menu.append(gtk.SeparatorMenuItem())
        
        menu.append(self._create_menu_item(
            lambda item: self.edit_appearance()
            , u"Modify the appearance of the puzzle"
            , title=u"Modify _appearance"
            , is_puzzle_sensitive=True))
        
        view_menu = gtk.MenuItem("_View", True)
        view_menu.set_submenu(menu)
        return view_menu
        
    def edit_appearance(self):
        editor = AppearanceDialog(self)
        editor.show_all()
        response = editor.run()
        if response == gtk.RESPONSE_OK:
            appearance = editor.gather_appearance()
            
            view = self.puzzle_manager.current_puzzle.view
            view.properties.tile_size = appearance["tile_size"]
            self.update_window()
        editor.destroy()

    def toggle_toolbar(self, widget):
        if widget.active:
            self.toolbar.show()
        else:
            self.toolbar.hide()        
        
    def toggle_statusbar(self, widget):
        if widget.active:
            self.statusbar.show()
        else:
            self.statusbar.hide()

    def create_help_menu(self):
        menu = gtk.Menu()
        
        menu.append(self._create_menu_item(
            self.on_help_about_activate
            , "About this application"
            , image=gtk.STOCK_ABOUT))
        
        help_menu = gtk.MenuItem("_Help", True)
        help_menu.set_submenu(menu)
        return help_menu
        
    def on_help_about_activate(self, widget, data=None):
        dialog = gtk.AboutDialog()
        dialog.set_title("About Palabra")
        dialog.set_program_name("Palabra")
        dialog.set_comments("Crossword creation software")
        dialog.set_version(constants.VERSION)
        dialog.set_authors(["Simeon Visser"])
        dialog.set_copyright("Copyright 2009 Simeon Visser")
        dialog.set_license("""This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
                
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses/>.""")
        dialog.set_wrap_license(True)
        dialog.set_transient_for(self)
        dialog.connect("response", lambda dialog, response: dialog.destroy())
        dialog.show_all()

def quit():
    gtk.main_quit()
    write_config_file()
