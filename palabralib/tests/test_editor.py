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
            self.assertTrue((i, 0, "color_current_word") in result)
            if i == 0:
                self.assertTrue((i, 0, "color_primary_selection") in result)
                
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
        self.assertTrue((1, 0, "color_primary_active") in result)
        
    def testCurrentTwo(self):
        self.e_settings.current = (3, 0)
        self.e_settings.settings["symmetries"] = [constants.SYM_180]
        cells = [(3, 0), (self.grid.width - 4, self.grid.height - 1)]
        result = editor.compute_editor_of_cell(cells, self.puzzle, self.e_settings)
        self.assertTrue((3, 0, "color_primary_active") in result)
        cell = (self.grid.width - 4, self.grid.height - 1, "color_secondary_active")
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
