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

import constants

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
            mode = constants.VIEW_MODE_EDITOR
            
        settings = {}
        if mode == constants.VIEW_MODE_EDITOR:
            settings["padding_around_puzzle"] = True
            settings["show_chars"] = True
            settings["show_numbers"] = False
        elif mode == constants.VIEW_MODE_EMPTY:
            settings["padding_around_puzzle"] = False
            settings["show_chars"] = False
            settings["show_numbers"] = True
        elif mode == constants.VIEW_MODE_SOLUTION:
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
