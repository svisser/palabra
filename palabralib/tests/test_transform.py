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

import unittest

import transform
from puzzle import Puzzle
from grid import Grid

class TransformTestCase(unittest.TestCase):
    def setUp(self):
        self.puzzle = Puzzle(Grid(15, 15))
        self.puzzle.grid.set_block(0, 0, True)
        
    def testClearAll(self):
        self.puzzle.grid.set_block(5, 5, True)
        self.puzzle.grid.set_char(10, 10, u"A")
        
        a = transform.clear_all(self.puzzle)
        a.perform_redo(self.puzzle)
        self.assertEquals(self.puzzle.grid.is_block(5, 5), False)
        self.assertEquals(self.puzzle.grid.get_char(10, 10), u"")
        
    def testClearChars(self):
        self.puzzle.grid.set_block(5, 5, True)
        self.puzzle.grid.set_char(10, 10, u"A")
        
        a = transform.clear_chars(self.puzzle)
        a.perform_redo(self.puzzle)
        self.assertEquals(self.puzzle.grid.is_block(5, 5), True)
        self.assertEquals(self.puzzle.grid.get_char(10, 10), u"")
        
    def testClearClues(self):
        self.puzzle.grid.store_clue(0, 0, "across", "text", "foo")
        self.puzzle.grid.set_block(5, 5, True)
        self.puzzle.grid.set_char(10, 10, u"A")
        
        a = transform.clear_clues(self.puzzle)
        a.perform_redo(self.puzzle)
        self.assertEquals("across" in self.puzzle.grid.get_clues(0, 0), False)
        self.assertEquals(self.puzzle.grid.is_block(5, 5), True)
        self.assertEquals(self.puzzle.grid.get_char(10, 10), u"A")
