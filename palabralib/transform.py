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

import constants
from grid import Grid

import copy

def replace_grid(puzzle, grid):
    """Completely replace the puzzle's grid by the specified grid."""
    puzzle.grid = grid

def modify_blocks(puzzle, blocks=[]):
    """Modify the blocks."""
    for x, y, status in blocks:
        if status and puzzle.grid.is_char(x, y):
            puzzle.grid.clear_char(x, y)
        puzzle.grid.set_block(x, y, status)

def modify_chars(puzzle, chars):
    # intuition says this should be constants.TRANSFORM_CONTENT but slight
    # hack to make update_window also recompute the status message when
    # adding/removing characters
    modify_chars.__setattr__('type', constants.TRANSFORM_STRUCTURE)
    """Modify the characters at the given locations."""
    for x, y, c in chars:
        puzzle.grid.set_char(x, y, c)

def modify_char(puzzle, x, y, next_char):
    """Modify the character at the given location."""
    modify_char.__setattr__('type', constants.TRANSFORM_CONTENT)
    modify_chars(puzzle, [(x, y, next_char)])
    
def modify_clue(puzzle, x, y, direction, key, value):
    """Store the given clue data at the given (x, y) and direction."""
    modify_clue.__setattr__('type', constants.TRANSFORM_CONTENT)
    puzzle.grid.store_clue(x, y, direction, key, value)

def clear_all(puzzle):
    """Clear the content of the grid."""
    puzzle.grid.clear()
    
def clear_bars(puzzle):
    """Clear the bars of the grid."""
    puzzle.grid.clear_bars()

def clear_blocks(puzzle):
    """Clear the blocks of the grid."""
    puzzle.grid.clear_blocks()

def clear_voids(puzzle):
    """Clear the voids of the grid."""
    puzzle.grid.clear_voids()
    
def clear_chars(puzzle):
    """Clear the characters of the grid."""
    puzzle.grid.clear_chars()
    
def clear_clues(puzzle):
    """Clear the clues of the grid."""
    puzzle.grid.clear_clues()
    
def shift_grid_up(puzzle):
    """Shift the grid's content up."""
    puzzle.grid.shift_up()
    
def shift_grid_down(puzzle):
    """Shift the grid's content down."""
    puzzle.grid.shift_down()

def shift_grid_left(puzzle):
    """Shift the grid's content left."""
    puzzle.grid.shift_left()
    
def shift_grid_right(puzzle):
    """Shift the grid's content right."""
    puzzle.grid.shift_right()

def resize_grid(puzzle, width, height):
    """Resize the grid."""
    puzzle.grid.resize(width, height)
    
def insert_row_above(puzzle, x, y):
    """Insert a row above the given location."""
    puzzle.grid.insert_row(y, True)

def insert_row_below(puzzle, x, y):
    """Insert a row below the given location."""
    puzzle.grid.insert_row(y, False)
    
def insert_column_left(puzzle, x, y):
    """Insert a column left of the given location."""
    puzzle.grid.insert_column(x, True)

def insert_column_right(puzzle, x, y):
    """Insert a column right of the given location."""
    puzzle.grid.insert_column(x, False)

def remove_row(puzzle, x, y):
    """Remove a row."""
    puzzle.grid.remove_row(y)

def remove_column(puzzle, x, y):
    """Remove a column."""
    puzzle.grid.remove_column(x)
    
def horizontal_flip(puzzle):
    """Flip the grid horizontally."""
    puzzle.grid.horizontal_flip()
    
def vertical_flip(puzzle):
    """Flip the grid vertically."""
    puzzle.grid.vertical_flip()
    
def diagonal_flip(puzzle):
    """Flip the grid diagonally and return and Action."""
    puzzle.grid.diagonal_flip()
