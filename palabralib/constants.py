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

import os

# application data
VERSION = "0.1.5"
WEBSITE = "http://bitbucket.org/svisser/palabra"

# configuration file
APPLICATION_DIRECTORY = os.path.expanduser("~/.palabra")
CONFIG_FILE_LOCATION = os.path.expanduser("~/.palabra/config.xml")

# patterns
STANDARD_PATTERN_FILES = ["xml/patterns.xml"]#, "xml/american.xml"]

# used for displaying entries
MISSING_CHAR = '?'

# words
WORDLIST_DIRECTORY = os.path.expanduser("~/.palabra/words")
MAX_WORD_LENGTH = 64 # also in .c

# transform types (used in gui.py/update_window to indicate postprocessing)
TRANSFORM_NONE = 0
TRANSFORM_CONTENT = 1
TRANSFORM_STRUCTURE = 2

# puzzle types
PUZZLE_PALABRA = 'palabra'
PUZZLE_XPF = 'xpf'

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
VIEW_MODE_EXPORT_PDF_PUZZLE = "export_pdf_grid"
VIEW_MODE_EXPORT_PDF_SOLUTION = "export_pdf_solution"
