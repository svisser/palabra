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

# Based on treemodel.py in pygtk/demos

import gtk
from operator import itemgetter

class WordStore(gtk.GenericTreeModel):
    def __init__(self):
        gtk.GenericTreeModel.__init__(self)
        self.columns = [str, bool, int, str]
        self.ordering = 0
        data = []
        self.data = data
        self.set_view(data)
        
    def on_get_flags(self):
        return gtk.TREE_MODEL_LIST_ONLY
        
    def on_get_n_columns(self):
        return len(self.columns)
        
    def on_get_column_type(self, index):
        return self.columns[index]
        
    def on_get_path(self, node):
        return node
        
    def on_get_iter(self, path):
        return path
        
    def on_get_value(self, node, column):
        if node[0] < self.view_length:
            return self.view[node[0]][column]
        return None
        
    def on_iter_next(self, node):
        if self.view_length == 0:
            return None
        if node[0] == self.view_length - 1:
            return None
        return (node[0] + 1,)
        
    def on_iter_children(self, node):
        if node == None:
            return (0,)
        return None
        
    def on_iter_has_child(self, node):
        return False
        
    def on_iter_n_children(self, node):
        return 0
        
    def on_iter_nth_child(self, node, n):
        if node == None:
            return (n,)
        return None
        
    def on_iter_parent(self, node):
        return None
        
    def set_view(self, view):
        if self.ordering == 0: # alphabet
            view.sort(key=itemgetter(0))
        elif self.ordering == 1: # suitability
            view.sort(key=itemgetter(2), reverse=True)
        self.view = view
        self.view_length = len(view)
        
    def set_data(self, data):
        # bit ugly but needed for speed
        self.data = [(word, has_intersections, indicator, '<span color="'
            + {True: "black", False: "gray"}[has_intersections] + '">' + word + "</span>")
            for word, has_intersections, indicator in data]
