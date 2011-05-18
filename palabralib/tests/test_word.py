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
            self.assertEquals(w[0], self.word)
        for w in clist.search(self.length, self.constraints):
            self.assertEquals(w[0], self.word)
        cPalabra.postprocess()
        
    def testSearchBasicTwo(self):
        clist = CWordList([self.word, self.word2])
        cs = [(0, "p"), (1, "a")]
        for w in clist.search(self.length, cs):
            self.assertEquals(w[0], self.word)
        for w in clist.search(self.length2, cs):
            self.assertEquals(w[0], self.word2)
        cPalabra.postprocess()
        
    def testSearchMore(self):
        clist = CWordList([self.word, self.word2, "peach", "azure", "roast", "reach", "oasis", "trunk"])
        for w in clist.search(5, [(0, "p")]):
            self.assertEquals(w[0], "peach")
        for w in clist.search(5, [(0, "a")]):
            self.assertEquals(w[0], "azure")
        rs = clist.search(5, [(0, "r")])
        rss = [w for w, x in rs]
        self.assertEquals("reach" in rss, True)
        self.assertEquals("roast" in rss, True)
        for w in clist.search(5, [(0, "o")]):
            self.assertEquals(w[0], "oasis")
        for w in clist.search(5, [(0, "t")]):
            self.assertEquals(w[0], "trunk")
        
        # all first characters
        css = [(0, 5, [(0, c)]) for c in "parrot"]
        for w in clist.search(self.length2, [], css):
            self.assertEquals(w[0], self.word2)
        cPalabra.postprocess()
        
    def testSearchMoreTwo(self):
        clist = CWordList([self.word, self.word2, "peach", "azure", "roast", "reach", "oasis", "trunk"
            , "cabin", "cargo", "beard", "amino", "adrift"])
        # diagonal
        css = [(i, 5, [(i, self.word2[i])]) for i in xrange(5)] + [(5, 6, [(5, "t")])]
        results = clist.search(self.length2, [(0, 'p')], css)
        self.assertEquals(len(results), 1)
        self.assertEquals(results[0][0], self.word2)
        cPalabra.postprocess()
                
    #####
    
    def testBasic(self):
        self.basic = CWordList(["koala", "kangaroo", "aardvark", "loophole", "outgoing"])
        self.assertEquals(self.basic.search(5, [], None), [("koala", True)])
        self.assertEquals(self.basic.search(6, [], None), [])
        css_eight = [(0, 8, []), (0, 8, []), (0, 8, []), (0, 8, []), (0, 8, [])]
        css_seven = [(0, 7, []), (0, 7, []), (0, 7, []), (0, 7, []), (0, 7, [])]
        css_eight_t = [(0, 8, [(7, 'o')]), (0, 8, []), (0, 8, []), (0, 8, []), (0, 8, [])]
        css_eight_f = [(0, 8, [(7, 'p')]), (0, 8, []), (0, 8, []), (0, 8, []), (0, 8, [])]
        self.assertEquals(self.basic.search(5, [], css_eight), [("koala", True)])
        self.assertEquals(self.basic.search(5, [], css_seven), [("koala", False)])
        self.assertEquals(self.basic.search(5, [(4, 'a')], css_eight), [("koala", True)])
        self.assertEquals(self.basic.search(5, [(4, 'a')], css_seven), [("koala", False)])
        self.assertEquals(self.basic.search(5, [(4, 'a')], css_eight_t), [("koala", True)])
        self.assertEquals(self.basic.search(5, [(4, 'a')], css_eight_f), [("koala", False)])
        cPalabra.postprocess()
        
    def testIntersecting(self):
        clist = CWordList(["aaaa", "bbbb", "abbb"])
        
        # 4 chars, starts with 'a', 4 chars at all intersections
        css = [(0, 4, []), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEquals(clist.search(4, [(0, 'a')], css), [("aaaa", True), ("abbb", True)])

        # 4 chars, starts with 'a', 4 chars at intersection 0 that ends with 'b'
        css = [(0, 4, [(3, 'b')]), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEquals(clist.search(4, [(0, 'a')], css), [("aaaa", True), ("abbb", True)])
        
        # 4 chars, starts with 'b', 4 chars at all intersections
        css = [(0, 4, []), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEquals(clist.search(4, [(0, 'b')], css), [("bbbb", True)])
        
        # 4 chars, starts with 'a', 4 chars at intersection 0 that starts with 'ab'
        css = [(0, 4, [(0, 'a'), (1, 'b')]), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEquals(clist.search(4, [(0, 'a')], css), [("aaaa", True), ("abbb", True)])
        
        # 4 chars, starts with 'b', 4 chars at intersection 0 that starts with 'aba'
        css = [(0, 4, [(0, 'a'), (1, 'b'), (2, 'a')]), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEquals(clist.search(4, [(0, 'b')], css), [("bbbb", False)])
        
        # 4 chars, starts with 'b', 4 chars at intersection 0 that ends with 'a'
        css = [(0, 4, [(3, 'a')]), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEquals(clist.search(4, [(0, 'b')], css), [("bbbb", False)])
        
        # 4 chars, ends with 'b', 4 chars at intersection 0 that ends with 'a'
        css = [(0, 4, [(3, 'a')]), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEquals(clist.search(4, [(3, 'b')], css), [("abbb", True), ("bbbb", False)])
        
        # 4 chars, 5 chars at intersection 0
        css = [(0, 5, []), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEquals(clist.search(4, [], css), [("aaaa", False), ("abbb", False), ("bbbb", False)])
        
        # 4 chars, 4 chars at intersection 0 that ends with 'c'
        css = [(0, 4, [(3, 'c')]), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEquals(clist.search(4, [], css), [("aaaa", False), ("abbb", False), ("bbbb", False)])

        # 3 chars, no further constraints
        self.assertEquals(clist.search(3, [], None), [])
        
        # 3 chars, no further constraints, 4 chars at all intersections
        css = [(0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEquals(clist.search(3, [], css), [])
        
        # negative, zero chars and MAX_WORD_LENGTH chars
        self.assertEquals(clist.search(-1, [], None), [])
        self.assertEquals(clist.search(0, [], None), [])
        self.assertEquals(clist.search(MAX_WORD_LENGTH, [], None), [])
        
        cPalabra.postprocess()
        
    def testEmpty(self):
        clist = CWordList([])
        self.assertEquals(clist.search(4, [], None), [])
        css = [(0, 4, []), (0, 5, []), (0, 6, []), (0, 7, [])]
        self.assertEquals(clist.search(4, [], css), [])
        # identical css, for testing skipping in C code
        css = [(0, 4, []), (0, 5, []), (0, 4, []), (0, 5, [])]
        self.assertEquals(clist.search(4, [], css), [])
        cPalabra.postprocess()
        
    def testInsertPrePost(self):
        clist = CWordList(self.MANY_WORDS)
        for l, words in clist.words.items():
            pre_list = clist.words[l]
            pre_count = len(pre_list)
            post_list = [a for a, b in clist.search(l, [], None)]
            post_count = len(post_list)
            self.assertEquals(pre_count, post_count)
            pre_list.sort()
            post_list.sort()
            self.assertEquals(pre_list, post_list)
        cPalabra.postprocess()
        
    def testScale(self):
        clist = CWordList(self.MANY_FOUR_WORDS)
        total4 = len(clist.search(4, [], None))
        totals = {}
        for c in string.ascii_lowercase:
            totals[c] = len(clist.search(4, [(0, c)], None))
        self.assertEquals(total4, sum(totals.values()))
        cPalabra.postprocess()
        
    def testMaxWordLength(self):
        l = MAX_WORD_LENGTH + 10
        words = ['a' * l, 'a' * MAX_WORD_LENGTH, 'a' * (MAX_WORD_LENGTH - 1)]
        clist = CWordList(words)
        self.assertEquals(clist.search(l, []), [])
        self.assertEquals(clist.search(MAX_WORD_LENGTH, []), [])
        self.assertEquals(len(clist.search(MAX_WORD_LENGTH - 1, [])), 1)
        cPalabra.postprocess()
        
    def testMaxWordLengthTwo(self):
        l = MAX_WORD_LENGTH + 10
        LOC = "palabralib/tests/test_wordlist.txt"
        with open(LOC, 'w') as f:
            words = ['a' * l, '\n', 'a' * MAX_WORD_LENGTH, '\n', 'a' * (MAX_WORD_LENGTH - 1), '\n']
            f.write(''.join(words))
        clist = CWordList(LOC)
        self.assertEquals(clist.search(l, []), [])
        self.assertEquals(clist.search(MAX_WORD_LENGTH, []), [])
        self.assertEquals(len(clist.search(MAX_WORD_LENGTH - 1, [])), 1)
        cPalabra.postprocess()
        if os.path.exists(LOC):
            os.remove(LOC)
            
    def testFileDoesNotExist(self):
        clist = CWordList('/does/not/exist/file')
        self.assertEquals(clist.search(5, [], None), [])
        cPalabra.postprocess()
        
    def testReadWordsWithRank(self):
        LOC = "palabralib/tests/test_wordlist.txt"
        with open(LOC, 'w') as f:
            f.write("worda\nwordb,0\nwordc , 100\nwordd, 500, is_wrong")
        clist = CWordList(LOC)
        words = [w for w, b in clist.search(5, [])]
        self.assertEquals(words, ["worda", "wordb", "wordc"])
        cPalabra.postprocess()
        
    def testRankedInput(self):
        clist = CWordList(["unranked", ("ranked", 50)])
        self.assertEquals(len(clist.search(6, [])), 1)
        self.assertEquals(len(clist.search(8, [])), 1)
        cPalabra.postprocess()
        
    def testCompoundOne(self):
        LOC = "palabralib/tests/test_wordlist.txt"
        with open(LOC, 'w') as f:
            f.write("word spaces")
        clist = CWordList(LOC)
        self.assertEquals(clist.search(10, []), [])
        self.assertEquals(clist.search(11, []), [])
        cPalabra.postprocess()
        
    def testCompoundTwo(self):
        clist = CWordList(["a a"])
        self.assertEquals(clist.search(2, []), [])
        self.assertEquals(clist.search(3, []), [])
        cPalabra.postprocess()
        
    def testEmptyWord(self):
        clist = CWordList([""])
        self.assertEquals(clist.search(0, []), [])
        cPalabra.postprocess()
        
    def testFindPattern(self):
        clist = CWordList(["w", "woo", "word"])
        self.assertEquals(len(clist.find_by_pattern("*")), 3)
        self.assertEquals(clist.find_by_pattern("?"), ["w"])
        self.assertEquals(len(clist.find_by_pattern("w*")), 3)
        self.assertEquals(clist.find_by_pattern("w*d"), ["word"])
        self.assertEquals(clist.find_by_pattern("wo"), [])
        self.assertEquals(len(clist.find_by_pattern("*o*")), 2)
        self.assertEquals(len(clist.find_by_pattern("?o*")), 2)
        self.assertEquals(clist.find_by_pattern("W"), ["w"])
        self.assertEquals(clist.find_by_pattern("w(!@@#$%??"), ["woo"])
        cPalabra.postprocess()
        
    def testSearchWordlistsByPattern(self):
        c1 = CWordList(["koala", "kangaroo", "wombat"], name="Australia")
        c2 = CWordList(["shark", "fish", "whale"], name="Marine")
        c3 = CWordList(["widget", "gui", "button"])
        c4 = CWordList(["baltimore", "washington", "huntsville"])
        c4.path = "/this/is/the/path"
        result = word.search_wordlists_by_pattern([c1, c2, c3, c4], "w*")
        self.assertEquals(len(result), 4)
        self.assertTrue(("Australia", "wombat") in result)
        self.assertTrue(("Marine", "whale") in result)
        self.assertTrue((None, "widget") in result)
        self.assertTrue(("/this/is/the/path", "washington") in result)
        cPalabra.postprocess()
        
    def testCreateWordLists(self):
        w1 = {'path': {'value': '/the/path'}, 'name': {'value': 'the name'}}
        w2 = {'path': {'value': '/somewhere/else'}, 'name': {'value': 'the name 2'}}
        prefs = [w1, w2]
        result = create_wordlists(prefs)
        self.assertEquals(len(result), 2)
        self.assertEquals(result[0].name, "the name")
        self.assertEquals(result[0].path, "/the/path")
        self.assertEquals(result[1].name, "the name 2")
        self.assertEquals(result[1].path, "/somewhere/else")
        self.assertTrue(result[0].index != result[1].index)
        
    def testCreateWordListsCapAtMax(self):
        prefs = []
        for n in xrange(MAX_WORD_LISTS + 10):
            prefs.append({'path': {'value': 'P'}, 'name': {'value': 'N'}})
        result = create_wordlists(prefs)
        self.assertEquals(len(result), MAX_WORD_LISTS)
        cPalabra.postprocess()
        
    def testCreateWordListsUniqueIndices(self):
        prefs = []
        for n in xrange(MAX_WORD_LISTS):
            prefs.append({'path': {'value': 'P'}, 'name': {'value': 'N'}})
        result = create_wordlists(prefs)
        self.assertEquals(len(set([item.index for item in result])), MAX_WORD_LISTS)
        cPalabra.postprocess()
        
    def testSearchWordlists(self):
        w1 = CWordList(["worda"], index=0)
        w2 = CWordList(["wordb"], index=1)
        wordlists = [w1, w2]
        words = [w for w, b in search_wordlists(wordlists, 5, ".....")]
        self.assertEquals(["worda", "wordb"], words)
        words = [w for w, b in search_wordlists([w1], 5, ".....")]
        self.assertEquals(["worda"], words)
        words = [w for w, b in search_wordlists([w2], 5, ".....")]
        self.assertEquals(["wordb"], words)
        cPalabra.postprocess()
        
    def testCheckStrForWords(self):
        wlist = CWordList(["abc", "def", "ghi"])
        result = check_str_for_words([wlist], 0, "abcdefghi")
        self.assertEquals(len(result), 3)
        self.assertTrue((0, 3) in result)
        self.assertTrue((3, 3) in result)
        self.assertTrue((6, 3) in result)
        cPalabra.postprocess()
        
    def testCheckStrForWordsOverlap(self):
        wlist = CWordList(["abc", "def", "cd"])
        result = check_str_for_words([wlist], 0, "abcdef")
        self.assertEquals(len(result), 3)
        self.assertTrue((0, 3) in result)
        self.assertTrue((2, 2) in result)
        self.assertTrue((3, 3) in result)
        cPalabra.postprocess()
        
    def testCheckStrForWordsOne(self):
        wlist = CWordList(["a", "b", "c"])
        result = check_str_for_words([wlist], 0, "abccba")
        self.assertEquals(len(result), 6)
        for i in xrange(6):
            self.assertTrue((i, 1) in result)
        cPalabra.postprocess()
            
    def testCheckStrForWordsEmpty(self):
        self.assertEquals(check_str_for_words([], 0, "abc"), [])
        
    def testCheckStrForWordsSameOffset(self):
        wlist = CWordList(["a", "ab", "abc", "abcd"])
        result = check_str_for_words([wlist], 0, "abcd")
        self.assertEquals(len(result), 4)
        for i in xrange(4):
            self.assertTrue((0, i + 1) in result)
        cPalabra.postprocess()
        
    def testCheckStrForWordsWithin(self):
        wlist = CWordList(["a", "ab"])
        result = check_str_for_words([wlist], 0, "abab")
        self.assertEquals(len(result), 4)
        self.assertTrue((0, 1) in result)
        self.assertTrue((2, 1) in result)
        self.assertTrue((0, 2) in result)
        self.assertTrue((2, 2) in result)
        cPalabra.postprocess()
        
    def testCheckStrForWordsOffset(self):
        wlist = CWordList(["abc", "def"])
        result = check_str_for_words([wlist], 5, "abcdef")
        self.assertEquals(len(result), 2)
        self.assertTrue((5, 3) in result)
        self.assertTrue((8, 3) in result)
        cPalabra.postprocess()
        
    def testSeqToCellsEmpty(self):
        result = word.seq_to_cells([(x, 0, MISSING_CHAR) for x in xrange(10)])
        self.assertEquals(result, [])
        
    def testSeqToCellsOneSplit(self):
        seq = [(0, 0, 'A'), (1, 0, 'B'), (2, 0, MISSING_CHAR), (3, 0, 'C'), (4, 0, 'D')]
        result = word.seq_to_cells(seq)
        self.assertEquals(len(result), 2)
        self.assertTrue((0, [(0, 0, 'A'), (1, 0, 'B')]) in result)
        self.assertTrue((3, [(3, 0, 'C'), (4, 0, 'D')]) in result)
        
    def testSeqToCellsTwoSplits(self):
        seq = [(0, 0, 'A'), (1, 0, 'B'), (2, 0, MISSING_CHAR)
            , (3, 0, 'C'), (4, 0, 'D'), (5, 0, MISSING_CHAR)
            , (6, 0, 'E'), (7, 0, 'F')
        ]
        result = word.seq_to_cells(seq)
        self.assertEquals(len(result), 3)
        self.assertTrue((0, [(0, 0, 'A'), (1, 0, 'B')]) in result)
        self.assertTrue((3, [(3, 0, 'C'), (4, 0, 'D')]) in result)
        self.assertTrue((6, [(6, 0, 'E'), (7, 0, 'F')]) in result)
        
    def testSeqToCellsShort(self):
        seq = [(0, 0, 'A'), (1, 0, MISSING_CHAR), (2, 0, 'B')]
        result = word.seq_to_cells(seq)
        self.assertEquals(result, [])
        
    def testSeqToCellsShortTwo(self):
        seq = [(0, 0, 'A'), (1, 0, MISSING_CHAR), (2, 0, 'B'), (3, 0, 'C')]
        result = word.seq_to_cells(seq)
        self.assertEquals(len(result), 1)
        self.assertTrue((2, [(2, 0, 'B'), (3, 0, 'C')]) in result)
        
    def testSeqToCellsMultipleMissing(self):
        seq = [(0, 0, 'A'), (1, 0, MISSING_CHAR)
            , (2, 0, MISSING_CHAR), (3, 0, 'C'), (4, 0, 'D')]
        result = word.seq_to_cells(seq)
        self.assertEquals(len(result), 1)
        self.assertTrue((3, [(3, 0, 'C'), (4, 0, 'D')]) in result)
        
    def testAccidentalWordlists(self):
        clist = CWordList(["steam"])
        seq = [(0, 0, 'S'), (1, 0, 'T'), (2, 0, 'E'), (3, 0, 'A'), (4, 0, 'M')]
        result = word.check_accidental_word([clist], seq)
        self.assertEquals(result, [(0, 5)])
        cPalabra.postprocess()
        
    def testAccidentalWordlistsTwo(self):
        clist = CWordList(["be", "cd"])
        seq = [(0, 0, 'B'), (1, 0, 'E'), (2, 0, 'X'), (3, 0, 'C'), (4, 0, 'D')]
        result = word.check_accidental_word([clist], seq)
        self.assertEquals(result, [(0, 2), (3, 2)])
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
        self.assertEquals(len(result), 4)
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
        self.assertEquals(len(result), 2)
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
        self.assertEquals(len(result), 1)
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
        self.assertEquals(len(result), 1)
        self.assertTrue(("across", [(0, 0, 'B'), (1, 0, 'A'), (2, 0, 'D')]) in result)
        cPalabra.postprocess()
        
    def testWordlistIllegalChars(self):
        clist = CWordList(["abc!", "john@example.com", "#number"])
        for l, words in clist.words.items():
            self.assertEquals(words, [])
        cPalabra.postprocess()
        
    def testWordListIllegalCharsFile(self):
        LOC = "palabralib/tests/test_wordlist.txt"
        with open(LOC, 'w') as f:
            f.write("abc!\njohn@example.com\n#number")
        clist = CWordList(LOC)
        for l, words in clist.words.items():
            self.assertEquals(words, [])
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
        self.assertEquals(len(result), 4)
        for d, cells in result:
            self.assertEquals("NO", ''.join([c for x, y, c in cells]))
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
        self.assertEquals(len(result), 4)
        for d, cells in result:
            self.assertEquals("NO", ''.join([c for x, y, c in cells]))
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
        self.assertEquals(len(result), 2)
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
        self.assertEquals(len(result), 1)
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
        self.assertEquals(len(result), 4)
        cPalabra.postprocess()
        
    def testAccidentalEntries(self):
        seq1 = ("across", [(0, 0, 'A'), (1, 0, 'B'), (2, 0, 'C')])
        seq2 = ("down", [(3, 3, 'D'), (3, 4, 'E'), (3, 5, 'F')])
        seqs = [seq1, seq2]
        entries = list(word.accidental_entries(seqs))
        self.assertEquals(len(entries), 2)
        s0, count0, indices0 = entries[0]
        s1, count1, indices1 = entries[1]
        self.assertEquals(s0, "ABC")
        self.assertEquals(s1, "DEF")
        self.assertEquals(count0, 1)
        self.assertEquals(count1, 1)
        self.assertEquals(indices0, str(0))
        self.assertEquals(indices1, str(1))
        
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
