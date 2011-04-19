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
    write_xpf,
    read_xpf,
    determine_file_type,
    ParserError,
    XPFParserError,
)
from palabralib.grid import Grid
from palabralib.puzzle import Puzzle
from palabralib.view import CellStyle

class FilesTestCase(unittest.TestCase):
    LOCATION = "palabralib/tests/test_xpf.xml"
    LOCATION2 = "palabralib/tests/test_not_xpf.txt"
    
    def setUp(self):
        self.puzzle = Puzzle(Grid(15, 15))
        self.puzzle.filename = self.LOCATION
        
    def tearDown(self):
        for f in [self.LOCATION, self.LOCATION2]:
            if os.path.exists(f):
                os.remove(f)
                
    def testXPFBackup(self):
        write_xpf(self.puzzle, backup=False)
        write_xpf(self.puzzle, backup=True)
        results = read_xpf(self.LOCATION + "~")
        results[0].filename = self.LOCATION
        self.assertEquals(self.puzzle, results[0])
        
    def testXPFMeta(self):
        self.puzzle.metadata['title'] = "TestTitle"
        self.puzzle.metadata['creator'] = "TestCreator"
        self.puzzle.metadata['contributor'] = "TestContributor"
        self.puzzle.metadata['rights'] = "TestRights"
        self.puzzle.metadata['publisher'] = "TestPublisher"
        self.puzzle.metadata['date'] = "TestDate"
        write_xpf(self.puzzle, False)
        results = read_xpf(self.LOCATION)
        self.assertEquals(len(results), 1)
        self.assertEquals(results[0], self.puzzle)
            
    def testXPFOne(self):
        self.puzzle.grid.set_block(0, 0, True)
        self.puzzle.grid.set_void(5, 5, True)
        self.puzzle.grid.set_char(3, 3, "A")
        self.puzzle.grid.store_clue(1, 0, "across", "text", "This is a clue")
        self.puzzle.grid.store_clue(5, 6, "down", "explanation", "This is an explanation")
        self.puzzle.grid.assign_numbers()
        self.puzzle.metadata['title'] = "This is the title"
        self.puzzle.notepad = '''\"Notepad with weird chars < > & " \"'''
        
        style = CellStyle()
        style.circle = True
        self.puzzle.view.properties.styles[2, 2] = style
        style = CellStyle()
        style.cell["color"] = (65535, 0, 0)
        self.puzzle.view.properties.styles[4, 4] = style
        
        write_xpf(self.puzzle, False)
        results = read_xpf(self.LOCATION)
        self.assertEquals(len(results), 1)
        self.assertEquals(self.puzzle.grid, results[0].grid)
        self.assertEquals(self.puzzle, results[0])
        
    def testXPFErrors(self):
        with open(self.LOCATION2, 'w') as f:
            f.write("THIS IS NOT XML")
        self.assertRaises(XPFParserError, read_xpf, self.LOCATION2)
        with open(self.LOCATION2, 'w') as f:
            f.write("<NotPuzzlesElement></NotPuzzlesElement>")
        self.assertRaises(XPFParserError, read_xpf, self.LOCATION2)
        with open(self.LOCATION2, 'w') as f:
            f.write("<Puzzles></Puzzles>")
        self.assertRaises(XPFParserError, read_xpf, self.LOCATION2)
        with open(self.LOCATION2, 'w') as f:
            f.write("<Puzzles Version=\"not_a_number\"></Puzzles>")
        self.assertRaises(XPFParserError, read_xpf, self.LOCATION2)
        with open(self.LOCATION2, 'w') as f:
            f.write("<Puzzles Version=\"0.99\"></Puzzles>")
        self.assertRaises(XPFParserError, read_xpf, self.LOCATION2)
        
    def testXPFErrors2(self):
        write_xpf(self.puzzle, False)
        with open(self.LOCATION, 'r') as f:
            xml_text = f.read()
        with open(self.LOCATION, 'w') as f:
            text = xml_text.replace("<Size><Rows>15</Rows><Cols>15</Cols></Size>", "<Size><Cols>15</Cols></Size>")
            f.write(text)
        self.assertRaises(XPFParserError, read_xpf, self.LOCATION)
        with open(self.LOCATION, 'w') as f:
            text = xml_text.replace("<Size><Rows>15</Rows><Cols>15</Cols></Size>", "<Size><Rows>15</Rows></Size>")
            f.write(text)
        self.assertRaises(XPFParserError, read_xpf, self.LOCATION)
        
    def testReadCrossword(self):
        write_xpf(self.puzzle)
        p = read_crossword(self.LOCATION)
        self.assertEquals(self.puzzle, p)
        
    def testReadCrosswordErrors(self):
        with open(self.LOCATION, 'w') as f:
            f.write("This is not XML")
        self.assertRaises(ParserError, read_crossword, self.LOCATION)
        
    def testDetermineFileType(self):
        with open(self.LOCATION, 'w') as f:
            f.write('<NotQuitePuzzles></NotQuitePuzzles>')
        self.assertEquals(determine_file_type(self.LOCATION), None)
        self.assertRaises(ParserError, read_crossword, self.LOCATION)
