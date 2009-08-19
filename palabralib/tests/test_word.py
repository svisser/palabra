# This file is part of Palabra
#
# Copyright (C) 2009 Simeon Visser
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
from palabralib.word import WordList

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
        self.assertEquals(self.wordlist.search(self.length, []), [self.word])
        self.assertEquals(self.wordlist.search(self.length, self.constraints), [self.word])
        
        cs = [(0, "p"), (1, "a")]
        self.wordlist.add_word(self.word2)
        self.assertEquals(self.wordlist.search(self.length, cs), [self.word])
        self.assertEquals(self.wordlist.search(self.length2, cs), [self.word2])
        
    def testSearchMore(self):
        self.wordlist.add_word(self.word)
        self.wordlist.add_word(self.word2)
        self.wordlist.add_word("peach")
        self.wordlist.add_word("azure")
        self.wordlist.add_word("roast")
        self.wordlist.add_word("reach")
        self.wordlist.add_word("oasis")
        self.wordlist.add_word("trunk")
        
        self.assertEquals(self.wordlist.search(5, [(0, "p")]), ["peach"])
        self.assertEquals(self.wordlist.search(5, [(0, "a")]), ["azure"])
        rs = self.wordlist.search(5, [(0, "r")])
        self.assertEquals("reach" in rs, True)
        self.assertEquals("roast" in rs, True)
        self.assertEquals(self.wordlist.search(5, [(0, "o")]), ["oasis"])
        self.assertEquals(self.wordlist.search(5, [(0, "t")]), ["trunk"])
        
        # all first characters
        css = [(0, 5, [(0, c)]) for c in "parrot"]
        self.assertEquals(self.wordlist.search(self.length2, [], css), [self.word2])
        
        # diagonal
        self.wordlist.add_word("cabin")
        self.wordlist.add_word("cargo")
        self.wordlist.add_word("beard")
        self.wordlist.add_word("amino")
        self.wordlist.add_word("adrift")
        
        css = [(i, 5, [(i, self.word2[i])]) for i in xrange(5)] + [(5, 6, [(5, "t")])]
        self.assertEquals(self.wordlist.search(self.length2, [], css), [self.word2])
