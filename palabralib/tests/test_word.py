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
from palabralib.constants import MAX_WORD_LENGTH
from palabralib.word import CWordList

class WordTestCase(unittest.TestCase):
    def setUp(self):
        self.word = "palabra"
        self.length = len(self.word)
        self.constraints = [(i, self.word[i]) for i in xrange(self.length)]
        
        self.word2 = "parrot"
        self.length2 = len(self.word2)
        self.constraints2 = [(i, self.word2[i]) for i in xrange(self.length2)]
        
    def testHasMatchesOneWord(self):
        clist = CWordList([self.word])
        check = clist.has_matches(self.length, self.constraints)
        self.assertEquals(check, True)
        check = clist.has_matches(self.length, [])
        self.assertEquals(check, True)
        for i in xrange(self.length):
            for j in xrange(i, self.length):
                check = clist.has_matches(self.length, self.constraints[i:j])
                self.assertEquals(check, True)
        cPalabra.postprocess()
                
    def testHasMatchesMultiple(self):
        clist = CWordList([self.word, self.word2])
        cs = [(0, "p"), (1, "a")]
        self.assertEquals(clist.has_matches(self.length, []), True)
        self.assertEquals(clist.has_matches(self.length2, []), True)
        self.assertEquals(clist.has_matches(self.length, cs), True)
        self.assertEquals(clist.has_matches(self.length2, cs), True)
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
        for l in xrange(64):
            self.assertEquals(self.basic.has_matches(l, []), l in [5, 8])
        self.assertEquals(self.basic.has_matches(5, [(0, 'k'), (4, 'a')]), True)
        self.assertEquals(self.basic.has_matches(5, [(0, 'k'), (4, 'b')]), False)
        self.assertEquals([w for w in self.basic.search(5, [], None)], [("koala", True)])
        self.assertEquals([w for w in self.basic.search(6, [], None)], [])
        css_eight = [(0, 8, []), (0, 8, []), (0, 8, []), (0, 8, []), (0, 8, [])]
        css_seven = [(0, 7, []), (0, 7, []), (0, 7, []), (0, 7, []), (0, 7, [])]
        css_eight_t = [(0, 8, [(7, 'o')]), (0, 8, []), (0, 8, []), (0, 8, []), (0, 8, [])]
        css_eight_f = [(0, 8, [(7, 'p')]), (0, 8, []), (0, 8, []), (0, 8, []), (0, 8, [])]
        self.assertEquals([w for w in self.basic.search(5, [], css_eight)], [("koala", True)])
        self.assertEquals([w for w in self.basic.search(5, [], css_seven)], [("koala", False)])
        self.assertEquals([w for w in self.basic.search(5, [(4, 'a')], css_eight)], [("koala", True)])
        self.assertEquals([w for w in self.basic.search(5, [(4, 'a')], css_seven)], [("koala", False)])
        self.assertEquals([w for w in self.basic.search(5, [(4, 'a')], css_eight_t)], [("koala", True)])
        self.assertEquals([w for w in self.basic.search(5, [(4, 'a')], css_eight_f)], [("koala", False)])
        self.basic.postprocess()
        
    def testIntersecting(self):
        clist = CWordList(["aaaa", "bbbb", "abbb"])
        
        # 4 chars, starts with 'a', 4 chars at all intersections
        css = [(0, 4, []), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEquals([w for w in clist.search(4, [(0, 'a')], css)], [("aaaa", True), ("abbb", True)])

        # 4 chars, starts with 'a', 4 chars at intersection 0 that ends with 'b'
        css = [(0, 4, [(3, 'b')]), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEquals([w for w in clist.search(4, [(0, 'a')], css)], [("aaaa", True), ("abbb", True)])
        
        # 4 chars, starts with 'b', 4 chars at all intersections
        css = [(0, 4, []), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEquals([w for w in clist.search(4, [(0, 'b')], css)], [("bbbb", True)])
        
        # 4 chars, starts with 'a', 4 chars at intersection 0 that starts with 'ab'
        css = [(0, 4, [(0, 'a'), (1, 'b')]), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEquals([w for w in clist.search(4, [(0, 'a')], css)], [("aaaa", True), ("abbb", True)])
        
        # 4 chars, starts with 'b', 4 chars at intersection 0 that starts with 'aba'
        css = [(0, 4, [(0, 'a'), (1, 'b'), (2, 'a')]), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEquals([w for w in clist.search(4, [(0, 'b')], css)], [("bbbb", False)])
        
        # 4 chars, starts with 'b', 4 chars at intersection 0 that ends with 'a'
        css = [(0, 4, [(3, 'a')]), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEquals([w for w in clist.search(4, [(0, 'b')], css)], [("bbbb", False)])
        
        # 4 chars, ends with 'b', 4 chars at intersection 0 that ends with 'a'
        css = [(0, 4, [(3, 'a')]), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEquals([w for w in clist.search(4, [(3, 'b')], css)], [("abbb", True), ("bbbb", False)])
        
        # 4 chars, 5 chars at intersection 0
        css = [(0, 5, []), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEquals([w for w in clist.search(4, [], css)], [("aaaa", False), ("abbb", False), ("bbbb", False)])
        
        # 4 chars, 4 chars at intersection 0 that ends with 'c'
        css = [(0, 4, [(3, 'c')]), (0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEquals([w for w in clist.search(4, [], css)], [("aaaa", False), ("abbb", False), ("bbbb", False)])

        # 3 chars, no further constraints
        self.assertEquals([w for w in clist.search(3, [], None)], [])
        
        # 3 chars, no further constraints, 4 chars at all intersections
        css = [(0, 4, []), (0, 4, []), (0, 4, [])]
        self.assertEquals([w for w in clist.search(3, [], css)], [])
        
        # negative, zero chars and MAX_WORD_LENGTH chars
        self.assertEquals([w for w in clist.search(-1, [], None)], [])
        self.assertEquals([w for w in clist.search(0, [], None)], [])
        self.assertEquals([w for w in clist.search(MAX_WORD_LENGTH, [], None)], [])
        
        cPalabra.postprocess()
        
    def testEmpty(self):
        clist = CWordList([])
        self.assertEquals(len([w for w in clist.search(4, [], None)]), 0)
        css = [(0, 4, []), (0, 5, []), (0, 6, []), (0, 7, [])]
        self.assertEquals(len([w for w in clist.search(4, [], css)]), 0)
        for x in xrange(35):
            self.assertEquals(clist.has_matches(x, []), False)
            for c in string.ascii_lowercase:
                self.assertEquals(clist.has_matches(x, [(0, c)]), False)
        # identical css, for testing skipping in C code
        css = [(0, 4, []), (0, 5, []), (0, 4, []), (0, 5, [])]
        self.assertEquals(len([w for w in clist.search(4, [], css)]), 0)
        cPalabra.postprocess()
        
    def testInsertPrePost(self):
        clist = CWordList('/usr/share/dict/words')
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
        clist = CWordList('/usr/share/dict/words')
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
        f = open(LOC, 'w')
        words = ['a' * l, '\n', 'a' * MAX_WORD_LENGTH, '\n', 'a' * (MAX_WORD_LENGTH - 1), '\n']
        f.write(''.join(words))
        f.close()
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
