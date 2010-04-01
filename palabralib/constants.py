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

import os

# application version
VERSION = "0.1.2"

# configuration file
APPLICATION_DIRECTORY = os.path.expanduser("~/.palabra")
CONFIG_FILE_LOCATION = os.path.expanduser("~/.palabra/config.xml")

# patterns
STANDARD_PATTERN_FILES = ["xml/patterns.xml"]

# words
WORDLIST_DIRECTORY = os.path.expanduser("~/.palabra/words")
MAX_WORD_LENGTH = 64 # also in .c

# statusbar identifiers
STATUS_MENU = "STATUS_MENU"
STATUS_GRID = "STATUS_GRID"

# dimensions of a grid
MINIMUM_WIDTH = 3
MAXIMUM_WIDTH = 35

# ordering of a histogram
ORDERING_ALPHABET = 0
ORDERING_FREQUENCY = 1

# modes for viewing a grid
VIEW_MODE_EDITOR = "editor"
VIEW_MODE_EMPTY = "empty"
VIEW_MODE_PREVIEW = "preview"
VIEW_MODE_SOLUTION = "solution"
