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

import os
import unittest

from lxml import etree

import palabralib.constants as constants
from palabralib.files import (
    read_crossword, 
    write_palabra,
    _read_metadata,
    _write_metadata,
    _read_grid,
    _write_grid,
    _read_clues,
    _write_clues,
    read_palabra,
    write_palabra,
    read_xpf,
    write_xpf,
)
from palabralib.grid import Grid
from palabralib.puzzle import Puzzle

class FilesTestCase(unittest.TestCase):
    LOCATION = "palabralib/tests/test_files.xml"
    
    def setUp(self):
        self.puzzle = Puzzle(Grid(15, 15))
        self.puzzle.filename = self.LOCATION
        
    def tearDown(self):
        if os.path.exists(self.LOCATION):
            os.remove(self.LOCATION)
            
    def testPalabra(self):
        clues = {"text": "foo", "explanation": "bar"}
        self.puzzle.grid.set_block(0, 0, True)
        self.puzzle.grid.set_void(5, 5, True)
        self.puzzle.grid.set_char(1, 1, "A")
        self.puzzle.grid.cell(2, 2)["clues"]["across"] = clues
        self.puzzle.grid.cell(3, 3)["bar"]["top"] = True
        self.puzzle.grid.cell(4, 4)["bar"]["left"] = True
        # TODO modify when arbitrary number schemes are implemented
        self.puzzle.grid.assign_numbers()
        self.puzzle.metadata = {"title": "A"
            , "creator": "B"
            , "description": "C"}
        self.puzzle.type = constants.PUZZLE_PALABRA
    
        write_palabra(self.puzzle, False)
        content = read_palabra(self.LOCATION)
        self.assertEquals(len(content), 1)
        self.assertEqual(content[0], self.puzzle)
        
    def testXPF(self):
        clues = {"text": "foo"}
        self.puzzle.grid.set_block(0, 0, True)
        self.puzzle.grid.set_char(1, 1, "A")
        self.puzzle.grid.cell(1, 0)["clues"]["across"] = clues
        # TODO modify when arbitrary number schemes are implemented
        self.puzzle.grid.assign_numbers()
        self.puzzle.metadata = {"title": "A", "creator": "B"}
        self.puzzle.type = constants.PUZZLE_XPF
    
        write_xpf(self.puzzle, False)
        content = read_xpf(self.LOCATION)
        self.assertEquals(len(content), 1)
        self.assertEqual(content[0], self.puzzle)
