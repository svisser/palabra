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
VERSION = "0.1.6"
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
MAX_WORD_LISTS = 64 # also in .c

# transform types (used in gui.py/update_window to indicate postprocessing)
TRANSFORM_NONE = 0
TRANSFORM_CONTENT = 1
TRANSFORM_STRUCTURE = 2

# filling options, also in .c
FILL_START_AT_ZERO = 0
FILL_START_AT_SELECTION = 1
FILL_START_AT_AUTO = 2

# fill options, also in .c (fill function)
FILL_OPTION_START = "start"

# puzzle types
PUZZLE_PALABRA = 'palabra'
# http://www.xwordinfo.com/XPF/
PUZZLE_XPF = 'xpf'
# http://www.ipuz.org/
PUZZLE_IPUZ = 'ipuz'

# canonical identifiers for metadata across various file formats
# (using simple Dublin Core)
META_TITLE = 'title'
META_CREATOR = 'creator'
META_EDITOR = 'contributor'
META_COPYRIGHT = 'rights'
META_PUBLISHER = 'publisher'
META_DATE = 'date'

# for export
META_CODES = {
    META_TITLE: "%T"
    , META_CREATOR: "%A"
    , META_EDITOR: "%E"
    , META_COPYRIGHT: "%C"
    , META_PUBLISHER: "%P"
    , META_DATE: "%D"
}

# statusbar identifiers
STATUS_MENU = "STATUS_MENU"
STATUS_GRID = "STATUS_GRID"

# numbering modes of grid
NUMBERING_AUTO = "NUMBERING_AUTO"
NUMBERING_MANUAL = "NUMBERING_MANUAL"

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
VIEW_MODE_PREVIEW_CELL = "preview_cell"
VIEW_MODE_PREVIEW_SOLUTION = "preview_solution"
