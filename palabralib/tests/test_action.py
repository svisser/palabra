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

import copy
import unittest

from action import FullTransformAction
from grid import Grid
from puzzle import Puzzle

class ActionTestCase(unittest.TestCase):
    def setUp(self):
        self.puzzle = Puzzle(Grid(15, 15))
        
    def testFullTransformAction(self):
        self.puzzle.grid.set_block(1, 1, True)
        cur_grid = copy.deepcopy(self.puzzle.grid)
        
        self.puzzle.grid.set_block(5, 5, True)
        self.puzzle.grid.set_char(3, 3, "Q")
        next_grid = copy.deepcopy(self.puzzle.grid)
        
        a = FullTransformAction(cur_grid, next_grid)
            
        a.perform_redo(self.puzzle)
        self.assertEqual(self.puzzle.grid.get_char(3, 3), "Q")
        self.assertEqual(self.puzzle.grid.is_block(5, 5), True)
        self.assertEqual(self.puzzle.grid.is_block(1, 1), True)
        
        a.perform_undo(self.puzzle)
        self.assertEqual(self.puzzle.grid.get_char(3, 3), "")
        self.assertEqual(self.puzzle.grid.is_block(5, 5), False)
        self.assertEqual(self.puzzle.grid.is_block(1, 1), True)
