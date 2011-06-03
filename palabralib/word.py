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

def visible_entries(words, grid, show_used=True, show_intersect=False, show_order=0):
    """
    Compute all words that should be shown in main word component
    next to puzzle, given the specified settings.
    """
    entries = []
    if not show_used:
        entries = [e.lower() for e in grid.entries() if constants.MISSING_CHAR not in e]
    shown = [row for row in words if 
        not ( (show_intersect and not row[2]) or (not show_used and row[0] in entries) ) ]
    if show_order == 1: # sort by score
        shown.sort(key=itemgetter(1), reverse=True)
    return shown

def accidental_entries(results, collapse=False, palindrome=False):
    """
    Yield all entries that should be displayed
    in the accidental words dialog.
    """
    if palindrome:
        slots = [cells for d, cells in results]
        use = []
        for i, (d, cells) in enumerate(results):
            if cells in slots:
                # s[::-1] = reverse sequence
                use.append((i, d, cells))
                r_cells = cells[::-1]
                palindrome = [c for x, y, c in cells] == [c for x, y, c in r_cells]
                if r_cells in slots and palindrome:
                    slots.remove(r_cells)
    else:
        use = [(i, d, r) for i, (d, r) in enumerate(results)]
    show = [(str(i), ''.join([c for x, y, c in r])) for i, d, r in use]
    show.sort(key=itemgetter(1))
    if collapse:
        ws = {}
        for index, s in show:
            if s not in ws:
                ws[s] = [index]
            else:
                ws[s].append(index)
        for index, s in show:
            if s not in ws:
                continue
            indices = ws[s]
            yield s, len(indices), ','.join(indices)
            del ws[s]
    else:
        for index, s in show:
            yield s, 1, index

def similar_entries(results):
    """
    Determine all entries that should be displayed
    in overview of similar words.
    """
    result = {}
    for s, words in results.items():
        if constants.MISSING_CHAR in s or len(words) == 1:
            continue
        result[s] = [(x, y, d, word.lower(), word.find(s)) for x, y, d, word in words]
    return result

def read_wordlist(path, default_score):
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
                word, score = line[0], default_score
            elif l_line == 2:
                word, score = line
            word = word.replace(" ", '')
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
                try:
                    words.add((lower(word), int(score)))
                except ValueError:
                    pass
    return words
    
def check_accidental_words(wordlists, grid):
    """
    Given a grid, check it for accidental occurences of words in
    the given wordlists.
    """
    accidentals = []
    slots = grid.generate_all_slots()
    for d, s in slots:
        l_s = len(s)
        for offset, length in check_accidental_word(wordlists, s):
            if (offset, length) == (0, l_s) and d in ["across", "down"]:
                continue
            accidentals.append((d, s[offset:offset + length]))
    return accidentals

def seq_to_cells(seq):
    """
    Given a list of (x, y, c) tuples, return all uninterrupted
    sequences of cells of length 2+. A sequence is interrupted
    if c == constants.MISSING_CHAR.
    """
    seqs = [(c if c[2] != constants.MISSING_CHAR else None) for c in seq]
    if False not in [(i is None) for i in seqs]:
        return []
    p = []
    p_r = []
    for i, item in enumerate(seqs):
        if item is None:
            p.append((i - len(p_r), p_r))
            p_r = []
        else:
            p_r.append(item)
    if p_r:
        p.append((len(seqs) - len(p_r), p_r))
    return [i for i in p if len(i[1]) >= 2]
        
def check_accidental_word(wordlists, seq):
    """
    Given a list of (x, y, c) tuples, check it for occurrences of words
    in the wordlists. This function returns (offset, length) pairs relative
    to the given sequence.
    """
    result = []
    for offset, s in seq_to_cells(seq):
        st = ''.join([c for x, y, c in s])
        r = check_str_for_words(wordlists, offset, st.lower())
        if r:
            result.extend(r)
    return result
    
def check_str_for_words(wordlists, offset, s):
    """
    Given a string s, returns pairs of (offset, length) of words that
    occur in the given wordlists. The given offset is the offset of
    string s in the original sequence.
    """
    l = len(s)
    return [(offset + i, j - i) for i in xrange(l) for j in xrange(i + 1, l + 1)
        if search_wordlists(wordlists, j - i, s[i:j], sort=False)]

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

