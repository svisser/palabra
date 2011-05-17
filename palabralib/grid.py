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

import cPalabra
import constants

def decompose_word(word, x, y, direction):
    """Decompose the word starting at (x, y) in the given direction into tuples."""
    if direction == "across":
        return [(x + i, y, word[i]) for i in xrange(len(word))]
    elif direction == "down":
        return [(x, y + j, word[j]) for j in xrange(len(word))]

def determine_scrabble_score(grid):
    """Compute the sum of each character's score in Scrabble."""
    # http://en.wikipedia.org/wiki/Scrabble_letter_distributions#English
    scores = {'A': 1, 'B': 3, 'C': 3, 'D': 2, 'E': 1, 'F': 4, 'G': 2
        , 'H': 4, 'I': 1, 'J': 8, 'K': 5, 'L': 1, 'M': 3, 'N': 1
        , 'O': 1, 'P': 3, 'Q': 10, 'R': 1, 'S': 1, 'T': 1, 'U': 1
        , 'V': 4, 'W': 4, 'X': 8, 'Y': 4, 'Z': 10, '': 0}
    chars = [grid.get_char(x, y) for x, y in grid.cells()]
    return sum([scores[c] for c in chars])

class Grid:
    def __init__(self, width, height, initialize=True, number_mode=constants.NUMBERING_AUTO):
        """Construct a grid with the given dimensions."""
        self.initialize(width, height, initialize, number_mode)
        
    def initialize(self, width, height, initialize=True, number_mode=constants.NUMBERING_AUTO):
        """Reset the grid to the given dimensions with all empty cells."""
        self.width = width
        self.height = height
        self.lines = None
        self.data = [[self._default_cell() for x in xrange(width)] for y in xrange(height)]
        self.number_mode = number_mode
        if initialize and number_mode == constants.NUMBERING_AUTO:
            self.assign_numbers()
        
    def _default_cell(self):
        return {
            "bar": {"top": False, "left": False}
            , "block": False
            , "char": ""
            , "clues": {}
            , "number": 0
            , "void": False
            , "rebus": None
        }
        
    def __eq__(self, other):
        if other is None:
            return False
        if self.size != other.size:
            return False
        for x, y in self.cells():
            if self.cell(x, y) != other.cell(x, y):
                return False
        return True
        
    def __ne__(self, other):
        return not self.__eq__(other)
        
    def __str__(self):
        s = []
        for y in xrange(self.height):
            for x in xrange(self.width):
                if self.data[y][x]["block"]:
                    s.append('.')
                elif self.data[y][x]["void"]:
                    s.append('~')
                else:
                    c = self.data[y][x]["char"]
                    s.append(c if c else ' ')
            s.append('\n')
        return ''.join(s)
        
    def assign_numbers(self):
        """Assign word numbers to cells as they are commonly numbered."""
        cPalabra.assign_numbers(self)
            
    def is_start_word(self, x, y, direction=None):
        """Return True when a word begins in the cell (x, y)."""
        width, height, data = self.width, self.height, self.data
        if not (0 <= x < width and 0 <= y < height):
            return False
        if data[y][x]["block"] or data[y][x]["void"]:
            return False
        for d in ([direction] if direction else ["across", "down"]):
            if d == "across":
                bdx, bdy, adx, ady, bar_side = -1, 0, 1, 0, "left"
            elif d == "down":
                bdx, bdy, adx, ady, bar_side = 0, -1, 0, 1, "top"
            is_available_xbdx_ybdy = ((0 <= x + bdx < width and 0 <= y + bdy < height)
                and not data[y + bdy][x + bdx]["block"] and not data[y + bdy][x + bdx]["void"])
            before = not is_available_xbdx_ybdy or data[y][x]["bar"][bar_side]
            if not before:
                continue
            is_available_xadx_yady = ((0 <= x + adx < width and 0 <= y + ady < height)
                and not data[y + ady][x + adx]["block"] and not data[y + ady][x + adx]["void"])
            after = is_available_xadx_yady and not data[y + ady][x + adx]["bar"][bar_side]
            if after:
                return True
        return False
        
    def get_start_word(self, x, y, direction):
        """Return the first cell of a word in the given direction that contains the cell (x, y)."""
        data = self.data
        width = self.width
        height = self.height
        if (not (0 <= x < width and 0 <= y < height)
            or data[y][x]["block"]
            or data[y][x]["void"]):
            return x, y
        dx = -1 if direction == "across" else 0
        dy = -1 if direction == "down" else 0
        while True:
            if dx < 0 and (x + dx < 0 or data[y][x]["bar"]["left"]):
                break
            if dy < 0 and (y + dy < 0 or data[y][x]["bar"]["top"]):
                break
            if data[y + dy][x + dx]["block"]:
                break
            if data[y + dy][x + dx]["void"]:
                break
            x += dx
            y += dy
        return (x, y)
            
    def get_end_word(self, x, y, direction):
        """Return the last cell of a word in the given direction that contains the cell (x, y)."""
        if not self.is_available(x, y):
            return x, y
        return [(x, y) for x, y in self.in_direction(x, y, direction)][-1]
        
    def get_check_count_all(self):
        """Return the check count for all cells."""
        data = self.data
        width = self.width
        height = self.height
        counts = {}
        hor_counts = {}
        ver_counts = {}
        for y in xrange(height):
            length = 0
            for x in xrange(width):
                if not data[y][x]["block"] and not data[y][x]["void"]:
                    length += 1
                if length >= 2:
                    hor_counts[x - 1, y] = 1
                if data[y][x]["block"] or data[y][x]["void"]:
                    length = 0
            if length >= 2:
                hor_counts[x, y] = 1
        for x in xrange(width):
            length = 0
            for y in xrange(height):
                if not data[y][x]["block"] and not data[y][x]["void"]:
                    length += 1
                if length >= 2:
                    ver_counts[x, y - 1] = 1
                if data[y][x]["block"] or data[y][x]["void"]:
                    length = 0
            if length >= 2:
                ver_counts[x, y] = 1
        for y in xrange(height):
            for x in xrange(width):
                if data[y][x]["block"] or data[y][x]["void"]:
                    counts[x, y] = -1
                    continue
                counts[x, y] = 0
                if (x, y) in hor_counts:
                    counts[x, y] += 1
                if (x, y) in ver_counts:
                    counts[x, y] += 1
        return counts
        
    def get_check_count(self, x, y):
        """
        Return the number of words that contain the cell (x, y).
        
        Return values:
        -1 : A block or void
        0 : An isolated cell: no words contain this cell
        1 : One word contains this cell
        2 : Two words contain this cell
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return -1
        if self.data[y][x]["block"] or self.data[y][x]["void"]:
            return -1
        count = 0
        for d in ["across", "down"]:
            if self.is_part_of_word(x, y, d):
                count += 1
        return count
        
    def is_part_of_word(self, x, y, direction):
        """Return True if the specified (x, y, direction) is part of a word (2+ letters)."""
        data = self.data
        width = self.width
        height = self.height
        if not (0 <= x < width and 0 <= y < height):
            return False
        if data[y][x]["block"] or data[y][x]["void"]:
            return False
        if direction == "across":
            # before = self.is_available(x - 1, y) and not self.has_bar(x, y, "left")
            before = True
            if x - 1 < 0:
                before = False
            else:
                before = not (data[y][x - 1]["block"]
                or data[y][x - 1]["void"]
                or data[y][x]["bar"]["left"])
            if before:
                return True
            # after = self.is_available(x + 1, y) and not self.has_bar(x + 1, y, "left")
            after = True
            if x + 1 >= width:
                after = False
            else:
                after = not (data[y][x + 1]["block"]
                or data[y][x + 1]["void"]
                or data[y][x + 1]["bar"]["left"])
            return after
        elif direction == "down":
            # before = self.is_available(x, y - 1) and not self.has_bar(x, y, "top")
            before = True
            if y - 1 < 0:
                before = False
            else:
                before = not (data[y - 1][x]["block"]
                or data[y - 1][x]["void"]
                or data[y][x]["bar"]["top"])
            if before:
                return True
            # after = self.is_available(x, y + 1) and not self.has_bar(x, y + 1, "top")
            after = True
            if y + 1 >= height:
                after = False
            else:
                after = not (data[y + 1][x]["block"]
                or data[y + 1][x]["void"]
                or data[y + 1][x]["bar"]["top"])
            return after
        #return before or after
        
    def determine_status(self, full=False):
        """Return a dictionary with the grid's properties."""
        status = {}
        status["block_count"] = self.count_blocks()
        status["void_count"] = self.count_voids()
        status["char_count"] = self.count_chars(True)
        status["actual_char_count"] = self.count_chars(False)
        status["word_count"] = self.count_words()
        percentage = (float(status["block_count"]) / float(self.width * self.height)) * 100
        status["block_percentage"] = percentage
        if full:
            status["mean_word_length"] = self.mean_word_length()
            status["blank_count"] = status["char_count"] - status["actual_char_count"]
            status["word_counts"] = self.determine_word_counts()
            status["char_counts"] = {}
            for x, y in self.cells():
                c = self.data[y][x]["char"]
                if not c:
                    continue
                try:
                    status["char_counts"][c] += 1
                except KeyError:
                    status["char_counts"][c] = 1
            status["char_counts_total"] = []
            for c in string.ascii_uppercase:
                try:
                    count = status["char_counts"][c]
                except KeyError:
                    count = 0
                status["char_counts_total"].append((c, count))
            counts = self.get_check_count_all()
            status["checked_count"] = 0
            status["unchecked_count"] = 0
            status["clue_count"] = 0
            for x, y in self.cells():
                if 0 <= counts[x, y] <= 1:
                    status["unchecked_count"] += 1
                elif counts[x, y] == 2:
                    status["checked_count"] += 1
                status["clue_count"] += len(self.data[y][x]["clues"])
            status["open_count"] = len(self.compute_open_squares())
            status["connected"] = self.is_connected()
            status["complete_count"] = self.count_complete()
        return status
        
    def determine_word_counts(self):
        """Calculate the number of words by direction and by length."""
        status = {}
        def count_by_dir(direction):
            status[direction] = 0
            for n, x, y in self.words_by_direction(direction):
                status[direction] += 1
                length = self.word_length(x, y, direction)
                try:
                    status[length] += 1
                except KeyError:
                    status[length] = 1
        count_by_dir("across")
        count_by_dir("down")
                
        status["total"] = []
        for length in range(2, max(self.width, self.height) + 1):
            try:
                count = status[length]
            except KeyError:
                count = 0
            status["total"].append((length, count))
        return status
        
    def words_by_direction(self, direction):
        """Iterate over the words in the grid by direction."""
        height = self.height
        width = self.width
        is_start_word = self.is_start_word
        data = self.data
        for y in xrange(height):
            for x in xrange(width):
                if is_start_word(x, y, direction):
                    yield data[y][x]["number"], x, y
                    
    def clues(self, direction):
        """Iterate over the clues of the grid by direction."""
        data = self.data
        for n, x, y in self.words_by_direction(direction):
            try:
                yield n, x, y, data[y][x]["clues"][direction]
            except KeyError:
                yield n, x, y, {}
    
    def words(self, allow_duplicates=False, include_dir=False):
        """
        Iterate over the words of the grid.
        
        allow_duplicates: If True, cells that contain the start
        of two words are encountered twice when iterating. Otherwise,
        they are encountered only once.
        
        include_dir: If True, include the direction in the output.
        allow_duplicates must be True for this to work.
        """
        data = self.data
        is_start_word = self.is_start_word
        for x, y in self.cells():
            n = data[y][x]["number"]
            if allow_duplicates:
                for d in ["across", "down"]:
                    if is_start_word(x, y, d):
                        if include_dir:
                            yield n, x, y, d
                        else:
                            yield n, x, y
            elif is_start_word(x, y):
                yield n, x, y
    
    def entries(self):
        """Return all entries in alphabetical order."""
        entries = [item[4] for item in self.gather_words()]
        entries.sort()
        return entries
        
    def slot(self, x, y, direction):
        """
        Iterate over all cells of a slot that contains (x, y) in an unspecified order.
        """
        sx, sy = self.get_start_word(x, y, direction)
        for p, q in self.in_direction(sx, sy, direction):
            yield p, q
                    
    def cells(self):
        """Iterate over the cells of the grid in left-to-right, top-to-bottom order."""
        for y in xrange(self.height):
            for x in xrange(self.width):
                yield x, y
                
    def availables(self):
        """Convenience function for iterating over available cells."""
        for x, y in self.cells():
            if self.is_available(x, y):
                yield x, y
                
    def gather_word(self, x, y, direction, empty_char=constants.MISSING_CHAR):
        """Return the word starting at (x, y) in the given direction."""
        word = ""
        data = self.data
        for p, q in self.in_direction(x, y, direction):
            c = data[q][p]["char"]
            word += (empty_char if c == "" else c)
        return word
            
    def gather_constraints(self, x, y, direction):
        """Create a list of all chars by position of the specified word."""
        word = self.gather_word(x, y, direction, constants.MISSING_CHAR)
        return [(i, c.lower()) for i, c in enumerate(word) if c != constants.MISSING_CHAR]
    
    def gather_all_constraints(self, x, y, direction, g_cs=None, g_lengths=None):
        """
        Gather constraints of all intersecting words of the word at (x, y).
        
        This function returns a list with tuples that contain the
        letters and positions of intersecting words. The item at place i of
        the list corresponds to the intersecting word at position i.
        
        Each tuple contains the position at which the word at
        (x, y, direction) intersects the intersecting word, the length
        of the intersecting word and the constraints.
        """
        get_start_word = self.get_start_word
        word_length = self.word_length
        gather_constraints = self.gather_constraints
        result = []
        other = {"across": "down", "down": "across"}[direction]
        sx, sy = get_start_word(x, y, direction)
        for s, t in self.in_direction(sx, sy, direction):
            p, q = get_start_word(s, t, other)
            if g_lengths is not None and (p, q, other) in g_lengths:
                length = g_lengths[p, q, other]
            else:
                length = word_length(p, q, other)
            if other == "across":
                index = x - p
            elif other == "down":
                index = y - q
            if g_cs is not None and (p, q, other) in g_cs:
                cs = g_cs[p, q, other]
            else:
                cs = gather_constraints(p, q, other)
            result.append((index, length, cs))
        return result
                
    def gather_words(self, direction=None):
        """Iterate over the word data in the given direction."""
        words_by_direction = self.words_by_direction
        data = self.data
        gather_word = self.gather_word
        for d in ([direction] if direction else ["across", "down"]):
            for n, x, y in words_by_direction(d):
                clues = data[y][x]["clues"]
                try:
                    clue = clues[d]["text"]
                except KeyError:
                    clue = ""
                try:
                    explanation = clues[d]["explanation"]
                except KeyError:
                    explanation = ""
                word = gather_word(x, y, d)
                yield n, x, y, d, word, clue, explanation
        
    def word_length(self, x, y, direction):
        """Return the length of the word starting at (x, y) in the given direction."""
        dx = 1 if direction == "across" else 0
        dy = 1 if direction == "down" else 0
        count = 0
        data = self.data
        width = self.width
        height = self.height
        while True:
            if data[y][x]["block"] or data[y][x]["void"]:
                break
            count += 1
            if dx and (x + dx >= width or data[y][x + dx]["bar"]["left"]):
                break
            if dy and (y + dy >= height or data[y + dy][x]["bar"]["top"]):
                break
            x += dx
            y += dy
        return count
        
    def in_direction(self, x, y, direction, reverse=False):
        """Iterate in the given direction from (x, y) while cells are available."""
        dx = 1 if direction == "across" else 0
        dy = 1 if direction == "down" else 0
        if reverse:
            dx *= -1
            dy *= -1
        data = self.data
        width = self.width
        height = self.height
        while (0 <= x < width and 0 <= y < height
            and not data[y][x]["block"]
            and not data[y][x]["void"]):
            yield x, y
            if not (0 <= x + dx < width and 0 <= y < height):
                break
            if dx == 1 and data[y][x + dx]["bar"]["left"]:
                break
            if dx == -1 and data[y][x]["bar"]["left"]:
                break
            if not (0 <= x < width and 0 <= y + dy < height):
                break
            if dy == 1 and data[y + dy][x]["bar"]["top"]:
                break
            if dy == -1 and data[y][x]["bar"]["top"]:
                break
            x += dx
            y += dy
            
    def count_blocks(self):
        """Return the number of blocks in the grid."""
        total = 0
        for y in xrange(self.height):
            for x in xrange(self.width):
                if self.data[y][x]["block"]:
                    total += 1
        return total
        
    def neighbors(self, x, y, diagonals=False):
        """
        Iterate over all neighboring cells of a cell.
        
        If diagonals is True, the diagonal neighbors will be included as well.
        """
        width = self.width
        height = self.height
        if diagonals:
            neighbors = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1]]
            neighbors.remove((0, 0))
        else:
            neighbors = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        for dx, dy in neighbors:
            if 0 <= x + dx < width and 0 <= y + dy < height:
                yield x + dx, y + dy
        
    def compute_open_squares(self):
        """
        Return the open squares.
        
        A square is open if it does not touch a block, including diagonally.
        """
        data = self.data
        neighbors = self.neighbors
        cells = []
        for x, y in self.cells():
            if data[y][x]["block"] or data[y][x]["void"]:
                continue
            for p, q in neighbors(x, y, diagonals=True):
                if data[q][p]["block"]:
                    break
            else:
                cells.append((x, y))
        return cells
        
    def is_connected(self):
        """
        Return True when all character cells are connected with each
        other by going from cell to cell, using only horizontal and
        vertical steps.
        """
        avs = [(x, y) for x, y in self.availables()]
        if len(avs) == 0:
            return True
    
        done = []
        check = [avs[0]]
        while check:
            x, y = check.pop()
            done.append((x, y))
            for p, q in self.neighbors(x, y):
                if (p, q) in done or (p, q) in check:
                    continue
                if self.is_available(p, q):
                    check.append((p, q))
        return len(avs) == len(done)
        
    def count_voids(self):
        """Return the number of voids in the grid."""
        total = 0
        for y in xrange(self.height):
            for x in xrange(self.width):
                if self.data[y][x]["void"]:
                    total += 1
        return total
        
    def get_cell_of_slot(self, slot, target):
        if target == "start":
            return self.get_start_word(*slot)
        elif target == "end":
            return self.get_end_word(*slot)
        
    def count_words(self):
        """Return the number of words in the grid."""
        count = 0
        data = self.data
        width = self.width
        height = self.height
        for y in xrange(height):
            length = 0
            for x in xrange(width):
                if (data[y][x]["bar"]["left"] or
                    data[y][x]["block"] or
                    data[y][x]["void"]):
                    length = 0
                if not data[y][x]["block"] and not data[y][x]["void"]:
                    length += 1
                if length == 2:
                    count += 1
        for x in xrange(width):
            length = 0
            for y in xrange(height):
                if (data[y][x]["bar"]["top"] or
                    data[y][x]["block"] or
                    data[y][x]["void"]):
                    length = 0
                if not data[y][x]["block"] and not data[y][x]["void"]:
                    length += 1
                if length == 2:
                    count += 1
        return count
        
    def count_chars(self, include_blanks=True, _return_at_one=False):
        """Return the number of chars in the grid."""
        count = 0
        for y in xrange(self.height):
            for x in xrange(self.width):
                if (self.data[y][x]["block"] or self.data[y][x]["void"]):
                    continue
                if include_blanks or self.data[y][x]["char"] != '':
                    count += 1
                    if _return_at_one:
                        return count
        return count
        
    def has_chars(self):
        """Return True iff the grid has at least one character."""
        return self.count_chars(include_blanks=False, _return_at_one=True) == 1
            
    def mean_word_length(self):
        """Return the mean length of the words in the grid."""
        word_count = self.count_words()
        if word_count == 0:
            return 0
        char_counts = [self.get_check_count(x, y) for x, y in self.availables()]
        return float(sum(char_counts)) / float(word_count)
        
    def generate_diagonals(self, direction=0):
        """
        Generate all sequences of diagonal character cells of length 2+.
        
        Direction: 0 = north-east, 1 = south-east.
        """
        data = self.data
        width = self.width
        height = self.height
        if direction == 0:
            cs1 = [(0, y) for y in xrange(1, height)]
            cs2 = [(x, height - 1) for x in xrange(1, width - 1)]
            dx, dy = 1, -1
        elif direction == 1:
            cs1 = [(0, y) for y in xrange(height)]
            cs2 = [(x, 0) for x in xrange(1, width - 1)]
            dx, dy = 1, 1
        seqs = []
        for cx, cy in (cs1 + cs2):
            cells = []
            while (0 <= cx < width and 0 <= cy < height):
                if not data[cy][cx]["block"] and not data[cy][cx]["void"]:
                    cells.append((cx, cy))
                else:
                    cells.append(None)
                cx += dx
                cy += dy
            seqs.append(cells)
        result = []
        for s in seqs:
            sr = []
            t = []
            for e in s:
                if e is None:
                    sr.append(t)
                    t = []
                else:
                    t.append(e)
            if t:
                sr.append(t)
            result.extend([i for i in sr if len(i) >= 2])
        return result
        
    def generate_all_slots(self):
        """
        Generate all sequences of cells of length 2+ in the directions across,
        across (reverse), down, down (reverse), north-east, south-east,
        south-west and north-west.
        """
        data = self.data
        gather_word = self.gather_word
        slots = []
        for n, x, y, d in self.words(allow_duplicates=True, include_dir=True):
            l1 = decompose_word(gather_word(x, y, d), x, y, d)
            l2 = decompose_word(gather_word(x, y, d), x, y, d)
            l2.reverse()
            slots.append((d, l1))
            slots.append((d + "r", l2))
        opp = {"ne": "sw", "se": "nw"}
        for i, d in [(0, "ne"), (1, "se")]:
            seqs = self.generate_diagonals(i)
            for s in seqs:
                t1, t2 = [], []
                for x, y in s:
                    c = data[y][x]["char"]
                    if c == '':
                        c = constants.MISSING_CHAR
                    t1.append((x, y, c))
                    t2.append((x, y, c))
                t2.reverse()
                slots.append((d, t1))
                slots.append((opp[d], t2))
        return slots
            
    def resize(self, width, height, make_dirty=True):
        """
        Resize the grid to the given dimensions.
        
        Content of the grid within these boundaries will be preserved.
        Content of the grid outside these boundaries will be lost.
        """
        ndata = [[self._default_cell() for x in range(width)] for y in range(height)]
        
        if make_dirty:
            a = [(x, y, "across") for x, y in self.cells()
                if x >= min(width - 1, self.width - 1)]
            d = [(x, y, "down") for x, y in self.cells()
                if y >= min(height - 1, self.height - 1)]
            self._clear_clues(a + d)
        
        for x in range(width):
            for y in range(height):
                if self.is_valid(x, y):
                    ndata[y][x] = self.data[y][x]
                    
        self.data = ndata
        self.width = width
        self.height = height
        # invalidate lines
        self.lines = None
        
    def count_complete(self):
        r = {"across": 0, "down": 0}
        for n, x, y, d in self.words(allow_duplicates=True, include_dir=True):
            for p, q in self.in_direction(x, y, d):
                if self.data[q][p]["char"] == '':
                    break
            else:
                r[d] += 1
        return r
        
    def _clear_clues(self, dirty_cells):
        """Remove the clues of the words that contain a dirty cell."""
        for x, y, direction in dirty_cells:
            p, q = self.get_start_word(x, y, direction)
            try:
                del self.data[q][p]["clues"][direction]
            except KeyError:
                pass
                    
    def _clear_clues_related_to_cell(self, x, y):
        sx, sy = self.get_start_word(x, y, "across")
        tx, ty = self.get_start_word(x, y, "down")
        self._clear_clues([(sx, sy, "across"), (tx, ty, "down")])
        
    def insert_row(self, y, insert_above=True):
        """Insert a row above or below the row at vertical coordinate y."""
        dirty = [(x, y, "down") for x in xrange(self.width)]

        ny = y - 1 if insert_above else y + 1
        nots = [x for x in xrange(self.width) if not self.is_available(x, y)]
        dirty += [(x, ny, "down") for x in nots if self.is_valid(x, ny)]
        self._clear_clues(dirty)

        self.resize(self.width, self.height + 1, False)
        row = [[self._default_cell() for x in range(self.width)]]
        if insert_above:
            self.data = self.data[:y] + row + self.data[y:]
            for x in xrange(self.width):
                if self.has_bar(x, y + 1, "top"):
                    self.data[y + 1][x]["bar"]["top"] = False
                    self.data[y][x]["bar"]["top"] = True
        else:
            self.data = self.data[:y + 1] + row + self.data[y + 1:]
            
    def insert_column(self, x, insert_left=True):
        """Insert a column to the left or right of the horizontal coordinate x."""
        dirty = [(x, y, "across") for y in xrange(self.height)]
        
        nx = x - 1 if insert_left else x + 1
        nots = [y for y in xrange(self.height) if not self.is_available(x, y)]
        dirty += [(nx, y, "across") for y in nots if self.is_valid(nx, y)]
        self._clear_clues(dirty)
        
        self.resize(self.width + 1, self.height, False)
        if insert_left:
            f = lambda row: row[:x] + [self._default_cell()] + row[x:]
        else:
            f = lambda row: row[:x + 1] + [self._default_cell()] + row[x + 1:]
        self.data = map(f, self.data)
        if insert_left:
            for y in xrange(self.height):
                if self.has_bar(x + 1, y, "left"):
                    self.data[y][x + 1]["bar"]["left"] = False
                    self.data[y][x]["bar"]["left"] = True
            
    def remove_column(self, x):
        """Remove the column at horizontal coordinate x."""
        dirty = [(x, y, "across") for y in xrange(self.height)]
        nots = [y for y in xrange(self.height) if not self.is_available(x, y)]
        for p in [x - 1, x + 1]:
            dirty += [(p, y, "across") for y in nots if self.is_valid(p, y)]
        self._clear_clues(dirty)
        
        self.data = map(lambda row: row[:x] + row[x + 1:], self.data)
        self.width -= 1
            
    def remove_row(self, y):
        """Remove the row at vertical coordinate y."""
        dirty = [(x, y, "down") for x in xrange(self.width)]
        nots = [x for x in xrange(self.width) if not self.is_available(x, y)]
        for q in [y - 1, y + 1]:
            dirty += [(x, q, "down") for x in nots if self.is_valid(x, q)]
        self._clear_clues(dirty)
        
        self.data = self.data[:y] + self.data[y + 1:]
        self.height -= 1
        
    def shift_up(self):
        """
        Move the content of the grid up by one cell.
        
        The content of the top row will be lost.
        An empty row will be inserted at the bottom.
        """
        dirty = [(x, y, "down") for x in xrange(self.width) for y in [0, self.height - 1]]
        self._clear_clues(dirty)
        self.data = self.data[1:] + [[self._default_cell() for x in range(self.width)]]
        for x in xrange(self.width):
            self.data[0][x]["bar"]["top"] = False
        
    def shift_down(self):
        """
        Move the content of the grid down by one cell.
        
        The content of the bottom row will be lost.
        An empty row will be inserted at the top.
        """
        dirty = [(x, y, "down") for x in xrange(self.width) for y in [0, self.height - 1]]
        self._clear_clues(dirty)
        self.data = [[self._default_cell() for x in range(self.width)]] + self.data[:-1]
        
    def shift_left(self):
        """
        Move the content of the grid left by one cell.
        
        The content of the left column will be lost.
        An empty column will be inserted at the right.
        """
        dirty = [(x, y, "across") for y in xrange(self.height) for x in [0, self.width - 1]]
        self._clear_clues(dirty)
        self.data = map(lambda x: x[1:] + [self._default_cell()], self.data)
        for y in xrange(self.height):
            self.data[y][0]["bar"]["left"] = False

    def shift_right(self):
        """
        Move the content of the grid right by one cell.
        
        The content of the right column will be lost.
        An empty column will be inserted at the left.
        """
        dirty = [(x, y, "across") for y in xrange(self.height) for x in [0, self.width - 1]]
        self._clear_clues(dirty)
        self.data = map(lambda x: [self._default_cell()] + x[:-1], self.data)
        
    def horizontal_flip(self):
        """Flip the content of the grid horizontally and clear the clues."""
        for y in xrange(self.height):
            for x in xrange(self.width / 2):
                first = self.data[y][x]
                second = self.data[y][self.width - 1 - x]
                self.data[y][x] = second
                self.data[y][self.width - 1 - x] = first
                
        # correct bars
        for y in xrange(self.height):
            for x in xrange(self.width - 1, -1, -1):
                if self.has_bar(x, y, "left"):
                    self.data[y][x]["bar"]["left"] = False
                    self.data[y][x + 1]["bar"]["left"] = True
        self.clear_clues()
        
    def vertical_flip(self):
        """Flip the content of the grid vertically and clear the clues."""
        for x in xrange(self.width):
            for y in xrange(self.height / 2):
                first = self.data[y][x]
                second = self.data[self.height -1 - y][x]
                self.data[y][x] = second
                self.data[self.height - 1 - y][x] = first
                
        # correct bars
        for x in xrange(self.width):
            for y in xrange(self.height - 1, -1, -1):
                if self.has_bar(x, y, "top"):
                    self.data[y][x]["bar"]["top"] = False
                    self.data[y + 1][x]["bar"]["top"] = True
        self.clear_clues()
        
    def diagonal_flip(self):
        """Flip the content of the grid diagonally."""
        
        # for now
        assert self.width == self.height
        
        def flip_bars(cell):
            """Turn all top bars into left bars and vice versa."""
            if cell["bar"]["top"] and cell["bar"]["left"]:
                return
            if cell["bar"]["top"]:
                cell["bar"]["top"] = False
                cell["bar"]["left"] = True
            elif cell["bar"]["left"]:
                cell["bar"]["left"] = False
                cell["bar"]["top"] = True
        
        for x in xrange(self.width):
            for y in xrange(x, self.height):
                first = self.data[y][x]
                second = self.data[x][y]
                
                # correct all bars but don't flip the
                # bars of cells on the diagonal twice
                flip_bars(first)
                if x != y:
                    flip_bars(second)
                
                self.data[y][x] = second
                self.data[x][y] = first

                # flip the clues
                other = {"across": "down", "down": "across"}
                for p, q in [(x, y), (y, x)]:
                    for dir1 in ["across", "down"]:
                        try:
                            clue1 = self.data[p][q]["clues"][dir1]
                            dir2 = other[dir1]
                            if dir2 in self.data[p][q]["clues"]:
                                clue2 = self.data[p][q]["clues"][dir2]
                                self.data[p][q]["clues"][dir1] = clue2
                            self.data[p][q]["clues"][dir2] = clue1
                        except KeyError:
                            pass
        
    def clear(self):
        """Clear the content of the grid."""
        self.initialize(self.width, self.height)
        
    def clear_bars(self):
        """Clear the bars of the grid."""
        for x, y in self.cells():
            self.set_bar(x, y, "top", False)
            self.set_bar(x, y, "left", False)
            
    def clear_blocks(self):
        """Clear the blocks of the grid."""
        for x, y in self.cells():
            self.set_block(x, y, False)
            
    def clear_voids(self):
        """Clear the void cells of the grid."""
        for x, y in self.cells():
            self.set_void(x, y, False)
                
    def clear_chars(self):
        """Clear the characters of the grid."""
        for x, y in self.cells():
            self.clear_char(x, y)
                
    def clear_clues(self):
        """Clear the clues of the grid."""
        for x, y in self.cells():
            self.cell(x, y)["clues"] = {}
                
    def store_clue(self, x, y, direction, key, value):
        """
        Store the given key/value pair as clue property of (x, y, direction).
        
        This function cleans the 'clues' dictionary if needed: if a value
        is empty, the key will be deleted. If no key/value pairs remain,
        the clue entry for this direction will be deleted.
        """
        clues = self.cell(x, y)["clues"]
        try:
            clue = clues[direction]
        except KeyError:
            clues[direction] = {}
            clue = clues[direction]
        
        if len(value) > 0:
            clues[direction][key] = value
        elif key in clue:
            del clues[direction][key]
         
        if len(clue) == 0:
            del clues[direction]
        
    def is_valid(self, x, y):
        """Return True if the given (x, y) is within the grid's boundaries."""
        return 0 <= x < self.width and 0 <= y < self.height
        
    def is_available(self, x, y):
        """Return True if the given (x, y) is valid and not a block or a void."""
        is_valid = 0 <= x < self.width and 0 <= y < self.height
        if not is_valid:
            return False
        is_block = self.data[y][x]["block"]
        is_void = self.data[y][x]["void"]
        return not is_block and not is_void
        
    def get_size(self):
        """Return a tuple containing the width and height of the grid."""
        return (self.width, self.height)
        
    size = property(get_size)
    
    def cell(self, x, y):
        return self.data[y][x]
    
    def get_clues(self, x, y):
        return self.data[y][x]["clues"]
        
    def set_block(self, x, y, status):
        self._on_cell_type_change(x, y, status)
        self.data[y][x]["block"] = status
        self.data[y][x]["void"] = False
        
    def is_block(self, x, y):
        return self.data[y][x]["block"]
        
    def clear_char(self, x, y):
        self.set_char(x, y, "")
        
    def set_char(self, x, y, char):
        self._clear_clues_related_to_cell(x, y)
        self.data[y][x]["char"] = char
        
    def get_char(self, x, y):
        return self.data[y][x]["char"]
        
    def is_char(self, x, y):
        return self.data[y][x]["char"] != ''
        
    def set_number(self, x, y, n):
        self.data[y][x]["number"] = n
        
    def get_number(self, x, y):
        return self.data[y][x]["number"]
        
    def has_bar(self, x, y, side):
        return self.data[y][x]["bar"][side]
        
    def set_bar(self, x, y, side, status):
        if side == "top":
            tx, ty = self.get_start_word(x, y, "down")
            self._clear_clues([(tx, ty, "down")])
        elif side == "left":
            sx, sy = self.get_start_word(x, y, "across")
            self._clear_clues([(sx, sy, "across")])
        self.data[y][x]["bar"][side] = status
        
    def is_void(self, x, y):
        return self.data[y][x]["void"]
        
    def set_void(self, x, y, status):
        self._on_cell_type_change(x, y, status)
        self.data[y][x]["void"] = status
        
    def has_rebus(self, x, y):
        return self.data[y][x]["rebus"] is not None
        
    def set_rebus(self, x, y, short, full):
        self.data[y][x]["rebus"] = (short, full)
        
    def _on_cell_type_change(self, x, y, status):
        if status:
            self._clear_clues_related_to_cell(x, y)
        else:
            for p, q in [(x, y + 1), (x, y - 1), (x + 1, y), (x - 1, y)]:
                if self.is_valid(p, q):
                    self._clear_clues_related_to_cell(p, q)
