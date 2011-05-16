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

import palabralib.constants as constants
from palabralib.grid import Grid, decompose_word
from palabralib.puzzle import Puzzle

class PuzzleTestCase(unittest.TestCase):
    def setUp(self):
        self.puzzle = Puzzle(Grid(14, 14))
        
    def testEquality(self):
        self.assertEquals(self.puzzle, Puzzle(Grid(14, 14)))
        self.assertNotEquals(self.puzzle, None)
        self.assertEquals(self.puzzle != None, True)
        
    def testEquality2(self):
        p = Puzzle(Grid(14, 14))
        self.puzzle.type = "FOO"
        p.type = "FOO2"
        self.assertNotEquals(self.puzzle, p)
        
    def testEquality3(self):
        p = Puzzle(Grid(14, 14))
        self.puzzle.filename = "BLA"
        p.filename = "BLA2"
        self.assertNotEquals(self.puzzle, p)
    
    def testEquality4(self):
        p = Puzzle(Grid(14, 14))
        self.puzzle.metadata["title"] = "This is the title"
        p.metadata["title"] = "This is a different title"
        self.assertNotEquals(self.puzzle, p)
        
    def testEquality5(self):
        p = Puzzle(Grid(14, 14))
        self.puzzle.notepad = "BAR"
        p.notepad = "BAR2"
        self.assertNotEquals(self.puzzle, p)
        
    def testEquality6(self):
        p = Puzzle(Grid(14, 14))
        p.grid = Grid(30, 30)
        self.assertNotEquals(self.puzzle, p)

