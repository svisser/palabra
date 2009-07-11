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

import cairo
import math
import pango
import pangocairo

MINIMUM_WIDTH = 3
MAXIMUM_WIDTH = 35

VIEW_MODE_EDITOR = "editor"
VIEW_MODE_EMPTY = "empty"
VIEW_MODE_SOLUTION = "solution"

class Grid:
    def __init__(self, width, height):
        self.initialize(width, height)
        
    def initialize(self, width, height):
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
        self.initialize(width, height)
        
        for x in range(width):
            for y in range(height):
                self.data[y][x]["char"] = chars[y][x]
                self.data[y][x]["block"] = blocks[y][x]

    def is_start_horizontal_word(self, x, y):
        if self.is_block(x, y):
            return False
            
        return ((x == 0 and self.width > 1 and not self.is_block(1, y))
            or (x > 0 and x < self.width - 1 and self.is_block(x - 1, y)
            and not self.is_block(x + 1, y)))
            
    def is_start_vertical_word(self, x, y):
        if self.is_block(x, y):
            return False
            
        return ((y == 0 and self.height > y + 1 and not self.is_block(x, y + 1))
            or (y > 0 and y < self.height - 1 and self.is_block(x, y - 1)
            and not self.is_block(x, y + 1)))
            
    def is_start_word(self, x, y):
        return (self.is_start_horizontal_word(x, y) or
            self.is_start_vertical_word(x, y))
            
    def get_start_horizontal_word(self, x, y):
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
        if self.is_block(x, y):
            return -1
            
        check_count = 0
        if self.is_available(x, y + 1) or self.is_available(x, y - 1):
            check_count += 1
            
        if self.is_available(x + 1, y) or self.is_available(x - 1, y):
            check_count += 1
            
        return check_count

    def determine_status(self, full=False):
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
                    
            status["char_counts"] = {}
            for x in range(self.width):
                for y in range(self.height):
                    c = self.get_char(x, y)
                    if c != "":
                        try:
                            status["char_counts"][c] += 1
                        except KeyError:
                            status["char_counts"][c] = 1
                            
            status["checked_count"] = 0
            status["unchecked_count"] = 0
            for y in range(self.height):
                for x in range(self.width):
                    check_count = self.get_check_count(x, y)
                    if 0 <= check_count <= 1:
                        status["unchecked_count"] += 1
                    if check_count == 2:
                        status["checked_count"] += 1
                        
            status["clue_count"] = 0
            for y in range(self.height):
                for x in range(self.width):
                    status["clue_count"] += len(self.data[y][x]["clues"])
        
        return status
        
    def determine_status_message(self):
        status = self.determine_status(False)
        
        return ''.join(
            ["Words: ", str(status["word_count"]), ", ",
             "Blocks: ", str(status["block_count"]), " ("
             , "%.2f" % status["block_percentage"], "%), "
             "Letters: ", str(status["char_count"])
            ])
            
    def horizontal_words(self):
        n = 0
        for y in range(self.height):
            for x in range(self.width):
                if self.is_start_word(x, y):
                    n += 1
                    
                if self.is_start_horizontal_word(x, y):
                    yield n, x, y
                    
    def vertical_words(self):
        n = 0
        for y in range(self.height):
            for x in range(self.width):
                if self.is_start_word(x, y):
                    n += 1
                    
                if self.is_start_vertical_word(x, y):
                    yield n, x, y
                    
    def horizontal_clues(self):
        for n, x, y in self.horizontal_words():
            try:
                yield n, x, y, self.cell(x, y)["clues"]["across"]
            except KeyError:
                yield n, x, y, {}
                
    def vertical_clues(self):
        for n, x, y in self.vertical_words():
            try:
                yield n, x, y, self.cell(x, y)["clues"]["down"]
            except KeyError:
                yield n, x, y, {}
                    
    def words(self):
        n = 0
        for y in range(self.height):
            for x in range(self.width):
                if self.is_start_word(x, y):
                    n += 1
                    yield n, x, y
                    
    def gather_word(self, x, y, direction, empty_char="_"):
        word = ""
        if direction == "across":
            while x < self.width and not self.is_block(x, y):
                c = self.get_char(x, y)
                if c == "":
                    word += empty_char
                else:
                    word += c
                x += 1
        elif direction == "down":
            while y < self.height and not self.is_block(x, y):
                c = self.get_char(x, y)
                if c == "":
                    word += empty_char
                else:
                    word += c
                y += 1
        return word
        
    def word_length(self, x, y, direction):
        length = 0
        if direction == "across":
            while x < self.width and not self.is_block(x, y):
                length += 1
                x += 1
        elif direction == "down":
            while y < self.height and not self.is_block(x, y):
                length += 1
                y += 1
        return length
            
    def count_blocks(self):
        total = 0
        for x in range(self.width):
            for y in range(self.height):
                if self.is_block(x, y):
                    total += 1
        return total
        
    def count_words(self):
        total = 0
        for x in range(self.width):
            for y in range(self.height):
                if self.is_start_horizontal_word(x, y):
                    total += 1
                if self.is_start_vertical_word(x, y):
                    total += 1
        return total
            
    def mean_word_length(self):
        word_count = self.count_words()
        if word_count == 0:
            return 0
        
        char_count = 0
        for x in range(self.width):
            for y in range(self.height):
                if self.is_start_horizontal_word(x, y):
                    char_count += self.word_length(x, y, "across")
                if self.is_start_vertical_word(x, y):
                    char_count += self.word_length(x, y, "down")
        
        return float(char_count) / float(word_count)
            
    def resize(self, width, height):
        ndata = [[self._default_cell() for x in range(width)] for y in range(height)]
        
        for x in range(width):
            for y in range(height):
                if self.is_valid(x, y):
                    ndata[y][x] = self.data[y][x]
                    
        self.data = ndata
        self.width = width
        self.height = height
        
    def cell(self, x, y):
        return self.data[y][x]
    
    def set_cell(self, x, y, cell):
        self.data[y][x] = cell
        
    def insert_row(self, y, insert_above=True):
        self.resize(self.width, self.height + 1)
        row = [[self._default_cell() for x in range(self.width)]]
        if insert_above:
            self.data = self.data[:y] + row + self.data[y:]
        else:
            self.data = self.data[:y + 1] + row + self.data[y + 1:]
            
    def insert_column(self, x, insert_left=True):
        self.resize(self.width + 1, self.height)
        if insert_left:
            self.data = map(lambda row: row[:x] + [self._default_cell()] + row[x:], self.data)
        else:
            self.data = map(lambda row: row[:x + 1] + [self._default_cell()] + row[x + 1:], self.data)
            
    def remove_column(self, x):
        self.data = map(lambda row: row[:x] + row[x + 1:], self.data)
        self.width -= 1
            
    def remove_row(self, y):
        self.data = self.data[:y] + self.data[y + 1:]
        self.height -= 1
        
    def move_cell(self, x, y, delta):
        self.data[y + delta[1]][x + delta[0]] = self.data[y][x]
        if delta[0] != 0 or delta[1] != 0:
            self.data[y][x] = self._default_cell()
        
    def shift_up(self):
        self.data = self.data[1:] + [[self._default_cell() for x in range(self.width)]]
        
    def shift_down(self):
        self.data = [[self._default_cell() for x in range(self.width)]] + self.data[:-1]
        
    def shift_left(self):
        self.data = map(lambda x: x[1:] + [self._default_cell()], self.data)

    def shift_right(self):
        self.data = map(lambda x: [self._default_cell()] + x[:-1], self.data)
        
    def clear(self):
        self.initialize(self.width, self.height)
                
    def clear_chars(self):
        for x in range(self.width):
            for y in range(self.height):
                self.clear_char(x, y)
                
    def clear_clues(self):
        for x in range(self.width):
            for y in range(self.height):
                self.cell(x, y)["clues"] = {}
        
    def is_valid(self, x, y):
        return x >= 0 and x < self.width and y >= 0 and y < self.height
        
    def is_available(self, x, y):
        return self.is_valid(x, y) and not self.is_block(x, y)
        
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

