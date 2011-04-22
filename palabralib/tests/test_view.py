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
from palabralib.view import GridView, DEFAULTS, CellStyle

class ViewTestCase(unittest.TestCase):
    def setUp(self):
        self.puzzle = Puzzle(Grid(13, 14))
        
    def testGetSet(self):
        props = self.puzzle.view.properties
        for key, value in DEFAULTS.items():
            self.assertEquals(props[key], value)
        for i, (key, value) in enumerate(DEFAULTS.items()):
            props[key] = "VALUE" + str(i)
            self.assertEquals(props[key], "VALUE" + str(i))
            
    def testGridToScreen(self):
        props = self.puzzle.view.properties
        props["border", "width"] = 5
        props["cell", "size"] = 64
        props["line", "width"] = 3
        sx, sy = 5 + 7 * (64 + 3), 5 + 7 * (64 + 3)
        self.assertEquals(props.grid_to_screen(x=7, include_padding=False), sx)
        self.assertEquals(props.grid_to_screen(y=7, include_padding=False), sy)
        self.assertEquals(props.grid_to_screen(x=7, y=7, include_padding=False), (sx, sy))
        
    def testScreenToGrid(self):
        props = self.puzzle.view.properties
        props.margin = 12, 21
        props["border", "width"] = 7
        props["cell", "size"] = 33
        props["line", "width"] = 2
        def get_sxy(x, y):
            sx = (props.margin[0] + props["border", "width"]
                + x * (props["cell", "size"] + props["line", "width"])
                + props["cell", "size"] / 2)
            sy = (props.margin[1] + props["border", "width"]
                + y * (props["cell", "size"] + props["line", "width"])
                + props["cell", "size"] / 2)
            return sx, sy
        for cell in [(0, 0), (5, 5), (5, 7)]:
            sx, sy = get_sxy(*cell)
            self.assertEquals(props.screen_to_grid(sx, sy), cell)
        sx, sy = get_sxy(*self.puzzle.grid.size)
        self.assertEquals(props.screen_to_grid(sx, sy), (-1, -1))
        
    def testCompScreen(self):
        xs, ys = self.puzzle.view.comp_screen()
        xxs = [x for x in xrange(self.puzzle.grid.width + 1)]
        yys = [y for y in xrange(self.puzzle.grid.height + 1)]
        self.assertEquals(all([p in xxs for p in xs]), True)
        self.assertEquals(all([q in yys for q in ys]), True)
        
    def testCellStyle(self):
        items = [(("block", "color"), "bla")
            , (("block", "margin"), 23)
            , (("cell", "color"), "foo")
            , (("char", "color"), "bar")
            , (("char", "font"), "Sans 13")
            , (("number", "color"), "foofoo")
            , (("number", "font"), "Sans 15")
            , ("circle", True)
        ]
        s = CellStyle()
        for k, v in items:
            s[k] = v
            self.assertEquals(s[k], v)
        s = CellStyle()
        t = CellStyle()
        self.assertEquals(s, t)
        s["circle"] = True
        self.assertNotEquals(s, t)
        
    def testCellProps(self):
        props = self.puzzle.view.properties
        props["cell", "color"] = (65535, 0, 0)
        props.update(5, 5, [(("cell", "color"), (65535, 0, 0))])
        props["cell", "color"] = (65535, 65535, 65535)
        self.assertEquals(props.style(5, 5)["cell", "color"], (65535, 65535, 65535))