class GridTestCase(unittest.TestCase):
    def setUp(self):
        self.grid = Grid(12, 15)
        self.square_grid = Grid(15, 15)
        
    def testEquality(self):
        self.assertEquals(self.grid, Grid(12, 15))
        self.assertNotEquals(self.grid, None)
        self.assertEquals(self.grid != None, True)
        self.assertNotEquals(self.grid, Grid(13, 15))
        self.assertNotEquals(self.grid, Grid(12, 16))
        grid2 = Grid(12, 15)
        grid2.set_block(5, 5, True)
        self.assertNotEquals(self.grid, grid2)
        
    def testBasicSize(self):
        """Basic functionality - size."""
        self.assertEqual(self.grid.width, 12)
        self.assertEqual(self.grid.height, 15)
        
    def testNumber(self):
        self.grid.set_number(5, 5, 20)
        self.assertEquals(self.grid.get_number(5, 5), 20)

    def testBasicBlock(self):
        """Basic functionality - blocks."""
        self.assertEqual(self.grid.is_block(5, 5), False)
        self.grid.set_block(5, 5, True)
        self.assertEqual(self.grid.is_block(5, 5), True)
        self.grid.set_block(5, 5, False)
        self.assertEqual(self.grid.is_block(5, 5), False)
        
    def testBasicChar(self):
        """Basic functionality - chars."""
        self.assertEqual(self.grid.get_char(5, 5), "")
        self.assertEqual(self.grid.is_char(5, 5), False)
        self.grid.set_char(5, 5, "A")
        self.assertEqual(self.grid.get_char(5, 5), "A")
        self.assertEqual(self.grid.is_char(5, 5), True)
        self.grid.set_char(5, 5, "")
        self.assertEqual(self.grid.get_char(5, 5), "")
        self.assertEqual(self.grid.is_char(5, 5), False)
        
    def testBasicBar(self):
        """Basic functionality - bars."""
        self.assertEqual(self.grid.has_bar(3, 3, "top"), False)
        self.grid.set_bar(3, 3, "top", True)
        self.assertEqual(self.grid.has_bar(3, 3, "top"), True)
        self.grid.set_bar(3, 3, "top", False)
        self.assertEqual(self.grid.has_bar(3, 3, "top"), False)
        
    def testBasicVoid(self):
        """Basic functionality - voids."""
        self.assertEqual(self.grid.is_void(0, 0), False)
        self.grid.set_void(0, 0, True)
        self.assertEqual(self.grid.is_void(0, 0), True)
        self.grid.set_void(0, 0, False)
        self.assertEqual(self.grid.is_void(0, 0), False)
        self.grid.set_void(5, 5, True)
        self.grid.set_block(5, 5, True)
        self.assertEquals(self.grid.is_void(5, 5), False)
        
    def testIsValid(self):
        """A cell is valid when its coordinates are within bounds."""
        for j in xrange(self.grid.height):
            for i in xrange(self.grid.width):
                self.assertEquals(self.grid.is_valid(i, j), True)
        self.assertEquals(self.grid.is_valid(-1, 1), False)
        self.assertEquals(self.grid.is_valid(1, -1), False)
        self.assertEquals(self.grid.is_valid(100, 1), False)
        self.assertEquals(self.grid.is_valid(1, 100), False)
    
    def testIsStartWordInvalidCell(self):
        """An invalid cell cannot be the start of a word."""
        self.assertEquals(self.grid.is_start_word(-1, 0), False)
        self.assertEquals(self.grid.is_start_word(0, -1), False)
        self.assertEquals(self.grid.is_start_word(self.grid.width + 10, 0), False)
        self.assertEquals(self.grid.is_start_word(0, self.grid.height + 10), False)
        
    def testIsStartHorizontalWordOne(self):
        """A single cell (ended by a block) is not a horizontal word."""
        self.assertEqual(self.grid.is_start_word(0, 0, "across"), True)
        self.grid.set_block(1, 0, True)
        self.assertEqual(self.grid.is_start_word(0, 0, "across"), False)
        
    def testIsStartHorizontalWordTwo(self):
        """Two or more cells constitute a horizontal word."""
        for x in xrange(2, self.grid.width):
            self.grid.set_block(x, 0, True)
            self.assertEqual(self.grid.is_start_word(0, 0, "across"), True)
            self.grid.set_block(x, 0, False)
        
    def testIsStartHorizontalWordThree(self):
        """A block in the cell to the left can start a horizontal word."""
        self.assertEqual(self.grid.is_start_word(5, 5, "across"), False)
        self.grid.set_block(4, 5, True)
        self.assertEqual(self.grid.is_start_word(5, 5, "across"), True)
        
    def testIsStartHorizontalWordFour(self):
        """Only the first cell is the start of a horizontal word."""
        for x in xrange(1, self.grid.width):
            self.assertEqual(self.grid.is_start_word(x, 0, "across"), False)
    
    def testIsStartHorizontalWordBarsOne(self):
        """A single cell (ended by a bar) is not a horizontal word."""
        self.grid.set_bar(1, 0, "left", True)
        self.assertEqual(self.grid.is_start_word(0, 0, "across"), False)
        
    def testIsStartHorizontalWordBarsTwo(self):
        """A bar to the left starts a horizontal word."""
        self.grid.set_bar(5, 5, "left", True)
        self.assertEqual(self.grid.is_start_word(5, 5, "across"), True)
        
    def testIsStartHorizontalWordBarsThree(self):
        """A bar on both sides is not a horizontal word."""
        self.grid.set_bar(5, 5, "left", True)
        self.grid.set_bar(6, 5, "left", True)
        self.assertEqual(self.grid.is_start_word(5, 5, "across"), False)
        
    def testIsStartHorizontalWordBarsFour(self):
        """A bar on the left and a bar on the right is not a horizontal word."""
        self.grid.set_bar(4, 4, "left", True)
        self.grid.set_block(5, 4, True)
        self.assertEqual(self.grid.is_start_word(4, 4, "across"), False)
        
    def testIsStartHorizontalWordBarsFive(self):
        """A block on the left and a bar on the right is not a horizontal word."""
        self.grid.set_block(7, 7, True)
        self.grid.set_bar(9, 7, "left", True)
        self.assertEqual(self.grid.is_start_word(8, 7, "across"), False)
        
    def testIsStartHorizontalWordBarsSix(self):
        """A bar on both sides is not a horizontal word."""
        self.grid.set_bar(8, 8, "left", True)
        self.assertEqual(self.grid.is_start_word(8, 8, "across"), True)
        self.grid.set_bar(9, 8, "left", True)
        self.assertEqual(self.grid.is_start_word(8, 8, "across"), False)
        
    def testIsStartVerticalWordOne(self):
        """A single cell (ended by a block) is not a vertical word."""
        self.assertEqual(self.grid.is_start_word(0, 0, "down"), True)
        self.grid.set_block(0, 1, True)
        self.assertEqual(self.grid.is_start_word(0, 0, "down"), False)
        
    def testIsStartVerticalWordTwo(self):
        """Two or more cells constitute a vertical word."""
        for y in xrange(2, self.grid.height):
            self.grid.set_block(0, y, True)
            self.assertEqual(self.grid.is_start_word(0, 0, "down"), True)
            self.grid.set_block(0, y, False)
        
    def testIsStartVerticalWordThree(self):
        """A block in the cell above can start a vertical word."""
        self.assertEqual(self.grid.is_start_word(5, 5, "down"), False)
        self.grid.set_block(5, 4, True)
        self.assertEqual(self.grid.is_start_word(5, 5, "down"), True)
        
    def testIsStartVerticalWordFour(self):
        """Only the first cell is the start of a vertical word."""
        for y in xrange(1, self.grid.height):
            self.assertEqual(self.grid.is_start_word(0, y, "down"), False)
        
    def testIsStartVerticalWordBarsOne(self):
        """A single cell (ended by a bar) is not a vertical word."""
        self.grid.set_bar(0, 1, "top", True)
        self.assertEqual(self.grid.is_start_word(0, 0, "down"), False)
        
    def testIsStartVerticalWordBarsTwo(self):
        """A bar above starts a vertical word."""
        self.grid.set_bar(5, 5, "top", True)
        self.assertEqual(self.grid.is_start_word(5, 5, "down"), True)
        
    def testIsStartVerticalWordBarsThree(self):
        """A bar above and below is not a vertical word."""
        self.grid.set_bar(5, 5, "top", True)
        self.grid.set_bar(5, 6, "top", True)
        self.assertEqual(self.grid.is_start_word(5, 5, "down"), False)
        
    def testIsStartVerticalWordBarsFour(self):
        """A bar above and a block below is not a vertical word."""
        self.grid.set_bar(4, 4, "top", True)
        self.grid.set_block(4, 5, True)
        self.assertEqual(self.grid.is_start_word(4, 4, "down"), False)
        
    def testIsStartVerticalWordBarsFive(self):
        """A block above and a block below is not a vertical word."""
        self.grid.set_block(7, 7, True)
        self.grid.set_bar(7, 9, "top", True)
        self.assertEqual(self.grid.is_start_word(7, 8, "down"), False)
        
    def testIsStartVerticalWordBarsSix(self):
        """A bar on both sides is not a vertical word."""
        self.grid.set_bar(8, 8, "top", True)
        self.assertEqual(self.grid.is_start_word(8, 8, "down"), True)
        self.grid.set_bar(8, 9, "top", True)
        self.assertEqual(self.grid.is_start_word(8, 8, "down"), False)
        
    def testIsStartWord(self):
        """A cell must have at least one word to be a word starting cell."""
        self.assertEqual(self.grid.is_start_word(0, 0), True)
        self.assertEqual(self.grid.is_start_word(0, 0, "across"), True)
        self.assertEqual(self.grid.is_start_word(0, 0, "down"), True)
        self.grid.set_block(0, 1, True)
        self.assertEqual(self.grid.is_start_word(0, 0), True)
        self.assertEqual(self.grid.is_start_word(0, 0, "across"), True)
        self.assertEqual(self.grid.is_start_word(0, 0, "down"), False)
        self.grid.set_block(1, 0, True)
        self.assertEqual(self.grid.is_start_word(0, 0), False)
        self.assertEqual(self.grid.is_start_word(0, 0, "across"), False)
        self.assertEqual(self.grid.is_start_word(0, 0, "down"), False)
        
    def testIsStartWordVoid(self):
        self.assertEqual(self.grid.is_start_word(5, 1), False)
        self.grid.set_void(4, 1, True)
        self.assertEqual(self.grid.is_start_word(5, 1), True)
        self.assertEqual(self.grid.is_start_word(1, 5), False)
        self.grid.set_void(1, 4, True)
        self.assertEqual(self.grid.is_start_word(1, 5), True)
        
    def testGetStartWordOne(self):
        """All cells in a word return the first cell as the word's start."""
        for x in range(self.grid.width):
            p, q = self.grid.get_start_word(x, 0, "across")
            self.assertEqual(p, 0)
            self.assertEqual(q, 0)
        for y in range(self.grid.height):
            p, q = self.grid.get_start_word(0, y, "down")
            self.assertEqual(p, 0)
            self.assertEqual(q, 0)
        
    def testGetStartWordTwo(self):
        """Return the cell itself when the start is requested of a block."""   
        self.grid.set_block(5, 0, True)
        p, q = self.grid.get_start_word(5, 0, "across")
        self.assertEqual(p, 5)
        self.assertEqual(q, 0)
        self.grid.set_block(0, 5, True)
        p, q = self.grid.get_start_word(0, 5, "down")
        self.assertEqual(p, 0)
        self.assertEqual(q, 5)
        
    def testGetStartWordThree(self):
        """A block splits a word into two."""
        self.grid.set_block(5, 0, True)
        for x in range(0, 5):
            p, q = self.grid.get_start_word(x, 0, "across")
            self.assertEqual(p, 0)
            self.assertEqual(q, 0)
        for x in range(6, self.grid.width):
            p, q = self.grid.get_start_word(x, 0, "across")
            self.assertEqual(p, 6)
            self.assertEqual(q, 0)
        self.grid.set_block(0, 5, True)
        for y in range(0, 5):
            p, q = self.grid.get_start_word(0, y, "down")
            self.assertEqual(p, 0)
            self.assertEqual(q, 0)
        for y in range(6, self.grid.height):
            p, q = self.grid.get_start_word(0, y, "down")
            self.assertEqual(p, 0)
            self.assertEqual(q, 6)
            
    def testGetStartWordFour(self):
        p, q = self.grid.get_start_word(0, 0, "across")
        self.assertEquals((0, 0), (p, q))
            
    def testGetEndWord(self):
        self.assertEquals(self.grid.get_end_word(0, 0, "across"), (self.grid.width - 1, 0))
        for i in xrange(10):
            self.grid.set_block(i, i, True)
        self.assertEquals(self.grid.get_end_word(0, 0, "across"), (0, 0))
        for i in xrange(8):
            self.assertEquals(self.grid.get_end_word(0, i + 2, "across"), (i + 1, i + 2))
        self.assertEquals(self.grid.get_end_word(0, 0, "down"), (0, 0))
        for i in xrange(8):
            self.assertEquals(self.grid.get_end_word(i + 2, 0, "down"), (i + 2, i + 1))
            
    def testInvalidCells(self):
        self.assertEquals(self.grid.get_check_count(-5, -5), -1)
        self.assertEquals(self.grid.is_part_of_word(-5, -5, "across"), False)
            
    def testCheckCountBlocks(self):
        """Check counts range from -1 to 2 for blocks/voids to default cells."""
        self.assertEqual(self.grid.get_check_count(5, 5), 2)
        self.grid.set_block(4, 5, True)
        self.assertEqual(self.grid.get_check_count(5, 5), 2)
        self.grid.set_void(6, 5, True)
        self.assertEqual(self.grid.get_check_count(5, 5), 1)
        self.grid.set_block(5, 4, True)
        self.assertEqual(self.grid.get_check_count(5, 5), 1)
        self.grid.set_void(5, 6, True)
        self.assertEqual(self.grid.get_check_count(5, 5), 0)
        self.grid.set_block(5, 5, True)
        self.assertEqual(self.grid.get_check_count(5, 5), -1)
        
    def testCheckCountBars(self):
        """Bars influence the check count of a cell."""
        self.grid.set_bar(5, 5, "left", True)
        self.grid.set_bar(6, 5, "left", True)
        self.assertEqual(self.grid.get_check_count(5, 5), 1)
        self.grid.set_bar(5, 5, "top", True)
        self.grid.set_bar(5, 6, "top", True)
        self.assertEqual(self.grid.get_check_count(5, 5), 0)
        self.grid.set_bar(1, 1, "left", True)
        self.assertEqual(self.grid.get_check_count(0, 1), 1)
        self.grid.set_bar(1, 1, "top", True)
        self.assertEqual(self.grid.get_check_count(1, 0), 1)
        
    def testCheckCountAll(self):
        counts = self.grid.get_check_count_all()
        for x, y in self.grid.cells():
            self.assertEquals(counts[x, y], self.grid.get_check_count(x, y))
        self.grid.set_block(0, 1, True)
        self.grid.set_block(1, 0, True)
        self.grid.set_block(5, 5, True)
        self.grid.set_void(10, 0, True)
        self.grid.set_void(11, 1, True)
        counts = self.grid.get_check_count_all()
        for x, y in self.grid.cells():
            self.assertEquals(counts[x, y], self.grid.get_check_count(x, y))
        
    def testIsPartOfWordAcross(self):
        """A word consists of 2+ letters."""
        self.grid.set_bar(5, 5, "left", True)
        self.assertEqual(self.grid.is_part_of_word(5, 5, "across"), True)
        self.grid.set_bar(6, 5, "left", True)
        self.assertEqual(self.grid.is_part_of_word(5, 5, "across"), False)
        self.grid.set_block(7, 7, True)
        self.assertEqual(self.grid.is_part_of_word(8, 7, "across"), True)
        self.grid.set_void(9, 7, True)
        self.assertEqual(self.grid.is_part_of_word(8, 7, "across"), False)

    def testIsPartOfWordDown(self):
        """A word consists of 2+ letters."""
        self.grid.set_bar(5, 5, "top", True)
        self.assertEqual(self.grid.is_part_of_word(5, 5, "down"), True)
        self.grid.set_bar(5, 6, "top", True)
        self.assertEqual(self.grid.is_part_of_word(5, 5, "down"), False)
        self.grid.set_block(7, 7, True)
        self.assertEqual(self.grid.is_part_of_word(7, 8, "down"), True)
        self.grid.set_void(7, 9, True)
        self.assertEqual(self.grid.is_part_of_word(7, 8, "down"), False)
        
    def testIsPartOfWordAvailable(self):
        """A cell that is not available cannot be part of a word."""
        self.assertEquals(self.grid.is_part_of_word(5, 5, "across"), True)
        self.grid.set_block(5, 5, True)
        self.assertEquals(self.grid.is_part_of_word(5, 5, "across"), False)
        self.assertEquals(self.grid.is_part_of_word(6, 6, "across"), True)
        self.grid.set_void(6, 6, True)
        self.assertEquals(self.grid.is_part_of_word(6, 6, "across"), False)
        
    def testSlotOne(self):
        """A slot consists of all cells starting from the first cell of that slot."""
        p, q = self.grid.get_start_word(5, 0, "across")
        indir = [(x, y) for x, y in self.grid.in_direction(p, q, "across")]
        cells = [cell for cell in self.grid.slot(5, 0, "across")]
        for cell in cells:
            self.assertEquals(cell in indir, True)
        self.assertEquals(len(cells), self.grid.width)
        
    def testSlotTwo(self):
        """A slot of length 1 is also a slot."""
        self.grid.set_block(1, 0, True)
        cells = [cell for cell in self.grid.slot(0, 0, "across")]
        self.assertEquals(cells, [(0, 0)])
        self.assertEquals(len(cells), 1)
        
    def testInDirectionNormal(self):
        """Direction iterator returns all cells in the given direction."""
        cells = [(x, 0) for x in xrange(self.grid.width)]
        indir = [(x, y) for x, y in self.grid.in_direction(0, 0, "across")]
        self.assertEqual(cells, indir)
        cells = [(0, y) for y in xrange(self.grid.height)]
        indir = [(x, y) for x, y in self.grid.in_direction(0, 0, "down")]
        self.assertEqual(cells, indir)
        
    def testInDirectionReverse(self):
        """
        Direction iterator returns all cells in the given direction (in reverse).
        """
        cells = [(x, 0) for x in xrange(self.grid.width - 1, -1, -1)]
        indir = [(x, y) for x, y
            in self.grid.in_direction(self.grid.width - 1, 0, "across", True)]
        self.assertEqual(cells, indir)
        cells = [(0, y) for y in xrange(self.grid.height - 1, -1, -1)]
        indir = [(x, y) for x, y
            in self.grid.in_direction(0, self.grid.height - 1, "down", True)]
        self.assertEqual(cells, indir)
        
    def testInDirectionBlocks(self):
        self.grid.set_block(5, 0, True)
        cells = [(x, 0) for x in xrange(5)]
        indir = [(x, y) for x, y in self.grid.in_direction(0, 0, "across")]
        self.assertEqual(cells, indir)
        self.grid.set_block(0, 5, True)
        cells = [(0, x) for x in xrange(5)]
        indir = [(x, y) for x, y in self.grid.in_direction(0, 0, "down")]
        self.assertEqual(cells, indir)

    def testInDirectionBlocksReverse(self):
        self.grid.set_void(5, 0, True)
        cells = [(x, 0) for x in xrange(self.grid.width - 1, 5, -1)]
        indir = [(x, y) for x, y
            in self.grid.in_direction(self.grid.width - 1, 0, "across", True)]
        self.assertEqual(cells, indir)
        self.grid.set_void(0, 5, True)
        cells = [(0, x) for x in xrange(self.grid.height - 1, 5, -1)]
        indir = [(x, y) for x, y
            in self.grid.in_direction(0, self.grid.height - 1, "down", True)]
        self.assertEqual(cells, indir)
        
    def testInDirectionBars(self):
        self.grid.set_bar(5, 0, "left", True)
        cells = [(x, 0) for x in xrange(5)]
        indir = [(x, y) for x, y in self.grid.in_direction(0, 0, "across")]
        self.assertEqual(cells, indir)
        self.grid.set_bar(0, 5, "top", True)
        cells = [(0, x) for x in xrange(5)]
        indir = [(x, y) for x, y in self.grid.in_direction(0, 0, "down")]
        self.assertEqual(cells, indir)
        
    def testInDirectionBarsReverse(self):
        self.grid.set_bar(5, 0, "left", True)
        cells = [(x, 0) for x in xrange(self.grid.width - 1, 4, -1)]
        indir = [(x, y) for x, y
            in self.grid.in_direction(self.grid.width - 1, 0, "across", True)]
        self.assertEqual(cells, indir)
        self.grid.set_bar(0, 5, "top", True)
        cells = [(0, x) for x in xrange(self.grid.height - 1, 4, -1)]
        indir = [(x, y) for x, y
            in self.grid.in_direction(0, self.grid.height - 1, "down", True)]
        self.assertEqual(cells, indir)
        
    def testInDirectionVoids(self):
        self.grid.set_void(5, 0, True)
        cells = [(x, 0) for x in xrange(5)]
        indir = [(x, y) for x, y in self.grid.in_direction(0, 0, "across")]
        self.assertEqual(cells, indir)
        self.grid.set_void(0, 5, True)
        cells = [(0, x) for x in xrange(5)]
        indir = [(x, y) for x, y in self.grid.in_direction(0, 0, "down")]
        self.assertEqual(cells, indir)
        
    def testWordCounts(self):
        counts = self.grid.determine_word_counts()
        self.assertEquals(counts["across"], 15)
        self.assertEquals(counts["down"], 12)
        self.assertEquals(counts[12], 15)
        self.assertEquals(counts[15], 12)
        for i in xrange(2, 16):
            if i == 12 or i == 15:
                continue
            self.assertEquals(i not in counts, True)
        for l, c in counts["total"]:
            if l == 12:
                self.assertEquals(c, 15)
            elif l == 15:
                self.assertEquals(c, 12)
            else:
                self.assertEquals(c, 0)
    
    def testGatherWordOne(self):
        word = self.grid.gather_word(0, 0, "across", "_")
        self.assertEqual(word, self.grid.width * "_")
        word = self.grid.gather_word(0, 0, "down", "_")
        self.assertEqual(word, self.grid.height * "_")
        
        self.grid.set_char(0, 0, "A")
        self.grid.set_char(2, 0, "B")
        self.grid.set_char(4, 0, "C")
        self.grid.set_block(6, 0, True)
        word = self.grid.gather_word(0, 0, "across", "_")
        self.assertEqual(word, "A_B_C_")
        
        self.grid.set_char(0, 0, "D")
        self.grid.set_char(0, 2, "E")
        self.grid.set_char(0, 4, "F")
        self.grid.set_block(0, 6, True)
        word = self.grid.gather_word(0, 0, "down", "_")
        self.assertEqual(word, "D_E_F_")
        
    def testGatherWordTwo(self):
        self.grid.set_block(4, 0, True)
        self.assertEquals(self.grid.gather_word(4, 0, "across"), "")
        self.assertEquals(self.grid.gather_word(4, 0, "down"), "")
        
        self.grid.set_char(0, 0, "A")
        self.grid.set_char(1, 0, "B")
        self.grid.set_char(2, 0, "C")
        self.grid.set_char(3, 0, "D")
        self.assertEquals(self.grid.gather_word(0, 0, "across"), "ABCD")
        
        self.grid.set_block(0, 4, True)
        self.assertEquals(self.grid.gather_word(0, 0, "down", "x"), "Axxx")
        
    def testWordLength(self):
        length = self.grid.word_length(0, 0, "across")
        self.assertEqual(length, self.grid.width)
        length = self.grid.word_length(0, 0, "down")
        self.assertEqual(length, self.grid.height)
        
        for i in range(10):
            self.grid.set_block(i, i, True)
            
        for x in range(10):
            length = self.grid.word_length(x, 0, "down")
            self.assertEqual(length, x)
            
        for y in range(10):
            length = self.grid.word_length(0, y, "across")
            self.assertEqual(length, y)
            
    def testMeanWordLength(self):
        g = Grid(3, 3)
        g.set_block(1, 0, True)
        g.set_block(0, 1, True)
        g.set_block(1, 2, True)
        g.set_block(2, 1, True)
        self.assertEquals(g.mean_word_length(), 0)
        g = Grid(5, 5)
        self.assertEquals(g.mean_word_length(), 5)
        g.set_block(0, 0, True)
        self.assertAlmostEqual(g.mean_word_length(), (8 * 5 + 2 * 4) / 10.0)
        g.set_block(1, 1, True)
        self.assertAlmostEqual(g.mean_word_length(), (2 * 4 + 2 * 3 + 6 * 5) / 10.0)
        g.set_block(1, 3, True)
        self.assertAlmostEqual(g.mean_word_length(), (2 * 4 + 2 * 3 + 5 * 5) / 9.0)
            
    def testCountBlocks(self):
        self.assertEqual(self.grid.count_blocks(), 0)
        
        for i in range(10):
            self.grid.set_block(i, i, True)
            self.assertEqual(self.grid.count_blocks(), i + 1)
        
        for i in range(10):
            self.grid.set_block(i, i, False)
        self.assertEqual(self.grid.count_blocks(), 0)
        
    def testCountAndHasChars(self):
        self.assertEqual(self.grid.count_chars(True), self.grid.width * self.grid.height)
        self.assertEqual(self.grid.count_chars(False), 0)
        self.assertEqual(self.grid.has_chars(), False)
        for i in range(10):
            self.grid.set_char(i, i, 'A')
            self.assertEqual(self.grid.has_chars(), True)
            self.assertEqual(self.grid.count_chars(False), i + 1)
        for i in range(10):
            self.grid.set_char(i, i, '')
        self.assertEqual(self.grid.count_chars(True), self.grid.width * self.grid.height)
        self.assertEqual(self.grid.count_chars(False), 0)
        self.assertEqual(self.grid.has_chars(), False)
        
    def testCountWords(self):
        count = self.grid.width + self.grid.height
        self.assertEquals(self.grid.count_words(), count)
        self.grid.set_block(2, 2, True)
        count = self.grid.width + self.grid.height + 2
        self.assertEquals(self.grid.count_words(), count)
        self.grid.set_bar(4, 4, "top", True)
        count = self.grid.width + self.grid.height + 3
        self.assertEquals(self.grid.count_words(), count)
        self.grid.set_bar(4, 5, "top", True)
        count = self.grid.width + self.grid.height + 3
        self.assertEquals(self.grid.count_words(), count)
        self.grid.set_bar(4, 4, "left", True)
        count = self.grid.width + self.grid.height + 4
        self.assertEquals(self.grid.count_words(), count)
        self.grid.set_bar(5, 4, "left", True)
        count = self.grid.width + self.grid.height + 4
        self.assertEquals(self.grid.count_words(), count)
        
    def testCountVoids(self):
        self.assertEqual(self.grid.count_voids(), 0)
        
        for i in range(10):
            self.grid.set_void(i, i, True)
            self.assertEqual(self.grid.count_voids(), i + 1)
        
        for i in range(10):
            self.grid.set_void(i, i, False)
        self.assertEqual(self.grid.count_voids(), 0)

    def testEntries(self):
        count = self.grid.count_words()
        entries = self.grid.entries()
        self.assertEquals(len(entries), count)
        
    def testGatherWords(self):
        count = self.grid.count_words()
        words = [item for item in self.grid.gather_words()]
        self.assertEquals(len(words), count)
        
        counts = self.grid.determine_word_counts()
        for d in ["across", "down"]:
            d_count = counts[d]
            d_words = [item for item in self.grid.gather_words(d)]
            self.assertEquals(len(d_words), d_count)
            
    def testGatherWordsEntries(self):
        entries = self.grid.entries()
        for d in ["across", "down"]:
            words = [item[4] for item in self.grid.gather_words(d)]
            for word in words:
                self.assertEquals(word in entries, True)

    def testResize(self):
        for i in [2, 4, 6, 8]:
            self.grid.set_block(i, i, True)
        for i in [1, 3, 5, 7]:
            self.grid.set_char(i, i, "A")
        self.grid.resize(30, 30)
        self.assertEqual(self.grid.width, 30)
        self.assertEqual(self.grid.height, 30)
        for i in [2, 4, 6, 8]:
            self.assertEqual(self.grid.is_block(i, i), True)
        for i in [1, 3, 5, 7]:
            self.assertEqual(self.grid.get_char(i, i), "A")
        
        self.grid.resize(3, 3)
        self.assertEqual(self.grid.width, 3)
        self.assertEqual(self.grid.height, 3)
        
        self.grid.resize(30, 30)
        self.assertEqual(self.grid.is_block(2, 2), True)
        for i in [4, 6, 8]:
            self.assertEqual(self.grid.is_block(i, i), False)
        self.assertEqual(self.grid.get_char(1, 1), "A")
        for i in [3, 5, 7]:
            self.assertEqual(self.grid.get_char(i, i), "")
            
    def testShiftGridUpDown(self):
        for i in range(self.grid.width):
            self.grid.set_block(i, 0, True)
            
            self.grid.set_block(i, 5, True)
            self.grid.set_char(i, 7, "A")
            
        self.grid.shift_up()
        
        for i in range(self.grid.width):
            self.assertEqual(self.grid.is_block(i, 0), False)
            self.assertEqual(self.grid.is_block(i, 4), True)
            self.assertEqual(self.grid.is_block(i, 5), False)
            self.assertEqual(self.grid.get_char(i, 6), "A")
            self.assertEqual(self.grid.get_char(i, 7), "")
            
        for i in range(self.grid.width):
            self.grid.set_block(i, self.grid.height - 1, True)
            
        self.grid.shift_down()
        
        for i in range(self.grid.width):
            self.assertEqual(self.grid.is_block(i, self.grid.height - 1), False)
            self.assertEqual(self.grid.is_block(i, 0), False)
            self.assertEqual(self.grid.is_block(i, 5), True)
            self.assertEqual(self.grid.get_char(i, 7), "A")
            
        self.grid.shift_down()
        
        for i in range(self.grid.width):
            self.assertEqual(self.grid.is_block(i, self.grid.height - 1), False)
            
    def testShiftGridLeftRight(self):
        for j in range(self.grid.height):
            self.grid.set_block(0, j, True)
            
            self.grid.set_block(5, j, True)
            self.grid.set_char(7, j, "A")
            
        self.grid.shift_left()
        
        for j in range(self.grid.height):
            self.assertEqual(self.grid.is_block(0, j), False)
            self.assertEqual(self.grid.is_block(4, j), True)
            self.assertEqual(self.grid.is_block(5, j), False)
            self.assertEqual(self.grid.get_char(6, j), "A")
            self.assertEqual(self.grid.get_char(7, j), "")
            
        for j in range(self.grid.height):
            self.grid.set_block(self.grid.width - 1, j, True)
            
        self.grid.shift_right()
        
        for j in range(self.grid.height):
            self.assertEqual(self.grid.is_block(self.grid.width - 1, j), False)
            self.assertEqual(self.grid.is_block(0, j), False)
            self.assertEqual(self.grid.is_block(5, j), True)
            self.assertEqual(self.grid.get_char(7, j), "A")
            
        self.grid.shift_left()
        
        for j in range(self.grid.height):
            self.assertEqual(self.grid.is_block(self.grid.width - 1, j), False)
            
    def testClear(self):
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                self.grid.set_block(x, y, True)
        self.grid.clear()
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                self.assertEqual(self.grid.is_block(x, y), False)
                
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                self.grid.set_char(x, y, "A")
        self.grid.clear()
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                self.assertEqual(self.grid.get_char(x, y), "")
                
    def testClearChars(self):
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                self.grid.set_block(x, y, True)
        self.grid.clear_chars()
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                self.assertEqual(self.grid.is_block(x, y), True)
                
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                self.grid.set_char(x, y, "A")
        self.grid.clear_chars()
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                self.assertEqual(self.grid.get_char(x, y), "")
                
    def testClearBlocks(self):
        for x, y in self.grid.cells():
            self.grid.set_block(x, y, True)
        self.grid.clear_blocks()
        for x, y in self.grid.cells():
            self.assertEquals(self.grid.is_block(x, y), False)
            
    def testClearVoids(self):
        for x, y in self.grid.cells():
            self.grid.set_void(x, y, True)
        self.grid.clear_voids()
        for x, y in self.grid.cells():
            self.assertEquals(self.grid.is_void(x, y), False)
    
    def testClearClues(self):
        for x, y in self.grid.cells():
            self.grid.store_clue(x, y, "across", "text", "foo")
        self.grid.clear_clues()
        for x, y in self.grid.cells():
            self.assertEquals(self.grid.get_clues(x, y), {})
                
    def testClearBars(self):
        for x, y in self.grid.cells():
            self.grid.set_bar(x, y, "top", True)
            self.grid.set_bar(x, y, "left", True)
        self.grid.clear_bars()
        for x, y in self.grid.cells():
            self.assertEqual(self.grid.has_bar(x, y, "top"), False)
            self.assertEqual(self.grid.has_bar(x, y, "left"), False)
                
    def testCells(self):
        n = sum([1 for x, y in self.grid.cells()])
        self.assertEquals(n, self.grid.width * self.grid.height)
        
    def testWords(self):
        n = sum([1 for n, x, y in self.grid.words(False)])
        self.assertEquals(n, self.grid.width + self.grid.height - 1)
        
        n = sum([1 for n, x, y in self.grid.words(True)])
        self.assertEquals(n, self.grid.width + self.grid.height)
        
        self.grid.set_block(2, 2, True)
        
        n = sum([1 for n, x, y in self.grid.words(False)])
        self.assertEquals(n, 28)
        n = sum([1 for n, x, y in self.grid.words(True)])
        self.assertEquals(n, 29)
        
        # added to test the appearance of d value (should not cause Python error)
        l = [d for n, x, y, d in self.grid.words(True, True)]
        l = [d for n, x, y in self.grid.words(True, False)]
        l = [d for n, x, y in self.grid.words(False, True)]
        l = [d for n, x, y in self.grid.words(False, False)]
        
    def testHorizontalWords(self):
        n = len([1 for x in self.grid.words_by_direction("across")])
        self.assertEquals(self.grid.height, n)
        
        for y in xrange(self.grid.height):
            self.grid.set_block(2, y, True)
        xs = [x for n, x, y in self.grid.words_by_direction("across")]
        self.assertEquals(xs, [0, 3] * self.grid.height)
        
    def testVerticalWords(self):
        n = len([1 for x in self.grid.words_by_direction("down")])
        self.assertEquals(self.grid.width, n)
        
        for x in xrange(self.grid.width):
            self.grid.set_block(x, 2, True)
        ys = [y for n, x, y in self.grid.words_by_direction("down")]
        self.assertEquals(ys, [0] * self.grid.width + [3] * self.grid.width)
        
    def testInsertRow(self):
        width, height = self.grid.width, self.grid.height
        self.grid.set_block(0, 0, True)
        self.grid.set_block(0, 1, True)
        
        self.grid.insert_row(0, True)
        self.assertEquals(self.grid.width, width)
        self.assertEquals(self.grid.height, height + 1)
        bs = [self.grid.is_block(x, y) for x, y in [(0, 0), (0, 1), (0, 2)]]
        self.assertEquals(bs, [False, True, True])
        for x, y in self.grid.in_direction(0, 0, "across"):
            self.assertEquals(self.grid.is_block(x, y), False)
            self.assertEquals(self.grid.get_char(x, y), "")

        self.grid.insert_row(1, False)
        self.assertEquals(self.grid.width, width)
        self.assertEquals(self.grid.height, height + 2)
        cells = [(0, 0), (0, 1), (0, 2), (0, 3)]
        bs = [self.grid.is_block(x, y) for x, y in cells]
        self.assertEquals(bs, [False, True, False, True])
        
    def testInsertRowBars(self):
        self.grid.set_bar(5, 5, "top", True)
        self.grid.insert_row(5, True)
        self.assertEquals(self.grid.has_bar(5, 5, "top"), True)
        
    def testInsertColumn(self):
        width, height = self.grid.width, self.grid.height
        self.grid.set_block(0, 0, True)
        self.grid.set_block(1, 0, True)
        
        self.grid.insert_column(0, True)
        self.assertEquals(self.grid.width, width + 1)
        self.assertEquals(self.grid.height, height)
        bs = [self.grid.is_block(x, y) for x, y in [(0, 0), (1, 0), (2, 0)]]
        self.assertEquals(bs, [False, True, True])
        for x, y in self.grid.in_direction(0, 0, "down"):
            self.assertEquals(self.grid.is_block(x, y), False)
            self.assertEquals(self.grid.get_char(x, y), "")

        self.grid.insert_column(1, False)
        self.assertEquals(self.grid.width, width + 2)
        self.assertEquals(self.grid.height, height)
        cells = [(0, 0), (1, 0), (2, 0), (3, 0)]
        bs = [self.grid.is_block(x, y) for x, y in cells]
        self.assertEquals(bs, [False, True, False, True])
        
    def testInsertColumnBars(self):
        self.grid.set_bar(5, 5, "left", True)
        self.grid.insert_column(5, True)
        self.assertEquals(self.grid.has_bar(5, 5, "left"), True)
        
    def testRemoveRow(self):
        width, height = self.grid.width, self.grid.height
        for x in xrange(self.grid.width):
            self.grid.set_block(x, 0, True)
        self.grid.remove_row(0)
        self.assertEquals(self.grid.height, height - 1)
        for x in xrange(self.grid.width):
            self.assertEquals(self.grid.is_block(x, 0), False)
            
    def _set_clues_one(self, direction):
        # top-left corner:
        # X _ _ _
        # _ X _ _
        # _ _ X _
        # _ _ _ _
        clues = [(2, 0, "A"), (0, 1, "B"), (1, 2, "C"), (2, 3, "D")]
        if direction == "across":
            clues = [(x, y, v) for y, x, v in clues]
        for i in xrange(3):
            self.grid.set_block(i, i, True)
        for x, y, value in clues:
            self.grid.store_clue(x, y, direction, "text", value)
            
    def _set_clues_two(self, direction):
        # bottom-right corner:
        # _ _ _ _
        # _ X _ _
        # _ _ X _
        # _ _ _ X
        for i in xrange(3):
            x = self.grid.width - 1 - i
            y = self.grid.height - 1 - i
            self.grid.set_block(x, y, True)
        clues = []
        if direction == "down":
            clues.append((self.grid.width - 3, self.grid.height - 2, "A"))
            clues.append((self.grid.width - 2, 0, "B"))
            clues.append((self.grid.width - 1, 0, "C"))
        else:
            clues.append((self.grid.width - 2, self.grid.height - 3, "A"))
            clues.append((0, self.grid.height - 2, "B"))
            clues.append((0, self.grid.height - 1, "C"))
        for x, y, value in clues:
            self.grid.store_clue(x, y, direction, "text", value)
    
    def testNeighbors(self):
        ns = [(x, y) for x, y in self.grid.neighbors(0, 0)]
        self.assertEquals(len(ns), 2)
        self.assertEquals((0, 1) in ns, True)
        self.assertEquals((1, 0) in ns, True)
        
        ns2 = [(x, y) for x, y in self.grid.neighbors(0, 0, diagonals=True)]
        self.assertEquals(len(ns2), 3)
        for n in ns:
            self.assertEquals(n in ns2, True)
        self.assertEquals((1, 1) in ns2, True)
        
        ns = [(x, y) for x, y in self.grid.neighbors(5, 5)]
        self.assertEquals(len(ns), 4)
        self.assertEquals((5, 6) in ns, True)
        self.assertEquals((6, 5) in ns, True)
        self.assertEquals((4, 5) in ns, True)
        self.assertEquals((5, 4) in ns, True)
        
        ns2 = [(x, y) for x, y in self.grid.neighbors(5, 5, diagonals=True)]
        self.assertEquals(len(ns2), 8)
        for n in ns:
            self.assertEquals(n in ns2, True)
        self.assertEquals((4, 4) in ns2, True)
        self.assertEquals((6, 4) in ns2, True)
        self.assertEquals((6, 6) in ns2, True)
        self.assertEquals((4, 6) in ns2, True)
        
        g = Grid(1, 1)
        ns = [(x, y) for x, y in g.neighbors(0, 0)]
        self.assertEquals(len(ns), 0)
            
    def testOpenSquares(self):
        g = Grid(5, 5)
        self.assertEquals(len(g.compute_open_squares()), 5 * 5)
        g.set_block(2, 2, True)
        self.assertEquals(len(g.compute_open_squares()), (5 * 5) - 1 - 8)
        g.set_block(0, 0, True)
        self.assertEquals(len(g.compute_open_squares()), (5 * 5) - 9 - 1 - 2)
        g.set_block(1, 1, True)
        self.assertEquals(len(g.compute_open_squares()), (5 * 5) - 9 - 3 - 2)
            
    def testIsConnected(self):
        g = Grid(5, 5)
        self.assertEquals(g.is_connected(), True)
        for i in xrange(5):
            g.set_block(i, i, True)
        self.assertEquals(g.is_connected(), False)
        for i in xrange(5):
            g.set_block(i, i, False)
            self.assertEquals(g.is_connected(), True)
            g.set_block(i, i, True)
        for i in xrange(5):
            for j in xrange(5):
                g.set_block(i, j, True)
        self.assertEquals(g.is_connected(), True)
       
    def testRemoveRowDirty(self):
        self._set_clues_one("down")
        self.grid.remove_row(1)
        results = [(2, 0, False), (0, 1, False), (1, 1, False), (2, 2, True)]
        for x, y, value in results:
            self.assertEquals("down" in self.grid.get_clues(x, y), value)
        self.assertEquals(self.grid.get_clues(2, 2)["down"]["text"], "D")
        
    def testRemoveRowDirtyTwo(self):
        self._set_clues_one("down")
        self.grid.remove_row(2)
        self.assertEquals("down" in self.grid.get_clues(2, 0), False)
        
    def testRemoveColumn(self):
        width, height = self.grid.width, self.grid.height
        for y in xrange(self.grid.height):
            self.grid.set_block(0, y, True)
        self.grid.remove_column(0)
        self.assertEquals(width - 1, self.grid.width)
        for y in xrange(self.grid.height):
            self.assertEquals(self.grid.is_block(0, y), False)
            
    def testRemoveColumnDirty(self):
        self._set_clues_one("across")
        self.grid.remove_column(1)
        results = [(0, 2, False), (1, 0, False), (1, 1, False), (2, 2, True)]
        for x, y, value in results:
            self.assertEquals("across" in self.grid.get_clues(x, y), value)
        self.assertEquals(self.grid.get_clues(2, 2)["across"]["text"], "D")
        
    def testRemoveColumnDirtyTwo(self):
        self._set_clues_one("across")
        self.grid.remove_row(2)
        self.assertEquals("across" in self.grid.get_clues(0, 2), False)
        
    def testShiftGridUpDirtyOne(self):
        self._set_clues_one("down")
        self.grid.shift_up()
        self.assertEquals("down" in self.grid.get_clues(0, 0), False)
        self.assertEquals("down" in self.grid.get_clues(1, 1), False)

    def testShiftGridUpDirtyTwo(self):    
        self.grid.set_block(0, 3, True)
        self._set_clues_one("down")
        self.grid.shift_up()
        self.assertEquals("down" in self.grid.get_clues(0, 0), True)
        self.assertEquals(self.grid.get_clues(0, 0)["down"]["text"], "B")
        self.assertEquals("down" in self.grid.get_clues(1, 1), False)
        
    def testShiftGridLeftDirtyOne(self):
        self._set_clues_one("across")
        self.grid.shift_left()
        self.assertEquals("across" in self.grid.get_clues(0, 0), False)
        self.assertEquals("across" in self.grid.get_clues(1, 1), False)
        
    def testShiftGridLeftDirtyTwo(self):
        self.grid.set_block(3, 0, True)
        self._set_clues_one("across")
        self.grid.shift_left()
        self.assertEquals("across" in self.grid.get_clues(0, 0), True)
        self.assertEquals(self.grid.get_clues(0, 0)["across"]["text"], "B")
        self.assertEquals("across" in self.grid.get_clues(1, 1), False)
        
    def testShiftGridRightDirtyOne(self):
        self._set_clues_two("across")
        self.grid.shift_right()
        clue = self.grid.get_clues(self.grid.width - 1, self.grid.height - 3)
        self.assertEquals("across" in clue, False)
        clue = self.grid.get_clues(0, self.grid.height - 2)
        self.assertEquals("across" in clue, False)
        clue = self.grid.get_clues(0, self.grid.height - 1)
        self.assertEquals("across" in clue, False)
        
    def testShiftGridRightDirtyTwo(self):
        self._set_clues_two("across")
        self.grid.set_block(2, self.grid.height - 1, True)
        self.grid.store_clue(3, self.grid.height - 1, "across", "text", "E")
        self.grid.shift_right()
        clue = self.grid.get_clues(4, self.grid.height - 1)
        self.assertEquals("across" in clue, True)
        self.assertEquals(clue["across"]["text"], "E")
        
    def testShiftGridDownDirtyOne(self):
        self._set_clues_two("down")
        self.grid.shift_down()
        clue = self.grid.get_clues(self.grid.width - 3, self.grid.height - 1)
        self.assertEquals("down" in clue, False)
        clue = self.grid.get_clues(self.grid.width - 2, 0)
        self.assertEquals("down" in clue, False)
        clue = self.grid.get_clues(self.grid.width - 1, 0)
        self.assertEquals("down" in clue, False)
        
    def testShiftGridDownDirtyTwo(self):
        self._set_clues_two("down")
        self.grid.set_block(self.grid.width - 1, 2, True)
        self.grid.store_clue(self.grid.width - 1, 3, "down", "text", "E")
        self.grid.shift_down()
        clue = self.grid.get_clues(self.grid.width - 1, 4)
        self.assertEquals("down" in clue, True)
        self.assertEquals(clue["down"]["text"], "E")

    def testShiftGridUpBars(self):
        self.grid.set_bar(1, 1, "top", True)
        self.grid.shift_up()
        self.assertEquals(self.grid.has_bar(1, 0, "top"), False)
        
    def testShiftGridLeftBars(self):
        self.grid.set_bar(1, 1, "left", True)
        self.grid.shift_left()
        self.assertEquals(self.grid.has_bar(0, 1, "left"), False)
        
    def testModifyCharDirty(self):
        self.grid.store_clue(0, 0, "across", "text", "A")
        self.grid.set_char(0, 0, "B")
        self.assertEquals("across" in self.grid.get_clues(0, 0), False)
        
        self.grid.store_clue(0, 0, "across", "text", "C")
        self.grid.set_char(5, 0, "D")
        self.assertEquals("across" in self.grid.get_clues(0, 0), False)
        
        self.grid.store_clue(0, 0, "across", "text", "E")
        for x in xrange(1, self.grid.width):
            for y in xrange(1, self.grid.height):
                self.grid.set_char(x, y, "F")
        self.assertEquals(self.grid.get_clues(0, 0)["across"]["text"], "E")
        
    def testModifyBlockDirtyOne(self):
        self.grid.store_clue(0, 0, "across", "text", "A")
        self.grid.set_block(0, 0, True)
        self.assertEquals("across" in self.grid.get_clues(0, 0), False)
        
    def testModifyBlockDirtyTwo(self):
        self.grid.store_clue(0, 0, "across", "text", "C")
        self.grid.set_block(5, 0, True)
        self.assertEquals("across" in self.grid.get_clues(0, 0), False)
        
        self.grid.store_clue(0, 0, "across", "text", "E")
        for x in xrange(1, self.grid.width):
            for y in xrange(1, self.grid.height):
                self.grid.set_block(x, y, True)
        self.assertEquals(self.grid.get_clues(0, 0)["across"]["text"], "E")
        
    def testModifyBlockDirtyThree(self):
        """
        Removing a block should remove clues of words that
        touch the cell that had the block.
        """
        self.grid.set_block(5, 5, True)
        self.grid.store_clue(5, 0, "down", "text", "A")
        self.grid.store_clue(0, 5, "across", "text", "B")
        self.grid.store_clue(6, 5, "across", "text", "C")
        self.grid.store_clue(5, 6, "down", "text", "D")
        self.grid.set_block(5, 5, False)
        self.assertEquals("down" in self.grid.get_clues(5, 0), False)
        self.assertEquals("across" in self.grid.get_clues(0, 5), False)
        self.assertEquals("across" in self.grid.get_clues(6, 5), False)
        self.assertEquals("down" in self.grid.get_clues(5, 6), False)
        
    def testSetBarDirtyOne(self):
        self.grid.store_clue(0, 0, "across", "text", "A")
        self.grid.store_clue(0, 0, "down", "text", "B")
        self.grid.set_bar(5, 0, "left", True)
        self.assertEquals("across" in self.grid.get_clues(0, 0), False)
        self.assertEquals("down" in self.grid.get_clues(0, 0), True)
        
    def testSetBarDirtyTwo(self):
        self.grid.store_clue(0, 0, "across", "text", "A")
        self.grid.store_clue(0, 0, "down", "text", "B")
        self.grid.set_bar(0, 5, "top", True)
        self.assertEquals("across" in self.grid.get_clues(0, 0), True)
        self.assertEquals("down" in self.grid.get_clues(0, 0), False)
        
    def testHorizontalFlip(self):
        self.grid.set_block(0, 0, True)
        self.grid.set_block(self.grid.width - 1, 1, True)
        self.grid.set_char(5, 2, "A")
        self.grid.set_char(6, 3, "B")
        self.grid.set_bar(1, 4, "left", True)
        self.grid.horizontal_flip()
        self.assertEquals(self.grid.is_block(self.grid.width - 1, 0), True)
        self.assertEquals(self.grid.is_block(0, 1), True)
        self.assertEquals(self.grid.get_char(6, 2), "A")
        self.assertEquals(self.grid.get_char(5, 3), "B")
        self.assertEquals(self.grid.has_bar(self.grid.width - 1, 4, "left"), True)
        
    def testVerticalFlip(self):
        self.grid.set_block(0, 0, True)
        self.grid.set_block(1, self.grid.height - 1, True)
        self.grid.set_char(2, 7, "A")
        self.grid.set_char(3, 6, "B")
        self.grid.set_char(4, 8, "C")
        self.grid.set_bar(5, 1, "top", True)
        self.grid.vertical_flip()
        self.assertEquals(self.grid.is_block(0, self.grid.height - 1), True)
        self.assertEquals(self.grid.is_block(1, 0), True)
        self.assertEquals(self.grid.get_char(2, 7), "A")
        self.assertEquals(self.grid.get_char(3, 8), "B")
        self.assertEquals(self.grid.get_char(4, 6), "C")
        self.assertEquals(self.grid.has_bar(5, self.grid.height - 1, "top"), True)
        
    def testDiagonalFlip(self):
        # TODO use self.grid when size assertion in diagonal_flip() is no longer needed
        self.square_grid.set_block(0, 1, True)
        self.square_grid.set_block(3, 3, True)
        self.square_grid.set_char(5, 0, "A")
        self.square_grid.store_clue(0, 0, "across", "text", "This is a clue")
        self.square_grid.store_clue(3, 4, "down", "text", "This is a clue2")
        self.square_grid.diagonal_flip()
        self.assertEquals(self.square_grid.is_block(1, 0), True)
        self.assertEquals(self.square_grid.is_block(3, 3), True)
        self.assertEquals(self.square_grid.get_char(0, 5), "A")
        self.assertEquals(self.square_grid.get_clues(0, 0)["down"]["text"], "This is a clue")
        self.assertEquals(self.square_grid.get_clues(4, 3)["across"]["text"], "This is a clue2")
        
    def testDiagonalFlipBars(self):
        # TODO use self.grid when size assertion in diagonal_flip() is no longer needed
        self.square_grid.set_bar(1, 1, "top", True)
        self.square_grid.diagonal_flip()
        self.assertEquals(self.square_grid.has_bar(1, 1, "left"), True)
        
        self.square_grid.set_bar(3, 3, "left", True)
        self.square_grid.diagonal_flip()
        self.assertEquals(self.square_grid.has_bar(3, 3, "top"), True)
        
        self.square_grid.set_bar(10, 3, "top", True)
        self.square_grid.diagonal_flip()
        self.assertEquals(self.square_grid.has_bar(3, 10, "left"), True)
        
        self.square_grid.set_bar(3, 10, "left", True)
        self.square_grid.diagonal_flip()
        self.assertEquals(self.square_grid.has_bar(10, 3, "top"), True)
        
        self.square_grid.set_bar(7, 7, "left", True)
        self.square_grid.set_bar(7, 7, "top", True)
        self.square_grid.diagonal_flip()
        self.assertEquals(self.square_grid.has_bar(7, 7, "left"), True)
        self.assertEquals(self.square_grid.has_bar(7, 7, "top"), True)
        
    def testIsAvailable(self):
        """A cell is available when text can be entered into it."""
        self.assertEquals(self.grid.is_available(0, 0), True)
        self.grid.set_block(0, 0, True)
        self.assertEquals(self.grid.is_available(0, 0), False)
        self.assertEquals(self.grid.is_available(1, 0), True)
        self.grid.set_void(1, 0, True)
        self.assertEquals(self.grid.is_available(1, 0), False)
        self.assertEquals(self.grid.is_available(-1, -1), False)
        self.assertEquals(self.grid.is_available(100, 100), False)
        
    def testGatherConstraints(self):
        self.grid.set_block(5, 0, True)
        self.grid.set_char(0, 0, 'A')
        self.assertEquals(self.grid.gather_constraints(5, 0, "across"), [])
        self.assertEquals(self.grid.gather_constraints(0, 0, "across"), [(0, 'a')])
        
        self.grid.set_block(5, 0, False)
        self.grid.set_bar(5, 0, "left", True)
        self.assertEquals(self.grid.gather_constraints(5, 0, "across"), [])
        self.assertEquals(self.grid.gather_constraints(0, 0, "across"), [(0, 'a')])
        
        self.grid.set_void(0, 5, True)
        self.grid.set_char(0, 4, 'Z')
        self.assertEquals(self.grid.gather_constraints(0, 5, "down"), [])
        self.assertEquals(self.grid.gather_constraints(0, 0, "down"), [(0, 'a'), (4, 'z')])
        
    def testGatherAllConstraints(self):
        self.grid.set_block(0, 0, True)
        self.grid.set_block(1, 1, True)
        self.grid.set_block(2, 2, True)
        self.grid.set_block(3, 3, True)
        self.assertEquals(self.grid.gather_all_constraints(0, 3, "across"), [(2, 14, []), (1, 13, []), (0, 12, [])])
        self.assertEquals(self.grid.gather_all_constraints(3, 0, "down"), [(2, 11, []), (1, 10, []), (0, 9, [])])
        
    def testDecomposeWord(self):
        self.assertEquals(decompose_word("abc", 0, 0, "across"), [(0, 0, 'a'), (1, 0, 'b'), (2, 0, 'c')])
        self.assertEquals(decompose_word("def", 0, 0, "down"), [(0, 0, 'd'), (0, 1, 'e'), (0, 2, 'f')])
        
    def testClues(self):
        ac = [clue for clue in self.grid.clues("across")]
        dc = [clue for clue in self.grid.clues("down")]
        ac2 = [(1, 0, 0, {})] + [(13 + i, 0, i + 1, {}) for i in xrange(self.grid.height - 1)] 
        self.assertEquals(ac, ac2)
        dc2 = [(1 + i, i, 0, {}) for i in xrange(self.grid.width)]
        self.assertEquals(dc, dc2)
        self.grid.data[0][0]["clues"] = {"down": {"text": "TEST"}}
        dc = [clue for clue in self.grid.clues("down")]
        dc3 = [(1, 0, 0, {"text": "TEST"})] + [(1 + i, i, 0, {}) for i in xrange(1, self.grid.width)]
        self.assertEquals(dc, dc3)
        
    def testNumbering(self):
        g = Grid(15, 15)
        self.assertEquals(g.data[0][0]["number"], 1)
        g = Grid(15, 15, number_mode=constants.NUMBERING_MANUAL)
        for x, y in g.cells():
            self.assertEquals(g.data[y][x]["number"], 0)
        g.set_number(5, 5, 33)
        self.assertEquals(g.data[5][5]["number"], 33)
        
    def testCountComplete(self):
        counts = self.grid.count_complete()
        self.assertEquals(counts["across"], 0)
        self.assertEquals(counts["down"], 0)
        for x in xrange(self.grid.width):
            self.grid.set_char(x, 0, 'A')
        counts = self.grid.count_complete()
        self.assertEquals(counts["across"], 1)
        self.assertEquals(counts["down"], 0)
        for y in xrange(self.grid.height):
            self.grid.set_char(0, y, 'A')
        counts = self.grid.count_complete()
        self.assertEquals(counts["across"], 1)
        self.assertEquals(counts["down"], 1)
        
    def testStatus(self):
        self.grid.set_block(0, 0, True)
        self.grid.set_char(1, 0, 'A')
        self.grid.set_void(2, 0, True)
        status = self.grid.determine_status(full=False)
        KEYS = ["block_count"
            , "void_count"
            , "char_count"
            , "actual_char_count"
            , "word_count"
            , "block_percentage"
        ]
        for key in KEYS:
            self.assertEquals(key in status, True)
        status = self.grid.determine_status(full=True)
        KEYS2 = ["mean_word_length"
            , "blank_count"
            , "word_counts"
            , "char_counts"
            , "char_counts_total"
            , "checked_count"
            , "unchecked_count"
            , "clue_count"
            , "open_count"
            , "connected"
            , "complete_count"
        ]
        for key in KEYS + KEYS2:
            self.assertEquals(key in status, True)
        self.assertEquals(status["block_count"], 1)
        self.assertEquals(status["void_count"], 1)
        self.assertEquals(status["actual_char_count"], 1)
        self.assertEquals(status["checked_count"], (self.grid.width * self.grid.height) - 3)
        self.assertEquals(status["unchecked_count"], 1);
        
    def testGridString(self):
        s = str(self.grid)
        g = Grid(12, 15)
        g.set_block(0, 0, True)
        t = str(g)
        g = Grid(12, 15)
        g.set_void(0, 0, True)
        u = str(g)
        self.assertNotEquals(s, t)
        self.assertNotEquals(s, u)
        self.assertNotEquals(t, u)
        
    def testDiagonalCells(self):
        g = Grid(5, 5)
        s = g.generate_diagonals(0)
        self.assertEquals(len(s), 7)
        self.assertEquals(sum([len(i) for i in s]), len(list(g.cells())) - 2)
        g.set_block(1, 1, True)
        s = g.generate_diagonals(0)
        self.assertEquals(len(s), 6)
        self.assertEquals(sum([len(i) for i in s]), len(list(g.cells())) - 5)
        g.set_void(3, 3, True)
        s = g.generate_diagonals(0)
        self.assertEquals(len(s), 5)
        self.assertEquals(sum([len(i) for i in s]), len(list(g.cells())) - 8)
        result = [[(0, 1), (1, 0)]
            , [(0, 3), (1, 2), (2, 1), (3, 0)]
            , [(0, 4), (1, 3), (2, 2), (3, 1), (4, 0)]
            , [(1, 4), (2, 3), (3, 2), (4, 1)]
            , [(3, 4), (4, 3)]]
        self.assertEquals(s, result)
        s = g.generate_diagonals(1)
        self.assertEquals(sum([len(i) for i in s]), len(list(g.cells())) - 7)
        
    def testCellOfSlot(self):
        g = Grid(5, 5)
        g.set_block(0, 0, True)
        self.assertEquals(g.get_cell_of_slot((3, 0, "across"), "start"), (1, 0))
        self.assertEquals(g.get_cell_of_slot((3, 0, "across"), "end"), (4, 0))
        self.assertEquals(g.get_cell_of_slot((3, 0, "down"), "start"), (3, 0))
        self.assertEquals(g.get_cell_of_slot((3, 0, "down"), "end"), (3, 4))
        
    def testGenerateAllSlots(self):
        g = Grid(5, 5)
        slots = g.generate_all_slots()
        # across + down + ne + se + sw + nw
        self.assertEquals(len(slots), 5 + 5 + 7 + 7 + 7 + 7)
        fives = [s for s in slots if len(s[1]) == 5]
        self.assertEquals(len(fives), 5 + 5 + 1 + 1 + 1 + 1)
        fours = [s for s in slots if len(s[1]) == 4]
        self.assertEquals(len(fours), 0 + 0 + 2 + 2 + 2 + 2)
        threes = [s for s in slots if len(s[1]) == 3]
        self.assertEquals(len(threes), 0 + 0 + 2 + 2 + 2 + 2)
        twos = [s for s in slots if len(s[1]) == 2]
        self.assertEquals(len(twos), 0 + 0 + 2 + 2 + 2 + 2)
        ones = [s for s in slots if len(s[1]) == 1]
        self.assertEquals(len(ones), 0)
        
    def testGenerateAllSlotsBlockVoid(self):
        #   _ _ _
        # _ _ _ _ _
        # _ _ X _ _
        # _ _ _ _ _
        #   _ _ _
        g = Grid(5, 5)
        g.set_block(2, 2, True)
        g.set_void(0, 0, True)
        g.set_void(4, 0, True)
        g.set_void(0, 4, True)
        g.set_void(4, 4, True)
        slots = g.generate_all_slots()
        # across + down + ne + se + sw + nw
        self.assertEquals(len(slots), 6 + 6 + 6 + 6 + 6 + 6)
        twos = [s for s in slots if len(s[1]) == 2]
        self.assertEquals(len(twos), 2 + 2 + 2 + 2 + 2 + 2)
        
    def testGenerateAllSlotsWords(self):
        # _ A _ _ _
        # B _ _ _ _
        # _ C _ _ _
        # _ _ _ _ _
        # _ _ _ _ _
        g = Grid(5, 5)
        g.set_char(1, 0, 'A')
        g.set_char(0, 1, 'B')
        g.set_char(1, 2, 'C')
        slots = g.generate_all_slots()
        self.assertTrue(("ne", [(0, 1, 'B'), (1, 0, 'A')]) in slots)
        seq = [(0, 1, 'B'), (1, 2, 'C'), (2, 3, constants.MISSING_CHAR), (3, 4, constants.MISSING_CHAR)]
        self.assertTrue(("se", seq) in slots)
