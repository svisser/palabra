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

import copy
import glib
import gtk
import os
import re
import time
from operator import itemgetter

import cPalabra
import constants
import preferences
from preferences import prefs_to_word_files

def extract(counts, s):
    chars = []
    s_counts = {}
    for c in s:
        if c not in s_counts:
            s_counts[c] = 1
        else:
            s_counts[c] += 1
        if c not in counts or s_counts[c] > counts[c]:
            chars.append(c)
    return s, chars

def read_wordlist(path):
    """Yield all words found in the specified file."""
    if not os.path.exists(path):
        return []
    words = set()
    with open(path, "r") as f:
        ord_A = ord("A")
        ord_Z = ord("Z")
        ord_a = ord("a")
        ord_z = ord("z")
        ords = {}
        lower = str.lower
        for line in f:
            line = line.strip("\n")
            line = line.split(",")
            l_line = len(line)
            if not line or l_line > 2:
                continue
            if l_line == 1:
                word = line[0]
            elif l_line == 2:
                word, r = line
            word = word.strip()
            if " " in word:
                continue # for now, reject compound
            if len(word) > constants.MAX_WORD_LENGTH:
                continue    
            for c in word:
                if c not in ords:
                    ord_c = ords[c] = ord(c)
                else:
                    ord_c = ords[c]                
                if not (ord_A <= ord_c <= ord_Z
                    or ord_a <= ord_c <= ord_z):
                    break
            else:
                words.add(lower(word))
    return words
    
def check_accidental_words(grid):
    accidentals = []
    slots = grid.generate_all_slots()
    for s in slots:
        for offset, length in check_accidental_word(s):
            accidentals.append(s[offset:offset + length])
    return accidentals
        
def check_accidental_word(seq):
    # return (offset, length) pairs
    seqs = [(c if c[2] != constants.MISSING_CHAR else None) for c in seq]
    if False not in [(i is None) for i in seqs]:
        return []
    p = []
    p_r = []
    for item in seqs:
        if item is None:
            p.append(p_r)
            p_r = []
        else:
            p_r.append(item)
    if p_r:
        p.append(p_r)
    check = [i for i in p if len(i) >= 2]
    result = []
    for s in check:
        r = _check_seq_for_words(s)
        if r is not None:
            result.append(r)
    return result
    
def _check_seq_for_words(seq):
    print seq
    return None

def produce_word_counts(word):
    counts = {}
    for i, c in enumerate(word):
        if c not in counts:
            counts[c] = 1
        else:
            counts[c] += 1
    return counts
    
def get_contained_words(wordlists, word):
    """
    Produce all words w, where len(w) > len(word), such that
    all characters of word are found in w.
    """
    c_items = produce_word_counts(word).items()
    result = []
    for p, wlist in wordlists.items():
        for l in xrange(len(word) + 1, constants.MAX_WORD_LENGTH):
            result.extend(cPalabra.get_contained_words(wlist.index, l, c_items, len(c_items)))
    return c_items, result
    
def verify_contained_words(wordlists, pairs):
    """
    Given pairs (a, b), produce all pairs such that all
    characters of b are found in a word of a wordlist.
    """
    result = []
    for p, wlist in wordlists.items():
        result.extend(cPalabra.verify_contained_words(wlist.index, pairs))
    return result

def create_wordlists(data):
    """
    Convert preference data of word files into CWordLists.
    """
    files = prefs_to_word_files(data)
    return [CWordList(path, index=i, name=name) for i, path, name in files]

def cs_to_str(l, cs):
    result = ['.' for i in xrange(l)]
    for (i, c) in cs:
        result[i] = c
    return ''.join(result)

def css_to_strs(css=None):
    return None if css is None else [(i, cs_to_str(l, cs)) for (i, l, cs) in css]

def search_wordlists(wordlists, length, constraints, more=None):
    indices = [item.index for item in wordlists]
    result = cPalabra.search(length
        , cs_to_str(length, constraints)
        , css_to_strs(more), indices)
    if len(indices) > 1:
        result.sort()
    return result
    
def analyze_words(grid, g_words, g_cs, g_lengths, words):
    cs = {}
    for n, x, y, d in g_words:
        cs[x, y, d] = grid.gather_all_constraints(x, y, d, g_cs, g_lengths)
    counts = cPalabra.compute_counts(words)
    for l in words:
        for i in xrange(l):
            counts[l][i] = sorted(counts[l][i].items(), key=itemgetter(1), reverse=True)
    result = {}
    for n, x, y, d in g_words:
        data = cPalabra.compute_distances(words[g_lengths[x, y, d]], cs, counts, (x, y, d))
        result[x, y, d] = [t[0] for t in sorted(data, key=itemgetter(1))]
    return result

class CWordList:
    def __init__(self, content, index=0, name=None):
        """Accepts either a filepath or a list of words, possibly with ranks."""
        if isinstance(content, str):
            words = [(w, 0) for w in list(read_wordlist(content))]
            self.path = content
        else:
            self.path = None
            words = [(w if isinstance(w, tuple) else (w, 0)) for w in content]
            # for now, reject compound
            words = [item for item in words if " " not in item[0]]
        self.words = cPalabra.preprocess(words, index)
        self.index = index
        self.name = name
        
    def find_by_pattern(self, pattern):
        """
        Find all words that match the specified pattern.
        ? = one character
        * = zero or more characters
        """
        ord_a, ord_z = ord("a"), ord("z")
        pattern = pattern.lower()
        pattern = ''.join([c for c in pattern if ord_a <= ord(c) <= ord_z or c in ['*', '?']])
        pattern = pattern.replace("?", ".")
        pattern = pattern.replace("*", ".*")
        prog = re.compile(pattern + "$")
        result = []
        for l, words in self.words.items():
            result.extend([w for w in words if prog.match(w)])
        return result
        
    def search(self, length, constraints, more=None):
        """
        Search for words that match the given criteria.
        
        This function returns a list with tuples, (str, bool).
        The first value is the word, the second value is whether all
        positions of the word have a matching word, when the
        more_constraints (more) argument is specified.
        If more is not specified, the second value
        in a tuple is True.
        
        If more is specified, then constraints must be
        specified for ALL intersecting words.
        
        constraints and more must match with each other
        (i.e., if intersecting word at position 0 starts with 'a' then
        main word must also have a constraint 'a' at position 0).
        
        Words are returned in alphabetical order.
        """
        return cPalabra.search(length
            , cs_to_str(length, constraints)
            , css_to_strs(more), [self.index])
