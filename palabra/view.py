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
from itertools import *
import math
import pango
import pangocairo

import constants

COLORS = {
    "background": (1, 1, 1)
    , "border": (0, 0, 0)
    , "block": (0, 0, 0)
    , "line": (0, 0, 0)
    , "char": (0, 0, 0)
    , "number": (0, 0, 0)
}
SETTINGS_PREVIEW = {
    "has_padding": True
    , "show_chars": False
    , "show_numbers": False
}
SETTINGS_EDITOR = {
    "has_padding": True
    , "show_chars": True
    , "show_numbers": False
}
SETTINGS_EMPTY = {
    "has_padding": False
    , "show_chars": False
    , "show_numbers": True
}
SETTINGS_SOLUTION = {
    "has_padding": False
    , "show_chars": True
    , "show_numbers": True
}
custom_settings = {}

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
        
    def render_horizontal_line(self, context, x, y, r, g, b):
        def render():
            a = self.grid.in_direction("across", x, y)
            b = self.grid.in_direction("across", x, y, reverse=True)
            for p, q in chain(a, b):
                rx = self.line_width + p * (self.tile_size + self.line_width)
                ry = self.line_width + y * (self.tile_size + self.line_width)
                context.rectangle(rx, ry, self.tile_size, self.tile_size)
            context.fill()
        self._render(context, (r, g, b), render)
        
    def render_vertical_line(self, context, x, y, r, g, b):
        def render():
            a = self.grid.in_direction("down", x, y)
            b = self.grid.in_direction("down", x, y, reverse=True)
            for p, q in chain(a, b):
                rx = self.line_width + x * (self.tile_size + self.line_width)
                ry = self.line_width + q * (self.tile_size + self.line_width)
                context.rectangle(rx, ry, self.tile_size, self.tile_size)
            context.fill()
        self._render(context, (r, g, b), render)
        
    def render(self, context, mode=None):
        settings = {}
        if mode == constants.VIEW_MODE_EDITOR:
            settings.update(SETTINGS_EDITOR)
            settings.update(custom_settings)
        elif mode == constants.VIEW_MODE_EMPTY:
            settings.update(SETTINGS_EMPTY)
        elif mode == constants.VIEW_MODE_PREVIEW:
            settings.update(SETTINGS_PREVIEW)
        elif mode == constants.VIEW_MODE_SOLUTION:
            settings.update(SETTINGS_SOLUTION)

        if settings["has_padding"]:
            context.translate(self.margin_x, self.margin_y)
        
        # excluding borders
        total_width = self.grid.width * (self.tile_size + self.line_width)
        total_height = self.grid.height * (self.tile_size + self.line_width)
        
        # blocks
        r, g, b = COLORS["block"]
        context.set_source_rgb(r, g, b)
        for x, y in self.grid.cells():
            if self.grid.is_block(x, y):
                # -0.5 for coordinates and +1 for size
                # are needed to render seamlessly in PDF
                draw_x = -0.5 + self.line_width + x * (self.tile_size + self.line_width)
                draw_y = -0.5 + self.line_width + y * (self.tile_size + self.line_width)
                context.rectangle(draw_x, draw_y, self.tile_size + 1, self.tile_size + 1)
        context.fill()
        
        # lines
        r, g, b = COLORS["line"]
        context.set_source_rgb(r, g, b)
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
        
        # border
        r, g, b = COLORS["border"]
        context.set_source_rgb(r, g, b)
        context.set_line_width(self.line_width)
        context.rectangle(0.5 * self.line_width, 0.5 * self.line_width, total_width, total_height)
        context.stroke()
        
        if settings["show_chars"]:
            self.render_chars(context)
        
        if settings["show_numbers"]:
            self.render_numbers(context)

        if settings["has_padding"]:
            context.translate(-self.margin_x, -self.margin_y)

    def render_chars(self, context):
        r, g, b = COLORS["char"]
        context.set_source_rgb(r, g, b)
        
        fascent, fdescent, fheight, fxadvance, fyadvance = context.font_extents()
        fe = context.font_extents()
        context.select_font_face("sans-serif", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        
        fheight = 0
        for x, y in self.grid.cells():
            c = self.grid.get_char(x, y)
            if c != '':
                self.render_char(context, x, y, c, fheight)
    
    def render_char(self, context, x, y, c, fheight):
        xbearing, ybearing, width, height, xadvance, yadvance = context.text_extents(c)
                    
        draw_x = (self.line_width +
            (x + 0.5) * (self.tile_size + self.line_width) -
            xbearing - (width / 2))
        draw_y = (self.line_width +
            (y + 0.25) * (self.tile_size + self.line_width) +
            (fheight / 2))
        pcr = pangocairo.CairoContext(context)
        layout = pcr.create_layout()

        layout.set_markup('''<span font_desc="%s">%s</span>''' % ("Sans 12", c))
        context.save()
        context.move_to(draw_x, draw_y)
        pcr.show_layout(layout)
        context.restore()
    
    def render_numbers(self, context):
        r, g, b = COLORS["number"]
        context.set_source_rgb(r, g, b)
        
        fascent, fdescent, fheight, fxadvance, fyadvance = context.font_extents()
        for n, x, y in self.grid.words():
            self.render_number(context, x, y, n, fheight, fdescent)

    def render_number(self, context, x, y, number, fheight, fdescent):
        draw_x = self.line_width + x * (self.tile_size + self.line_width) + 1
        draw_y = self.line_width + y * (self.tile_size + self.line_width)
        pcr = pangocairo.CairoContext(context)
        layout = pcr.create_layout()
        layout.set_markup('''<span font_desc="%s">%s</span>''' % ("Sans 7", str(number)))
        context.save()
        context.move_to(draw_x, draw_y)
        pcr.show_layout(layout)
        context.restore()
        
    def render_location(self, context, x, y, r, g, b):
        def render():
            # -0.5 for coordinates and +1 for size
            # are needed to render seamlessly in PDF
            draw_x = -0.5 + self.line_width + x * (self.tile_size + self.line_width)
            draw_y = -0.5 + self.line_width + y * (self.tile_size + self.line_width)
            context.rectangle(draw_x, draw_y, self.tile_size + 1, self.tile_size + 1)
            context.fill()
        self._render(context, (r, g, b), render)
    
    def render_background(self, context):
        def render():
            width = self.grid.width * (self.tile_size + self.line_width)
            height = self.grid.height * (self.tile_size + self.line_width)
            context.rectangle(self.line_width, self.line_width, width, height)
            context.fill()
        self._render(context, COLORS["background"], render)
        
    def _render(self, context, color, function):
        r, g, b = color
        context.set_source_rgb(r, g, b)
        
        context.translate(self.margin_x, self.margin_y)
        function()
        context.translate(-self.margin_x, -self.margin_y)
        
    def refresh_horizontal_line(self, drawing_area, y):
        self._refresh(drawing_area, self.grid.in_direction("across", 0, y))
        
    def refresh_vertical_line(self, drawing_area, x):
        self._refresh(drawing_area, self.grid.in_direction("down", x, 0))
        
    def refresh_location(self, drawing_area, x, y):
        self._refresh(drawing_area, [(x, y)])
        
    def _refresh(self, drawing_area, cells):
        for x, y in cells:
            rx = self.grid_to_screen_x(x)
            ry = self.grid_to_screen_y(y)
            drawing_area.queue_draw_area(rx, ry, self.tile_size, self.tile_size)
            
    # needs manual queue_draw() on drawing_area afterwards
    def update_visual_size(self, drawing_area):
        visual_width = self.visual_width()
        visual_height = self.visual_height()
        drawing_area.set_size_request(visual_width, visual_height)
            
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
            
    def visual_width(self, include_padding=True):
        if include_padding:
            return self.margin_x * 2 + self.get_grid_width()
        return self.get_grid_width()
        
    def visual_height(self, include_padding=True):
        if include_padding:
            return self.margin_y * 2 + self.get_grid_height()
        return self.get_grid_height()
            
    def get_grid_width(self):
        return self.grid.width * (self.tile_size + self.line_width) + self.line_width
        
    def get_grid_height(self):
        return self.grid.height * (self.tile_size + self.line_width) + self.line_width
