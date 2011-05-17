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

import palabralib.cPalabra as cPalabra
from palabralib.grid import Grid
from palabralib.puzzle import Puzzle
import palabralib.constants as constants
import palabralib.editor as editor

class EditorTestCase(unittest.TestCase):
    def setUp(self):
        self.grid = Grid(15, 15)
        self.puzzle = Puzzle(self.grid)
        self.e_settings = editor.EditorSettings()
        self.e_settings.selection = editor.Selection(0, 0, "across")
        self.warnings = {}
        for w in constants.WARNINGS:
            self.warnings[w] = False
        cPalabra.preprocess_all()
        
    def testCharSlots(self):
        slots = editor.get_char_slots(self.grid, 'K')
        self.assertEquals(slots, [])
        cells = [(i, i) for i in xrange(5)]
        for i, j in cells:
            self.grid.set_char(i, j, 'K')
        slots = editor.get_char_slots(self.grid, 'K')
        self.assertEquals(len(slots), 5)
        lengths = [l for x, y, d, l in slots]
        self.assertEquals(lengths.count(1), 5)
        self.assertEquals([(x, y) for x, y, d, l in slots], cells)
    
    def testLengthSlots(self):
        for l in [-1, 0, 14]:
            slots = editor.get_length_slots(self.grid, l)
            self.assertEquals(slots, [])
        slots = editor.get_length_slots(self.grid, 15)
        self.assertEquals(len(slots), 30)
        for x, y, d, l in slots:
            self.assertEquals(l, 15)
        self.assertEquals(len([1 for x, y, d, l in slots if d == "across"]), 15)
        self.assertEquals(len([1 for x, y, d, l in slots if d == "down"]), 15)
        
    def testOpenSlots(self):
        slots = editor.get_open_slots(self.grid)
        self.assertEquals(len(slots), len(self.grid.compute_open_squares()))
        for x, y, d, l in slots:
            self.assertEquals(l, 1)
            
    def testExpandSlots(self):
        slots_a = [(0, 0, "across", 5)]
        slots_d = [(3, 4, "down", 6)]
        exp_a = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)]
        exp_d = [(3, 4), (3, 5), (3, 6), (3, 7), (3, 8), (3, 9)]
        result_a = editor.expand_slots(slots_a)
        result_d = editor.expand_slots(slots_d)
        self.assertEquals(result_a, exp_a)
        self.assertEquals(result_d, exp_d)
        self.assertEquals(editor.expand_slots(slots_a + slots_d), exp_a + exp_d)
        
    def testHighlights(self):
        for i in xrange(5):
            self.grid.set_char(i, i, 'A')
        cells = editor.compute_highlights(self.grid, clear=True)
        self.assertEquals(cells, [])
        cells = editor.compute_highlights(self.grid, "length", 15)
        self.assertEquals(len(cells), self.grid.count_words())
        cells = editor.compute_highlights(self.grid, "char", 'A')
        self.assertEquals(len(cells), 5)
        cells = editor.compute_highlights(self.grid, "open")
        self.assertEquals(len(cells), len(list(self.grid.cells())))
        
    def testHighlightsTwo(self):
        arg = [(1, 1), (5, 5), (3, 4), (4, 3)]
        cells = editor.compute_highlights(self.grid, "cells", arg)
        self.assertEquals(len(arg), len(cells))
        for x, y in arg:
            self.assertTrue((x, y, "across", 1) in cells)
        result = editor.compute_highlights(self.grid, "slot", (0, 0, "down"))
        self.assertTrue((0, 0, "down", 15) in result)
        self.grid.set_block(5, 0, True)
        result = editor.compute_highlights(self.grid, "slot", (0, 0, "across"))
        self.assertTrue((0, 0, "across", 5) in result)
        
    def testSymmetryInvalid(self):
        self.assertEquals(editor.apply_symmetry(self.grid, [], -1, -1), [])

    def testSymmetryHorizontal(self):
        symms = [constants.SYM_HORIZONTAL]
        for x in xrange(5):
            result = editor.apply_symmetry(self.grid, symms, x, x)
            self.assertEquals(result, [(x, self.grid.height - 1 - x)])
        self.assertEquals(editor.apply_symmetry(self.grid, symms, 7, 7), [(7, 7)])
        
    def testSymmetryVertical(self):
        symms = [constants.SYM_VERTICAL]
        for x in xrange(5):
            result = editor.apply_symmetry(self.grid, symms, x, x)
            self.assertEquals(result, [(self.grid.width - 1 - x, x)])
        self.assertEquals(editor.apply_symmetry(self.grid, symms, 7, 7), [(7, 7)])

    def _checkSymms(self, result, expect):
        for c in expect:
            self.assertTrue(c in result)
        self.assertEquals(len(result), len(expect))

    def testSymmetryTwo(self):
        expect = [(0, self.grid.height - 1)
            , (self.grid.width - 1, 0)
            , (self.grid.width - 1, self.grid.height - 1)]
        symms_1 = [constants.SYM_HORIZONTAL, constants.SYM_VERTICAL]
        symms_2 = [constants.SYM_90]
        self._checkSymms(editor.apply_symmetry(self.grid, symms_1, 0, 0), expect)
        self._checkSymms(editor.apply_symmetry(self.grid, symms_2, 0, 0), expect)

    def testSymmetryThree(self):
        symms = [constants.SYM_90]
        for g in [self.grid, Grid(12, 14)]:
            result = editor.apply_symmetry(g, symms, 1, 0)
            expect = [(g.width - 1, 1)
                , (g.width - 2, g.height - 1)
                , (0, g.height - 2)]
            self._checkSymms(result, expect)
            
    def testSymmetryFour(self):
        symms = [constants.SYM_180]
        cells = [(0, 0, [(14, 14)]), (5, 5, [(9, 9)])]
        for x, y, expect in cells:
            self._checkSymms(editor.apply_symmetry(self.grid, symms, x, y), expect)
            
    def testSymmetryFive(self):
        symms = [constants.SYM_DIAGONALS]
        result = editor.apply_symmetry(self.grid, symms, 1, 0)
        self._checkSymms(result, [(0, 1), (14, 13), (13, 14)])
        
    def testTransformBlocks(self):
        self.assertEquals(editor.transform_blocks(self.grid, [], -1, -1, True), [])
        result = editor.transform_blocks(self.grid, [], 0, 0, True)
        self.assertEquals(result, [(0, 0, True)])
        result = editor.transform_blocks(self.grid, [constants.SYM_180], 0, 0, True)
        self.assertEquals(result, [(0, 0, True), (14, 14, True)])
        
    def testTransformBlocksTwo(self):
        self.grid.set_block(0, 0, True)
        result = editor.transform_blocks(self.grid, [], 0, 0, True)
        self.assertEquals(result, [])
        result = editor.transform_blocks(self.grid, [constants.SYM_180], 14, 14, True)
        self.assertEquals(result, [(14, 14, True)])
        result = editor.transform_blocks(self.grid, [], 0, 0, False)
        self.assertEquals(result, [(0, 0, False)])
        result = editor.transform_blocks(self.grid, [constants.SYM_180], 14, 14, False)
        self.assertEquals(result, [(0, 0, False)])
        
    def testComputeWordCellsNone(self):
        o = editor.compute_word_cells(self.grid, None, 0, 0, "across")
        self.assertEquals(o, [])
        
    def testComputeWordCellsOne(self):
        o = editor.compute_word_cells(self.grid, "palabra", 0, 0, "across")
        expect = [(0, 0, 'P'), (1, 0, 'A'), (2, 0, 'L'), (3, 0, 'A'), (4, 0, 'B'), (5, 0, 'R'), (6, 0, 'A')]
        self.assertEquals(o, expect)
        
    def testComputeWordCellsTwo(self):
        self.grid.set_char(0, 0, 'P')
        self.grid.set_char(3, 0, 'A')
        o = editor.compute_word_cells(self.grid, "palabra", 0, 0, "across")
        expect = [(1, 0, 'A'), (2, 0, 'L'), (4, 0, 'B'), (5, 0, 'R'), (6, 0, 'A')]
        self.assertEquals(o, expect)
        o = editor.compute_word_cells(self.grid, "PALABRA", 0, 0, "across")
        expect = [(1, 0, 'A'), (2, 0, 'L'), (4, 0, 'B'), (5, 0, 'R'), (6, 0, 'A')]
        self.assertEquals(o, expect)
        
    def testSelection(self):
        for i in xrange(self.grid.width):
            result = editor.compute_editor_of_cell([(i, 0)], self.puzzle, self.e_settings)
            self.assertTrue((i, 0, constants.COLOR_CURRENT_WORD) in result)
            if i == 0:
                self.assertTrue((i, 0, constants.COLOR_PRIMARY_SELECTION) in result)
                
    def testSelectionTwo(self):
        """Cells behind a block are not part of the selection."""
        self.grid.set_block(5, 0, True)
        result = editor.compute_editor_of_cell([(6, 0)], self.puzzle, self.e_settings)
        self.assertEquals(result, [])
        
    def testSelectionThree(self):
        """Cells behind a void are not part of the selection."""
        self.grid.set_void(5, 0, True)
        result = editor.compute_editor_of_cell([(6, 0)], self.puzzle, self.e_settings)
        self.assertEquals(result, [])
        
    def testCurrentOne(self):
        self.e_settings.current = (1, 0)
        self.e_settings.settings["symmetries"] = [constants.SYM_180]
        result = editor.compute_editor_of_cell([(1, 0)], self.puzzle, self.e_settings)
        self.assertTrue((1, 0, constants.COLOR_PRIMARY_ACTIVE) in result)
        
    def testCurrentTwo(self):
        self.e_settings.current = (3, 0)
        self.e_settings.settings["symmetries"] = [constants.SYM_180]
        cells = [(3, 0), (self.grid.width - 4, self.grid.height - 1)]
        result = editor.compute_editor_of_cell(cells, self.puzzle, self.e_settings)
        self.assertTrue((3, 0, constants.COLOR_PRIMARY_ACTIVE) in result)
        cell = (self.grid.width - 4, self.grid.height - 1, constants.COLOR_SECONDARY_ACTIVE)
        self.assertTrue(cell in result)
        
    def testWarningsTwoLetterAcross(self):
        g = self.grid
        g.set_block(2, 0, True)
        self.warnings[constants.WARN_TWO_LETTER] = True
        result = list(editor.compute_warnings_of_cells(g, list(g.cells()), self.warnings))
        self.assertTrue((0, 0) in result)
        self.assertTrue((1, 0) in result)
        self.assertTrue(len(result) == 2)

    def testWarningsTwoLetterDown(self):
        g = self.grid
        g.set_block(0, 2, True)
        self.warnings[constants.WARN_TWO_LETTER] = True
        result = list(editor.compute_warnings_of_cells(g, list(g.cells()), self.warnings))
        self.assertTrue((0, 0) in result)
        self.assertTrue((0, 1) in result)
        self.assertTrue(len(result) == 2)
    
    def testWarningsUnchecked(self):
        g = self.grid
        g.set_block(1, 0, True)
        self.warnings[constants.WARN_UNCHECKED] = True
        result = list(editor.compute_warnings_of_cells(g, list(g.cells()), self.warnings))
        self.assertTrue((0, 0) in result)
        self.assertTrue(len(result) == 1)
        
    def testWarningsIsolation(self):
        g = self.grid
        g.set_block(1, 0, True)
        g.set_block(0, 1, True)
        self.warnings[constants.WARN_UNCHECKED] = True
        result = list(editor.compute_warnings_of_cells(g, list(g.cells()), self.warnings))
        self.assertTrue((0, 0) in result)
        self.assertTrue(len(result) == 1)
    
    def testWarningsConsecutive(self):
        g = self.grid
        g.set_block(1, 0, True)
        self.warnings[constants.WARN_CONSECUTIVE] = True
        result = list(editor.compute_warnings_of_cells(g, list(g.cells()), self.warnings))
        self.assertEquals(result, [])
        g.set_block(1, 1, True)
        result = list(editor.compute_warnings_of_cells(g, list(g.cells()), self.warnings))
        self.assertTrue((0, 0) in result)
        self.assertTrue((0, 1) in result)
        self.assertTrue(len(result) == 2)
        
    def testWarningsMultiple(self):
        g = self.grid
        g.set_block(4, 0, True)
        g.set_block(4, 1, True)
        g.set_block(3, 2, True)
        self.warnings[constants.WARN_UNCHECKED] = True
        self.warnings[constants.WARN_CONSECUTIVE] = True
        self.warnings[constants.WARN_TWO_LETTER] = True
        result = list(editor.compute_warnings_of_cells(g, list(g.cells()), self.warnings))
        self.assertTrue((3, 0) in result)
        self.assertTrue((3, 1) in result)
        self.assertTrue(len(result) == 2)
        
    def testEditorWarnings(self):
        self.grid.set_block(2, 0, True)
        self.grid.set_block(self.grid.width - 2, 0, True)
        self.e_settings.warnings[constants.WARN_UNCHECKED] = True
        self.e_settings.warnings[constants.WARN_TWO_LETTER] = True
        result = editor.compute_editor_of_cell(list(self.grid.cells()), self.puzzle, self.e_settings)
        self.assertTrue((0, 0, constants.COLOR_WARNING) in result)
        self.assertTrue((self.grid.width - 1, 0, constants.COLOR_WARNING) in result)
        
    def testComputeSelectionOtherDir(self):
        s = self.e_settings.selection
        next = editor.compute_selection(s, other_dir=True)
        self.assertEquals(next[0], s.x)
        self.assertEquals(next[1], s.y)
        self.assertEquals(next[2], "down")
        
    def testComputeSelectionPos(self):
        s = self.e_settings.selection
        next = editor.compute_selection(s, x=5, y=3)
        self.assertEquals(next[0], 5)
        self.assertEquals(next[1], 3)
        self.assertEquals(next[2], "across")
        
    def testComputeSelectionDir(self):
        s = self.e_settings.selection
        next = editor.compute_selection(s, direction="down")
        self.assertEquals(next[0], s.x)
        self.assertEquals(next[1], s.y)
        self.assertEquals(next[2], "down")
        
    def testComputeSelectionPosDir(self):
        s = self.e_settings.selection
        next = editor.compute_selection(s, x=2, y=7, direction="down")
        self.assertEquals(next[0], 2)
        self.assertEquals(next[1], 7)
        self.assertEquals(next[2], "down")
        
    def testComputeSelectionAlone(self):
        s = self.e_settings.selection
        next = editor.compute_selection(s, x=2)
        self.assertEquals(next[0], 2)
        self.assertEquals(next[1], 0)
        self.assertEquals(next[2], "across")
        next = editor.compute_selection(s, y=2)
        self.assertEquals(next[0], 0)
        self.assertEquals(next[1], 2)
        self.assertEquals(next[2], "across")
        
    def testSearchArgsOne(self):
        g = Grid(5, 5)
        l, cs, more = editor.compute_search_args(g, (0, 0, "across"))
        self.assertEquals(l, 5)
        self.assertEquals(cs, [])
        self.assertEquals(len(more), 5)
        for i in xrange(5):
            self.assertEquals(more[i], (0, 5, []))
            
    def testSearchArgsInvalid(self):
        result = editor.compute_search_args(Grid(5, 5), (-1, -1, "across"), True)
        self.assertEquals(result, None)
        
    def testSearchArgsLengthOne(self):
        g = Grid(5, 5)
        g.set_block(1, 0, True)
        result = editor.compute_search_args(g, (0, 0, "across"), True)
        self.assertEquals(result, None)
        
    def testSearchArgsFullyFilledIn(self):
        g = Grid(5, 5)
        g.set_char(0, 0, 'A')
        g.set_char(1, 0, 'A')
        g.set_char(2, 0, 'A')
        g.set_char(3, 0, 'A')
        g.set_char(4, 0, 'A')
        result = editor.compute_search_args(g, (0, 0, "across"), False)
        self.assertEquals(result, None)
        l, cs, more = editor.compute_search_args(g, (0, 0, "across"), True)
        self.assertEquals(l, 5)
        self.assertEquals(len(cs), 5)
        self.assertEquals(len(more), 5)
        
    def testAttempFill(self):
        g = Grid(5, 5)
        g2 = editor.attempt_fill(g, ["koala"])
        self.assertEquals(g2.count_chars(include_blanks=False), 5)
        g = Grid(5, 5)
        g2 = editor.attempt_fill(g, ["koala", "steam"])
        self.assertEquals(g2.count_chars(include_blanks=False), 10)
        cPalabra.postprocess()
        
    def testAttempFillTwo(self):
        g = Grid(5, 5)
        g2 = editor.attempt_fill(g, ["doesnotfit"])
        self.assertEquals(g, g2)
        cPalabra.postprocess()
        
    def testAttempFillIntersect(self):
        g = Grid(3, 3)
        g.set_block(1, 1, True)
        g.set_block(2, 2, True)
        g2 = editor.attempt_fill(g, ["foo", "fix"])
        self.assertEquals(g2.count_chars(include_blanks=False), 5)
        cPalabra.postprocess()
        
    def testAttemptFillIntersectTwo(self):
        # A B C
        # D   F
        # E H G
        words = ["abc", "ade", "cfg", "ehg"]
        g = Grid(3, 3)
        g.set_block(1, 1, True)
        g2 = editor.attempt_fill(g, words)
        self.assertEquals(g2.count_chars(include_blanks=False), 8)
        counts = dict([(g2.data[y][x]["char"], 1) for x, y in g2.cells() if not g2.data[y][x]["block"]])
        self.assertEquals(len(counts), 8)
        words.reverse()
        g3 = editor.attempt_fill(g, words)
        self.assertEquals(g2.count_chars(include_blanks=False), 8)
        counts = dict([(g2.data[y][x]["char"], 1) for x, y in g3.cells() if not g2.data[y][x]["block"]])
        self.assertEquals(len(counts), 8)
        cPalabra.postprocess()
        
    def testAttemptFillNoIntersectingAcross(self):
        g = Grid(3, 1)
        g2 = editor.attempt_fill(g, ["abc"])
        self.assertEquals(g2.count_chars(include_blanks=False), 3)
        
    def testAttemptFillNoIntersectingDown(self):
        g = Grid(1, 3)
        g2 = editor.attempt_fill(g, ["def"])
        self.assertEquals(g2.count_chars(include_blanks=False), 3)
        
    def testAttemptFillVoids(self):
        g = Grid(3, 3)
        g.set_void(0, 0, True)
        g.set_void(2, 2, True)
        g2 = editor.attempt_fill(g, ["axa", "bxb"])
        self.assertEquals(g2.count_chars(include_blanks=False), 5)
        
    def testAttemptFillAlreadyFilledIn(self):
        g = Grid(3, 3)
        g.set_block(1, 1, True)
        g.set_block(2, 2, True)
        g.set_char(0, 0, 'A')
        g2 = editor.attempt_fill(g, ["aaa"])
        self.assertEquals(g2.count_chars(include_blanks=False), 3)
        
    def testAttemptFillVarLengths(self):
        g = Grid(5, 5)
        for y in xrange(5):
            for x in xrange(y, 5):
                g.set_block(x, y, True)
        g2 = editor.attempt_fill(g, ["aaaa", "bbb", "cc"])
        self.assertEquals(g2.count_chars(include_blanks=False), 9)
        
    def testAttemptFillTwo(self):
        # A B
        # D C
        g = Grid(2, 2)
        g2 = editor.attempt_fill(g, ["ab", "bc", "dc", "ad"])
        self.assertEquals(g2.count_chars(include_blanks=False), 4)
        
    def testAttemptFillNine(self):
        pass
        # K L M
        # N O P
        # Q R S
        #pass # TODO don't run: will create infinite loop
        #g = Grid(3, 3)
        #g2 = editor.attempt_fill(g, ["klm", "nop", "qrs", "knq", "lor", "mps"])
        #self.assertEquals(g2.count_chars(include_blanks=False), 9)
