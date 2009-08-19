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
        self.combinations = {}
        self.size = 0
        
    def add_word(self, word):
        try:
            self.lengths[len(word)].append(word)
        except KeyError:
            self.lengths[len(word)] = [word]
        if len(word) not in self.combinations:
            self.combinations[len(word)] = {}
        for x in xrange(len(word)):
            if x not in self.combinations[len(word)]:
                self.combinations[len(word)][x] = {}
        for i, c in enumerate(word):
            try:
                self.combinations[len(word)][i][c].append(self.size)
            except KeyError:
                self.combinations[len(word)][i][c] = [self.size]
        self.size += 1
            
    def has_matches(self, length, constraints):
        if length not in self.lengths:
            return False
        result = None
        for i, c in constraints:
            if i not in self.combinations[length]:
                return False
            if c not in self.combinations[length][i]:
                return False
            query = self.combinations[length][i][c]
            if len(query) == 0:
                return False
            if result is None:
                result = query
                continue
            else:
                reduced = filter(lambda j: j in result, query)
                if len(reduced) == 0:
                    return False
                result = reduced
        return True
    
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
                    
                    for l, cs in filled_constraints:
                        if not self.has_matches(l, cs):
                            break
                    else:
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
