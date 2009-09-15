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

from lxml import etree

from palabralib.files import (
    read_crossword, 
    write_crossword_to_xml,
    _read_metadata,
    _write_metadata,
    _read_grid,
    _write_grid,
    _read_clues,
    _write_clues,
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
        
    def testReadWriteCrossword(self):
        clues = {"text": "foo", "explanation": "bar"}
        self.puzzle.grid.set_block(0, 0, True)
        self.puzzle.grid.set_void(5, 5, True)
        self.puzzle.grid.set_char(1, 1, "A")
        self.puzzle.grid.cell(2, 2)["clues"]["across"] = clues
        self.puzzle.grid.cell(3, 3)["bar"]["top"] = True
        self.puzzle.grid.cell(4, 4)["bar"]["left"] = True
        self.puzzle.metadata = {"title": "A", "author": "B"}
    
        write_crossword_to_xml(self.puzzle)
        puzzle = read_crossword(self.LOCATION)
        for x, y in self.puzzle.grid.cells():
            self.assertEqual(puzzle.grid.cell(x, y), self.puzzle.grid.cell(x, y))
        self.assertEqual(puzzle.metadata["title"], "A")
        self.assertEqual(puzzle.metadata["author"], "B")
        
    def testReadWriteMetadata(self):
        metadata = {"title": "A"
            , "author": "B"
            , "copyright": "C"
            , "description": "D"}
        root = etree.Element("root")
        _write_metadata(root, metadata)
        result = _read_metadata(root[0])
        self.assertEqual(result, metadata)
        
    def testReadWriteGrid(self):
        clues = {"text": "C", "explanation": "D"}
        self.puzzle.grid.set_block(5, 5, True)
        self.puzzle.grid.set_char(6, 6, "A")
        self.puzzle.grid.set_void(7, 7, True)
        root = etree.Element("root")
        _write_grid(root, self.puzzle.grid)
        result = _read_grid(root[0])
        self.assertEqual(result.is_block(5, 5), True)
        self.assertEqual(result.get_char(6, 6), "A")
        self.assertEqual(result.is_void(7, 7), True)
        
    def testReadWriteClues(self):
        a = {"text": "foo", "explanation": "bar"}
        self.puzzle.grid.cell(0, 0)["clues"]["across"] = a
        d = {"text": "bar", "explanation": "foo"}
        self.puzzle.grid.cell(0, 0)["clues"]["down"] = d
        root = etree.Element("root")
        _write_clues(root, self.puzzle.grid, "across")
        _write_clues(root, self.puzzle.grid, "down")
        dir_a, result_a = _read_clues(root[0])
        dir_d, result_d = _read_clues(root[1])
        self.assertEqual(dir_a, "across")
        self.assertEqual(dir_d, "down")
        self.assertEqual((0, 0, a) in result_a, True)
        self.assertEqual((0, 0, d) in result_d, True)
