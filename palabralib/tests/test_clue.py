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

import unittest
import os

import palabralib.clue as clue
import palabralib.constants as constants

class ClueTestCase(unittest.TestCase):
    LOCATION = "palabralib/tests/test_clues.txt"

    def tearDown(self):
        if os.path.exists(self.LOCATION):
            os.remove(self.LOCATION)
            
    def testReadCluesDoesNotExist(self):
        """If the clue database does not exist then an empty dict is returned."""
        self.assertEqual(clue.read_clues("/this/path/does/not/exist"), {})
    
    def testReadClues(self):
        """A clue database is a dict with key = word, value = list of clues."""
        with open(self.LOCATION, 'w') as f:
            f.write("word,clue\nword,clue2\notherword,clue3")
        result = clue.read_clues(self.LOCATION)
        self.assertEqual(len(result), 2)
        self.assertTrue("word" in result)
        self.assertTrue("otherword" in result)
        self.assertTrue("clue" in result["word"])
        self.assertTrue("clue2" in result["word"])
        self.assertTrue("clue3" in result["otherword"])
        
    def testReadCluesStripClue(self):
        """Spaces are stripped from a clue."""
        with open(self.LOCATION, 'w') as f:
            f.write("word,  so much space  ")
        result = clue.read_clues(self.LOCATION)
        self.assertTrue("word" in result)
        self.assertEqual(result["word"], ["so much space"])
        
    def testReadCluesUpperCase(self):
        """Upper case characters in a word are converted to lower case."""
        with open(self.LOCATION, 'w') as f:
            f.write("Word, clue")
        result = clue.read_clues(self.LOCATION)
        self.assertTrue("word" in result)
        self.assertEqual(result["word"], ["clue"])
        
    def testReadCluesTooLongWord(self):
        """Too long words in clue databases are rejected."""
        with open(self.LOCATION, 'w') as f:
            f.write("a" * (constants.MAX_WORD_LENGTH + 1) + ",clue")
        self.assertEqual(clue.read_clues(self.LOCATION), {})
        
    def testReadCluesRejectCompound(self): # for now, reject compound
        with open(self.LOCATION, 'w') as f:
            f.write("This is a compound word,clue")
        result = clue.read_clues(self.LOCATION)
        self.assertEqual(result, {})
