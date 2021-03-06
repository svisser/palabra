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
import string
import unittest

import palabralib.cPalabra as cPalabra
import palabralib.constants as constants
from palabralib.constants import (
    MAX_WORD_LISTS,
    MAX_WORD_LENGTH,
    MISSING_CHAR,
)
from palabralib.grid import Grid
import palabralib.word as word
from palabralib.word import (
    CWordList,
    create_wordlists,
    search_wordlists,
    check_str_for_words,
)

def test_insert(grid, content):
    rows = content.split("\n")
    for i, row in enumerate(rows):
        for j, c in enumerate(row):
            if c == '.':
                continue
            grid.set_char(j, i, c)

class WordTestCase(unittest.TestCase):
    def setUp(self):
        self.word = "palabra"
        self.length = len(self.word)
        self.constraints = [(i, self.word[i]) for i in xrange(self.length)]
        self.word2 = "parrot"
        self.length2 = len(self.word2)
        self.constraints2 = [(i, self.word2[i]) for i in xrange(self.length2)]
        self.MANY_WORDS = [string.ascii_lowercase[0:l] for l in xrange(len(string.ascii_lowercase) + 1)]
        self.MANY_FOUR_WORDS = [string.ascii_lowercase[i:i + 4] for i in xrange(len(string.ascii_lowercase) - 3)]
        cPalabra.preprocess_all()

    def testPostprocess(self):
        # must not fail when nothing was allocated
        cPalabra.postprocess()

    def testSearchBasic(self):
        clist = CWordList([self.word])
        for w in clist.search(self.length, []):
            self.assertEqual(w[0], self.word)
        for w in clist.search(self.length, self.constraints):
            self.assertEqual(w[0], self.word)
        cPalabra.postprocess()

    def testSearchBasicTwo(self):
        clist = CWordList([self.word, self.word2])
        cs = [(0, "p"), (1, "a")]
        for w in clist.search(self.length, cs):
            self.assertEqual(w[0], self.word)
        for w in clist.search(self.length2, cs):
            self.assertEqual(w[0], self.word2)
        cPalabra.postprocess()

    def testSearchMore(self):
        clist = CWordList([self.word, self.word2, "peach", "azure", "roast", "reach", "oasis", "trunk"])
        for w in clist.search(5, [(0, "p")]):
            self.assertEqual(w[0], "peach")
        for w in clist.search(5, [(0, "a")]):
            self.assertEqual(w[0], "azure")
        rs = clist.search(5, [(0, "r")])
        rss = [w for w, score, b in rs]
        self.assertEqual("reach" in rss, True)
        self.assertEqual("roast" in rss, True)
        for w in clist.search(5, [(0, "o")]):
            self.assertEqual(w[0], "oasis")
        for w in clist.search(5, [(0, "t")]):
            self.assertEqual(w[0], "trunk")

        # all first characters
        css = [(0, 5, [(0, c)]) for c in "parrot"]
        for w in clist.search(self.length2, [], css):
            self.assertEqual(w[0], self.word2)
        cPalabra.postprocess()

    def testSearchMoreTwo(self):
        clist = CWordList([self.word, self.word2, "peach", "azure", "roast", "reach", "oasis", "trunk"
            , "cabin", "cargo", "beard", "amino", "adrift"])
        # diagonal
        css = [(i, 5, [(i, self.word2[i])]) for i in xrange(5)] + [(5, 6, [(5, "t")])]
        results = clist.search(self.length2, [(0, 'p')], css)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], self.word2)
        cPalabra.postprocess()

    #####

    def testBasic(self):
        self.basic = CWordList(["koala", "kangaroo", "aardvark", "loophole", "outgoing"])
        self.assertEqual(self.basic.search(5, [], None), [("koala", 0, True)])
        self.assertEqual(self.basic.search(6, [], None), [])
        css_eight = [(0, 8, []), (0, 8, []), (0, 8, []), (0, 8, []), (0, 8, [])]
        css_seven = [(0, 7, []), (0, 7, []), (0, 7, []), (0, 7, []), (0, 7, [])]
        css_eight_t = [(0, 8, [(7, 'o')]), (0, 8, []), (0, 8, []), (0, 8, []), (0, 8, [])]
        css_eight_f = [(0, 8, [(7, 'p')]), (0, 8, []), (0, 8, []), (0, 8, []), (0, 8, [])]
        self.assertEqual(self.basic.search(5, [], css_eight), [("koala", 0, True)])
        self.assertEqual(self.basic.search(5, [], css_seven), [("koala", 0, False)])
        self.assertEqual(self.basic.search(5, [(4, 'a')], css_eight), [("koala", 0, True)])
        self.assertEqual(self.basic.search(5, [(4, 'a')], css_seven), [("koala", 0, False)])
        self.assertEqual(self.basic.search(5, [(4, 'a')], css_eight_t), [("koala", 0, True)])
        self.assertEqual(self.basic.search(5, [(4, 'a')], css_eight_f), [("koala", 0, False)])
        cPalabra.postprocess()

    def testIntersecting(self):
        clist = CWordList(["aaaa", "bbbb", "abbb"])

        # 4 chars, starts with 'a', 4 chars at all intersections
        css = [(0, 4, []), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEqual(clist.search(4, [(0, 'a')], css), [("aaaa", 0, True), ("abbb", 0, True)])

        # 4 chars, starts with 'a', 4 chars at intersection 0 that ends with 'b'
        css = [(0, 4, [(3, 'b')]), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEqual(clist.search(4, [(0, 'a')], css), [("aaaa", 0, True), ("abbb", 0, True)])

        # 4 chars, starts with 'b', 4 chars at all intersections
        css = [(0, 4, []), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEqual(clist.search(4, [(0, 'b')], css), [("bbbb", 0, True)])

        # 4 chars, starts with 'a', 4 chars at intersection 0 that starts with 'ab'
        css = [(0, 4, [(0, 'a'), (1, 'b')]), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEqual(clist.search(4, [(0, 'a')], css), [("aaaa", 0, True), ("abbb", 0, True)])

        # 4 chars, starts with 'b', 4 chars at intersection 0 that starts with 'aba'
        css = [(0, 4, [(0, 'a'), (1, 'b'), (2, 'a')]), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEqual(clist.search(4, [(0, 'b')], css), [("bbbb", 0, False)])

        # 4 chars, starts with 'b', 4 chars at intersection 0 that ends with 'a'
        css = [(0, 4, [(3, 'a')]), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEqual(clist.search(4, [(0, 'b')], css), [("bbbb", 0, False)])

        # 4 chars, ends with 'b', 4 chars at intersection 0 that ends with 'a'
        css = [(0, 4, [(3, 'a')]), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEqual(clist.search(4, [(3, 'b')], css), [("abbb", 0, True), ("bbbb", 0, False)])

        # 4 chars, 5 chars at intersection 0
        css = [(0, 5, []), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEqual(clist.search(4, [], css), [("aaaa", 0, False), ("abbb", 0, False), ("bbbb", 0, False)])

        # 4 chars, 4 chars at intersection 0 that ends with 'c'
        css = [(0, 4, [(3, 'c')]), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEqual(clist.search(4, [], css), [("aaaa", 0, False), ("abbb", 0, False), ("bbbb", 0, False)])

        # 3 chars, no further constraints
        self.assertEqual(clist.search(3, [], None), [])

        # 3 chars, no further constraints, 4 chars at all intersections
        css = [(0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEqual(clist.search(3, [], css), [])

        # negative, zero chars and MAX_WORD_LENGTH chars
        self.assertEqual(clist.search(-1, [], None), [])
        self.assertEqual(clist.search(0, [], None), [])
        self.assertEqual(clist.search(MAX_WORD_LENGTH, [], None), [])

        cPalabra.postprocess()

    def testEmpty(self):
        clist = CWordList([])
        self.assertEqual(clist.search(4, [], None), [])
        css = [(0, 4, []), (0, 5, []), (0, 6, []), (0, 7, [])]
        self.assertEqual(clist.search(4, [], css), [])
        # identical css, for testing skipping in C code
        css = [(0, 4, []), (0, 5, []), (0, 4, []), (0, 5, [])]
        self.assertEqual(clist.search(4, [], css), [])
        cPalabra.postprocess()

    def testInsertPrePost(self):
        clist = CWordList(self.MANY_WORDS)
        for l, words in clist.words.items():
            pre_list = clist.words[l]
            pre_count = len(pre_list)
            post_list = [w for w, score, b in clist.search(l, [], None)]
            post_count = len(post_list)
            self.assertEqual(pre_count, post_count)
            pre_list.sort()
            post_list.sort()
            self.assertEqual([w for w, score in pre_list], post_list)
        cPalabra.postprocess()

    def testScale(self):
        """A word list can deal with a variety of words."""
        clist = CWordList(self.MANY_FOUR_WORDS)
        total4 = len(clist.search(4, [], None))
        totals = {}
        for c in string.ascii_lowercase:
            totals[c] = len(clist.search(4, [(0, c)], None))
        self.assertEqual(total4, sum(totals.values()))
        cPalabra.postprocess()

    def testMaxWordLength(self):
        """All words in a word list are shorter than MAX_WORD_LENGTH."""
        l = MAX_WORD_LENGTH + 10
        words = ['a' * l, 'a' * MAX_WORD_LENGTH, 'a' * (MAX_WORD_LENGTH - 1)]
        clist = CWordList(words)
        self.assertEqual(clist.search(l, []), [])
        self.assertEqual(clist.search(MAX_WORD_LENGTH, []), [])
        self.assertEqual(len(clist.search(MAX_WORD_LENGTH - 1, [])), 1)
        cPalabra.postprocess()

    def testMaxWordLengthTwo(self):
        l = MAX_WORD_LENGTH + 10
        LOC = "palabralib/tests/test_wordlist.txt"
        with open(LOC, 'w') as f:
            words = ['a' * l, '\n', 'a' * MAX_WORD_LENGTH, '\n', 'a' * (MAX_WORD_LENGTH - 1), '\n']
            f.write(''.join(words))
        clist = CWordList(LOC)
        self.assertEqual(clist.search(l, []), [])
        self.assertEqual(clist.search(MAX_WORD_LENGTH, []), [])
        self.assertEqual(len(clist.search(MAX_WORD_LENGTH - 1, [])), 1)
        cPalabra.postprocess()
        if os.path.exists(LOC):
            os.remove(LOC)

    def testInvalidScore(self):
        """Words with an invalid score are ignored."""
        LOC = "palabralib/tests/test_wordlist.txt"
        with open(LOC, 'w') as f:
            f.write("word,score")
        clist = CWordList(LOC)
        self.assertEqual(clist.words[4], [])
        cPalabra.postprocess()
        if os.path.exists(LOC):
            os.remove(LOC)

    def testFileDoesNotExist(self):
        """Loading a file that does not exist results in an empty word list."""
        clist = CWordList('/does/not/exist/file')
        for k, words in clist.words.items():
            self.assertEqual(clist.search(k, []), [])
            self.assertEqual(words, [])
        cPalabra.postprocess()

    def testReadWordsWithScore(self):
        """Word lists in files can have scores."""
        LOC = "palabralib/tests/test_wordlist.txt"
        with open(LOC, 'w') as f:
            f.write("worda\nwordb,0\nwordc , 100\nwordd, 500, is_wrong")
        clist = CWordList(LOC)
        result = clist.search(5, [])
        self.assertEqual(len(result), 3)
        self.assertTrue(("worda", 0, True) in result)
        self.assertTrue(("wordb", 0, True) in result)
        self.assertTrue(("wordc", 100, True) in result)
        cPalabra.postprocess()

    def testRankedInput(self):
        """A word can optionally have a score."""
        clist = CWordList(["unranked", ("ranked", 50)])
        self.assertEqual(clist.search(6, []), [("ranked", 50, True)])
        self.assertEqual(clist.search(8, []), [("unranked", 0, True)])
        cPalabra.postprocess()

    def testCompoundOne(self):
        LOC = "palabralib/tests/test_wordlist.txt"
        with open(LOC, 'w') as f:
            f.write("word spaces")
        clist = CWordList(LOC)
        self.assertEqual(clist.search(10, []), [("wordspaces", 0, True)])
        self.assertEqual(clist.search(11, []), [])
        cPalabra.postprocess()

    def testCompoundTwo(self):
        clist = CWordList(["a a"])
        self.assertEqual(clist.search(2, []), [("aa", 0, True)])
        self.assertEqual(clist.search(3, []), [])
        cPalabra.postprocess()

    def testCompoundMaxFile(self):
        """
        A word has at most constants.MAX_WORD_LENGTH - 1 (inclusive)
        non-space characters.
        """
        LOC = "palabralib/tests/test_wordlist.txt"
        with open(LOC, 'w') as f:
            f.write("a " * (constants.MAX_WORD_LENGTH - 1))
        clist = CWordList(LOC)
        result = clist.search(constants.MAX_WORD_LENGTH - 1, [])
        expected = [((constants.MAX_WORD_LENGTH - 1) * "a", 0, True)]
        self.assertEqual(result, expected)
        cPalabra.postprocess()

    def testCompoundMaxList(self):
        """
        A word has at most constants.MAX_WORD_LENGTH - 1 (inclusive)
        non-space characters.
        """
        clist = CWordList(["a " * (constants.MAX_WORD_LENGTH - 1)])
        result = clist.search(constants.MAX_WORD_LENGTH - 1, [])
        expected = [((constants.MAX_WORD_LENGTH - 1) * "a", 0, True)]
        self.assertEqual(result, expected)
        cPalabra.postprocess()

    def testEmptyWord(self):
        """An empty word is ignored when creating a word list."""
        clist = CWordList([""])
        self.assertEqual(clist.search(0, []), [])
        cPalabra.postprocess()

    def testFindPattern(self):
        """A word list can be searched using a basic regex pattern."""
        clist = CWordList(["w", "woo", "word"])
        self.assertEqual(len(clist.find_by_pattern("*")), 3)
        self.assertEqual(clist.find_by_pattern("?"), [("w", 0)])
        self.assertEqual(len(clist.find_by_pattern("w*")), 3)
        self.assertEqual(clist.find_by_pattern("w*d"), [("word", 0)])
        self.assertEqual(clist.find_by_pattern("wo"), [])
        self.assertEqual(len(clist.find_by_pattern("*o*")), 2)
        self.assertEqual(len(clist.find_by_pattern("?o*")), 2)
        self.assertEqual(clist.find_by_pattern("W"), [("w", 0)])
        self.assertEqual(clist.find_by_pattern("w(!@@#$%??"), [("woo", 0)])
        cPalabra.postprocess()

    def testSearchWordlistsByPattern(self):
        """Multiple word lists can be searched by pattern."""
        c1 = CWordList(["koala", "kangaroo", "wombat"], name="Australia")
        c2 = CWordList(["shark", "fish", "whale"], name="Marine")
        c3 = CWordList(["widget", "gui", "button"])
        c4 = CWordList(["baltimore", "washington", "huntsville"])
        c4.path = "/this/is/the/path"
        result = word.search_wordlists_by_pattern([c1, c2, c3, c4], "w*")
        self.assertEqual(len(result), 4)
        self.assertTrue(("Australia", "wombat", 0) in result)
        self.assertTrue(("Marine", "whale", 0) in result)
        self.assertTrue((None, "widget", 0) in result)
        self.assertTrue(("/this/is/the/path", "washington", 0) in result)
        cPalabra.postprocess()

    def testSearchByPatternSorting(self):
        """The result of searching by pattern can be sorted."""
        c1 = CWordList([("koala", 50), ("australia", 10), ("wombat", 5)], name="Words")
        # alphabet
        result = word.search_wordlists_by_pattern([c1], "*", sort=0)
        expected = [("Words", "australia", 10), ("Words", "koala", 50), ("Words", "wombat", 5)]
        self.assertEqual(result, expected)
        # length
        result = word.search_wordlists_by_pattern([c1], "*", sort=1)
        expected = [("Words", "koala", 50), ("Words", "wombat", 5), ("Words", "australia", 10)]
        self.assertEqual(result, expected)
        # score
        result = word.search_wordlists_by_pattern([c1], "*", sort=2)
        expected = [("Words", "koala", 50), ("Words", "australia", 10), ("Words", "wombat", 5)]
        self.assertEqual(result, expected)
        cPalabra.postprocess()

    def testCreateWordLists(self):
        w1 = {'path': {'value': '/the/path'}, 'name': {'value': 'the name'}}
        w2 = {'path': {'value': '/somewhere/else'}, 'name': {'value': 'the name 2'}}
        prefs = [w1, w2]
        result = create_wordlists(prefs)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "the name")
        self.assertEqual(result[0].path, "/the/path")
        self.assertEqual(result[1].name, "the name 2")
        self.assertEqual(result[1].path, "/somewhere/else")
        self.assertTrue(result[0].index != result[1].index)
        cPalabra.postprocess()

    def testCreateWordListsCapAtMax(self):
        prefs = []
        for n in xrange(MAX_WORD_LISTS + 10):
            prefs.append({'path': {'value': 'P'}, 'name': {'value': 'N'}})
        result = create_wordlists(prefs)
        self.assertEqual(len(result), MAX_WORD_LISTS)
        cPalabra.postprocess()

    def testCreateWordListsUniqueIndices(self):
        prefs = []
        for n in xrange(MAX_WORD_LISTS):
            prefs.append({'path': {'value': 'P'}, 'name': {'value': 'N'}})
        result = create_wordlists(prefs)
        self.assertEqual(len(set([item.index for item in result])), MAX_WORD_LISTS)
        cPalabra.postprocess()

    def testCreateWordListsPrevious(self):
        """A word list can be added to the list of word lists."""
        w1 = {'path': {'value': '/the/path'}, 'name': {'value': 'the name'}}
        previous = create_wordlists([w1])
        w2 = {'path': {'value': '/the/other/path'}, 'name': {'value': 'the other name'}}
        result = create_wordlists([w1, w2], previous=previous)
        self.assertEqual(len(result), 2)
        self.assertTrue(result[0].path != result[1].path)
        cPalabra.postprocess()

    def testCreateWordListsPreviousRemove(self):
        """A word list can be removed and the previous word list is still used."""
        w1 = {'path': {'value': '/the/path'}, 'name': {'value': 'the name'}}
        w2 = {'path': {'value': '/the/other/path'}, 'name': {'value': 'the other name'}}
        previous = create_wordlists([w1, w2])
        result = create_wordlists([w2], previous=previous)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].path, '/the/other/path')

    def testCreateWordListsPreviousRemoveMultiple(self):
        """Removing multiple word lists at once is possible."""
        prefs = []
        for n in xrange(MAX_WORD_LISTS):
            prefs.append({'path': {'value': 'P' + str(n)}, 'name': {'value': str(n)}})
        previous = create_wordlists(prefs)
        next = [p for p in prefs if int(p["name"]["value"]) % 2 == 0]
        result = create_wordlists(next, previous=previous)
        self.assertEqual(len(result), MAX_WORD_LISTS / 2)
        for clist in result:
            self.assertEqual(int(clist.index) % 2, 0)

    def testCreateWordListsPreviousAddMultiple(self):
        """Adding multiple word lists is possible."""
        prefs = []
        for n in xrange(MAX_WORD_LISTS):
            prefs.append({'path': {'value': 'P' + str(n)}, 'name': {'value': str(n)}})
        previous = create_wordlists([p for p in prefs if n % 2 == 0])
        result = create_wordlists(prefs, previous=previous)
        self.assertEqual(len(result), MAX_WORD_LISTS)
        indices = [clist.index for clist in result]
        self.assertEqual(len(set(indices)), MAX_WORD_LISTS)

    def testCreateAndSearch(self):
        PATH1 = "palabralib/tests/test_wordlist1.txt"
        PATH2 = "palabralib/tests/test_wordlist2.txt"
        with open(PATH1, 'w') as f:
            f.write("fish\nwhale")
        with open(PATH2, 'w') as g:
            g.write("bear\nlion\ntiger")
        p1 = {"path": {"value": PATH1}, "name": {"value": "Word list name 1"}}
        p2 = {"path": {"value": PATH2}, "name": {"value": "Word list name 2"}}
        wordlists = create_wordlists([p1, p2])
        result = search_wordlists(wordlists, 4, "....")
        self.assertEqual(len(result), 3)
        self.assertTrue(("fish", 0, True) in result)
        self.assertTrue(("bear", 0, True) in result)
        self.assertTrue(("lion", 0, True) in result)
        os.remove(PATH1)
        os.remove(PATH2)

    def testSearchWordlists(self):
        w1 = CWordList(["worda"], index=0)
        w2 = CWordList(["wordb"], index=1)
        wordlists = [w1, w2]
        words = [w for w, score, b in search_wordlists(wordlists, 5, ".....")]
        self.assertEqual(["worda", "wordb"], words)
        words = [w for w, score, b in search_wordlists([w1], 5, ".....")]
        self.assertEqual(["worda"], words)
        words = [w for w, score, b in search_wordlists([w2], 5, ".....")]
        self.assertEqual(["wordb"], words)
        cPalabra.postprocess()

    def testCheckStrForWords(self):
        wlist = CWordList(["abc", "def", "ghi"])
        result = check_str_for_words([wlist], 0, "abcdefghi")
        self.assertEqual(len(result), 3)
        self.assertTrue((0, 3) in result)
        self.assertTrue((3, 3) in result)
        self.assertTrue((6, 3) in result)
        cPalabra.postprocess()

    def testCheckStrForWordsOverlap(self):
        wlist = CWordList(["abc", "def", "cd"])
        result = check_str_for_words([wlist], 0, "abcdef")
        self.assertEqual(len(result), 3)
        self.assertTrue((0, 3) in result)
        self.assertTrue((2, 2) in result)
        self.assertTrue((3, 3) in result)
        cPalabra.postprocess()

    def testCheckStrForWordsOne(self):
        wlist = CWordList(["a", "b", "c"])
        result = check_str_for_words([wlist], 0, "abccba")
        self.assertEqual(len(result), 6)
        for i in xrange(6):
            self.assertTrue((i, 1) in result)
        cPalabra.postprocess()

    def testCheckStrForWordsEmpty(self):
        self.assertEqual(check_str_for_words([], 0, "abc"), [])

    def testCheckStrForWordsSameOffset(self):
        wlist = CWordList(["a", "ab", "abc", "abcd"])
        result = check_str_for_words([wlist], 0, "abcd")
        self.assertEqual(len(result), 4)
        for i in xrange(4):
            self.assertTrue((0, i + 1) in result)
        cPalabra.postprocess()

    def testCheckStrForWordsWithin(self):
        wlist = CWordList(["a", "ab"])
        result = check_str_for_words([wlist], 0, "abab")
        self.assertEqual(len(result), 4)
        self.assertTrue((0, 1) in result)
        self.assertTrue((2, 1) in result)
        self.assertTrue((0, 2) in result)
        self.assertTrue((2, 2) in result)
        cPalabra.postprocess()

    def testCheckStrForWordsOffset(self):
        wlist = CWordList(["abc", "def"])
        result = check_str_for_words([wlist], 5, "abcdef")
        self.assertEqual(len(result), 2)
        self.assertTrue((5, 3) in result)
        self.assertTrue((8, 3) in result)
        cPalabra.postprocess()

    def testSeqToCellsEmpty(self):
        result = word.seq_to_cells([(x, 0, MISSING_CHAR) for x in xrange(10)])
        self.assertEqual(result, [])

    def testSeqToCellsOneSplit(self):
        seq = [(0, 0, 'A'), (1, 0, 'B'), (2, 0, MISSING_CHAR), (3, 0, 'C'), (4, 0, 'D')]
        result = word.seq_to_cells(seq)
        self.assertEqual(len(result), 2)
        self.assertTrue((0, [(0, 0, 'A'), (1, 0, 'B')]) in result)
        self.assertTrue((3, [(3, 0, 'C'), (4, 0, 'D')]) in result)

    def testSeqToCellsTwoSplits(self):
        seq = [(0, 0, 'A'), (1, 0, 'B'), (2, 0, MISSING_CHAR)
            , (3, 0, 'C'), (4, 0, 'D'), (5, 0, MISSING_CHAR)
            , (6, 0, 'E'), (7, 0, 'F')
        ]
        result = word.seq_to_cells(seq)
        self.assertEqual(len(result), 3)
        self.assertTrue((0, [(0, 0, 'A'), (1, 0, 'B')]) in result)
        self.assertTrue((3, [(3, 0, 'C'), (4, 0, 'D')]) in result)
        self.assertTrue((6, [(6, 0, 'E'), (7, 0, 'F')]) in result)

    def testSeqToCellsShort(self):
        seq = [(0, 0, 'A'), (1, 0, MISSING_CHAR), (2, 0, 'B')]
        result = word.seq_to_cells(seq)
        self.assertEqual(result, [])

    def testSeqToCellsShortTwo(self):
        seq = [(0, 0, 'A'), (1, 0, MISSING_CHAR), (2, 0, 'B'), (3, 0, 'C')]
        result = word.seq_to_cells(seq)
        self.assertEqual(len(result), 1)
        self.assertTrue((2, [(2, 0, 'B'), (3, 0, 'C')]) in result)

    def testSeqToCellsMultipleMissing(self):
        seq = [(0, 0, 'A'), (1, 0, MISSING_CHAR)
            , (2, 0, MISSING_CHAR), (3, 0, 'C'), (4, 0, 'D')]
        result = word.seq_to_cells(seq)
        self.assertEqual(len(result), 1)
        self.assertTrue((3, [(3, 0, 'C'), (4, 0, 'D')]) in result)

    def testAccidentalWordlists(self):
        clist = CWordList(["steam"])
        seq = [(0, 0, 'S'), (1, 0, 'T'), (2, 0, 'E'), (3, 0, 'A'), (4, 0, 'M')]
        result = word.check_accidental_word([clist], seq)
        self.assertEqual(result, [(0, 5)])
        cPalabra.postprocess()

    def testAccidentalWordlistsTwo(self):
        clist = CWordList(["be", "cd"])
        seq = [(0, 0, 'B'), (1, 0, 'E'), (2, 0, 'X'), (3, 0, 'C'), (4, 0, 'D')]
        result = word.check_accidental_word([clist], seq)
        self.assertEqual(result, [(0, 2), (3, 2)])
        cPalabra.postprocess()

    def testAccidentalGrid(self):
        clist = CWordList(["no"])
        # N _ _ _ N
        # _ O _ O _
        # _ _ _ _ _
        # _ O _ O _
        # N _ _ _ N
        g = Grid(5, 5)
        g.set_char(0, 0, 'N')
        g.set_char(4, 0, 'N')
        g.set_char(0, 4, 'N')
        g.set_char(4, 4, 'N')
        g.set_char(1, 1, 'O')
        g.set_char(1, 3, 'O')
        g.set_char(3, 1, 'O')
        g.set_char(3, 3, 'O')
        result = word.check_accidental_words([clist], g)
        self.assertEqual(len(result), 4)
        self.assertTrue(("ne", [(0, 4, 'N'), (1, 3, 'O')]) in result)
        self.assertTrue(("se", [(0, 0, 'N'), (1, 1, 'O')]) in result)
        self.assertTrue(("sw", [(4, 0, 'N'), (3, 1, 'O')]) in result)
        self.assertTrue(("nw", [(4, 4, 'N'), (3, 3, 'O')]) in result)
        cPalabra.postprocess()

    def testAccidentalGridMissingChars(self):
        clist = CWordList(["no", "on"])
        # N _ _
        # _ O _
        # _ _ _
        g = Grid(3, 3)
        g.set_char(0, 0, 'N')
        g.set_char(1, 1, 'O')
        result = word.check_accidental_words([clist], g)
        self.assertEqual(len(result), 2)
        for d, cells in result:
            for x, y, c in cells:
                self.assertTrue(c != MISSING_CHAR)
        cPalabra.postprocess()

    def testAccidentalGridIgnoreNormalSlots(self):
        clist = CWordList(["bad"])
        # B A D
        # A A _
        # D _ D
        g = Grid(3, 3)
        g.set_char(0, 0, 'B')
        g.set_char(1, 0, 'A')
        g.set_char(2, 0, 'D')
        g.set_char(0, 1, 'A')
        g.set_char(0, 2, 'D')
        g.set_char(1, 1, 'A')
        g.set_char(2, 2, 'D')
        result = word.check_accidental_words([clist], g)
        self.assertEqual(len(result), 1)
        self.assertTrue(("se", [(0, 0, 'B'), (1, 1, 'A'), (2, 2, 'D')]) in result)
        cPalabra.postprocess()

    def testAccidentalSubstrings(self):
        clist = CWordList(["bad"])
        g = Grid(5, 5)
        g.set_char(0, 0, 'B')
        g.set_char(1, 0, 'A')
        g.set_char(2, 0, 'D')
        g.set_char(3, 0, 'L')
        g.set_char(4, 0, 'Y')
        result = word.check_accidental_words([clist], g)
        self.assertEqual(len(result), 1)
        self.assertTrue(("across", [(0, 0, 'B'), (1, 0, 'A'), (2, 0, 'D')]) in result)
        cPalabra.postprocess()

    def testWordlistIllegalChars(self):
        clist = CWordList(["abc!", "john@example.com", "#number"])
        for l, words in clist.words.items():
            self.assertEqual(words, [])
        cPalabra.postprocess()

    def testWordListIllegalCharsFile(self):
        LOC = "palabralib/tests/test_wordlist.txt"
        with open(LOC, 'w') as f:
            f.write("abc!\njohn@example.com\n#number")
        clist = CWordList(LOC)
        for l, words in clist.words.items():
            self.assertEqual(words, [])
        cPalabra.postprocess()

    def testAccidentalGridTwo(self):
        clist = CWordList(["no"])
        # N _ N
        # _ O _
        # N _ N
        g = Grid(3, 3)
        g.set_char(0, 0, 'N')
        g.set_char(2, 0, 'N')
        g.set_char(0, 2, 'N')
        g.set_char(2, 2, 'N')
        g.set_char(1, 1, 'O')
        result = word.check_accidental_words([clist], g)
        self.assertEqual(len(result), 4)
        for d, cells in result:
            self.assertEqual("NO", ''.join([c for x, y, c in cells]))
        cPalabra.postprocess()

    def testAccidentalGridThree(self):
        clist = CWordList(["no"])
        # _ _ _ _ _
        # _ N _ N _
        # _ _ O _ _
        # _ N _ N _
        # _ _ _ _ _
        g = Grid(5, 5)
        g.set_char(1, 1, 'N')
        g.set_char(3, 1, 'N')
        g.set_char(1, 3, 'N')
        g.set_char(3, 3, 'N')
        g.set_char(2, 2, 'O')
        result = word.check_accidental_words([clist], g)
        self.assertEqual(len(result), 4)
        for d, cells in result:
            self.assertEqual("NO", ''.join([c for x, y, c in cells]))
        cPalabra.postprocess()

    def testAccidentalGridReverse(self):
        clist = CWordList(["radar"])
        g = Grid(6, 5)
        g.set_char(0, 0, 'R')
        g.set_char(1, 0, 'A')
        g.set_char(2, 0, 'D')
        g.set_char(3, 0, 'A')
        g.set_char(4, 0, 'R')
        result = word.check_accidental_words([clist], g)
        self.assertEqual(len(result), 2)
        cPalabra.postprocess()

    def testAccidentalGridReverseTwo(self):
        clist = CWordList(["abcde"])
        g = Grid(5, 1)
        g.set_char(0, 0, 'E')
        g.set_char(1, 0, 'D')
        g.set_char(2, 0, 'C')
        g.set_char(3, 0, 'B')
        g.set_char(4, 0, 'A')
        result = word.check_accidental_words([clist], g)
        self.assertEqual(len(result), 1)
        cPalabra.postprocess()

    def testAccidentalGridMultipleLists(self):
        clist1 = CWordList(["ab"], index=0)
        clist2 = CWordList(["ba"], index=1)
        # _ _ A
        # _ B _
        # A _ _
        g = Grid(3, 3)
        g.set_char(0, 2, 'A')
        g.set_char(1, 1, 'B')
        g.set_char(2, 0, 'A')
        result = word.check_accidental_words([clist1, clist2], g)
        self.assertEqual(len(result), 4)
        cPalabra.postprocess()

    def testAccidentalEntries(self):
        seq1 = ("across", [(0, 0, 'A'), (1, 0, 'B'), (2, 0, 'C')])
        seq2 = ("down", [(3, 3, 'D'), (3, 4, 'E'), (3, 5, 'F')])
        seqs = [seq1, seq2]
        entries = list(word.accidental_entries(seqs))
        self.assertEqual(len(entries), 2)
        s0, count0, indices0 = entries[0]
        s1, count1, indices1 = entries[1]
        self.assertEqual(s0, "ABC")
        self.assertEqual(s1, "DEF")
        self.assertEqual(count0, 1)
        self.assertEqual(count1, 1)
        self.assertEqual(indices0, str(0))
        self.assertEqual(indices1, str(1))