def similar_words(grid, min_length=3):
    """
    Compute all substrings of at least min_length characters
    and the words in which they can be found.
    """
    lengths = {}
    words = []
    for n, x, y, d in grid.words(allow_duplicates=True, include_dir=True):
        word = grid.gather_word(x, y, d)
        words.append((x, y, d, word, len(word)))
    substrings = {}
    for x, y, d, word, l_word in words:
        for l in xrange(min_length, l_word):
            for o in xrange(0, l_word - min_length + 1):
                subs = word[o:o + l]
                if subs not in substrings:
                    substrings[subs] = []
    for s in substrings.keys():
        for x, y, d, word, l_word in words:
            if s in word:
                substrings[s].append((x, y, d, word))
    return substrings
    
def create_wordlists(prefs, previous=None):
    """
    Convert preference data of word files into CWordLists.
    """
    files = []
    for i, data in enumerate(prefs):
        if i >= constants.MAX_WORD_LISTS:
            break
        files.append((i, data["path"]["value"], data["name"]["value"]))
    if previous is not None:
        indices = [clist.index for clist in previous]
        free_indices = [i for i in xrange(constants.MAX_WORD_LISTS) if i not in indices]
        wordlists = []
        f = 0
        for data in prefs:
            for clist in previous:
                if data["path"]["value"] == clist.path:
                    wordlists.append(clist)
                    break
            else:
                index = free_indices[f]
                f += 1
                path = data["path"]["value"]
                name = data["name"]["value"]
                wordlists.append(CWordList(path, index=index, name=name))
        return wordlists
    return [CWordList(path, index=i, name=name) for i, path, name in files]

def remove_wordlist(prefs, wordlists, path):
    n_prefs = [p for p in prefs if p["path"]["value"] != path]
    n_wordlists = [wlist for wlist in wordlists if wlist.path != path]
    return n_prefs, n_wordlists
    
def rename_wordlists(prefs, wordlists, path, name):
    """
    Rename the word list with the given path to the given name
    in the preferences and wordlists.
    """
    for p in prefs:
        if p["path"]["value"] == path:
            p["name"]["value"] = name
            break
    for wlist in wordlists:
        for p in prefs:
            if wlist.path == p["path"]["value"]:
                wlist.name = p["name"]["value"]

