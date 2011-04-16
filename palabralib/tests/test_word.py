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

import string
import unittest
from palabralib.word import WordList, CWordList, read_wordlist

class WordTestCase(unittest.TestCase):
    def setUp(self):
        self.wordlist = WordList()
        
        self.word = "palabra"
        self.length = len(self.word)
        self.constraints = [(i, self.word[i]) for i in xrange(self.length)]
        
        self.word2 = "parrot"
        self.length2 = len(self.word2)
        self.constraints2 = [(i, self.word2[i]) for i in xrange(self.length2)]
        
    def testHasMatchesEmpty(self):
        for x in xrange(35):
            self.assertEquals(self.wordlist.has_matches(x, []), False)
            for y in xrange(26):
                c = chr(ord("a") + y)
                self.assertEquals(self.wordlist.has_matches(x, [(0, c)]), False)
        
    def testHasMatchesOneWord(self):
        self.wordlist.add_word(self.word)
        check = self.wordlist.has_matches(self.length, self.constraints)
        
        self.assertEquals(check, True)
        check = self.wordlist.has_matches(self.length, [])
        self.assertEquals(check, True)
        
        for i in xrange(self.length):
            for j in xrange(i, self.length):
                check = self.wordlist.has_matches(self.length, self.constraints[i:j])
                self.assertEquals(check, True)
                
    def testHasMatchesMultiple(self):
        self.wordlist.add_word(self.word)
        self.wordlist.add_word(self.word2)
        cs = [(0, "p"), (1, "a")]
        self.assertEquals(self.wordlist.has_matches(self.length, []), True)
        self.assertEquals(self.wordlist.has_matches(self.length2, []), True)
        self.assertEquals(self.wordlist.has_matches(self.length, cs), True)
        self.assertEquals(self.wordlist.has_matches(self.length2, cs), True)
    
    def testSearchBasic(self):
        self.wordlist.add_word(self.word)
        for w in self.wordlist.search(self.length, []):
            self.assertEquals(w[0], self.word)
        for w in self.wordlist.search(self.length, self.constraints):
            self.assertEquals(w[0], self.word)
        
        cs = [(0, "p"), (1, "a")]
        self.wordlist.add_word(self.word2)
        for w in self.wordlist.search(self.length, cs):
            self.assertEquals(w[0], self.word)
        for w in self.wordlist.search(self.length2, cs):
            self.assertEquals(w[0], self.word2)
        
    def testSearchMore(self):
        self.wordlist.add_word(self.word)
        self.wordlist.add_word(self.word2)
        self.wordlist.add_word("peach")
        self.wordlist.add_word("azure")
        self.wordlist.add_word("roast")
        self.wordlist.add_word("reach")
        self.wordlist.add_word("oasis")
        self.wordlist.add_word("trunk")
        
        for w in self.wordlist.search(5, [(0, "p")]):
            self.assertEquals(w[0], "peach")
        for w in self.wordlist.search(5, [(0, "a")]):
            self.assertEquals(w[0], "azure")
        rs = self.wordlist.search(5, [(0, "r")])
        rss = [w for w, x in rs]
        self.assertEquals("reach" in rss, True)
        self.assertEquals("roast" in rss, True)
        for w in self.wordlist.search(5, [(0, "o")]):
            self.assertEquals(w[0], "oasis")
        for w in self.wordlist.search(5, [(0, "t")]):
            self.assertEquals(w[0], "trunk")
        
        # all first characters
        css = [(0, 5, [(0, c)]) for c in "parrot"]
        for w in self.wordlist.search(self.length2, [], css):
            self.assertEquals(w[0], self.word2)
        
        # diagonal
        self.wordlist.add_word("cabin")
        self.wordlist.add_word("cargo")
        self.wordlist.add_word("beard")
        self.wordlist.add_word("amino")
        self.wordlist.add_word("adrift")
        
        css = [(i, 5, [(i, self.word2[i])]) for i in xrange(5)] + [(5, 6, [(5, "t")])]
        for i, w in enumerate(self.wordlist.search(self.length2, [], css)):
            if i ==  0:
                self.assertEquals(w[0], self.word2)
                
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
        
        clist.postprocess()
        
    def testEmpty(self):
        clist = CWordList([])
        self.assertEquals(len([w for w in clist.search(4, [], None)]), 0)
        css = [(0, 4, []), (0, 5, []), (0, 6, []), (0, 7, [])]
        self.assertEquals(len([w for w in clist.search(4, [], css)]), 0)
        clist.postprocess()
        
    def testScale(self):
        clist = CWordList(read_wordlist('/usr/share/dict/words'))
        total4 = len(clist.search(4, [], None))
        totals = {}
        for c in string.ascii_lowercase:
            totals[c] = len(clist.search(4, [(0, c)], None))
        self.assertEquals(total4, sum(totals.values()))
        clist.postprocess()
