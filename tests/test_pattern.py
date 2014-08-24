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

from palabralib.grid import Grid
import palabralib.pattern as pattern

class PatternTestCase(unittest.TestCase):
    def setUp(self):
        self.grid = Grid(15, 15)
        
    def testApplyPattern(self):
        """A pattern consists of blocks, voids and bars."""
        pat = pattern.Pattern()
        pat.blocks = [(0, 0)]
        pat.voids = [(5, 5)]
        pat.bars = [(7, 7, "top")]
        pattern.apply_pattern(self.grid, pat)
        self.assertEqual(self.grid.is_block(0, 0), True)
        self.assertEqual(self.grid.is_void(5, 5), True)
        self.assertEqual(self.grid.has_bar(7, 7, "top"), True)
        
    def testTilePatternTopLeft(self):
        """A tiled pattern from (0, 0) has 64 blocks."""
        pat = pattern.tile_from_cell(15, 15, 0, 0)
        self.assertEqual(len(pat.blocks), 8 * 8)
        self.assertEqual(len(pat.voids), 0)
        self.assertEqual(len(pat.bars), 0)
        for x, y in pat.blocks:
            self.assertTrue(y % 2 == 0)
            self.assertTrue(x % 2 == 0)
            
    def testTilePatternOneZero(self):
        """A tiled pattern from (1, 0) has 56 blocks."""
        pat = pattern.tile_from_cell(15, 15, 1, 0)
        self.assertEqual(len(pat.blocks), 7 * 8)
        self.assertEqual(len(pat.voids), 0)
        self.assertEqual(len(pat.bars), 0)
        for x, y in pat.blocks:
            self.assertTrue(y % 2 == 0)
            self.assertTrue(x % 2 == 1)
            
    def testFillWithContentBlocks(self):
        """An entire grid can be filled with blocks."""
        pat = pattern.fill_with_content(15, 15, "block")
        self.assertEqual(pat.voids, [])
        self.assertEqual(pat.bars, [])
        for cell in self.grid.cells():
            self.assertTrue(cell in pat.blocks)
            
    def testFillWithContentVoids(self):
        """An entire grid can be filled with voids."""
        pat = pattern.fill_with_content(15, 15, "void")
        self.assertEqual(pat.blocks, [])
        self.assertEqual(pat.bars, [])
        for cell in self.grid.cells():
            self.assertTrue(cell in pat.voids)
