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
import gtk
import os

import palabralib.clue as clue
import palabralib.constants as constants

class ClueTestCase(unittest.TestCase):
    LOCATION = "palabralib/tests/test_clues.txt"
    LOCATION2 = "palabralib/tests/test_clues2.txt"

    def tearDown(self):
        if os.path.exists(self.LOCATION):
            os.remove(self.LOCATION)
        if os.path.exists(self.LOCATION2):
            os.remove(self.LOCATION2)

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

    def testReadCluesMalformedLines(self):
        """Lines that do not have 1 word and 1 clue are rejected."""
        with open(self.LOCATION, 'w') as f:
            f.write("word\nword,\n,clue\n,\n\n")
        self.assertEqual(clue.read_clues(self.LOCATION), {})

    def testReadCluesRejectCompound(self): # for now, reject compound
        with open(self.LOCATION, 'w') as f:
            f.write("This is a compound word,clue")
        result = clue.read_clues(self.LOCATION)
        self.assertEqual(result, {})

    def testCreateClueFiles(self):
        """Clue files can be read."""
        with open(self.LOCATION, 'w') as f:
            f.write("word,clue")
        prefs = [{"path": {"value": self.LOCATION}, "name": {"value": "ClueFile"}}]
        result = clue.create_clues(prefs)
        self.assertEqual(result[0].path, self.LOCATION)
        self.assertEqual(result[0].name, "ClueFile")
        self.assertEqual(result[0].data, {"word": ["clue"]})

    def testLookupWordForClues(self):
        """Looking up for a word in clue files results in a list of clues."""
        with open(self.LOCATION, 'w') as f:
            f.write("word,This is a clue")
        prefs = [{"path": {"value": self.LOCATION}, "name": {"value": "ClueFile"}}]
        files = clue.create_clues(prefs)
        self.assertEqual(clue.lookup_clues(files, "word"), ["This is a clue"])

    def testLookupWordForCluesMultiple(self):
        """Clues from multiple files are merged into one list."""
        with open(self.LOCATION, 'w') as f:
            f.write("word,The first clue\nfoobar,Clue for foobar")
        with open(self.LOCATION2, 'w') as f:
            f.write("word,The second clue\n")
        p1 = {"path": {"value": self.LOCATION}, "name": {"value": "P1"}}
        p2 = {"path": {"value": self.LOCATION2}, "name": {"value": "P2"}}
        files = clue.create_clues([p1, p2])
        result = clue.lookup_clues(files, "word")
        self.assertEqual(len(result), 2)
        self.assertTrue("The first clue" in result)
        self.assertTrue("The second clue" in result)
        result = clue.lookup_clues(files, "foobar")
        self.assertEqual(len(result), 1)
        self.assertTrue("Clue for foobar" in result)

    def testLookupCluesCaseInsensitive(self):
        """Looking up clues is case insensitive."""
        with open(self.LOCATION, 'w') as f:
            f.write("word,clue")
        p1 = {"path": {"value": self.LOCATION}, "name": {"value": "P1"}}
        files = clue.create_clues([p1])
        result1 = clue.lookup_clues(files, "word")
        result2 = clue.lookup_clues(files, "Word")
        self.assertEqual(result1, result2)
        self.assertTrue("clue" in result1)

    def testClueWithComma(self):
        """A clue can have a comma in it."""
        with open(self.LOCATION, 'w') as f:
            f.write("word,clue, with comma")
        p1 = {"path": {"value": self.LOCATION}, "name": {"value": "P1"}}
        files = clue.create_clues([p1])
        result = clue.lookup_clues(files, "word")
        self.assertEqual(result, ["clue, with comma"])

    def testClueIterNext(self):
        """It is possible to cycle forward through a list store."""
        store = gtk.ListStore(str)
        store.append(["1"])
        store.append(["2"])
        store.append(["3"])
        it = clue.store_get_item("next", store, store.iter_nth_child(None, 0))
        self.assertEqual(store[it][0], "2")
        it = clue.store_get_item("next", store, store.iter_nth_child(None, 2))
        self.assertEqual(store[it][0], "1")

    def testClueIterPrevious(self):
        """It is possible to cycle backward through a list store."""
        store = gtk.ListStore(str)
        store.append(["1"])
        store.append(["2"])
        store.append(["3"])
        it = clue.store_get_item("previous", store, store.iter_nth_child(None, 2))
        self.assertEqual(store[it][0], "2")
        it = clue.store_get_item("previous", store, store.iter_nth_child(None, 0))
        self.assertEqual(store[it][0], "3")

    def testCountWords(self):
        """The number of words in a clue database can be counted."""
        with open(self.LOCATION, 'w') as f:
            f.write("word,clue\nword2,value2\nword2,value3")
        prefs = [{"path": {"value": self.LOCATION}, "name": {"value": "ClueFile"}}]
        result = clue.create_clues(prefs)
        self.assertEqual(clue.count_n_words(result[0]), 2)

    def testCountClues(self):
        """The number of clues in a clue database can be counted."""
        with open(self.LOCATION, 'w') as f:
            f.write("word,clue\nword2,value2\nword2,value3")
        prefs = [{"path": {"value": self.LOCATION}, "name": {"value": "ClueFile"}}]
        result = clue.create_clues(prefs)
        self.assertEqual(clue.count_n_clues(result[0]), 3)
