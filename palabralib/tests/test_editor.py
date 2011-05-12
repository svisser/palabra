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
import palabralib.constants as constants
import palabralib.editor as editor

class EditorTestCase(unittest.TestCase):
    def setUp(self):
        self.grid = Grid(15, 15)
        
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
            self.assertEquals(c in result, True)
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
