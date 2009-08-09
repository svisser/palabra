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

class Grid:
    def __init__(self, width, height):
        """Construct a grid with the given dimensions."""
        self.initialize(width, height)
        
    def initialize(self, width, height):
        """Reset the grid to the given dimensions with all empty cells."""
        self.width = width
        self.height = height
        self.data = [[self._default_cell() for x in range(width)] for y in range(height)]
        
    def _default_cell(self):
        cell = {}
        cell["block"] = False
        cell["char"] = ""
        cell["clues"] = {}
        return cell

    def set_data(self, width, height, chars, blocks):
        """Set the grid's data to the given data."""
        self.initialize(width, height)
        
        for x, y in self.cells():
            self.data[y][x]["char"] = chars[y][x]
            self.data[y][x]["block"] = blocks[y][x]

    def is_start_horizontal_word(self, x, y):
        """Return True when a horizontal words begins in the cell at (x, y)."""
        if self.is_block(x, y):
            return False
            
        return ((x == 0 and self.width > 1 and not self.is_block(1, y))
            or (x > 0 and x < self.width - 1 and self.is_block(x - 1, y)
            and not self.is_block(x + 1, y)))
            
    def is_start_vertical_word(self, x, y):
        """Return True when a vertical word begins in the cell at (x, y)."""
        if self.is_block(x, y):
            return False
            
        return ((y == 0 and self.height > y + 1 and not self.is_block(x, y + 1))
            or (y > 0 and y < self.height - 1 and self.is_block(x, y - 1)
            and not self.is_block(x, y + 1)))
            
    def is_start_word(self, x, y):
        """Return True when a word begins in either direction in the cell (x, y)."""
        return (self.is_start_horizontal_word(x, y) or
            self.is_start_vertical_word(x, y))
            
    def get_start_horizontal_word(self, x, y):
        """Return the first cell of a horizontal word that contains the cell (x, y)."""
        while x >= 0:
            if self.is_start_horizontal_word(x, y):
                return x, y
            if (not self.is_available(x, y) or
                (x > 0 and not self.is_available(x - 1, y))):
                return x, y
            x -= 1
        if x < 0:
            return 0, y
        return x, y
        
    def get_start_vertical_word(self, x, y):
        """Return the first cell of a vertical word that contains the cell (x, y)."""
        while y >= 0:
            if self.is_start_vertical_word(x, y):
                return x, y
            if (not self.is_available(x, y) or
                (y > 0 and not self.is_available(x, y - 1))):
                return x, y
            y -= 1
        if y < 0:
            return x, 0
        return x, y
        
    def get_check_count(self, x, y):
        """
        Return the number of words that contain the cell (x, y).
        
        Return values:
        -1 : A block
        0 : An isolated cell: no words contain this cell
        1 : One word contains this cell
        2 : Two words contain this cell
        """
        if self.is_block(x, y):
            return -1
            
        check_count = 0
        if self.is_available(x, y + 1) or self.is_available(x, y - 1):
            check_count += 1
        if self.is_available(x + 1, y) or self.is_available(x - 1, y):
            check_count += 1
        return check_count

    def determine_status(self, full=False):
        """Return a dictionary with the grid's properties."""
        size = self.width * self.height
        
        status = {}
        status["block_count"] = self.count_blocks()
        status["char_count"] = size - status["block_count"]
        status["word_count"] = self.count_words()
        
        block_percentage = (float(status["block_count"]) / float(size)) * 100
        status["block_percentage"] = block_percentage
        
        if full:
            status["mean_word_length"] = self.mean_word_length()
            
            status["word_counts"] = {}
            status["across_word_count"] = 0
            status["down_word_count"] = 0
            for n, x, y in self.horizontal_words():
                length = self.word_length(x, y, "across")
                
                status["across_word_count"] += 1
                
                try:
                    status["word_counts"][length] += 1
                except KeyError:
                    status["word_counts"][length] = 1
                    
            for n, x, y in self.vertical_words():
                length = self.word_length(x, y, "down")
                
                status["down_word_count"] += 1
                
                try:
                    status["word_counts"][length] += 1
                except KeyError:
                    status["word_counts"][length] = 1
                    
            status["word_counts_total"] = []
            for length in range(2, max(self.width, self.height) + 1):
                try:
                    count = status["word_counts"][length]
                except KeyError:
                    count = 0
                status["word_counts_total"].append((length, count))
                    
            status["char_counts"] = {}
            for x, y in self.cells():
                c = self.get_char(x, y)
                if c != "":
                    try:
                        status["char_counts"][c] += 1
                    except KeyError:
                        status["char_counts"][c] = 1
                            
            status["char_counts_total"] = []
            for c in map(chr, range(ord('A'), ord('Z') + 1)):
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
        
        return status
            
    def horizontal_words(self):
        """Iterate over the horizontal words in the grid."""
        n = 0
        for x, y in self.cells():
            if self.is_start_word(x, y):
                n += 1
                
            if self.is_start_horizontal_word(x, y):
                yield n, x, y
                    
    def vertical_words(self):
        """Iterate over the vertical words in the grid."""
        n = 0
        for x, y in self.cells():
            if self.is_start_word(x, y):
                n += 1
                
            if self.is_start_vertical_word(x, y):
                yield n, x, y
                    
    def horizontal_clues(self):
        """Iterate over the horizontal clues of the grid."""
        for n, x, y in self.horizontal_words():
            try:
                yield n, x, y, self.cell(x, y)["clues"]["across"]
            except KeyError:
                yield n, x, y, {}
                
    def vertical_clues(self):
        """Iterate over the vertical clues of the grid."""
        for n, x, y in self.vertical_words():
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
        n = 0
        for x, y in self.cells():
            if allow_duplicates:
                if self.is_start_horizontal_word(x, y):
                    n += 1
                    yield n, x, y
                if self.is_start_vertical_word(x, y):
                    yield n, x, y
            else:
                if self.is_start_word(x, y):
                    n += 1
                    yield n, x, y
                    
    def cells(self):
        """Iterate over the cells of the grid in left-to-right, top-to-bottom order."""
        for y in xrange(self.height):
            for x in xrange(self.width):
                yield x, y
                    
    def gather_word(self, x, y, direction, empty_char="?"):
        """Return the word starting at (x, y) in the given direction."""
        word = ""
        for p, q in self.in_direction(direction, x, y):
            c = self.get_char(p, q)
            if c == "":
                word += empty_char
            else:
                word += c
        return word
                
    def gather_words(self, direction):
        """Iterate over the word data in the given direction."""
        if direction == "across":
            iter_words = self.horizontal_words()
        elif direction == "down":
            iter_words = self.vertical_words()
            
        for n, x, y in iter_words:
            try:
                clue = self.cell(x, y)["clues"][direction]["text"]
            except KeyError:
                clue = ""
                
            word = self.gather_word(x, y, direction)
            yield n, x, y, word, clue
        
    def word_length(self, x, y, direction):
        """Return the length of the word starting at (x, y) in the given direction."""
        return sum([1 for x, y in self.in_direction(direction, x, y)])
        
    def line(self, x, y, direction):
        """Iterate in the given direction from (x, y)."""
        dx = 1 if direction == "across" else 0
        dy = 1 if direction == "down" else 0
        return self._start_from(x, y, dx, dy)
        
    def in_direction(self, direction, x, y, reverse=False):
        """Iterate in the given direction from (x, y) while cells are available."""
        dx = 1 if direction == "across" else 0
        dy = 1 if direction == "down" else 0
        if reverse:
            dx *= -1
            dy *= -1
        return self._start_from(x, y, dx, dy, self.is_block)
                
    def _start_from(self, x, y, delta_x, delta_y, predicate=None):
        """Repeatedly add the delta to (x, y) until the predicate becomes True."""
        while self.is_valid(x, y):
            if predicate is not None and predicate(x, y):
                break
            yield x, y
            x += delta_x
            y += delta_y
            
    def count_blocks(self):
        """Return the number of blocks in the grid."""
        return sum([1 for x, y in self.cells() if self.is_block(x, y)])
        
    def count_words(self):
        """Return the number of words in the grid."""
        total = 0
        for x, y in self.cells():
            if self.is_start_horizontal_word(x, y):
                total += 1
            if self.is_start_vertical_word(x, y):
                total += 1
        return total
            
    def mean_word_length(self):
        """Return the mean length of the words in the grid."""
        word_count = self.count_words()
        if word_count == 0:
            return 0
        
        char_count = 0
        for x, y in self.cells():
            if self.is_start_horizontal_word(x, y):
                char_count += self.word_length(x, y, "across")
            if self.is_start_vertical_word(x, y):
                char_count += self.word_length(x, y, "down")
        
        return float(char_count) / float(word_count)
            
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
            if direction == "across":
                p, q = self.get_start_horizontal_word(x, y)
                try:
                    del self.cell(p, q)["clues"]["across"]
                except KeyError:
                    pass
            elif direction == "down":
                p, q = self.get_start_vertical_word(x, y)
                try:
                    del self.cell(p, q)["clues"]["down"]
                except KeyError:
                    pass
        
    def insert_row(self, y, insert_above=True):
        """Insert a row above or below the row at vertical coordinate y."""
        dirty = [(x, y, "down") for x in xrange(self.width)]

        ny = y - 1 if insert_above else y + 1
        blocks = [x for x in xrange(self.width) if self.is_block(x, y)]
        dirty += [(x, ny, "down") for x in blocks if self.is_valid(x, ny)]
        self._clear_clues(dirty)

        self.resize(self.width, self.height + 1, False)
        row = [[self._default_cell() for x in range(self.width)]]
        if insert_above:
            self.data = self.data[:y] + row + self.data[y:]
        else:
            self.data = self.data[:y + 1] + row + self.data[y + 1:]
            
    def insert_column(self, x, insert_left=True):
        """Insert a column to the left or right of the horizontal coordinate x."""
        dirty = [(x, y, "across") for y in xrange(self.height)]
        
        nx = x - 1 if insert_left else x + 1
        blocks = [y for y in xrange(self.height) if self.is_block(x, y)]
        dirty += [(nx, y, "across") for y in blocks if self.is_valid(nx, y)]
        self._clear_clues(dirty)
        
        self.resize(self.width + 1, self.height, False)
        if insert_left:
            f = lambda row: row[:x] + [self._default_cell()] + row[x:]
        else:
            f = lambda row: row[:x + 1] + [self._default_cell()] + row[x + 1:]
        self.data = map(f, self.data)
            
    def remove_column(self, x):
        """Remove the column at horizontal coordinate x."""
        dirty = [(x, y, "across") for y in xrange(self.height)]
        blocks = [y for y in xrange(self.height) if self.is_block(x, y)]
        for p in [x - 1, x + 1]:
            dirty += [(p, y, "across") for y in blocks if self.is_valid(p, y)]
        self._clear_clues(dirty)
        
        self.data = map(lambda row: row[:x] + row[x + 1:], self.data)
        self.width -= 1
            
    def remove_row(self, y):
        """Remove the row at vertical coordinate y."""
        dirty = [(x, y, "down") for x in xrange(self.width)]
        blocks = [x for x in xrange(self.width) if self.is_block(x, y)]
        for q in [y - 1, y + 1]:
            dirty += [(x, q, "down") for x in blocks if self.is_valid(x, q)]
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
        self.clear_clues()
        
    def vertical_flip(self):
        """Flip the content of the grid vertically and clear the clues."""
        for x in xrange(self.width):
            for y in xrange(self.height / 2):
                first = self.data[y][x]
                second = self.data[self.height -1 - y][x]
                self.data[y][x] = second
                self.data[self.height - 1 - y][x] = first
        self.clear_clues()
        
    def diagonal_flip(self):
        """Flip the content of the grid diagonally."""
        for x in xrange(self.width):
            for y in xrange(x, self.height):
                first = self.data[y][x]
                second = self.data[x][y]
                self.data[y][x] = second
                self.data[x][y] = first
                
                # also flip the clues
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
        """Return True if the given (x, y) is valid and not a block."""
        return self.is_valid(x, y) and not self.is_block(x, y)
        
    def get_size(self):
        return (self.width, self.height)
        
    size = property(get_size)
    
    def cell(self, x, y):
        return self.data[y][x]
    
    def set_cell(self, x, y, cell):
        self.data[y][x] = cell
        
    def get_clues(self, x, y):
        return self.data[y][x]["clues"]
        
    def set_block(self, x, y, status):
        self.data[y][x]["block"] = status
        
    def is_block(self, x, y):
        return self.data[y][x]["block"]
        
    def clear_char(self, x, y):
        self.set_char(x, y, '')
        
    def set_char(self, x, y, char):
        self.data[y][x]["char"] = char
        
    def get_char(self, x, y):
        return self.data[y][x]["char"]
        
    def is_char(self, x, y):
        return self.data[y][x]["char"] != ''
