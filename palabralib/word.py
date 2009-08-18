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

import gobject
from threading import Thread
import time

class WordList:
    def __init__(self):
        self.lengths = {}
        #self.combinations = {}
        
    def add_word(self, word):
        try:
            self.lengths[len(word)].append(word)
        except KeyError:
            self.lengths[len(word)] = [word]
        #if len(word) not in self.combinations:
        #    self.combinations[len(word)] = {}
        #decompose = [(i, c) for i, c in enumerate(word)]
        #for j in xrange(len(word)):
        #    i, c = decompose[j]
        #    s = decompose[:j] + decompose[j + 1:]
        #    if i not in self.combinations[len(word)]:
        #        self.combinations[len(word)][i] = []
        #    if c not in self.combinations[len(word)][i]:
        #        self.combinations[len(word)][i].append(c)
            
    def has_matches(self, length, constraints):
        #if length not in self.combinations:
        #    return False
        #for i, c in constraints:
        #    if c not in self.combinations[length][i]:
        #        return False
        #return True
        if length not in self.lengths:
            return False
        for word in self.lengths[length]:
            if False not in [word[i] == c for i, c in constraints]:
                return True
        return False
    
    def search(self, length, constraints, more_constraints=None):
        if length not in self.lengths:
            return []
        result = []
        for word in self.lengths[length]:
            if self._predicate(constraints, word):
                if more_constraints is not None:
                    filled_constraints = []
                    for j, (i, l, cs) in enumerate(more_constraints):
                        filled_constraints.append((l, cs + [(i, word[j])]))
                    checks = [self.has_matches(l, cs) for l, cs in filled_constraints]
                    if False not in checks:
                        result.append(word)
                else:
                    result.append(word)
        return result
        
    @staticmethod
    def _predicate(constraints, word):
        for position, letter in constraints:
            if not word[position] == letter:
                return False
        return True

def read_wordlist(filename):
    f = open(filename, "r")
    result = []
    for line in f:
        line = line.strip("\n")
        if len(line) == 0:
            continue
        for c in line:
            if not (ord("A") <= ord(c) <= ord("Z") or ord("a") <= ord(c) <= ord("z")):
                break
        else:
            result.append(line)
    return result

class WordListThread(Thread):
    def __init__(self, window):
        Thread.__init__(self)
        self.window = window

    def run(self):
        def callback(wordlists):
            self.window.wordlists = wordlists
            try:
                self.window.editor.refresh_words(True)
            except AttributeError:
                pass
        
        files = ["/usr/share/dict/words"]
        wordlists = []
        for f in files:
            words = read_wordlist(f)
            wordlist = WordList()
            for word in words:
                wordlist.add_word(word.lower())
            wordlists.append(wordlist)
        gobject.idle_add(callback, wordlists)

def search_wordlists(wordlists, length, constraints, more_constraints=None):
    result = []
    for wl in wordlists:
        result += wl.search(length, constraints, more_constraints)
    result.sort()
    return result