class GridView:
    def __init__(self, grid):
        self.grid = grid
        
        # 0.5 for sharp lines
        self.origin_x = 0.5
        self.origin_y = 0.5
        self.tile_size = 32
        self.margin_x = 10
        self.margin_y = 10
        self.line_width = 1
    
    # needs manual queue_draw() on drawing_area afterwards
    def update_visual_size(self, drawing_area):
        visual_width = self.visual_width()
        visual_height = self.visual_height()
        drawing_area.set_size_request(visual_width, visual_height)

    def visual_width(self, include_padding=True):
        if include_padding:
            return self.margin_x * 2 + self.get_grid_width()
        return self.get_grid_width()
        
    def visual_height(self, include_padding=True):
        if include_padding:
            return self.margin_y * 2 + self.get_grid_height()
        return self.get_grid_height()

    def get_grid_width(self):
        return self.grid.width * (self.tile_size + self.line_width) + self.line_width # * 2
        
    def get_grid_height(self):
        return self.grid.height * (self.tile_size + self.line_width) + self.line_width # * 2
        
    def screen_to_grid_x(self, screen_x):
        for x in range(self.grid.width):
            left_x = self.margin_x + self.line_width + x * (self.tile_size + self.line_width)
            right_x = self.margin_x + (x + 1) * (self.tile_size + self.line_width)
            if screen_x >= left_x and screen_x < right_x:
                return x
        return -1
        
    def screen_to_grid_y(self, screen_y):
        for y in range(self.grid.height):
            top_y = self.margin_y + self.line_width + y * (self.tile_size + self.line_width)
            bottom_y = self.margin_y + (y + 1) * (self.tile_size + self.line_width)
            if screen_y >= top_y and screen_y < bottom_y:
                return y
        return -1
        
    def grid_to_screen_x(self, x):
        return self.margin_x + x * self.tile_size + (x + 1) * self.line_width
    
    def grid_to_screen_y(self, y):
        return self.margin_y + y * self.tile_size + (y + 1) * self.line_width
        
    def update_location(self, drawing_area, x, y):
        draw_x = self.grid_to_screen_x(x)
        draw_y = self.grid_to_screen_y(y)
        drawing_area.queue_draw_area(draw_x, draw_y, self.tile_size, \
            self.tile_size)
            
    def draw_horizontal_line(self, context, x, y, red, green, blue):
        context.translate(self.margin_x, self.margin_y)
        context.set_source_rgb(red, green, blue)
        
        draw_y = self.line_width + y * (self.tile_size + self.line_width)
        
        for k in reversed(range(x)):
            if self.grid.is_block(k, y):
                break
            draw_x = self.line_width + k * (self.tile_size + self.line_width)
            context.rectangle(draw_x, draw_y, self.tile_size, self.tile_size)
        for k in range(x, self.grid.width):
            if self.grid.is_block(k, y):
                break
            draw_x = self.line_width + k * (self.tile_size + self.line_width)
            context.rectangle(draw_x, draw_y, self.tile_size, self.tile_size)
        context.fill()
        
        context.translate(-self.margin_x, -self.margin_y)
        
    def draw_vertical_line(self, context, x, y, red, green, blue):
        context.translate(self.margin_x, self.margin_y)
        context.set_source_rgb(red, green, blue)
        
        draw_x = self.line_width + x * (self.tile_size + self.line_width)
        
        for k in reversed(range(y)):
            if self.grid.is_block(x, k):
                break
            draw_y = self.line_width + k * (self.tile_size + self.line_width)
            context.rectangle(draw_x, draw_y, self.tile_size, self.tile_size)
        for k in range(y, self.grid.height):
            if self.grid.is_block(x, k):
                break
            draw_y = self.line_width + k * (self.tile_size + self.line_width)
            context.rectangle(draw_x, draw_y, self.tile_size, self.tile_size)
        context.fill()
        
        context.translate(-self.margin_x, -self.margin_y)
        
    def update_horizontal_line(self, drawing_area, y):
        draw_y = self.grid_to_screen_y(y)
        for x in range(self.grid.width):
            draw_x = self.grid_to_screen_x(x)
            drawing_area.queue_draw_area(draw_x, draw_y, self.tile_size, self.tile_size)
        
    def update_vertical_line(self, drawing_area, x):
        draw_x = self.grid_to_screen_x(x)
        for y in range(self.grid.height):
            draw_y = self.grid_to_screen_y(y)
            drawing_area.queue_draw_area(draw_x, draw_y, self.tile_size, self.tile_size)
        
    def update_view(self, context, mode=None):
        if mode is None:
            mode = "editor"
            
        settings = {}
        if mode == "editor":
            settings["padding_around_puzzle"] = True
            settings["show_chars"] = True
            settings["show_numbers"] = False
        elif mode == "empty":
            settings["padding_around_puzzle"] = False
            settings["show_chars"] = False
            settings["show_numbers"] = True
        elif mode == "solution":
            settings["padding_around_puzzle"] = False
            settings["show_chars"] = True
            settings["show_numbers"] = True

        if settings["padding_around_puzzle"]:
            context.translate(self.margin_x, self.margin_y)
        
        # excluding borders
        total_width = self.grid.width * (self.tile_size + self.line_width)
        total_height = self.grid.height * (self.tile_size + self.line_width)
        
        context.set_source_rgb(0, 0, 0)
        
        # border
        context.set_line_width(self.line_width)
        context.rectangle(0.5 * self.line_width, 0.5 * self.line_width, \
            total_width, total_height)
        context.stroke()
        
        # blocks
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                if self.grid.is_block(x, y):
                    # -0.5 for coordinates and +1 for size are needed to
                    # render seamlessly in PDF
                    draw_x = -0.5 + self.line_width + x * (self.tile_size + self.line_width)
                    draw_y = -0.5 + self.line_width + y * (self.tile_size + self.line_width)
                    context.rectangle(draw_x, draw_y, self.tile_size + 1, self.tile_size + 1)
        context.fill()
        
        # lines
        context.set_line_width(self.line_width)
        context.move_to(self.tile_size + 1.5 * self.line_width, self.line_width)
        for i in range(self.grid.width - 1):
            line_length = total_height
            
            context.rel_line_to(0, line_length)
            context.rel_move_to(self.tile_size + self.line_width, -line_length)
            
        context.move_to(self.line_width, self.tile_size + 1.5 * self.line_width)
        for j in range(self.grid.height - 1):
            line_length = total_width
            
            context.rel_line_to(line_length, 0)
            context.rel_move_to(-line_length, self.tile_size + self.line_width)
        context.stroke()
        
        if settings["show_chars"]:
            self.draw_chars(context)
        
        if settings["show_numbers"]:
            self.draw_numbers(context)
        
        if settings["padding_around_puzzle"]:
            context.translate(-self.margin_x, -self.margin_y)

    def draw_chars(self, context):
        fascent, fdescent, fheight, fxadvance, fyadvance = context.font_extents()
        fe = context.font_extents()
        context.select_font_face("sans-serif", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        
        fheight = 0
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                c = self.grid.get_char(x, y)
                if c != '':
                    self.draw_char(context, x, y, c, fheight)
    
    def draw_char(self, context, x, y, c, fheight):
        xbearing, ybearing, width, height, xadvance, yadvance = ( \
                    context.text_extents(c))
                    
        draw_x = self.line_width + \
            (x + 0.5) * (self.tile_size + self.line_width) - \
            xbearing - (width / 2)
        draw_y = self.line_width + \
            (y + 0.25) * (self.tile_size + self.line_width) + \
            (fheight / 2)
        pcr = pangocairo.CairoContext(context)
        layout = pcr.create_layout()
        #font = pango.FontDescription()
        #font.set_family("Sans")
        #font.set_absolute_size(12 * pango.SCALE)
        #layout.set_font_description(font)
        #layout.set_markup('''<span>%s</span>''' % c)
        
        layout.set_markup('''<span font_desc="%s">%s</span>''' % ("Sans 12", c))
        context.save()
        context.move_to(draw_x, draw_y)
        pcr.show_layout(layout)
        context.restore()
    
    def draw_numbers(self, context):
        fascent, fdescent, fheight, fxadvance, fyadvance = context.font_extents()
        context.select_font_face("sans-serif", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        
        counter = 0
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                if self.grid.is_start_word(x, y):
                    counter += 1
                    self.draw_number(context, x, y, counter, fheight, fdescent)

    def draw_number(self, context, x, y, number, fheight, fdescent):
        draw_x = self.line_width + x * (self.tile_size + self.line_width) + 1 #+ fdescent / 2 - 1
        draw_y = self.line_width + y * (self.tile_size + self.line_width) #+ fheight / 2 - 1
        pcr = pangocairo.CairoContext(context)
        layout = pcr.create_layout()
        layout.set_markup('''<span font_desc="%s">%s</span>''' % ("Sans 7", str(number)))
        context.save()
        context.move_to(draw_x, draw_y)
        pcr.show_layout(layout)
        context.restore()
        
    def draw_location(self, context, x, y, red, green, blue):
        context.translate(self.margin_x, self.margin_y)
        
        context.set_source_rgb(red, green, blue)
        
        draw_x = -0.5 + self.line_width + x * (self.tile_size + self.line_width)
        draw_y = -0.5 + self.line_width + y * (self.tile_size + self.line_width)
        
        context.new_path()
        context.rectangle(draw_x, draw_y, self.tile_size + 1, self.tile_size + 1)
        context.fill()
        
        context.translate(-self.margin_x, -self.margin_y)
    
    def draw_background(self, context):
        context.translate(self.margin_x, self.margin_y)
        
        context.set_source_rgb(1, 1, 1)
        
        context.new_path()
        total_width = self.grid.width * (self.tile_size + self.line_width)
        total_height = self.grid.height * (self.tile_size + self.line_width)
        context.rectangle(self.line_width, self.line_width \
            , total_width, total_height)
        context.fill()
        
        context.translate(-self.margin_x, -self.margin_y)
