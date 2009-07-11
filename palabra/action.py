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

from grid import (
    Grid,
)
import preferences

class Action():
    def __init__(self, undo_functions=None, redo_functions=None):
        if undo_functions is None:
            undo_functions = []
        self.undo_functions = undo_functions
        if redo_functions is None:
            redo_functions = []
        self.redo_functions = redo_functions
        
    def add_undo_function(self, function):
        self.undo_functions.append(function)
        
    def add_redo_function(self, function):
        self.redo_functions.append(function)

    def perform_undo(self, puzzle):
        for f in self.undo_functions:
            f(puzzle)
            
    def perform_redo(self, puzzle):
        for f in self.redo_functions:
            f(puzzle)

class FullTransformAction(Action):
    def __init__(self, from_grid, to_grid):
        Action.__init__(self)
        self.from_grid = from_grid
        self.to_grid = to_grid
        self.size_changed = \
            from_grid.width != to_grid.width or \
            from_grid.height != to_grid.height
        
    def perform_undo(self, puzzle):
        Action.perform_undo(self, puzzle)
        self._perform_action(puzzle, self.from_grid)
        
    def perform_redo(self, puzzle):
        Action.perform_redo(self, puzzle)
        self._perform_action(puzzle, self.to_grid)
        
    def _perform_action(self, puzzle, source_grid):
        if self.size_changed:
            puzzle.grid.initialize(source_grid.width, source_grid.height)
        for y in range(source_grid.height):
            for x in range(source_grid.width):
                puzzle.grid.set_cell(x, y, source_grid.cell(x, y))

class ActionStack:
    def __init__(self):
        self.clear()
        
    def push_action(self, action):
        if preferences.prefs["undo_use_finite_buffer"] and \
            len(self.undo_stack) >= preferences.prefs["undo_buffer_size"]:
            self.undo_stack = self.undo_stack[1:]
        self.undo_stack.append(action)
        self.redo_stack = []
        self.distance_from_saved_puzzle += 1
        
    def undo_action(self, puzzle):
        if len(self.undo_stack) > 0:
            a = self.undo_stack.pop()
            a.perform_undo(puzzle)
            
            if len(self.undo_stack) > 0:
                b = self.undo_stack.pop()
                b.perform_redo(puzzle)
                self.undo_stack.append(b)
                
            self.distance_from_saved_puzzle -= 1
            
            if preferences.prefs["undo_use_finite_buffer"] and \
                len(self.redo_stack) >= preferences.prefs["undo_buffer_size"]:
                self.redo_stack = self.redo_stack[1:]
            self.redo_stack.append(a)
            
    def redo_action(self, puzzle):
        if len(self.redo_stack) > 0:
            a = self.redo_stack.pop()
            a.perform_redo(puzzle)
            
            self.distance_from_saved_puzzle += 1
            
            if preferences.prefs["undo_use_finite_buffer"] and \
                len(self.undo_stack) >= preferences.prefs["undo_buffer_size"]:
                self.undo_stack = self.undo_stack[1:]
            self.undo_stack.append(a)
    
    def cap_stack(self, max_size):
        if len(self.undo_stack) > max_size:
            self.undo_stack = self.undo_stack[-max_size:]
        if len(self.redo_stack) > max_size:
            self.redo_stack = self.redo_stack[-max_size:]
            
    def clear(self):
        self.undo_stack = []
        self.redo_stack = []
        
        # non-zero = puzzle has unsaved changes
        self.distance_from_saved_puzzle = 0

stack = ActionStack()
