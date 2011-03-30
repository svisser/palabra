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

from palabralib.action import Action, ActionStack, FullTransformAction
from palabralib.grid import Grid
from palabralib.puzzle import Puzzle
import palabralib.preferences as preferences

class ActionTestCase(unittest.TestCase):
    def setUp(self):
        self.puzzle = Puzzle(Grid(15, 15))
        
    def testActionSingle(self):
        u = lambda puzzle: puzzle.grid.set_block(0, 0, False)
        r = lambda puzzle: puzzle.grid.set_block(0, 0, True)
        a = Action([u], [r])
        
        a.perform_redo(self.puzzle)
        self.assertEqual(self.puzzle.grid.is_block(0, 0), True)
        a.perform_undo(self.puzzle)
        self.assertEqual(self.puzzle.grid.is_block(0, 0), False)
        
        u2 = lambda puzzle: puzzle.grid.set_char(5, 5, "")
        r2 = lambda puzzle: puzzle.grid.set_char(5, 5, "A")
        b = Action([u, u2], [r, r2])
        
        b.perform_redo(self.puzzle)
        self.assertEqual(self.puzzle.grid.is_block(0, 0), True)
        self.assertEqual(self.puzzle.grid.get_char(5, 5), "A")
        b.perform_undo(self.puzzle)
        self.assertEqual(self.puzzle.grid.get_char(5, 5), "")
        
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

class ActionStackTestCase(unittest.TestCase):
    def setUp(self):
        self.stack = ActionStack()
        self.puzzle = Puzzle(Grid(15, 15))
        
    @staticmethod
    def createAction():
        u = lambda puzzle: puzzle.grid.set_block(0, 0, False)
        r = lambda puzzle: puzzle.grid.set_block(0, 0, True)
        return Action([u], [r])
        
    @staticmethod
    def createActionTwo():
        u = lambda puzzle: puzzle.grid.set_char(5, 5, "")
        r = lambda puzzle: puzzle.grid.set_char(5, 5, "A")
        return Action([u], [r])
        
    def testClear(self):
        a = self.createAction()
        
        preferences.prefs["undo_use_finite_stack"] = True
        preferences.prefs["undo_stack_size"] = 5
        
        for x in xrange(5):
            self.stack.push_action(a)
        self.assertEqual(len(self.stack.undo_stack), 5)
        self.assertEqual(len(self.stack.redo_stack), 0)
        self.assertEqual(self.stack.distance_from_saved_puzzle, 5)
        self.stack.clear()
        self.assertEqual(len(self.stack.undo_stack), 0)
        self.assertEqual(len(self.stack.redo_stack), 0)
        self.assertEqual(self.stack.distance_from_saved_puzzle, 0)
        
    def testPushAction(self):
        a = self.createAction()
        
        preferences.prefs["undo_use_finite_stack"] = True
        preferences.prefs["undo_stack_size"] = 10
        self.stack.push_action(a)
        self.assertEqual(len(self.stack.undo_stack), 1)
        for i in xrange(25):
            self.stack.push_action(a)
        self.assertEqual(len(self.stack.undo_stack), 10)
        
        preferences.prefs["undo_use_finite_stack"] = False
        for i in xrange(25):
            self.stack.push_action(a)
        self.assertEqual(len(self.stack.undo_stack), 35)
        
    def testUnitStack(self):
        a = self.createAction()
        a.perform_redo(self.puzzle)
        b = self.createActionTwo()
        b.perform_redo(self.puzzle)
        
        preferences.prefs["undo_use_finite_stack"] = True
        preferences.prefs["undo_stack_size"] = 1
        self.stack.push_action(a)
        self.stack.push_action(b)
        self.stack.undo_action(self.puzzle)
        self.stack.undo_action(self.puzzle)
        self.assertEqual(self.puzzle.grid.is_block(0, 0), True)
        self.stack.redo_action(self.puzzle)
        self.assertEqual(self.puzzle.grid.get_char(5, 5), "A")
        
    def testUndoRedoAction(self):
        a = self.createAction()
        a.perform_redo(self.puzzle)
        
        preferences.prefs["undo_use_finite_stack"] = True
        preferences.prefs["undo_stack_size"] = 5
        self.stack.push_action(a)
        
        self.stack.undo_action(self.puzzle)
        self.assertEqual(self.puzzle.grid.is_block(0, 0), False)
        self.assertEqual(len(self.stack.undo_stack), 0)
        self.assertEqual(len(self.stack.redo_stack), 1)
        
        self.stack.redo_action(self.puzzle)
        self.assertEqual(self.puzzle.grid.is_block(0, 0), True)
        self.assertEqual(len(self.stack.undo_stack), 1)
        self.assertEqual(len(self.stack.redo_stack), 0)
        
    def testUndoRedoActionFiniteStack(self):
        a = self.createAction()
        
        preferences.prefs["undo_stack_size"] = 5
        
        preferences.prefs["undo_use_finite_stack"] = False
        for x in xrange(10):
            self.stack.push_action(a)
        self.assertEqual(len(self.stack.undo_stack), 10)
        
        preferences.prefs["undo_use_finite_stack"] = True
        for x in xrange(5):
            self.stack.undo_action(self.puzzle)
        self.assertEqual(len(self.stack.undo_stack), 5)
        self.assertEqual(len(self.stack.redo_stack), 5)
        
        self.stack.undo_action(self.puzzle)
        self.assertEqual(len(self.stack.undo_stack), 4)
        self.assertEqual(len(self.stack.redo_stack), 5)
        
    def testCapStack(self):
        a = self.createAction()
        
        preferences.prefs["undo_use_finite_stack"] = False
        preferences.prefs["undo_stack_size"] = 10
        for x in xrange(100):
            self.stack.push_action(a)
        for i in xrange(50):
            self.stack.undo_action(self.puzzle)
        self.assertEqual(len(self.stack.undo_stack), 50)
        self.assertEqual(len(self.stack.redo_stack), 50)
        
        self.stack.cap_stack(25)
        self.assertEqual(len(self.stack.undo_stack), 25)
        self.assertEqual(len(self.stack.redo_stack), 25)
        
    def testDistance(self):
        a = self.createAction()
        b = self.createActionTwo()
        
        preferences.prefs["undo_use_finite_stack"] = False
        preferences.prefs["undo_stack_size"] = 1
        self.assertEqual(self.stack.distance_from_saved_puzzle, 0)
        self.stack.push_action(a)
        self.stack.push_action(b)
        self.assertEqual(self.stack.distance_from_saved_puzzle, 2)
        self.stack.undo_action(self.puzzle)
        self.assertEqual(self.stack.distance_from_saved_puzzle, 1)
        self.stack.redo_action(self.puzzle)
        self.assertEqual(self.stack.distance_from_saved_puzzle, 2)
        self.stack.clear()
        self.assertEqual(self.stack.distance_from_saved_puzzle, 0)
