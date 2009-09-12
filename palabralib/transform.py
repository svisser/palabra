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
from action import Action, ClueTransformAction, FullTransformAction
from grid import Grid

import copy

def _delta_transform(puzzle, undo_function, redo_function):
    """Return an Action based on the given undo/redo functions."""
    redo_function(puzzle)
    return Action([undo_function], [redo_function])

def _full_transform(puzzle, transform):
    """
    Return a FullTransformAction based on the given transform function.
    """
    from_grid = copy.deepcopy(puzzle.grid)
    transform(puzzle)
    to_grid = copy.deepcopy(puzzle.grid)
    
    return FullTransformAction(from_grid, to_grid)

def _clue_transform(puzzle, transform, x, y, direction, key):
    """Return a ClueTransformAction based on the given values."""
    from_grid = copy.deepcopy(puzzle.grid)
    transform(puzzle)
    to_grid = copy.deepcopy(puzzle.grid)
    
    return ClueTransformAction(from_grid, to_grid, x, y, direction, key)

def modify_blocks(puzzle, blocks=[]):
    """Modify the blocks and return an Action."""
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

# TODO merge with modify_char
def modify_chars(puzzle, chars):
    def transform(puzzle):
        for x, y, c in chars:
            puzzle.grid.set_char(x, y, c)
    return _full_transform(puzzle, transform)

def modify_char(puzzle, x, y, next_char):
    """Modify the character at the given location and return an Action."""
    transform = lambda puzzle: puzzle.grid.set_char(x, y, next_char)
    return _full_transform(puzzle, transform)
    
def modify_clue(puzzle, x, y, direction, key, value):
    """Store the given clue data at the given (x, y) and direction."""
    transform = lambda puzzle: puzzle.grid.store_clue(x, y, direction, key, value)
    return _clue_transform(puzzle, transform, x, y, direction, key)

def clear_all(puzzle):
    """Clear the content of the grid and return an Action."""
    transform = lambda puzzle: puzzle.grid.clear()
    return _full_transform(puzzle, transform)
    
def clear_bars(puzzle):
    """Clear the bars of the grid and return an Action."""
    transform = lambda puzzle: puzzle.grid.clear_bars()
    return _full_transform(puzzle, transform)

def clear_blocks(puzzle):
    """Clear the blocks of the grid and return an Action."""
    transform = lambda puzzle: puzzle.grid.clear_blocks()
    return _full_transform(puzzle, transform)
    
def clear_chars(puzzle):
    """Clear the characters of the grid and return an Action."""
    transform = lambda puzzle: puzzle.grid.clear_chars()
    return _full_transform(puzzle, transform)
    
def clear_clues(puzzle):
    """Clear the clues of the grid and return an Action."""
    transform = lambda puzzle: puzzle.grid.clear_clues()
    return _full_transform(puzzle, transform)
    
def shift_grid_up(puzzle):
    """Shift the grid's content up and return an Action."""
    transform = lambda puzzle: puzzle.grid.shift_up()
    return _full_transform(puzzle, transform)
    
def shift_grid_down(puzzle):
    """Shift the grid's content down and return an Action."""
    transform = lambda puzzle: puzzle.grid.shift_down()
    return _full_transform(puzzle, transform)

def shift_grid_left(puzzle):
    """Shift the grid's content left and return an Action."""
    transform = lambda puzzle: puzzle.grid.shift_left()
    return _full_transform(puzzle, transform)
    
def shift_grid_right(puzzle):
    """Shift the grid's content right and return an Action."""
    transform = lambda puzzle: puzzle.grid.shift_right()
    return _full_transform(puzzle, transform)

def resize_grid(puzzle, width, height):
    """Resize the grid and return an Action."""
    transform = lambda puzzle: puzzle.grid.resize(width, height)
    return _full_transform(puzzle, transform)
    
def insert_row_above(puzzle, x, y):
    """Insert a row above the given location and return an Action."""
    transform = lambda puzzle: puzzle.grid.insert_row(y, True)
    return _full_transform(puzzle, transform)

def insert_row_below(puzzle, x, y):
    """Insert a row below the given location and return an Action."""
    transform = lambda puzzle: puzzle.grid.insert_row(y, False)
    return _full_transform(puzzle, transform)
    
def insert_column_left(puzzle, x, y):
    """Insert a column left of the given location and return an Action."""
    transform = lambda puzzle: puzzle.grid.insert_column(x, True)
    return _full_transform(puzzle, transform)

def insert_column_right(puzzle, x, y):
    """Insert a column right of the given location and return an Action."""
    transform = lambda puzzle: puzzle.grid.insert_column(x, False)
    return _full_transform(puzzle, transform)

def remove_row(puzzle, x, y):
    """Remove a row and return an Action."""
    transform = lambda puzzle: puzzle.grid.remove_row(y)
    return _full_transform(puzzle, transform)

def remove_column(puzzle, x, y):
    """Remove a column and return an Action."""
    transform = lambda puzzle: puzzle.grid.remove_column(x)
    return _full_transform(puzzle, transform)
    
def horizontal_flip(puzzle):
    """Flip the grid horizontally and return an Action."""
    transform = lambda puzzle: puzzle.grid.horizontal_flip()
    return _full_transform(puzzle, transform)
    
def vertical_flip(puzzle):
    """Flip the grid vertically and return an Action."""
    transform = lambda puzzle: puzzle.grid.vertical_flip()
    return _full_transform(puzzle, transform)
    
def diagonal_flip(puzzle):
    """Flip the grid diagonally and return and Action."""
    transform = lambda puzzle: puzzle.grid.diagonal_flip()
    return _full_transform(puzzle, transform)
