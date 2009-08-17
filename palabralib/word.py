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

class WordList:
    def __init__(self):
        self.lengths = {}
        
    def add_word(self, word):
        try:
            self.lengths[len(word)].append(word)
        except KeyError:
            self.lengths[len(word)] = [word]
    
    def search(self, length, constraints):
        def predicate(word):
            for position, letter in constraints:
                if not word[position] == letter:
                    return False
            return True
        return filter(predicate, self.lengths[length])

def read_wordlist(filename):
    f = open(filename, "r")
    result = []
    for line in f:
        line = line.strip("\n")
        if len(line) == 0:
            continue
        for c in line:
            if not (65 <= ord(c) <= 90 or 97 <= ord(c) <= 122):
                break
        else:
            result.append(line)
    return result

def create_predicate(constraints):
    def predicate(word):
        for c in constraints:
            if not c(word):
                return False
        return True
    return predicate

def initialize_wordlists():
    words = read_wordlist("/usr/share/dict/words")
    wl = WordList()
    for w in words:
        wl.add_word(w.lower())
    return [wl]

wordlists = initialize_wordlists()
        
def search_wordlists(length, constraints):
    result = []
    for wl in wordlists:
        result += wl.search(length, constraints)
    print result
    return result
