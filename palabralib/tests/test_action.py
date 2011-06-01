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

import copy
import unittest

from palabralib.action import State, StateStack
from palabralib.grid import Grid
from palabralib.puzzle import Puzzle

class ActionTestCase(unittest.TestCase):
    def setUp(self):
        self.grid = Grid(15, 15)
        self.puzzle = Puzzle(self.grid)
        self.stack = StateStack()
        
    def testDistance(self):
        self.assertEqual(self.stack.distance_from_saved, 0)
        self.stack.push(State(self.grid), initial=True)
        self.assertEqual(self.stack.distance_from_saved, 0)
        for i in xrange(1, 10):
            self.stack.push(State(self.grid))
            self.assertEqual(self.stack.distance_from_saved, i)
            
    def testDistanceUndo(self):
        self.stack.push(State(self.grid), initial=True)
        for i in xrange(10):
            self.stack.push(State(self.grid))
        for i in xrange(10):
            self.stack.undo(self.puzzle)
            self.assertEqual(self.stack.distance_from_saved, 9 - i)
            
    def testUndoRedo(self):
        self.stack.push(State(self.grid), initial=True)
        self.grid.set_block(0, 0, True)
        self.stack.push(State(self.grid))
        self.assertEqual(self.puzzle.grid.is_block(0, 0), True)
        self.stack.undo(self.puzzle)
        self.assertEqual(self.puzzle.grid.is_block(0, 0), False)
        self.stack.redo(self.puzzle)
        self.assertEqual(self.puzzle.grid.is_block(0, 0), True)
        
    def testPeek(self):
        self.assertEqual(self.stack.peek(), None)
        self.stack.push(State(self.grid), initial=True)
        self.assertTrue(self.stack.peek() is not None)
        
    def testHasUndo(self):
        self.stack.push(State(self.grid), initial=True)
        self.assertEqual(self.stack.has_undo(), False)
        for i in xrange(10):
            self.stack.push(State(self.grid))
            self.assertEqual(self.stack.has_undo(), True)
            
    def testHasRedo(self):
        self.stack.push(State(self.grid), initial=True)
        self.assertEqual(self.stack.has_redo(), False)
        for i in xrange(10):
            self.stack.push(State(self.grid))
            self.assertEqual(self.stack.has_redo(), False)
        self.stack.undo(self.puzzle)
        self.assertEqual(self.stack.has_redo(), True)
        self.stack.redo(self.puzzle)
        self.assertEqual(self.stack.has_redo(), False)
        
    def testUndoGrid(self):
        self.stack.push(State(self.grid), initial=True)
        self.grid.set_char(0, 0, 'A')
        self.grid.set_block(1, 0, True)
        self.grid.set_void(2, 0, True)
        self.stack.push(State(self.grid))
        self.assertEqual(self.puzzle.grid, self.grid)
        self.stack.undo(self.puzzle)
        self.assertEqual(self.puzzle.grid, Grid(15, 15))
        
    def testUndoGridMultiple(self):
        self.stack.push(State(self.grid), initial=True)
        self.grid.set_char(0, 0, 'A')
        self.stack.push(State(self.grid))
        self.grid.set_block(1, 0, True)
        self.stack.push(State(self.grid))
        self.grid.set_void(2, 0, True)
        self.stack.push(State(self.grid))
        self.stack.undo(self.puzzle)
        self.assertEqual(self.puzzle.grid.is_void(2, 0), False)
        self.assertEqual(self.puzzle.grid.is_block(1, 0), True)
        self.assertEqual(self.puzzle.grid.get_char(0, 0), 'A')
        self.stack.undo(self.puzzle)
        self.assertEqual(self.puzzle.grid.is_void(2, 0), False)
        self.assertEqual(self.puzzle.grid.is_block(1, 0), False)
        self.assertEqual(self.puzzle.grid.get_char(0, 0), 'A')
        self.stack.undo(self.puzzle)
        self.assertEqual(self.puzzle.grid, Grid(15, 15))
        
    def testUndoRedoMultiple(self):
        self.stack.push(State(self.grid), initial=True)
        for i in xrange(10):
            self.grid.set_block(i, i, True)
            self.stack.push(State(self.grid))
        for i in xrange(5):
            self.stack.undo(self.puzzle)
        self.assertEqual(self.puzzle.grid.count_blocks(), 5)
        for i in xrange(5):
            self.stack.redo(self.puzzle)
        self.assertEqual(self.puzzle.grid.count_blocks(), 10)
        
    def testMergeClueActions(self):
        """Repeated clue modifications to the same slot are merged."""
        self.stack.push(State(self.grid), initial=True)
        self.grid.data[0][0]["clues"]["across"] = {"text": "Bla"}
        self.stack.push(State(self.grid, clue_slot=(0, 0, 'across')))
        self.grid.data[0][0]["clues"]["across"] = {"text": "Blalala"}
        self.stack.push(State(self.grid, clue_slot=(0, 0, 'across')))
        self.assertEqual(len(self.stack.undo_stack), 2)
        self.stack.undo(self.puzzle)
        self.assertEqual(self.puzzle.grid.data[0][0]["clues"], {})
        self.stack.redo(self.puzzle)
        self.assertEqual(self.puzzle.grid.data[0][0]["clues"], {"across": {"text": "Blalala"}})