def search_wordlists(wordlists, length, constraints, more=None, sort=True, options=None):
    """
    Search the specified wordlists for words that match
    the constraints and the given length.
    
    This function returns a list with tuples, (str, score, bool).
    The first value is the word, the third value is whether all
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
    def cs_to_str(l, cs):
        result = ['.' for i in xrange(l)]
        for (i, c) in cs:
            result[i] = c
        return ''.join(result)
    def css_to_strs(css=None):
        return None if css is None else [(i, cs_to_str(l, cs)) for (i, l, cs) in css]
    if isinstance(constraints, list):
        constraints = cs_to_str(length, constraints)
    if more is not None and isinstance(more, list):
        more = css_to_strs(more)
    indices = [wlist.index for wlist in wordlists]
    result = cPalabra.search(length, constraints, more, indices, options)
    if sort and len(indices) > 1:
        result.sort(key=itemgetter(0))
    return result
    
def search_wordlists_by_pattern(wordlists, pattern, sort=None):
    """
    Give all (descr, word) pairs of words in wordlists that match the
    pattern. descr is either the name of the wordlist or its path.
    """
    result = []
    for wlist in wordlists:
        name = wlist.name if wlist.name is not None else wlist.path
        result.extend([(name, w, score) for w, score in wlist.find_by_pattern(pattern)])
    if sort is not None:
        if sort == 0: # alphabet
            result.sort(key=itemgetter(1))
        elif sort == 1: # length
            result.sort(key=lambda r: len(r[1]))
        elif sort == 2: # score
            result.sort(key=itemgetter(2), reverse=True)
    return result
    
def analyze_words(grid, g_words, g_cs, g_lengths, words):
    cs = {}
    for n, x, y, d in g_words:
        cs[x, y, d] = grid.gather_all_constraints(x, y, d, g_cs, g_lengths)
    counts = cPalabra.compute_counts(words)
    for l in words:
        for i in xrange(l):
            counts[l][i] = sorted(counts[l][i].items(), key=itemgetter(1), reverse=True)
            #if counts[l][i]:
            #    print l, i, counts[l][i]
    result = {}
    for n, x, y, d in g_words:
        data = cPalabra.compute_distances([w for w, score in words[g_lengths[x, y, d]]], cs, counts, (x, y, d))
        result[x, y, d] = [t[0] for t in sorted(data, key=itemgetter(1))]
        #print x, y, d, result[x, y, d], data
    return result
    
def write_wordlists(wlists):
    """Write the given word lists to a file. Return errors if they occur."""
    fail = []
    for wlist in wlists:
        try:
            wlist.write_to_file()
        except IOError as e:
            fail.append((wlist.name, e.strerror))
    return fail

class CWordList:
    def __init__(self, content, index=0, name=None, score=0):
        """Accepts either a filepath or a list of words, possibly with ranks."""
        if isinstance(content, str):
            words = list(read_wordlist(content, score))
            self.path = content
        else:
            self.path = None
            words = [(w if isinstance(w, tuple) else (w, score)) for w in content]
            # for now, concat compound words
            words = [(w.replace(" ", ''), score) for w, score in words]
            # reject all non-alphabet chars
            ord_A = ord("A")
            ord_Z = ord("Z")
            ord_a = ord("a")
            ord_z = ord("z")
            def is_ok(w):
                for c in w:
                    ord_c = ord(c)
                    if not (ord_A <= ord_c <= ord_Z
                        or ord_a <= ord_c <= ord_z):
                        return False
                return True
            words = [item for item in words if is_ok(item[0])]
        self.words = cPalabra.preprocess(words, index)
        # keys of self.words = lengths
        # values = list of words of that length with (word, score)
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
            result.extend([item for item in words if prog.match(item[0])])
        return result
        
    def search(self, length, constraints, more=None, options=None):
        """
        Search for words that match the given criteria.
        """
        return search_wordlists([self], length, constraints, more, options)
        
    def update_score(self, word, new_score):
        """Update the first occurrence of word with the new score."""
        l_word = len(word)
        for w, score in self.words[l_word]:
            if w == word:
                item = (w, score)
                break
        index = self.words[l_word].index(item)
        self.words[l_word][index] = (word, new_score)
        cPalabra.update_score(word, len(word), new_score, self.index)
        
    def write_to_file(self):
        """Write the contents of this word list to a file."""
        with open(self.path, 'w') as f:
            text = []
            for l in sorted(self.words.keys()):
                text.extend([w + "," + str(score) + "\n" for w, score in self.words[l]])
            f.write(''.join(text))
            
    def count_words(self):
        """Return the number of words in this word list."""
        return sum([len(self.words[i]) for i in self.words.keys()])
        
    def get_word_counts(self):
        """Return the number of words in this word list by length."""
        return dict([(k, len(ws)) for k, ws in self.words.items()])
    
    def get_score_counts(self):
        """Return the number of words in this word list by score."""
        scores = {}
        for k, k_words in self.words.items():
            for w, s in k_words:
                if s in scores:
                    scores[s] += 1
                else:
                    scores[s] = 1
        return scores
        
    def average_word_length(self):
        """Return the average length of a word in this word list."""
        counts = self.get_word_counts()
        n_words = self.count_words()
        if n_words == 0:
            return 0
        total = 0.0
        for l in self.words.keys():
            total += (l * counts[l])
        return total / n_words
        
    def average_word_score(self):
        """Return the average score of a word in this word list."""
        scores = self.get_score_counts()
        n_words = self.count_words()
        if n_words == 0:
            return 0
        total = 0.0
        for s, count in scores.items():
            total += (s * count)
        return total / n_words
        
    def add_word(self, word, score):
        """Add a word to the word list."""
        key = len(word)
        self.words[key].append((word, score))
        cPalabra.insert_word(self.index, len(word), word, score)
    
    def remove_words(self, words):
        """
        Remove a list of words from the word list.
        This method removes the words and rebuilds the word list.
        """
        rebuild = False
        for item in words:
            key = len(item[0])
            if item in self.words[key]:
                self.words[key].remove(item)
                rebuild = True
        if rebuild:
            new_words = []
            for l in self.words.keys():
                new_words.extend(self.words[l])
            self.words = cPalabra.preprocess(new_words, self.index)
