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
TITLE = "Palabra"
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
FILL_NICE_FALSE = 0
FILL_NICE_TRUE = 1
FILL_DUPLICATE_FALSE = 0
FILL_DUPLICATE_TRUE = 1

# fill options, also in .c (fill function)
FILL_OPTION_START = "start"
FILL_OPTION_NICE = "nice"
FILL_OPTION_DUPLICATE = "duplicate"
FILL_NICE_COUNT = "nice_count"

# puzzle types
PUZZLE_PALABRA = 'palabra'
# http://www.xwordinfo.com/XPF/
PUZZLE_XPF = 'xpf'
# http://www.ipuz.org/
PUZZLE_IPUZ = 'ipuz'

# symmetry options
SYM_HORIZONTAL = "horizontal"
SYM_VERTICAL = "vertical"
SYM_90 = "90_degree"
SYM_180 = "180_degree"
SYM_DIAGONALS = "diagonals"

# canonical identifiers for metadata across various file formats
# (using simple Dublin Core)
META_TITLE = 'title'
META_CREATOR = 'creator'
META_EDITOR = 'contributor'
META_COPYRIGHT = 'rights'
META_PUBLISHER = 'publisher'
META_DATE = 'date'

# additional meta identifiers for headers
META_FILENAME = 'filename'
META_FILEPATH = 'filepath'
META_WIDTH = 'width'
META_HEIGHT = 'height'
META_N_WORDS = 'word_count'
META_N_BLOCKS = 'block_count'
META_PAGE_NUMBER = 'page_number'
META_EXPORT_VALUES = [
    META_FILENAME
    , META_FILEPATH
    , META_WIDTH
    , META_HEIGHT
    , META_N_WORDS
    , META_N_BLOCKS
    , META_PAGE_NUMBER
]

# for export
META_CODES = {
    META_TITLE: "%T"
    , META_CREATOR: "%A"
    , META_EDITOR: "%E"
    , META_COPYRIGHT: "%C"
    , META_PUBLISHER: "%P"
    , META_DATE: "%D"
    , META_FILENAME: "%F"
    , META_FILEPATH: "%FF"
    , META_WIDTH: "%W"
    , META_HEIGHT: "%H"
    , META_N_WORDS: "%N"
    , META_N_BLOCKS: "%B"
    , META_PAGE_NUMBER: "%G"
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

# editor warnings
WARN_UNCHECKED = "warn_unchecked_cells"
WARN_CONSECUTIVE = "warn_consecutive_unchecked"
WARN_TWO_LETTER = "warn_two_letter_words"
WARNINGS = [WARN_UNCHECKED, WARN_CONSECUTIVE, WARN_TWO_LETTER]

COLOR_WARNING = "color_warning"
COLOR_HIGHLIGHT = "color_highlight"
COLOR_CURRENT_WORD = "color_current_word"
COLOR_PRIMARY_SELECTION = "color_primary_selection"
COLOR_PRIMARY_ACTIVE = "color_primary_active"
COLOR_SECONDARY_ACTIVE = "color_secondary_active"

INPUT_DELAY = 350
INPUT_DELAY_SHORT = 250

PREF_COPY_BEFORE_SAVE = "backup_copy_before_save"
PREF_INITIAL_HEIGHT = "new_initial_height"
PREF_INITIAL_WIDTH = "new_initial_width"
PREF_UNDO_STACK_SIZE = "undo_stack_size"
PREF_UNDO_FINITE_STACK = "undo_use_finite_stack"
PREF_PATTERN_FILES = "pattern_files"
PREF_WORD_FILES = "word_files"
