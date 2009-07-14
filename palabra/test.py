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
import copy

from action import (
    FullTransformAction,
)
from grid import Grid
from puzzle import Puzzle
import transform

class ActionTest(unittest.TestCase):
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

class GridTest(unittest.TestCase):
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
    
    def testGatherWord(self):
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

class TransformTest(unittest.TestCase):
    def setUp(self):
        self.puzzle = Puzzle(Grid(15, 15))
        self.puzzle.grid.set_block(0, 0, True)
        
    def testClearAll(self):
        #transform.clear_all(self.puzzle)
        pass
        
if __name__ == '__main__':
    unittest.main()
