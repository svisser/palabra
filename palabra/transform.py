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

import action
from action import (
    Action,
    FullTransformAction,
)
from grid import (
    Grid,
)

import copy

def _delta_transform(puzzle, undo_function, redo_function):
    redo_function(puzzle)
    
    a = Action()
    a.add_undo_function(undo_function)
    a.add_redo_function(redo_function)

    return a

def _full_transform(puzzle, transform):
    from_grid = copy.deepcopy(puzzle.grid)
    transform(puzzle)
    to_grid = copy.deepcopy(puzzle.grid)
    
    return FullTransformAction(from_grid, to_grid)

def modify_blocks(puzzle, blocks=[]):
    redo_blocks = []
    undo_blocks = []
    for x, y, status in blocks:
        clear_char = status and puzzle.grid.is_char(x, y)
        redo_blocks.append([x, y, status, clear_char])
        undo_blocks.append([x, y, not status, puzzle.grid.get_char(x, y)])
        
    def undo_function(puzzle):
        for x, y, status, char in undo_blocks:
            puzzle.grid.set_char(x, y, char)
            puzzle.grid.set_block(x, y, status)
    def redo_function(puzzle):
        for x, y, status, clear_char in redo_blocks:
            if clear_char:
                puzzle.grid.clear_char(x, y)
            puzzle.grid.set_block(x, y, status)
    return _delta_transform(puzzle, undo_function, redo_function)

def modify_char(puzzle, x, y, next_char):
    transform = lambda puzzle: puzzle.grid.set_char(x, y, next_char)
    return _full_transform(puzzle, transform)

def clear_all(puzzle):
    transform = lambda puzzle: puzzle.grid.clear()
    return _full_transform(puzzle, transform)
    
def clear_chars(puzzle):
    transform = lambda puzzle: puzzle.grid.clear_chars()
    return _full_transform(puzzle, transform)
    
def clear_clues(puzzle):
    transform = lambda puzzle: puzzle.grid.clear_clues()
    return _full_transform(puzzle, transform)
    
def shift_grid_up(puzzle):
    transform = lambda puzzle: puzzle.grid.shift_up()
    return _full_transform(puzzle, transform)
    
def shift_grid_down(puzzle):
    transform = lambda puzzle: puzzle.grid.shift_down()
    return _full_transform(puzzle, transform)

def shift_grid_left(puzzle):
    transform = lambda puzzle: puzzle.grid.shift_left()
    return _full_transform(puzzle, transform)
    
def shift_grid_right(puzzle):
    transform = lambda puzzle: puzzle.grid.shift_right()
    return _full_transform(puzzle, transform)

def resize_grid(puzzle, width, height):
    transform = lambda puzzle: puzzle.grid.resize(width, height)
    return _full_transform(puzzle, transform)
    
def insert_row_above(puzzle, x, y):
    transform = lambda puzzle: puzzle.grid.insert_row(y, True)
    return _full_transform(puzzle, transform)

def insert_row_below(puzzle, x, y):
    transform = lambda puzzle: puzzle.grid.insert_row(y, False)
    return _full_transform(puzzle, transform)
    
def insert_column_left(puzzle, x, y):
    transform = lambda puzzle: puzzle.grid.insert_column(x, True)
    return _full_transform(puzzle, transform)

def insert_column_right(puzzle, x, y):
    transform = lambda puzzle: puzzle.grid.insert_column(x, False)
    return _full_transform(puzzle, transform)

def remove_row(puzzle, x, y):
    transform = lambda puzzle: puzzle.grid.remove_row(y)
    return _full_transform(puzzle, transform)

def remove_column(puzzle, x, y):
    transform = lambda puzzle: puzzle.grid.remove_column(x)
    return _full_transform(puzzle, transform)
