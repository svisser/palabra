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

import gtk

import action
import constants
from grid import Grid
from view import GridView

class Puzzle:
    def __init__(self, grid, styles=None, gstyles=None):
        self.type = constants.PUZZLE_XPF
        self.grid = grid
        self.view = GridView(grid, styles, gstyles)
        self.filename = None
        self.metadata = {}
        self.notepad = ""
        
    def __eq__(self, other):
        if (other is None
            or self.type != other.type
            or self.filename != other.filename
            or self.metadata != other.metadata
            or self.notepad != other.notepad
            or self.grid != other.grid):
            return False
        return True
        
    def __ne__(self, other):
        return not self.__eq__(other)
        
    def update_type(self, filetype, filename, extension):
        if not filename.endswith(extension):
            filename = filename + extension
        self.filename = filename
        self.type = filetype

class PuzzleManager:
    def __init__(self):
        self.current_puzzle = None
        
    def new_puzzle(self, configuration):
        if configuration["type"] == "crossword":
                
            if "grid" in configuration:
                grid = configuration["grid"]
                self.current_puzzle = Puzzle(grid)
            else:
                # TODO
                print "PuzzleManager.new_puzzle: FAIL"

    def has_puzzle(self):
        return self.current_puzzle != None
