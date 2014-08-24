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
            self.assertEqual(props[key], value)
        for i, (key, value) in enumerate(DEFAULTS.items()):
            props[key] = i
            self.assertEqual(props[key], i)

    def testGridToScreen(self):
        props = self.puzzle.view.properties
        props["border", "width"] = 5
        props["cell", "size"] = 64
        props["line", "width"] = 3
        sx, sy = 5 + 7 * (64 + 3), 5 + 7 * (64 + 3)
        self.assertEqual(props.grid_to_screen(x=7, include_padding=False), sx)
        self.assertEqual(props.grid_to_screen(y=7, include_padding=False), sy)
        self.assertEqual(props.grid_to_screen(x=7, y=7, include_padding=False), (sx, sy))

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
            self.assertEqual(props.screen_to_grid(sx, sy), cell)
        sx, sy = get_sxy(*self.puzzle.grid.size)
        self.assertEqual(props.screen_to_grid(sx, sy), (-1, -1))

    def testCompScreen(self):
        xs, ys = self.puzzle.view.comp_screen()
        xxs = [x for x in xrange(self.puzzle.grid.width + 1)]
        yys = [y for y in xrange(self.puzzle.grid.height + 1)]
        self.assertEqual(all([p in xxs for p in xs]), True)
        self.assertEqual(all([q in yys for q in ys]), True)

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
            self.assertEqual(s[k], v)
        s = CellStyle()
        t = CellStyle()
        self.assertEqual(s, t)
        s["circle"] = True
        self.assertNotEquals(s, t)
        self.assertTrue(s != t)

    def testCellProps(self):
        props = self.puzzle.view.properties
        props["cell", "color"] = (65535, 0, 0)
        props.update(5, 5, [(("cell", "color"), (65535, 0, 0))])
        props["cell", "color"] = (65535, 65535, 65535)
        self.assertEqual(props.style(5, 5)["cell", "color"], (65535, 65535, 65535))

        props.update(1, 1, [("circle", True)])
        self.assertEqual(props.style(1, 1)["circle"], True)
        props.update(1, 1, [("circle", False)])
        self.assertEqual(props.style(1, 1)["circle"], False)
        props["circle"] = True
        self.assertEqual(props.style(1, 1)["circle"], True)

    def testFontSize(self):
        """Updating cell size also updates font sizes."""
        keys = [("char", "size"), ("number", "size")]
        pre = []
        for k in keys:
            pre.append(self.puzzle.view.properties[k])
        self.puzzle.view.properties["cell", "size"] = 64
        post = []
        for k in keys:
            post.append(self.puzzle.view.properties[k])
        for i_pre, i_post in zip(pre, post):
            self.assertEqual(i_pre[0], i_post[0])
            self.assertNotEquals(i_pre[1], i_post[1])

    def testVisualSize(self):
        """
        The visual dimensions of a 1x1 grid equals 2x border width + cell width.
        """
        p = Puzzle(Grid(1, 1))
        props = p.view.properties
        props["border", "width"] = 5
        props["cell", "size"] = 64
        self.assertEqual(props.visual_size(False), (5 + 64 + 5, 5 + 64 + 5))

    def testVisualSizeTwo(self):
        """The visual dimensions can vary for width and height."""
        p = Puzzle(Grid(3, 2))
        props = p.view.properties
        props["border", "width"] = 5
        props["cell", "size"] = 64
        props["line", "width"] = 3
        width = 5 + 64 + 3 + 64 + 3 + 64 + 5
        height = 5 + 64 + 3 + 64 + 5
        self.assertEqual(props.visual_size(False), (width, height))

    def testVisualSizePadding(self):
        p = Puzzle(Grid(2, 1))
        props = p.view.properties
        props.margin = (10, 20)
        props["border", "width"] = 5
        props["cell", "size"] = 64
        props["line", "width"] = 3
        width = 10 + 5 + 64 + 3 + 64 + 5 + 10
        height = 20 + 5 + 64 + 5 + 20
        self.assertEqual(props.visual_size(True), (width, height))
