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

import unittest

from palabralib.puzzle import Puzzle
from palabralib.grid import Grid
import palabralib.transform as transform

class TransformTestCase(unittest.TestCase):
    def setUp(self):
        self.grid = Grid(15, 15)
        self.puzzle = Puzzle(self.grid)
        
    def testClearAll(self):
        """transform.clear_all removes all content of a puzzle."""
        self.grid.set_block(5, 5, True)
        self.grid.set_char(10, 10, u"A")
        self.grid.set_void(1, 1, True)
        a = transform.clear_all(self.puzzle)
        self.assertEqual(self.grid.is_block(5, 5), False)
        self.assertEqual(self.grid.get_char(10, 10), u"")
        self.assertEqual(self.grid.is_void(1, 1), False)
        
    def testClearChars(self):
        """transform.clear_chars removes all characters of a puzzle."""
        self.grid.set_block(5, 5, True)
        self.grid.set_char(10, 10, u"A")
        
        a = transform.clear_chars(self.puzzle)
        self.assertEqual(self.grid.is_block(5, 5), True)
        self.assertEqual(self.grid.get_char(10, 10), u"")
        
    def testClearClues(self):
        """transform.clear_clues removes all clues of a puzzle."""
        self.grid.store_clue(0, 0, "across", "text", "foo")
        self.grid.set_block(5, 5, True)
        self.grid.set_char(10, 10, u"A")
        
        a = transform.clear_clues(self.puzzle)
        self.assertEqual("across" in self.grid.get_clues(0, 0), False)
        self.assertEqual(self.grid.is_block(5, 5), True)
        self.assertEqual(self.grid.get_char(10, 10), u"A")
        
    def testModifyBlocks(self):
        """transform.modify_blocks modifies the blocks of a puzzle."""
        self.grid.set_block(4, 4, True)
        blocks = [(3, 3, True), (4, 4, False)]
        a = transform.modify_blocks(self.puzzle, blocks)
        for x, y, status in blocks:
            self.assertEqual(self.grid.is_block(x, y), status)
            
    def testModifyChars(self):
        """transform.modify_chars modifies a character of a puzzle."""
        a = transform.modify_chars(self.puzzle, [(3, 3, 'C'), (4, 5, 'D')])
        self.assertEqual(self.grid.get_char(3, 3), "C")
        self.assertEqual(self.grid.get_char(4, 5), "D")
        
    def testModifyClue(self):
        a = transform.modify_clue(self.puzzle, 3, 3, "across", "text", "foo")
        b = transform.modify_clue(self.puzzle, 3, 3, "down", "text", "bar")
        
        clues = self.grid.cell(3, 3)["clues"]
        self.assertEqual(clues["across"], {"text": "foo"})
        self.assertEqual(clues["down"], {"text": "bar"})
        
        c = transform.modify_clue(self.puzzle, 3, 3, "down", "text", "")
        self.assertEqual("down" in clues, False)
        
        d = transform.modify_clue(self.puzzle, 3, 3, "down", "text", "foo")
        e = transform.modify_clue(self.puzzle, 3, 3, "down", "explanation", "bar")
        f = transform.modify_clue(self.puzzle, 3, 3, "down", "text", "")
        self.assertEqual(clues["down"], {"explanation": "bar"})
        
    def testClearBlocks(self):
        """transform.clear_blocks removes all blocks of a puzzle."""
        self.grid.set_block(0, 0, True)
        self.grid.set_block(5, 5, True)
        transform.clear_blocks(self.puzzle)
        self.assertEqual(self.grid.count_blocks(), 0)
    
    def testClearBars(self):
        """transform.clear_bars removes all bars of a puzzle."""
        self.grid.set_bar(3, 3, "top", True)
        self.grid.set_bar(7, 7, "left", True)
        transform.clear_bars(self.puzzle)
        self.assertEqual(self.grid.has_bar(3, 3, "top"), False)
        self.assertEqual(self.grid.has_bar(7, 7, "left"), False)
        
    def testClearVoids(self):
        """transform.clear_voids removes all voids of a puzzle."""
        self.grid.set_void(0, 0, True)
        self.grid.set_void(5, 5, True)
        transform.clear_voids(self.puzzle)
        self.assertEqual(self.grid.count_voids(), 0)
        
    def testReplaceGrid(self):
        """The grid can be replaced completely."""
        p = Puzzle(Grid(15, 15))
        next = Grid(3, 3)
        next.set_block(2, 2, True)
        transform.replace_grid(p, next)
        self.assertEqual(p.grid.size, (3, 3))
        self.assertEqual(p.grid.is_block(2, 2), True)
        
    def testModifyBlocksWithChars(self):
        """When placing one or more blocks, the characters are removed."""
        self.grid.set_char(3, 3, 'A')
        self.grid.set_char(5, 5, 'B')
        transform.modify_blocks(self.puzzle, [(3, 3, True), (5, 5, False)])
        self.assertEqual(self.puzzle.grid.data[3][3]["char"], '')
        self.assertEqual(self.puzzle.grid.data[5][5]["char"], 'B')
