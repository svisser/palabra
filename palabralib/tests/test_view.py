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
from palabralib.view import GridView, DEFAULTS

class ViewTestCase(unittest.TestCase):
    def setUp(self):
        self.puzzle = Puzzle(Grid(15, 15))
        
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
        sx = (props.margin_x + props["border", "width"]
            + 5 * (props["cell", "size"] + props["line", "width"])
            + props["cell", "size"] / 2)
        sy = (props.margin_x + props["border", "width"]
            + 7 * (props["cell", "size"] + props["line", "width"])
            + props["cell", "size"] / 2)
        self.assertEquals(props.screen_to_grid(sx, sy), (5, 7))
