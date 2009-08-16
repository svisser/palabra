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

import os
import unittest

from palabralib.files import read_crossword, write_crossword_to_xml
from palabralib.grid import Grid
from palabralib.puzzle import Puzzle

class FilesTestCase(unittest.TestCase):
    LOCATION = "palabralib/tests/test_files.xml"
    
    def setUp(self):
        self.puzzle = Puzzle(Grid(15, 15))
        self.puzzle.filename = self.LOCATION
        
    def tearDown(self):
        os.remove(self.LOCATION)
        
    def testReadWrite(self):
        clues = {"text": "foo", "explanation": "bar"}
        self.puzzle.grid.set_block(0, 0, True)
        self.puzzle.grid.set_char(1, 1, "A")
        self.puzzle.grid.cell(2, 2)["clues"]["across"] = clues
    
        write_crossword_to_xml(self.puzzle)
        puzzle = read_crossword(self.LOCATION)

        self.assertEqual(puzzle.grid.is_block(0, 0), True)
        self.assertEqual(puzzle.grid.get_char(1, 1), "A")
        self.assertEqual(puzzle.grid.cell(2, 2)["clues"]["across"], clues)
        for x, y in self.puzzle.grid.cells():
            self.assertEqual(puzzle.grid.cell(x, y), self.puzzle.grid.cell(x, y))
