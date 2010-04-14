# This file is part of Palabra
#
# Copyright (C) 2009 - 2010 Simeon Visser
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

import constants

class Grid:
    def __init__(self, width, height):
        """Construct a grid with the given dimensions."""
        self.initialize(width, height)
        
    def initialize(self, width, height):
        """Reset the grid to the given dimensions with all empty cells."""
        self.width = width
        self.height = height
        self.data = [[self._default_cell() for x in range(width)] for y in range(height)]
        # TODO modify when arbitrary number schemes are implemented
        self.assign_numbers()
        
    def _default_cell(self):
        cell = {}
        cell["bar"] = {"top": False, "left": False}
        cell["block"] = False
        cell["char"] = ""
        cell["clues"] = {}
        cell["number"] = 0
        cell["void"] = False
        return cell
        
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
        
    def assign_numbers(self):
        """Assign word numbers to cells as they are commonly numbered."""
        n = 1
        for x, y in self.cells():
            self.cell(x, y)["number"] = 0
            if self.is_start_word(x, y):
                self.cell(x, y)["number"] = n
                n += 1
            
    def is_start_word(self, x, y, direction=None):
        """Return True when a word begins in the cell (x, y)."""
        if not self.is_available(x, y):
            return False
        def _is_start_word(d):
            if d == "across":
                bdx, bdy, adx, ady, bar_side = -1, 0, 1, 0, "left"
            elif d == "down":
                bdx, bdy, adx, ady, bar_side = 0, -1, 0, 1, "top"
            
            before = not self.is_available(x + bdx, y + bdy) or self.has_bar(x, y, bar_side)
            after = self.is_available(x + adx, y + ady) and not self.has_bar(x + adx, y + ady, bar_side)
            return before and after
        if direction:
            return _is_start_word(direction)
        return _is_start_word("across") or _is_start_word("down")
        
    def get_start_word(self, x, y, direction):
        """Return the first cell of a word in the given direction that contains the cell (x, y)."""
        if not self.is_available(x, y):
            return x, y
        return [(x, y) for x, y in self.in_direction(x, y, direction, reverse=True)][-1]
            
    def get_end_word(self, x, y, direction):
        """Return the last cell of a word in the given direction that contains the cell (x, y)."""
        if not self.is_available(x, y):
            return x, y
        return [(x, y) for x, y in self.in_direction(x, y, direction)][-1]
        
    def get_check_count(self, x, y):
        """
        Return the number of words that contain the cell (x, y).
        
        Return values:
        -1 : A block or void
        0 : An isolated cell: no words contain this cell
        1 : One word contains this cell
        2 : Two words contain this cell
        """
        if not self.is_available(x, y):
            return -1
        count = 0
        for d in ["across", "down"]:
            if self.is_part_of_word(x, y, d):
                count += 1
        return count
        
    def is_part_of_word(self, x, y, direction):
        """Return True if the specified (x, y, direction) is part of a word (2+ letters)."""
        if direction == "across":
            bdx, bdy, adx, ady, bar_side = -1, 0, 1, 0, "left"
        elif direction == "down":
            bdx, bdy, adx, ady, bar_side = 0, -1, 0, 1, "top"
        before = self.is_available(x + bdx, y + bdy) and not self.has_bar(x, y, bar_side)
        after = self.is_available(x + adx, y + ady) and not self.has_bar(x + adx, y + ady, bar_side)
        return before or after

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
                c = self.get_char(x, y)
                if c:
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
                            
            status["checked_count"] = 0
            status["unchecked_count"] = 0
            for x, y in self.cells():
                check_count = self.get_check_count(x, y)
                if 0 <= check_count <= 1:
                    status["unchecked_count"] += 1
                if check_count == 2:
                    status["checked_count"] += 1
                        
            status["clue_count"] = 0
            for x, y in self.cells():
                status["clue_count"] += len(self.data[y][x]["clues"])
                
            status["open_count"] = self.count_open_squares()
            status["connected"] = self.is_connected()
        return status
        
    def determine_word_counts(self):
        """Calculate the number of words by direction and by length."""
        status = {}
        def count_by_dir(direction):
            for n, x, y in self.words_by_direction(direction):
                status[direction] += 1
                length = self.word_length(x, y, direction)
                try:
                    status[length] += 1
                except KeyError:
                    status[length] = 1
        status = {"across": 0, "down": 0}
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
        for x, y in self.cells():
            if self.is_start_word(x, y, direction):
                yield self.cell(x, y)["number"], x, y

    def horizontal_clues(self):
        """Iterate over the horizontal clues of the grid."""
        for n, x, y in self.words_by_direction("across"):
            try:
                yield n, x, y, self.cell(x, y)["clues"]["across"]
            except KeyError:
                yield n, x, y, {}
                
    def vertical_clues(self):
        """Iterate over the vertical clues of the grid."""
        for n, x, y in self.words_by_direction("down"):
            try:
                yield n, x, y, self.cell(x, y)["clues"]["down"]
            except KeyError:
                yield n, x, y, {}
                    
    def words(self, allow_duplicates=False):
        """
        Iterate over the words of the grid.
        
        allow_duplicates: If True, cells that contain the start
        of two words are encountered twice when iterating. Otherwise,
        they are encountered only once.
        """
        for x, y in self.cells():
            n = self.cell(x, y)["number"]
            if allow_duplicates:
                if self.is_start_word(x, y, "across"):
                    yield n, x, y
                if self.is_start_word(x, y, "down"):
                    yield n, x, y
            else:
                if self.is_start_word(x, y):
                    yield n, x, y
    
    def entries(self):
        """Return all entries in alphabetical order."""
        a = [word for (n, x, y, word, clue, explanation) in self.gather_words("across")]
        d = [word for (n, x, y, word, clue, explanation) in self.gather_words("down")]
        entries = (a + d)
        entries.sort()
        return entries
                    
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
                
    def lines_of_cell(self, x, y):
        """Return the lines of a cell (uses nonexistent cells for outer lines)."""
        lines = []
        for edge, (dx, dy) in [("left", (-1, 0)), ("top", (0, -1))]:
            if self.is_valid(x + dx, y + dy):
                v0 = self.is_void(x, y)
                v1 = self.is_void(x + dx, y + dy)
                if not (v0 and v1):
                    side = "normal"
                    if v0 and not v1:
                        side = "innerborder"
                    elif not v0 and v1:
                        side = "outerborder"
                    lines.append((x, y, edge, side))
            elif not self.is_void(x, y):
                lines.append((x, y, edge, "outerborder"))
                
        # also include lines at the bottom and the right
        if y == self.height - 1:
            if not self.is_void(x, self.height - 1):
                lines.append((x, self.height, "top", "innerborder"))
        if x == self.width - 1:
            if not self.is_void(self.width - 1, y):
                lines.append((self.width, y, "left", "innerborder"))
        return lines
                
    def lines(self):
        """Return the lines of the grid (uses nonexistent cells for outer lines)."""
        lines = []
        for x, y in self.cells():
            lines.extend(self.lines_of_cell(x, y))
        return lines
                    
    def gather_word(self, x, y, direction, empty_char=constants.MISSING_CHAR):
        """Return the word starting at (x, y) in the given direction."""
        word = ""
        for p, q in self.in_direction(x, y, direction):
            c = self.get_char(p, q)
            word += (empty_char if c == "" else c)
        return word
        
    @staticmethod
    def decompose_word(word, x, y, direction):
        """Decompose the word starting at (x, y) in the given direction into tuples."""
        if direction == "across":
            return [(x + i, y, word[i]) for i in xrange(len(word))]
        elif direction == "down":
            return [(x, y + j, word[j]) for j in xrange(len(word))]
            
    def gather_constraints(self, x, y, direction):
        """Create a list of all chars by position of the specified word."""
        word = self.gather_word(x, y, direction, constants.MISSING_CHAR)
        return [(i, c.lower()) for i, c in enumerate(word) if c != constants.MISSING_CHAR]
    
    def gather_all_constraints(self, x, y, direction):
        """
        Gather constraints of all intersecting words of the word at (x, y).
        
        This function returns a list with tuples that contain the
        letters and positions of intersecting words. The item at place i of
        the list corresponds to the intersecting word at position i.
        
        Each tuple contains the position at which the word at
        (x, y, direction) intersects the intersecting word, the length
        of the intersecting word and the constraints.
        """
        result = []
        other = {"across": "down", "down": "across"}[direction]
        sx, sy = self.get_start_word(x, y, direction)
        for s, t in self.in_direction(sx, sy, direction):
            p, q = self.get_start_word(s, t, other)
            length = self.word_length(p, q, other)
            
            if other == "across":
                index = x - p
            elif other == "down":
                index = y - q
            
            constraints = self.gather_constraints(p, q, other)
            result.append((index, length, constraints))
        return result
                
    def gather_words(self, direction):
        """Iterate over the word data in the given direction."""
        for n, x, y in self.words_by_direction(direction):
            try:
                clue = self.cell(x, y)["clues"][direction]["text"]
            except KeyError:
                clue = ""
            try:
                explanation = self.cell(x, y)["clues"][direction]["explanation"]
            except KeyError:
                explanation = ""
                
            word = self.gather_word(x, y, direction)
            yield n, x, y, word, clue, explanation
        
    def word_length(self, x, y, direction):
        """Return the length of the word starting at (x, y) in the given direction."""
        return sum([1 for x, y in self.in_direction(x, y, direction)])
        
    def in_direction(self, x, y, direction, reverse=False):
        """Iterate in the given direction from (x, y) while cells are available."""
        dx = 1 if direction == "across" else 0
        dy = 1 if direction == "down" else 0
        if reverse:
            dx *= -1
            dy *= -1
        while self.is_available(x, y):
            yield x, y
            if dx == 1 and self.is_valid(x + dx, y) and self.has_bar(x + dx, y, "left"):
                break
            if dx == -1 and self.has_bar(x, y, "left"):
                break
            if dy == 1 and self.is_valid(x, y + dy) and self.has_bar(x, y + dy, "top"):
                break
            if dy == -1 and self.has_bar(x, y, "top"):
                break
            x += dx
            y += dy
            
    def count_blocks(self):
        """Return the number of blocks in the grid."""
        return sum([1 for x, y in self.cells() if self.is_block(x, y)])
        
    def neighbors(self, x, y, diagonals=False):
        """
        Iterate over all neighboring cells of a cell.
        
        If diagonals is True, the diagonal neighbors will be included as well.
        """
        if diagonals:
            neighbors = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1]]
            neighbors.remove((0, 0))
        else:
            neighbors = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        for dx, dy in neighbors:
            if self.is_valid(x + dx, y + dy):
                yield x + dx, y + dy
        
    def count_open_squares(self):
        """
        Return the number of open squares.
        
        A square is open if it does not touch a block, including diagonally.
        """
        def is_open(x, y):
            if not self.is_available(x, y):
                return False
            for p, q in self.neighbors(x, y, diagonals=True):
                if self.is_block(p, q):
                    return False
            return True
        return sum([1 for x, y in self.cells() if is_open(x, y)])
        
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
        
    # TODO incorrect
    def count_cheaters(self):
        """Return the number of cheating blocks in the grid."""
        def is_cheater(x, y):
            if not self.is_block(x, y):
                return False
            if self.is_start_word(x + 1, y, "across") and self.is_part_of_word(x - 1, y, "across"):
                return False
            if self.is_start_word(x, y + 1, "down") and self.is_part_of_word(x, y - 1, "down"):
                return False
            return True
        cells = [(x, y) for x, y in self.cells() if is_cheater(x, y)]
        print cells
        return len(cells)
        
    def count_voids(self):
        """Return the number of voids in the grid."""
        return sum([1 for x, y in self.cells() if self.is_void(x, y)])
        
    def count_words(self):
        """Return the number of words in the grid."""
        total = 0
        for x, y in self.cells():
            for d in ["across", "down"]:
                if self.is_start_word(x, y, d):
                    total += 1
        return total
        
    def count_chars(self, include_blanks=True):
        """Return the number of chars in the grid."""
        count = 0
        for x, y in self.availables():
            if include_blanks or self.get_char(x, y) != '':
                count += 1
        return count
            
    def mean_word_length(self):
        """Return the mean length of the words in the grid."""
        word_count = self.count_words()
        if word_count == 0:
            return 0
        char_counts = [self.get_check_count(x, y) for x, y in self.availables()]
        return float(sum(char_counts)) / float(word_count)
            
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
        
    def _clear_clues(self, dirty_cells):
        """Remove the clues of the words that contain a dirty cell."""
        for x, y, direction in dirty_cells:
            p, q = self.get_start_word(x, y, direction)
            try:
                del self.cell(p, q)["clues"][direction]
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
        return (self.is_valid(x, y) and not self.is_block(x, y)
            and not self.is_void(x, y))
        
    def get_size(self):
        """Return a tuple containing the width and height of the grid."""
        return (self.width, self.height)
        
    size = property(get_size)
    
    def cell(self, x, y):
        return self.data[y][x]
    
    def set_cell(self, x, y, cell):
        self.data[y][x] = cell
        
    def get_clues(self, x, y):
        return self.data[y][x]["clues"]
        
    def set_block(self, x, y, status):
        self._on_cell_type_change(x, y, status)
        self.data[y][x]["block"] = status
        
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
        
    def _on_cell_type_change(self, x, y, status):
        if status:
            self._clear_clues_related_to_cell(x, y)
        else:
            for p, q in [(x, y + 1), (x, y - 1), (x + 1, y), (x - 1, y)]:
                if self.is_valid(p, q):
                    self._clear_clues_related_to_cell(p, q)
