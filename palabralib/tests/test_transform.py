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

from palabralib.puzzle import Puzzle
from palabralib.grid import Grid
import palabralib.transform as transform

class TransformTestCase(unittest.TestCase):
    def setUp(self):
        self.puzzle = Puzzle(Grid(15, 15))
        
    def testClearAll(self):
        self.puzzle.grid.set_block(5, 5, True)
        self.puzzle.grid.set_char(10, 10, u"A")
        
        a = transform.clear_all(self.puzzle)
        self.assertEqual(self.puzzle.grid.is_block(5, 5), False)
        self.assertEqual(self.puzzle.grid.get_char(10, 10), u"")
        
    def testClearChars(self):
        self.puzzle.grid.set_block(5, 5, True)
        self.puzzle.grid.set_char(10, 10, u"A")
        
        a = transform.clear_chars(self.puzzle)
        self.assertEqual(self.puzzle.grid.is_block(5, 5), True)
        self.assertEqual(self.puzzle.grid.get_char(10, 10), u"")
        
    def testClearClues(self):
        self.puzzle.grid.store_clue(0, 0, "across", "text", "foo")
        self.puzzle.grid.set_block(5, 5, True)
        self.puzzle.grid.set_char(10, 10, u"A")
        
        a = transform.clear_clues(self.puzzle)
        self.assertEqual("across" in self.puzzle.grid.get_clues(0, 0), False)
        self.assertEqual(self.puzzle.grid.is_block(5, 5), True)
        self.assertEqual(self.puzzle.grid.get_char(10, 10), u"A")
        
    def testModifyBlocks(self):
        blocks = [(3, 3, True), (4, 4, True)]
        a = transform.modify_blocks(self.puzzle, blocks)
        for x, y, status in blocks:
            self.assertEqual(self.puzzle.grid.is_block(x, y), status)
            
    def testModifyChar(self):
        a = transform.modify_char(self.puzzle, 3, 3, "C")
        self.assertEqual(self.puzzle.grid.get_char(3, 3), "C")
        
    def testModifyClue(self):
        a = transform.modify_clue(self.puzzle, 3, 3, "across", "text", "foo")
        b = transform.modify_clue(self.puzzle, 3, 3, "down", "text", "bar")
        
        clues = self.puzzle.grid.cell(3, 3)["clues"]
        self.assertEqual(clues["across"], {"text": "foo"})
        self.assertEqual(clues["down"], {"text": "bar"})
        
        c = transform.modify_clue(self.puzzle, 3, 3, "down", "text", "")
        self.assertEqual("down" in clues, False)
        
        d = transform.modify_clue(self.puzzle, 3, 3, "down", "text", "foo")
        e = transform.modify_clue(self.puzzle, 3, 3, "down", "explanation", "bar")
        f = transform.modify_clue(self.puzzle, 3, 3, "down", "text", "")
        self.assertEqual(clues["down"], {"explanation": "bar"})        
