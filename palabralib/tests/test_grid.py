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

from palabralib.grid import Grid

class GridTestCase(unittest.TestCase):
    def setUp(self):
        self.grid = Grid(12, 15)
        
    def testSize(self):
        self.assertEqual(self.grid.width, 12)
        self.assertEqual(self.grid.height, 15)
        
    def testBlock(self):
        self.assertEqual(self.grid.is_block(3, 3), False)
        self.assertEqual(self.grid.is_block(5, 5), False)
        self.grid.set_block(5, 5, True)
        self.assertEqual(self.grid.is_block(3, 3), False)
        self.assertEqual(self.grid.is_block(5, 5), True)
        self.grid.set_block(5, 5, False)
        self.assertEqual(self.grid.is_block(3, 3), False)
        self.assertEqual(self.grid.is_block(5, 5), False)
        
    def testChar(self):
        self.assertEqual(self.grid.get_char(3, 3), "")
        self.assertEqual(self.grid.get_char(5, 5), "")
        self.assertEqual(self.grid.is_char(3, 3), False)
        self.assertEqual(self.grid.is_char(5, 5), False)
        self.grid.set_char(5, 5, "A")
        self.assertEqual(self.grid.get_char(3, 3), "")
        self.assertEqual(self.grid.get_char(5, 5), "A")
        self.assertEqual(self.grid.is_char(3, 3), False)
        self.assertEqual(self.grid.is_char(5, 5), True)
        self.grid.set_char(5, 5, "")
        self.assertEqual(self.grid.get_char(3, 3), "")
        self.assertEqual(self.grid.get_char(5, 5), "")
        self.assertEqual(self.grid.is_char(3, 3), False)
        self.assertEqual(self.grid.is_char(5, 5), False)
        
    def testIsStartHorizontalWord(self):
        self.assertEqual(self.grid.is_start_horizontal_word(0, 0), True)
        self.grid.set_block(1, 0, True)
        self.assertEqual(self.grid.is_start_horizontal_word(0, 0), False)
        self.grid.set_block(1, 0, False)
        self.grid.set_block(2, 0, True)
        self.assertEqual(self.grid.is_start_horizontal_word(0, 0), True)
        
        self.assertEqual(self.grid.is_start_horizontal_word(5, 5), False)
        self.grid.set_block(4, 5, True)
        self.assertEqual(self.grid.is_start_horizontal_word(5, 5), True)
        
        cond = self.grid.is_start_horizontal_word(self.grid.width - 1, 0)
        self.assertEqual(cond, False)
        
    def testIsStartVerticalWord(self):
        self.assertEqual(self.grid.is_start_vertical_word(0, 0), True)
        self.grid.set_block(0, 1, True)
        self.assertEqual(self.grid.is_start_vertical_word(0, 0), False)
        self.grid.set_block(0, 1, False)
        self.grid.set_block(0, 2, True)
        self.assertEqual(self.grid.is_start_vertical_word(0, 0), True)
        
        self.assertEqual(self.grid.is_start_vertical_word(5, 5), False)
        self.grid.set_block(5, 4, True)
        self.assertEqual(self.grid.is_start_vertical_word(5, 5), True)
        
        cond = self.grid.is_start_vertical_word(0, self.grid.height - 1)
        self.assertEqual(cond, False)
        
    def testIsStartWord(self):
        self.assertEqual(self.grid.is_start_word(0, 0), True)
        self.grid.set_block(0, 1, True)
        self.assertEqual(self.grid.is_start_word(0, 0), True)
        self.grid.set_block(1, 0, True)
        self.assertEqual(self.grid.is_start_word(0, 0), False)
        
    def testGetStartHorizontalWord(self):
        for x in range(self.grid.width):
            p, q = self.grid.get_start_horizontal_word(x, 0)
            self.assertEqual(p, 0)
            self.assertEqual(q, 0)
            
        self.grid.set_block(5, 0, True)
        p, q = self.grid.get_start_horizontal_word(5, 0)
        self.assertEqual(p, 5)
        self.assertEqual(q, 0)
        
        for x in range(0, 5):
            p, q = self.grid.get_start_horizontal_word(x, 0)
            self.assertEqual(p, 0)
            self.assertEqual(q, 0)
        for x in range(6, self.grid.width):
            p, q = self.grid.get_start_horizontal_word(x, 0)
            self.assertEqual(p, 6)
            self.assertEqual(q, 0)
            
    def testGetStartVerticalWord(self):
        for y in range(self.grid.height):
            p, q = self.grid.get_start_vertical_word(0, y)
            self.assertEqual(p, 0)
            self.assertEqual(q, 0)
            
        self.grid.set_block(0, 5, True)
        p, q = self.grid.get_start_vertical_word(0, 5)
        self.assertEqual(p, 0)
        self.assertEqual(q, 5)
        
        for y in range(0, 5):
            p, q = self.grid.get_start_vertical_word(0, y)
            self.assertEqual(p, 0)
            self.assertEqual(q, 0)
        for y in range(6, self.grid.height):
            p, q = self.grid.get_start_vertical_word(0, y)
            self.assertEqual(p, 0)
            self.assertEqual(q, 6)
            
    def testCheckCount(self):
        self.assertEqual(self.grid.get_check_count(5, 5), 2)
        self.grid.set_block(4, 5, True)
        self.assertEqual(self.grid.get_check_count(5, 5), 2)
        self.grid.set_block(6, 5, True)
        self.assertEqual(self.grid.get_check_count(5, 5), 1)
        self.grid.set_block(5, 4, True)
        self.assertEqual(self.grid.get_check_count(5, 5), 1)
        self.grid.set_block(5, 6, True)
        self.assertEqual(self.grid.get_check_count(5, 5), 0)
        self.grid.set_block(5, 5, True)
        self.assertEqual(self.grid.get_check_count(5, 5), -1)
    
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
            
    def testCountBlocks(self):
        self.assertEqual(self.grid.count_blocks(), 0)
        
        for i in range(10):
            self.grid.set_block(i, i, True)
        self.assertEqual(self.grid.count_blocks(), 10)
        
        for i in range(10):
            self.grid.set_block(i, i, False)
        self.assertEqual(self.grid.count_blocks(), 0)
        
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
        
    def testHorizontalWords(self):
        n = len([1 for x in self.grid.horizontal_words()])
        self.assertEquals(self.grid.height, n)
        
        for y in xrange(self.grid.height):
            self.grid.set_block(2, y, True)
        xs = [x for n, x, y in self.grid.horizontal_words()]
        self.assertEquals(xs, [0, 3] * self.grid.height)
        
    def testVerticalWords(self):
        n = len([1 for x in self.grid.vertical_words()])
        self.assertEquals(self.grid.width, n)
        
        for x in xrange(self.grid.width):
            self.grid.set_block(x, 2, True)
        ys = [y for n, x, y in self.grid.vertical_words()]
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
        for x, y in self.grid.in_direction("across", 0, 0):
            self.assertEquals(self.grid.is_block(x, y), False)
            self.assertEquals(self.grid.get_char(x, y), "")

        self.grid.insert_row(1, False)
        self.assertEquals(self.grid.width, width)
        self.assertEquals(self.grid.height, height + 2)
        cells = [(0, 0), (0, 1), (0, 2), (0, 3)]
        bs = [self.grid.is_block(x, y) for x, y in cells]
        self.assertEquals(bs, [False, True, False, True])
        
    def testInsertColumn(self):
        width, height = self.grid.width, self.grid.height
        self.grid.set_block(0, 0, True)
        self.grid.set_block(1, 0, True)
        
        self.grid.insert_column(0, True)
        self.assertEquals(self.grid.width, width + 1)
        self.assertEquals(self.grid.height, height)
        bs = [self.grid.is_block(x, y) for x, y in [(0, 0), (1, 0), (2, 0)]]
        self.assertEquals(bs, [False, True, True])
        for x, y in self.grid.in_direction("down", 0, 0):
            self.assertEquals(self.grid.is_block(x, y), False)
            self.assertEquals(self.grid.get_char(x, y), "")

        self.grid.insert_column(1, False)
        self.assertEquals(self.grid.width, width + 2)
        self.assertEquals(self.grid.height, height)
        cells = [(0, 0), (1, 0), (2, 0), (3, 0)]
        bs = [self.grid.is_block(x, y) for x, y in cells]
        self.assertEquals(bs, [False, True, False, True])
        
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
