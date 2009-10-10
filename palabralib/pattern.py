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

import gtk

from grid import Grid
from newpuzzle import GridPreview

class PatternFileEditor(gtk.Dialog):
    def __init__(self, palabra_window):
        gtk.Dialog.__init__(self, u"Pattern file manager"
            , palabra_window, gtk.DIALOG_MODAL)
        self.palabra_window = palabra_window
        self.set_size_request(640, 480)
        
        self.preview = GridPreview()
        self.preview.set_size_request(200, -1)
        self.preview.display(Grid(9, 9))
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        
        hbox.pack_start(self.preview, True, True, 0)
        
        self.vbox.pack_start(hbox, True, True, 0)
        
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)

class Pattern:
    def __init__(self):
        self.blocks = []
        self.voids = []
        self.bars = []

def apply_pattern(grid, pattern):
    for x, y in pattern.blocks:
        grid.set_block(x, y, True)
    for x, y in pattern.voids:
        grid.set_void(x, y, True)
    for x, y, side in pattern.bars:
        grid.set_bar(x, y, side, True)

def tile_from_cell(width, height, x, y):
    pattern = Pattern()
    xs = [i for i in xrange(x, width, 2)]
    ys = [j for j in xrange(y, height, 2)]
    pattern.blocks = [(p, q) for p in xs for q in ys]
    return pattern
    
def example(grid):
    p = tile_from_cell(grid.width, grid.height, 1, 1)
    apply_pattern(grid, p)
