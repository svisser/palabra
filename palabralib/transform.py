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
from puzzle import Puzzle

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

def modify_chars(content, chars):
    # intuition says this should be constants.TRANSFORM_CONTENT but slight
    # hack to make update_window also recompute the status message when
    # adding/removing characters
    modify_chars.__setattr__('type', constants.TRANSFORM_STRUCTURE)
    """Modify the characters at the given locations (content = Puzzle or Grid)."""
    g = content.grid if isinstance(content, Puzzle) else content
    for x, y, c in chars:
        g.set_char(x, y, c)

def modify_char(puzzle, x, y, next_char):
    """Modify the character at the given location."""
    # for explanation of type, see modify_chars
    modify_char.__setattr__('type', constants.TRANSFORM_STRUCTURE)
    modify_chars(puzzle, [(x, y, next_char)])
    
def modify_clue(puzzle, x, y, direction, key, value):
    """Store the given clue data at the given (x, y) and direction."""
    modify_clue.__setattr__('type', constants.TRANSFORM_CONTENT)
    puzzle.grid.store_clue(x, y, direction, key, value)

clear_all = lambda p: p.grid.clear()
clear_bars = lambda p: p.grid.clear_bars()
clear_blocks = lambda p: p.grid.clear_blocks()
clear_voids = lambda p: p.grid.clear_voids()
clear_chars = lambda p: p.grid.clear_chars()
clear_clues = lambda p: p.grid.clear_clues()
shift_grid_up = lambda p: p.grid.shift_up()
shift_grid_down = lambda p: p.grid.shift_down()
shift_grid_left = lambda p: p.grid.shift_left()
shift_grid_right = lambda p: p.grid.shift_right()
resize_grid = lambda p, width, height: p.grid.resize(width, height)
insert_row_above = lambda p, x, y: p.grid.insert_row(y, True)
insert_row_below = lambda p, x, y: p.grid.insert_row(y, False)
insert_column_left = lambda p, x, y: p.grid.insert_column(x, True)
insert_column_right = lambda p, x, y: p.grid.insert_column(x, False)
remove_row = lambda p, x, y: p.grid.remove_row(y)
remove_column = lambda p, x, y: p.grid.remove_column(x)
horizontal_flip = lambda p: p.grid.horizontal_flip()
vertical_flip = lambda p: p.grid.vertical_flip()
diagonal_flip = lambda p: p.grid.diagonal_flip()
