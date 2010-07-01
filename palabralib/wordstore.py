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

import gtk

class WordStore(gtk.ListStore):
    def __init__(self):
        gtk.ListStore.__init__(self, str, bool, str)
        self.data = []
        
    def store_words(self, strings):
        self.data = []
        colors = {True: "black", False: "gray"}
        for word, has_intersections in strings:
            msg = '<span color="' + colors[has_intersections] + '">' + word + "</span>"
            self.data.append((word, has_intersections, msg))
