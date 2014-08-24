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
    FILETYPES,
    read_crossword,
    write_xpf,
    read_xpf,
    determine_file_type,
    ParserError,
    XPFParserError,
    color_to_hex,
    hex_to_color,
    read_ipuz,
    write_ipuz,
    compute_header,
)
import palabralib.files as files
from palabralib.grid import Grid
from palabralib.puzzle import Puzzle
from palabralib.view import CellStyle, _relative_to

METADATA = {
    constants.META_TITLE: "TestTitle"
    , constants.META_CREATOR: "TestCreator"
    , constants.META_EDITOR: "TestEditor"
    , constants.META_COPYRIGHT: "TestRights"
    , constants.META_PUBLISHER: "TestPublisher"
    , constants.META_DATE: "TestDate"
}

class FilesTestCase(unittest.TestCase):
    LOCATION = "palabralib/tests/test.puzzle"
    LOCATION2 = "palabralib/tests/test.not_puzzle"
    LOCATION3 = "palabralib/tests/test.container"
    _LOCATION3B = "tests/test.container"
    
    def setUp(self):
        # XPF
        self.puzzle = Puzzle(Grid(15, 15))
        self.puzzle.filename = self.LOCATION
        
        # IPUZ
        self.ipuzzle = Puzzle(Grid(15, 15))
        self.ipuzzle.type = constants.PUZZLE_IPUZ
        self.ipuzzle.filename = self.LOCATION
        
    def tearDown(self):
        for f in [self.LOCATION, self.LOCATION2, self.LOCATION3]:
            if os.path.exists(f):
                os.remove(f)
                
    def testXPFBackup(self):
        write_xpf(self.puzzle, backup=False)
        write_xpf(self.puzzle, backup=True)
        results = read_xpf(self.LOCATION + "~", warnings=False)
        results[0].filename = self.LOCATION
        self.assertEqual(self.puzzle, results[0])
        
    def testIPUZBackup(self):
        write_ipuz(self.ipuzzle, backup=False)
        write_ipuz(self.ipuzzle, backup=True)
        results = read_ipuz(self.LOCATION + "~", warnings=False)
        results[0].filename = self.LOCATION
        self.assertEqual(self.ipuzzle, results[0])
        
    def testHexColor(self):
        for c0 in ["#abcdef", "#654321"]:
            c1 = color_to_hex(hex_to_color(c0), include=True)
            self.assertEqual(c0, c1)
        for c0 in ["abcdef", "eb8832", "123456"]:
            c1 = color_to_hex(hex_to_color(c0), include=False)
            self.assertEqual(c0, c1)
        
    def testXPFMeta(self):
        self.puzzle.metadata.update(METADATA)
        write_xpf(self.puzzle, False)
        results = read_xpf(self.LOCATION, warnings=False)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.puzzle)
            
    def testReadWriteXPF(self):
        self.puzzle.grid.set_block(0, 0, True)
        self.puzzle.grid.set_void(5, 5, True)
        self.puzzle.grid.set_char(3, 3, "A")
        self.puzzle.grid.store_clue(1, 0, "across", "text", "This is a clue")
        self.puzzle.grid.store_clue(5, 6, "down", "explanation", "This is an explanation")
        self.puzzle.grid.set_rebus(0, 1, "Y", "YELLOW")
        self.puzzle.grid.assign_numbers()
        self.puzzle.metadata['title'] = "This is the title"
        self.puzzle.notepad = '''\"Notepad with weird chars < > & " \"'''
        write_xpf(self.puzzle, False)
        results = read_xpf(self.LOCATION, warnings=False)
        self.assertEqual(len(results), 1)
        self.assertEqual(self.puzzle, results[0])
    
    def testReadWriteIPUZ(self):
        self.ipuzzle.grid.set_block(0, 0, True)
        self.ipuzzle.grid.set_void(5, 5, True)
        self.ipuzzle.grid.set_char(3, 3, "A")
        self.ipuzzle.grid.store_clue(1, 0, "across", "text", "This is a clue")
        self.ipuzzle.grid.assign_numbers()
        self.ipuzzle.metadata['title'] = "This is the title"
        self.ipuzzle.metadata['difficulty'] = "This is the difficulty"
        write_ipuz(self.ipuzzle, False)
        results = read_ipuz(self.LOCATION, warnings=False)
        self.assertEqual(len(results), 1)
        self.assertEqual(self.ipuzzle, results[0])
        
    def testIPUZTech(self):
        self.ipuzzle.grid.set_block(3, 4, True)
        self.ipuzzle.grid.assign_numbers()
        self.ipuzzle.metadata['block'] = "B"
        self.ipuzzle.metadata['empty'] = "_"
        write_ipuz(self.ipuzzle, False)
        results = read_ipuz(self.LOCATION, warnings=False)
        self.assertEqual(self.ipuzzle, results[0])
        
    def testStyleIPUZ(self):
        props = self.ipuzzle.view.properties
        style = CellStyle()
        style["circle"] = True
        props.styles[2, 2] = style
        style = CellStyle()
        style["cell", "color"] = (65535, 0, 0)
        style["char", "color"] = (0, 65535, 0)
        props.styles[4, 4] = style
        write_ipuz(self.ipuzzle, False)
        results = read_ipuz(self.LOCATION, warnings=False)
        self.assertEqual(self.ipuzzle, results[0])
        
    def testStyleXPF(self):
        props = self.puzzle.view.properties
        props.update(2, 2, [("circle", True)])
        style = CellStyle()
        style["cell", "color"] = (65535, 0, 0)
        props.styles[4, 4] = style
        write_xpf(self.puzzle, False)
        results = read_xpf(self.LOCATION, warnings=False)
        self.assertEqual(self.puzzle, results[0])
        
        # test 'gray' as shade color
        with open(self.LOCATION, 'r') as f:
            xml_text = f.read()
        with open(self.LOCATION, 'w') as f:
            text = xml_text.replace("<Shade Row=\"5\" Col=\"5\">#ff0000</Shade>"
                , "<Shade Row=\"5\" Col=\"5\">gray</Shade>")
            f.write(text)
        results = read_xpf(self.LOCATION, warnings=False)
        self.puzzle.view.properties.styles[4, 4]["cell", "color"] = (32767, 32767, 32767)
        s1 = self.puzzle.view.properties.styles[4, 4]
        s2 = results[0].view.properties.styles[4, 4]
        self.assertEqual(s1, s2)
        
    def testXPFErrors(self):
        with open(self.LOCATION2, 'w') as f:
            f.write("THIS IS NOT XML")
        self.assertRaises(XPFParserError, read_xpf, self.LOCATION2, warnings=False)
        with open(self.LOCATION2, 'w') as f:
            f.write("<NotPuzzlesElement></NotPuzzlesElement>")
        self.assertRaises(XPFParserError, read_xpf, self.LOCATION2, warnings=False)
        with open(self.LOCATION2, 'w') as f:
            f.write("<Puzzles></Puzzles>")
        self.assertRaises(XPFParserError, read_xpf, self.LOCATION2, warnings=False)
        with open(self.LOCATION2, 'w') as f:
            f.write("<Puzzles Version=\"not_a_number\"></Puzzles>")
        self.assertRaises(XPFParserError, read_xpf, self.LOCATION2, warnings=False)
        with open(self.LOCATION2, 'w') as f:
            f.write("<Puzzles Version=\"0.99\"></Puzzles>")
        self.assertRaises(XPFParserError, read_xpf, self.LOCATION2, warnings=False)
        
    def testXPFErrors2(self):
        write_xpf(self.puzzle, False)
        with open(self.LOCATION, 'r') as f:
            xml_text = f.read()
        with open(self.LOCATION, 'w') as f:
            text = xml_text.replace("<Size><Rows>15</Rows><Cols>15</Cols></Size>"
                , "<Size><Cols>15</Cols></Size>")
            f.write(text)
        self.assertRaises(XPFParserError, read_xpf, self.LOCATION, warnings=False)
        with open(self.LOCATION, 'w') as f:
            text = xml_text.replace("<Size><Rows>15</Rows><Cols>15</Cols></Size>"
                , "<Size><Rows>15</Rows></Size>")
            f.write(text)
        self.assertRaises(XPFParserError, read_xpf, self.LOCATION, warnings=False)
        with open(self.LOCATION, 'w') as f:
            text = xml_text.replace("<Size><Rows>15</Rows><Cols>15</Cols></Size>"
                , "<Size><Rows>noNumber</Rows><Cols>15</Cols></Size>")
            f.write(text)
        self.assertRaises(XPFParserError, read_xpf, self.LOCATION, warnings=False)
        with open(self.LOCATION, 'w') as f:
            text = xml_text.replace("<Size><Rows>15</Rows><Cols>15</Cols></Size>"
                , "<Size><Rows>15</Rows><Cols>noNumber</Cols></Size>")
            f.write(text)
        self.assertRaises(XPFParserError, read_xpf, self.LOCATION, warnings=False)
        
    # the following tests are just to make sure the parser doesn't stop somewhere
    def testXPFCanComplete1(self):
        write_xpf(self.puzzle, False)
        with open(self.LOCATION, 'r') as f:
            xml_text = f.read()
        with open(self.LOCATION, 'w') as f:
            text = xml_text.replace("<Row>               </Row>"
                , "<Row></Row>")
            f.write(text)
        read_xpf(self.LOCATION, warnings=False)
        with open(self.LOCATION, 'w') as f:
            text = xml_text.replace("<Row>               </Row>"
                , "<Row>TOO.SHORT</Row>")
            f.write(text)
        read_xpf(self.LOCATION, warnings=False)
        with open(self.LOCATION, 'w') as f:
            text = xml_text.replace("<Row>               </Row>"
                , "<NotRow>               </NotRow>")
            f.write(text)
        read_xpf(self.LOCATION, warnings=False)
        
    def testXPFCanComplete2(self):
        style = CellStyle()
        style.circle = True
        self.puzzle.view.properties.styles[0, 0] = style
        write_xpf(self.puzzle, False)
        with open(self.LOCATION, 'r') as f:
            xml_text = f.read()
        with open(self.LOCATION, 'w') as f:
            text = xml_text.replace("<Circle Row=\"1\" Col=\"1\"/>"
                , "<Circle Row=\"1\"/>")
            f.write(text)
        read_xpf(self.LOCATION, warnings=False)
        with open(self.LOCATION, 'w') as f:
            text = xml_text.replace("<Circle Row=\"1\" Col=\"1\"/>"
                , "<Circle Col=\"1\"/>")
            f.write(text)
        read_xpf(self.LOCATION, warnings=False)
        with open(self.LOCATION, 'w') as f:
            text = xml_text.replace("<Circle Row=\"1\" Col=\"1\"/>"
                , "<NotQuiteACircle/>")
            f.write(text)
        read_xpf(self.LOCATION, warnings=False)
        with open(self.LOCATION, 'w') as f:
            text = xml_text.replace("<Circle Row=\"1\" Col=\"1\"/>"
                , "<Circle Row=\"noNumber\" Col=\"1\"/>")
            f.write(text)
        read_xpf(self.LOCATION, warnings=False)
        with open(self.LOCATION, 'w') as f:
            text = xml_text.replace("<Circle Row=\"1\" Col=\"1\"/>"
                , "<Circle Row=\"1\" Col=\"noNumber\"/>")
            f.write(text)
        read_xpf(self.LOCATION, warnings=False)
        
    def testXPFAppearance(self):
        props = self.puzzle.view.properties
        props["bar", "width"] = 5
        props["border", "width"] = 4
        props["border", "color"] = (1234, 2345, 3456)
        props["cell", "size"] = 64
        props["line", "width"] = 3
        props["line", "color"] = (4567, 5678, 6789)
        props["block", "color"] = (7890, 8901, 9012)
        props["block", "margin"] = 20
        props["char", "color"] = (1111, 2222, 3333)
        props["cell", "color"] = (4444, 5555, 6666)
        props["number", "color"] = (7777, 8888, 9999)
        write_xpf(self.puzzle)
        results = read_xpf(self.LOCATION, warnings=False)
        propsL = results[0].view.properties
        def process(c):
            return hex_to_color(color_to_hex(c))
        self.assertEqual(propsL["bar", "width"], 5)
        self.assertEqual(propsL["border", "width"], 4)
        self.assertEqual(propsL["border", "color"], process((1234, 2345, 3456)))
        self.assertEqual(propsL["cell", "size"], 64)
        self.assertEqual(propsL["line", "width"], 3)
        self.assertEqual(propsL["line", "color"], process((4567, 5678, 6789)))
        self.assertEqual(propsL["block", "color"], process((7890, 8901, 9012)))
        self.assertEqual(propsL["block", "margin"], 20)
        self.assertEqual(propsL["char", "color"], process((1111, 2222, 3333)))
        self.assertEqual(propsL["cell", "color"], process((4444, 5555, 6666)))
        self.assertEqual(propsL["number", "color"], process((7777, 8888, 9999)))
        
    def testXPFFont(self):
        props = self.puzzle.view.properties
        props["char", "size"] = (55, _relative_to(("cell", "size"), 0.55, d=props))
        props["number", "size"] = (33, _relative_to(("cell", "size"), 0.33, d=props))
        write_xpf(self.puzzle)
        results = read_xpf(self.LOCATION, warnings=False)
        propsL = results[0].view.properties
        self.assertEqual(propsL["char", "size"][0], 55)
        self.assertEqual(propsL["number", "size"][0], 33)
        
    def testReadCrossword(self):
        write_xpf(self.puzzle)
        p = read_crossword(self.LOCATION, warnings=False)
        self.assertEqual(self.puzzle, p)
        write_ipuz(self.ipuzzle)
        p = read_crossword(self.LOCATION, warnings=False)
        self.assertEqual(self.ipuzzle, p)
        
    def testReadCrosswordErrors(self):
        with open(self.LOCATION, 'w') as f:
            f.write("This is not XPF or IPUZ")
        self.assertRaises(ParserError, read_crossword, self.LOCATION, warnings=False)
        
    def testDetermineFileType(self):
        with open(self.LOCATION, 'w') as f:
            f.write('<NotQuitePuzzles></NotQuitePuzzles>')
        self.assertEqual(determine_file_type(self.LOCATION), None)
        self.assertRaises(ParserError, read_crossword, self.LOCATION, warnings=False)
        
    def testComputeHeader(self):
        p = self.puzzle
        p.metadata[constants.META_TITLE] = "Title"
        p.metadata[constants.META_CREATOR] = "Author"
        p.metadata[constants.META_EDITOR] = "Editor"
        p.metadata[constants.META_COPYRIGHT] = "Copyright"
        p.metadata[constants.META_PUBLISHER] = "Publisher"
        p.metadata[constants.META_DATE] = "2011/01/01"
        header = compute_header(p, "%T %A %E %C %P %D")
        self.assertEqual(header, "Title Author Editor Copyright Publisher 2011/01/01")
        self.puzzle.filename = None
        header = compute_header(p, "%F %L")
        self.assertEqual(header, "%F %L")
        self.puzzle.filename = self.LOCATION
        header = compute_header(p, "%F %L")
        self.assertEqual(header, os.path.basename(self.LOCATION) + " " + self.LOCATION)
        p.grid.set_block(0, 0, True)
        p.grid.set_block(5, 0, True)
        header = compute_header(p, "%W %H %N %B")
        self.assertEqual(header, "15 15 31 2")
        header = compute_header(p, "%G")
        self.assertEqual(header, "%G")
        header = compute_header(p, "%G", page_n=3)
        self.assertEqual(header, "4")
        
    def testReadWritePatterns(self):
        """Container files with grid patterns can be read and written."""
        p1 = Puzzle(Grid(15, 15))
        g = Grid(3, 3)
        g.set_block(1, 1, True)
        g.set_void(2, 2, True)
        g.assign_numbers()
        p2 = Puzzle(g)
        files.write_containers([(self.LOCATION3, {}, [p1, p2])])
        result = files.read_containers([self._LOCATION3B])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], files.get_real_filename(self._LOCATION3B))
        puzzles = result[0][2]
        self.assertEqual(len(puzzles), 2)
        self.assertEqual(puzzles[0].grid, p1.grid)
        self.assertEqual(puzzles[1].grid, p2.grid)
        
    def testReadContainerDoesNotExist(self):
        """When a container file does not exist, None is returned."""
        result = files.read_containers(["/does/not/exist"])
        self.assertEqual(result, [(None, {}, [])])
