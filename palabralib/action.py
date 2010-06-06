# This file is part of Palabra
#
# Copyright (C) 2009 - 2010 Simeon Visser
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

class ActionStack:
    """
    Contains two stacks with the actions that can be undone or redone.
    """
    def __init__(self):
        self.clear()
        
    def peek_action(self):
        """Return the action that is currently on top of the undo stack."""
        return self.undo_stack[-1] if len(self.undo_stack) > 0 else None
        
    def push_action(self, action):
        """
        Push an action onto the undo stack and clear the redo stack.
        
        If a finite undo stack is used, the oldest action
        in the undo stack will be removed first.
        """
        if (preferences.prefs["undo_use_finite_stack"] and
            len(self.undo_stack) >= preferences.prefs["undo_stack_size"]):
            self.undo_stack = self.undo_stack[1:]
        self.undo_stack.append(action)
        self.redo_stack = []
        self.distance_from_saved_puzzle += 1
        
    def undo_action(self, puzzle):
        """
        Perform the most recent action in the undo stack.
        
        After performing the action, it will be placed in
        the redo stack.
        
        If a finite redo stack is used, the oldest action
        in the redo stack will be removed first.
        """
        if len(self.undo_stack) > 0:
            a = self.undo_stack.pop()
            a.perform_undo(puzzle)
            
            # since states of the puzzle are represented by
            # undo/redo functions, we also need to redo the
            # action currently on top
            if len(self.undo_stack) > 0:
                b = self.undo_stack.pop()
                b.perform_redo(puzzle)
                self.undo_stack.append(b)
                
            self.distance_from_saved_puzzle -= 1
            
            self._append_to_stack(self.redo_stack, a)
            
    def redo_action(self, puzzle):
        """
        Perform the most recent action in the redo stack.
        
        After performing the action, it will be placed in
        the undo stack.
        
        If a finite undo stack is used, the oldest action
        in the undo stack will be removed first.
        """
        if len(self.redo_stack) > 0:
            a = self.redo_stack.pop()
            a.perform_redo(puzzle)
            
            self.distance_from_saved_puzzle += 1
            
            self._append_to_stack(self.undo_stack, a)
            
    def _append_to_stack(self, stack, action):
        """
        Append the action to the stack.
        
        An older action may be removed to maintain the preferred size.
        """
        if (preferences.prefs["undo_use_finite_stack"] and
            len(stack) >= preferences.prefs["undo_stack_size"]):
            stack = stack[1:]
        stack.append(action)
    
    def cap_stack(self, max_size):
        """Limit the size of the undo and redo stacks to max_size."""
        if len(self.undo_stack) > max_size:
            self.undo_stack = self.undo_stack[-max_size:]
        if len(self.redo_stack) > max_size:
            self.redo_stack = self.redo_stack[-max_size:]
            
    def clear(self):
        """Remove all actions from the stacks."""
        self.undo_stack = []
        self.redo_stack = []
        
        # non-zero = puzzle has unsaved changes
        self.distance_from_saved_puzzle = 0

old_stack = ActionStack()

#####

class State:
    def __init__(self, source):
        self.grid = cPickle.dumps(source)
        
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
        
    def redo(self, puzzle):
        state = self.redo_stack.pop()
        self.undo_stack.append(state)
        puzzle.grid = cPickle.loads(state.grid)
        self.distance_from_saved += 1
        
    def has_undo(self):
        return len(self.undo_stack) > 1
        
    def has_redo(self):
        return len(self.redo_stack) > 0

stack = StateStack()
