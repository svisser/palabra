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

import cPickle

from grid import Grid
import preferences

class State:
    def __init__(self, source, clue_slot=None):
        self.grid = cPickle.dumps(source)
        # needed for clues
        self.clue_slot = clue_slot
        
class StateStack():
    def __init__(self):
        self.clear()
        
    def clear(self):
        """Remove all states from the stack."""
        self.undo_stack = []
        self.redo_stack = []
        
        # non-zero = puzzle has unsaved changes
        self.distance_from_saved = 0
    
    def push(self, state, initial=False):
        # clue modifications are merged with previous ones if needed
        if state.clue_slot is not None:
            s = self.peek()
            if (s is not None and s.clue_slot == state.clue_slot):
                self.undo_stack.pop()
                self.undo_stack.append(state)
                return
        self.undo_stack.append(state)
        self.redo_stack = []
        if not initial:
            self.distance_from_saved += 1
        
    def undo(self, puzzle):
        state = self.undo_stack.pop()
        self.redo_stack.append(state)
        prev = self.undo_stack.pop()
        puzzle.grid = cPickle.loads(prev.grid)
        self.undo_stack.append(prev)
        self.distance_from_saved -= 1
        return state
        
    def redo(self, puzzle):
        state = self.redo_stack.pop()
        self.undo_stack.append(state)
        puzzle.grid = cPickle.loads(state.grid)
        self.distance_from_saved += 1
        return state
        
    def peek(self):
        return self.undo_stack[-1] if len(self.undo_stack) > 0 else None
        
    def has_undo(self):
        return len(self.undo_stack) > 1
        
    def has_redo(self):
        return len(self.redo_stack) > 0

stack = StateStack()
