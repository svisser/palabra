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
import unittest

import palabralib.cPalabra as cPalabra
import palabralib.constants as constants
from palabralib.grid import Grid
import palabralib.word as word
from palabralib.word import CWordList, search_wordlists, create_wordlists
from palabralib.tests.test_word import test_insert

class WordTestCase2(unittest.TestCase):
    def setUp(self):
        cPalabra.preprocess_all()

    def testAccidentalEntriesDuplicate(self):
        seq1 = ("across", [(0, 0, 'A'), (1, 0, 'B'), (2, 0, 'C')])
        seq2 = ("down", [(3, 3, 'A'), (3, 4, 'B'), (3, 5, 'C')])
        seqs = [seq1, seq2]
        entries = list(word.accidental_entries(seqs, True))
        self.assertEquals(len(entries), 1)
        s0, count0, indices0 = entries[0]
        self.assertEquals(s0, "ABC")
        self.assertEquals(count0, 2)
        self.assertEquals(indices0, "0,1")
        
    def testAccidentalGridPalindrome(self):
        """A palindrome is counted only once as accidental word."""
        seq1 = ("across", [(0, 0, 'N'), (1, 0, 'O'), (2, 0, 'N')])
        seq2 = ("acrossr", [(2, 0, 'N'), (1, 0, 'O'), (0, 0, 'N')])
        seqs = [seq1, seq2]
        entries = list(word.accidental_entries(seqs, True, True))
        self.assertEquals(len(entries), 1)
        s0, count0, indices0 = entries[0]
        self.assertEquals(s0, "NON")
        self.assertEquals(count0, 1)
        self.assertEquals(indices0, "0")
        
    def testAccidentalEntriesPreserveIndices(self):
        seq1 = ("across", [(0, 0, 'N'), (1, 0, 'O'), (2, 0, 'N')])
        seq2 = ("acrossr", [(2, 0, 'N'), (1, 0, 'O'), (0, 0, 'N')])
        seq3 = ("across", [(0, 4, 'X'), (1, 4, 'Y'), (2, 4, 'Z')])
        seqs = [seq1, seq2, seq3]
        entries = list(word.accidental_entries(seqs, True, True))
        self.assertEquals(len(entries), 2)
        s0, count0, indices0 = entries[0]
        s1, count1, indices1 = entries[1]
        self.assertEquals(s0, "NON")
        self.assertEquals(s1, "XYZ")
        self.assertEquals(count0, 1)
        self.assertEquals(count1, 1)
        self.assertEquals(indices0, "0")
        self.assertEquals(indices1, "2")
        
    def testSimilarWords(self):
        """Words are similar when they share a substring of length 3+."""
        # A B C D
        # B _ _ _
        # C _ . _
        # D _ _ _
        g = Grid(4, 4)
        test_insert(g, "ABCD\nB...\nC...\nD...")
        g.set_block(2, 2, True)
        result = word.similar_words(g)
        self.assertTrue("ABC" in result)
        self.assertTrue("BCD" in result)
        self.assertTrue((0, 0, "across", "ABCD") in result["ABC"])
        self.assertTrue((0, 0, "down", "ABCD") in result["ABC"])
        self.assertTrue((0, 0, "across", "ABCD") in result["BCD"])
        self.assertTrue((0, 0, "down", "ABCD") in result["BCD"])
        self.assertTrue("AB" not in result)
        self.assertTrue("BC" not in result)
        self.assertTrue("CD" not in result)
        
    def testSimilarWordsToItself(self):
        """A word is not similar to itself."""
        g = Grid(6, 1)
        test_insert(g, "TAMTAM")
        result = word.similar_words(g)
        # unique substrings of length 3, 4, 5
        self.assertEquals(len(result), 3 + 3 + 2)
        for s, words in result.items():
            self.assertTrue(len(words), 1)
            
    def testSimilarWordsLengths(self):
        """The minimum length of similar words can be specified."""
        # G R A N I T E
        # L I T E . _ _
        g = Grid(7, 2)
        g.set_block(4, 1, True)
        test_insert(g, "GRANITE\nLITE...")
        result = word.similar_words(g, min_length=3)
        self.assertTrue("ITE" in result)
        self.assertTrue((0, 0, "across", "GRANITE") in result["ITE"])
        self.assertTrue((0, 1, "across", "LITE") in result["ITE"])
        result = word.similar_words(g, min_length=4)
        self.assertTrue("ITE" not in result)
        result = word.similar_words(g, min_length=10)
        self.assertEquals(result, {})
        
    def testSimilarEntries(self):
        """A substring in only one word does not appear as similar entry."""
        g = Grid(5, 2)
        test_insert(g, "ABCDE\nBCD..")
        similar = word.similar_words(g)
        self.assertTrue("CDE" in similar)
        entries = word.similar_entries(similar)
        self.assertTrue("CDE" not in entries)
        
    def testSimilarEntriesPartial(self):
        """A substring with missing characters does not appear as similar entry."""
        g = Grid(4, 4)
        test_insert(g, "ABCD\n....\n....\nEFGH")
        similar = word.similar_words(g)
        self.assertTrue("A??" in similar)
        entries = word.similar_entries(similar)
        self.assertTrue("A??" not in entries)
        
    def testSimilarEntriesOffsets(self):
        """Similar entries have (x, y, d, word, offset) of the common substrings."""
        g = Grid(4, 2)
        test_insert(g, "ABCD\nBCDE")
        entries = word.similar_entries(word.similar_words(g))
        self.assertTrue("BCD" in entries)
        self.assertTrue(len(entries["BCD"]), 2)
        self.assertTrue((0, 0, "across", "abcd", 1) in entries["BCD"])
        self.assertTrue((0, 1, "across", "bcde", 0) in entries["BCD"])
        
    def testSearchMultipleListsIntersection(self):
        """Intersection boolean in search result can be due to other word list."""
        w1 = CWordList(["worda"], index=0)
        w2 = CWordList(["wwwww", "ooooo", "rrrrr", "ddddd", "aaaaa"], index=1)
        wordlists = [w1, w2]
        css = [(0, 5, [(0, 'w')])
            , (0, 5, [(0, 'o')])
            , (0, 5, [(0, 'r')])
            , (0, 5, [(0, 'd')])
            , (0, 5, [(0, 'a')])
        ]
        result = search_wordlists(wordlists, 5, "worda", css)
        self.assertTrue(("worda", 0, True) in result)
        cPalabra.postprocess()
        
    def testSearchMultipleListsIntersectionTwo(self):
        """Intersection boolean in search result can be due to multiple lists."""
        w1 = CWordList(["steam", "ttttt", "aaaaa"], index=0)
        w2 = CWordList(["sssss", "eeeee", "mmmmm"], index=1)
        wordlists = [w1, w2]
        css = [(0, 5, [(0, 's')])
            , (0, 5, [(0, 't')])
            , (0, 5, [(0, 'e')])
            , (0, 5, [(0, 'a')])
            , (0, 5, [(0, 'm')])
        ]
        result = search_wordlists(wordlists, 5, "steam", css)
        self.assertTrue(("steam", 0, True) in result)
        cPalabra.postprocess()
        
    def testSearchMultipleListsIntersectionN(self):
        """Intersection boolean in search result can be due to N lists."""
        w1 = CWordList(["reach"], index=0)
        w2 = CWordList(["radar"], index=1)
        w3 = CWordList(["eager"], index=2)
        w4 = CWordList(["adapt"], index=3)
        w5 = CWordList(["cabin"], index=4)
        w6 = CWordList(["haven"], index=5)
        w7 = CWordList(["realm"], index=6)
        wordlists = [w1, w2, w3, w4, w5, w6, w7]
        css = [(0, 5, [(0, 'r')])
            , (0, 5, [(0, 'e')])
            , (0, 5, [(0, 'a')])
            , (0, 5, [(0, 'c')])
            , (0, 5, [(0, 'h')])
        ]
        result = search_wordlists(wordlists, 5, "reach", css)
        self.assertTrue(("reach", 0, True) in result)
        css = [(0, 5, [(0, 'r')])
            , (0, 5, [(0, 'e')])
            , (0, 5, [(0, 'a')])
            , (0, 5, [(0, 'l')])
            , (0, 5, [(0, 'm')])
        ]
        result = search_wordlists(wordlists, 5, "realm", css)
        self.assertTrue(("realm", 0, False) in result)
        cPalabra.postprocess()
        
    def testSearchIntersectionCountMultipleTimes(self):
        """A word can be used multiple times as intersecting word."""
        w1 = CWordList(["aaaaa"], index=0)
        w2 = CWordList(["abaaa"], index=1)
        w3 = CWordList(["bbbbb"], index=2)
        wordlists = [w1, w2, w3]
        css = [(0, 5, [(0, 'a')])
            , (0, 5, [(0, 'b')])
            , (0, 5, [])
            , (0, 5, [])
            , (0, 5, [])
        ]
        result = search_wordlists(wordlists, 5, "ab...", css)
        self.assertTrue(("abaaa", 0, True) in result)
        cPalabra.postprocess()
        
    def testCWordListIndex(self):
        """The same index of a CWordList can be used again."""
        w1 = CWordList(["aaaaa"], index=0)
        w2 = CWordList(["bbbbb"], index=0)
        # now w1 works the same as w2
        self.assertEquals(search_wordlists([w1], 5, "aaaaa"), [])
        self.assertEquals(search_wordlists([w2], 5, "aaaaa"), [])
        self.assertEquals(search_wordlists([w1], 5, "bbbbb"), [("bbbbb", 0, True)])
        self.assertEquals(search_wordlists([w2], 5, "bbbbb"), [("bbbbb", 0, True)])
        cPalabra.postprocess()
        
    def testCWordListIndexArbitrary(self):
        """A CWordList can be created with an arbitrary index (< MAX_WORD_LISTS)."""
        w1 = CWordList(["abcde"], index=33)
        self.assertEquals(search_wordlists([w1], 5, "abcde"), [("abcde", 0, True)])
        cPalabra.postprocess()
        
    def testCWordListIndexArbitraryCSS(self):
        """A CWordList with arbitrary index can be searched with all constraints."""
        w1 = CWordList(["abcde", "bcdef", "cdefg", "defgh", "efghi"], index=33)
        css = [(0, 5, [(0, 'a')])
            , (0, 5, [(0, 'b')])
            , (0, 5, [(0, 'c')])
            , (0, 5, [(0, 'd')])
            , (0, 5, [(0, 'e')])
        ]
        self.assertEqual(search_wordlists([w1], 5, "abcde", css), [("abcde", 0, True)])
        cPalabra.postprocess()
        
    def testRenameWordlists(self):
        """A word list can be renamed in preferences and wordlists data."""
        w1 = {'path': {'value': '/the/path'}, 'name': {'value': "The Word List"}}
        prefs = [w1]
        wordlists = create_wordlists(prefs)
        self.assertTrue(wordlists[0].name, "The Word List")
        word.rename_wordlists(prefs, wordlists, '/the/path', "The New Word List")
        self.assertTrue(prefs[0]["name"]["value"], "The New Word List")
        self.assertTrue(wordlists[0].name, "The New Word List")
        cPalabra.postprocess()
        
    def testRenameWordListMissingPath(self):
        """When a specific path is not present, nothing happens when renaming."""
        w1 = {'path': {'value': '/the/path'}, 'name': {'value': "The Word List"}}
        prefs = [w1]
        wordlists = create_wordlists(prefs)
        self.assertTrue(wordlists[0].name, "The Word List")
        word.rename_wordlists(prefs, wordlists, '/the/missing/path', "The New Word List")
        self.assertTrue(prefs[0]["name"]["value"], "The Word List")
        self.assertTrue(wordlists[0].name, "The Word List")
        cPalabra.postprocess()
        
    def testSearchWordlistsScore(self):
        """Words are stored with a score."""
        w1 = CWordList(["aaaaa", ("bbbbb", 5)])
        result = search_wordlists([w1], 5, ".....")
        self.assertTrue(("aaaaa", 0, True) in result)
        self.assertTrue(("bbbbb", 5, True) in result)
        cPalabra.postprocess()
        
    def testSearchWordListsDefaultScore(self):
        """CWordLists can be created with a default score other than zero."""
        w1 = CWordList(["aaaaa"], score=77)
        result = search_wordlists([w1], 5, ".....")
        self.assertTrue(("aaaaa", 77, True) in result)
        cPalabra.postprocess()
        
    def testSearchScores(self):
        """CWordLists can have the same word with different scores."""
        w1 = CWordList([("aaaaa", 0), ("aaaaa", 5), ("aaaaa", 10)])
        result = search_wordlists([w1], 5, ".....")
        self.assertTrue(("aaaaa", 0, True) in result)
        self.assertTrue(("aaaaa", 5, True) in result)
        self.assertTrue(("aaaaa", 10, True) in result)
        cPalabra.postprocess()
    
    def testSearchDuplicate(self):
        """When inserting a word twice then data structures and search have same length."""
        w1 = CWordList(["abcd", "abcd"])
        result = search_wordlists([w1], 4, "....")
        self.assertEqual(len(result), 2)
        self.assertEqual(len(w1.words[4]), 2)
        cPalabra.postprocess()
        
    def testSearchDuplicateSameScores(self):
        """It is possible to insert the same (word, score) more than once."""
        w1 = CWordList([("foobar", 30), ("foobar", 30), ("foobar", 30)])
        result = search_wordlists([w1], 6, "......")
        self.assertEqual(result, [("foobar", 30, True)] * 3)
        cPalabra.postprocess()
        
    def testNegativeWordScores(self):
        """Words can have negative scores."""
        w1 = CWordList([("word", -1), ("foobar", -100)])
        self.assertTrue(("word", -1) in w1.words[4])
        self.assertTrue(("foobar", -100) in w1.words[6])
        result = search_wordlists([w1], 6, "......")
        self.assertTrue(("foobar", -100, True) in result)
        cPalabra.postprocess()
        
    def testSearchOptionsMinScore(self):
        """A minimum score can be specified for word search."""
        options = {constants.SEARCH_OPTION_MIN_SCORE: 5}
        w1 = CWordList([("car", 0), ("plane", 50), ("hovercraft", 100)])
        result = search_wordlists([w1], 3, "...", options=None)
        self.assertEqual(result, [("car", 0, True)])
        result = search_wordlists([w1], 3, "...", options=options)
        self.assertEqual(result, [])
        cPalabra.postprocess()
        
    def testSearchOptionsScoreEqualToMinScore(self):
        """A word that is equal to the minimum word score will be included."""
        options = {constants.SEARCH_OPTION_MIN_SCORE: 50}
        w1 = CWordList([("foo", 0), ("bar", 50), ("baz", 100)])
        result = search_wordlists([w1], 3, "...", options=options)
        self.assertEqual(len(result), 2)
        self.assertTrue(("bar", 50, True) in result)
        self.assertTrue(("baz", 100, True) in result)
        cPalabra.postprocess()
        
    def testVisibleEntries(self):
        """With no options active then the words are returned identically as visible words."""
        words = [("aaaaa", 0, True), ("ccccc", 0, False), ("bbbbb", 10, True)]
        grid = Grid(5, 5)
        result = word.visible_entries(words, grid
            , show_used=True, show_intersect=False, show_order=0)
        self.assertEqual(result, words)
        
    def testVisibleEntriesScore(self):
        """The visible words can be sorted by score, high-to-low."""
        words = [("aaaaa", 0, True), ("bbbbb", 10, True), ("ccccc", 0, False)]
        grid = Grid(5, 5)
        result = word.visible_entries(words, grid
            , show_used=True, show_intersect=False, show_order=1)
        words2 = [("bbbbb", 10, True), ("aaaaa", 0, True), ("ccccc", 0, False)]
        self.assertEqual(result, words2)
        
    def testVisibleEntriesShowUsed(self):
        """With show_used=False then words already used are not shown as visible word."""
        words = [("aaaaa", 0, True), ("bbbbb", 10, True), ("ccccc", 0, False)]
        grid = Grid(5, 5)
        grid.set_char(0, 0, 'A')
        grid.set_char(1, 0, 'A')
        grid.set_char(2, 0, 'A')
        grid.set_char(3, 0, 'A')
        grid.set_char(4, 0, 'A')
        result = word.visible_entries(words, grid
            , show_used=False, show_intersect=False, show_order=0)
        self.assertEqual(result, [("bbbbb", 10, True), ("ccccc", 0, False)])
        
    def testVisibleEntriesShowIntersect(self):
        """With show_intersect=True then words with no intersecting words are not shown."""
        words = [("aaaaa", 0, True), ("bbbbb", 10, True), ("ccccc", 0, False)]
        grid = Grid(5, 5)
        result = word.visible_entries(words, grid
            , show_used=True, show_intersect=True, show_order=0)
        self.assertEqual(result, [("aaaaa", 0, True), ("bbbbb", 10, True)])
        
    def testVisibleEntriesAllOptions(self):
        """The various options of visible_entries can be combined."""
        words = [("aaaaa", 0, True), ("bbbbb", 10, True), ("ccccc", 0, False)]
        grid = Grid(5, 5)
        result = word.visible_entries(words, grid
            , show_used=False, show_intersect=True, show_order=1)
        self.assertEqual(result, [("bbbbb", 10, True), ("aaaaa", 0, True)])
    
    def testMinimumWordScoreIntersection(self):
        """
        The minimum word score influences
        whether the intersection boolean is True or False.
        """
        w1 = CWordList([("abc", 1), ("aaa", 0), ("bbb", 0), ("ccc", 0)])
        css = [(0, 3, [(0, 'a')])
            , (0, 3, [(0, 'b')])
            , (0, 3, [(0, 'c')])
        ]
        result = search_wordlists([w1], 3, "abc", css)
        self.assertEqual(result, [("abc", 1, True)])
        options = {
            constants.SEARCH_OPTION_MIN_SCORE: 1
        }
        result = search_wordlists([w1], 3, "abc", css, options=options)
        self.assertEqual(result, [("abc", 1, False)])
        cPalabra.postprocess()
        
    def testSearchWordlistsFullIntersectingWord(self):
        """
        A fully filled in intersectin word is effectively ignored for
        intersection boolean in search results.
        """
        w1 = CWordList(["abc", "aaa", "bbb", "ccc"])
        css = [(0, 3, [(0, 'a'), (1, 'b'), (2, 'c')]), (0, 3, []), (0, 3, [])]
        result = search_wordlists([w1], 3, "a..", css)
        self.assertEqual(len(result), 2)
        self.assertTrue(("abc", 0, True) in result)
        self.assertTrue(("aaa", 0, True) in result)
        cPalabra.postprocess()
        
    def testUpdateScore(self):
        """The score of a word can be updated."""
        w1 = CWordList([("abc", 10), ("abc", 20), ("def", 0)])
        w1.update_score("abc", 30)
        self.assertTrue(("abc", 30) in w1.words[3])
        self.assertTrue(("abc", 20) in w1.words[3])
        self.assertTrue(("def", 0) in w1.words[3])
        cPalabra.postprocess()
        
    def testUpdateScoreSearchAfterwards(self):
        """When searching for words after updating a score, the new score is returned."""
        w1 = CWordList([("score", 10)])
        w1.update_score("score", 40)
        result = search_wordlists([w1], 5, "score")
        self.assertTrue(("score", 40, True) in result)
        cPalabra.postprocess()
        
    def testWriteWordLists(self):
        """Word lists can be written to file."""
        LOC = "palabralib/tests/test_wordlist.txt"
        w1 = CWordList(["one", "two", "three"])
        w1.path = LOC
        w2 = CWordList("/usr/does/not/exist")
        w2.name = "fail"
        self.assertEqual(word.write_wordlists([w1]), [])
        result = word.write_wordlists([w1, w2])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "fail")
        cPalabra.postprocess()
        if os.path.exists(LOC):
            os.remove(LOC)
            
    def testCountWords(self):
        """The number of words in a word list can be computed."""
        w1 = CWordList([], index=0)
        self.assertEqual(w1.count_words(), 0)
        w2 = CWordList(["a", "ab", "abc", "abcd"], index=1)
        self.assertEqual(w2.count_words(), 4)
        cPalabra.postprocess()
        
    def testComputeWordCounts(self):
        """The number of words by length can be computed."""
        w1 = CWordList(["a", "bc", "def", "klm", "ghij"])
        counts = w1.get_word_counts()
        self.assertTrue(len(counts), constants.MAX_WORD_LENGTH)
        self.assertTrue(counts[1], 1)
        self.assertTrue(counts[2], 1)
        self.assertTrue(counts[3], 2)
        self.assertTrue(counts[4], 1)
        cPalabra.postprocess()
        
    def testComputeScoreCounts(self):
        """The number of words by score can be computed."""
        w1 = CWordList([("a", 3), ("bc", 4), ("def", 3), ("klm", 4), "ghij"])
        scores = w1.get_score_counts()
        self.assertEqual(len(scores), 3)
        self.assertEqual(scores[3], 2)
        self.assertEqual(scores[4], 2)
        self.assertEqual(scores[0], 1)
        cPalabra.postprocess()
        
    def testAverageWordLength(self):
        """The average word length of words in a word list can be computed."""
        w1 = CWordList([])
        self.assertEqual(w1.average_word_length(), 0)
        w2 = CWordList(["abc", "abcd", "abcde", "abcdef", "abcdefg"])
        self.assertEqual(w2.average_word_length(), 5)
        w3 = CWordList(["abc", "abcd", "abcde", "abcdef", "abcdefg", "abcdefgh"])
        self.assertEqual(w3.average_word_length(), 5.5)
        cPalabra.postprocess()
        
    def testAverageWordScore(self):
        """The average score of words in a word list can be computed."""
        w1 = CWordList([])
        self.assertEqual(w1.average_word_score(), 0)
        w2 = CWordList([("a", 3), ("b", 4), ("c", 5), ("d", 6), ("e", 7)])
        self.assertEqual(w2.average_word_score(), 5)
        w3 = CWordList([("a", 3), ("b", 4), ("c", 5), ("d", 6), ("e", 7), ("f", 8)])
        self.assertEqual(w3.average_word_score(), 5.5)
        cPalabra.postprocess()
        
    def testWriteToFile(self):
        """An individual word list can be written to and read from a file."""
        LOC = "palabralib/tests/test_wordlist.txt"
        w1 = CWordList([("abc", 0), ("palabra", 50), ("australia", 100)])
        w1.path = LOC
        w1.write_to_file()
        w2 = CWordList(LOC)
        self.assertTrue(('abc', 0) in w2.words[3])
        self.assertTrue(('palabra', 50) in w2.words[7])
        self.assertTrue(('australia', 100) in w2.words[9])
        cPalabra.postprocess()
        if os.path.exists(LOC):
            os.remove(LOC)
        
    def testAddWord(self):
        """A word can be added to a word list."""
        w1 = CWordList([])
        w1.add_word("palabra", 33)
        self.assertTrue(('palabra', 33) in w1.words[7])
        results = search_wordlists([w1], 7, "palabra")
        self.assertEqual(results, [('palabra', 33, True)])
        self.assertEqual(w1.count_words(), 1)
        cPalabra.postprocess()
    
    def testRemoveWords(self):
        """One or more words can be removed from a word list."""
        w1 = CWordList([("palabra", 33), ("palabra", 50)])
        w1.remove_words([("palabra", 50)])
        self.assertTrue(w1.words[7], [('palabra', 33)])
        results = search_wordlists([w1], 7, "palabra")
        self.assertEqual(results, [('palabra', 33, True)])
        self.assertEqual(w1.count_words(), 1)
        cPalabra.postprocess()
        
    def testRemoveNotExistWord(self):
        """Requesting to remove a word that is not in the word list is possible."""
        w1 = CWordList(["koala"])
        w1.remove_words([("steam", 33)])
        self.assertEqual(w1.words[5], [('koala', 0)])
        cPalabra.postprocess()
    
    def testChangeAllScoresTo(self):
        """All scores in a word list can be changed to a specified value."""
        words = ["koala", "wombat", "australia"]
        w1 = CWordList(words)
        for w in words:
            self.assertTrue((w, 0) in w1.words[len(w)])
        w1.change_scores("to", 44)
        for w in words:
            self.assertTrue((w, 44) in w1.words[len(w)])
        cPalabra.postprocess()
    
    def testChangeAllScoresBy(self):
        """All scores in a word list can be changed by a specified delta."""
        words = [("singapore", 50), ("malaysia", 40), ("australia", 30)]
        w1 = CWordList(words)
        for item in words:
            self.assertTrue(item in w1.words[len(item[0])])
        w1.change_scores("by", -4)
        for w, score in words:
            self.assertTrue((w, score - 4) in w1.words[len(w)])
        w1.change_scores("by", 40)
        for w, score in words:
            self.assertTrue((w, score - 4 + 40) in w1.words[len(w)])
        cPalabra.postprocess()
