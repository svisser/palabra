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

class RenderTask:
    def __init__(self, context, grid):
        self.context = context
        self.grid = grid
        self.settings = {}
        
        # 0.5 for sharp lines
        self.origin_x = 0.5
        self.origin_y = 0.5
        self.tile_size = 32
        self.margin_x = 10
        self.margin_y = 10
        self.line_width = 1
        
        # excluding borders
        self.total_width = self.grid.width * (self.tile_size + self.line_width)
        self.total_height = self.grid.height * (self.tile_size + self.line_width)
        
    def grid_to_screen_x(self, x, include_padding=True):
        result = x * self.tile_size + (x + 1) * self.line_width
        if include_padding:
            result += self.margin_x
        return result
    
    def grid_to_screen_y(self, y, include_padding=True):
        result = y * self.tile_size + (y + 1) * self.line_width
        if include_padding:
            result += self.margin_y
        return result
        
class RenderHorizontalLine(RenderTask):
    def render(self):
        x, y = self.settings["location"]
        
        a = self.grid.in_direction("across", x, y)
        b = self.grid.in_direction("across", x, y, reverse=True)
        for p, q in chain(a, b):
            rx = self.grid_to_screen_x(p, False)
            ry = self.grid_to_screen_y(y, False)
            self.context.rectangle(rx, ry, self.tile_size, self.tile_size)
        self.context.fill()
        
class RenderVerticalLine(RenderTask):
    def render(self):
        x, y = self.settings["location"]
        
        a = self.grid.in_direction("down", x, y)
        b = self.grid.in_direction("down", x, y, reverse=True)
        for p, q in chain(a, b):
            rx = self.grid_to_screen_x(x, False)
            ry = self.grid_to_screen_y(q, False)
            self.context.rectangle(rx, ry, self.tile_size, self.tile_size)
        self.context.fill()
        
class RenderBlocks(RenderTask):
    def render(self):
        for x, y in self.grid.cells():
            if self.grid.is_block(x, y):
                # -0.5 for coordinates and +1 for size
                # are needed to render seamlessly in PDF
                rx = self.grid_to_screen_x(x, False) - 0.5
                ry = self.grid_to_screen_y(y, False) - 0.5
                self.context.rectangle(rx, ry, self.tile_size + 1, self.tile_size + 1)
        self.context.fill()
        
class RenderLines(RenderTask):
    def render(self):
        self.context.set_line_width(self.line_width)
        self.context.move_to(self.tile_size + 1.5 * self.line_width, self.line_width)
        for i in range(self.grid.width - 1):
            line_length = self.total_height
            self.context.rel_line_to(0, line_length)
            self.context.rel_move_to(self.tile_size + self.line_width, -line_length)
            
        self.context.move_to(self.line_width, self.tile_size + 1.5 * self.line_width)
        for j in range(self.grid.height - 1):
            line_length = self.total_width
            self.context.rel_line_to(line_length, 0)
            self.context.rel_move_to(-line_length, self.tile_size + self.line_width)
        self.context.stroke()
        
class RenderBorder(RenderTask):
    def render(self):
        self.context.set_line_width(self.line_width)
        x = 0.5 * self.line_width
        y = 0.5 * self.line_width
        self.context.rectangle(x, y, self.total_width, self.total_height)
        self.context.stroke()
        
class RenderPangoTask(RenderTask):
    def _render_pango(self, x, y, font, content):
        pcr = pangocairo.CairoContext(self.context)
        layout = pcr.create_layout()
        layout.set_markup('''<span font_desc="%s">%s</span>''' % (font, content))
        self.context.save()
        self.context.move_to(x, y)
        pcr.show_layout(layout)
        self.context.restore()
        
class RenderChars(RenderPangoTask):
    def render(self):
        for x, y in self.grid.cells():
            c = self.grid.get_char(x, y)
            if c != '':
                self._render_char(x, y, c)
                
    def _render_char(self, x, y, c):
        xbearing, ybearing, width, height, xadvance, yadvance = self.context.text_extents(c)
                    
        rx = (self.line_width +
            (x + 0.5) * (self.tile_size + self.line_width) -
            xbearing - (width / 2))
        ry = (self.line_width +
            (y + 0.25) * (self.tile_size + self.line_width))
        self._render_pango(rx, ry, "Sans 12", c)
        
class RenderNumbers(RenderPangoTask):
    def render(self):
        for n, x, y in self.grid.words():
            self._render_number(x, y, n)
            
    def _render_number(self, x, y, n):
        rx = self.grid_to_screen_x(x, False) + 1
        ry = self.grid_to_screen_y(y, False)
        self._render_pango(rx, ry, "Sans 7", str(n))

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
        task = RenderHorizontalLine(context, self.grid)
        task.settings = {"has_padding": True, "location": (x, y), "color": (r, g, b)}
        self._render(context, [(task.settings, task.render)])
        
    def render_vertical_line(self, context, x, y, r, g, b):
        task = RenderVerticalLine(context, self.grid)
        task.settings = {"has_padding": True, "location": (x, y), "color": (r, g, b)}
        self._render(context, [(task.settings, task.render)])
        
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
        
        # blocks
        task = RenderBlocks(context, self.grid)
        task.settings = {"has_padding": settings["has_padding"], "color": COLORS["block"]}
        self._render(context, [(task.settings, task.render)])
        
        # lines
        task = RenderLines(context, self.grid)
        task.settings = {"has_padding": settings["has_padding"], "color": COLORS["line"]}
        self._render(context, [(task.settings, task.render)])
        
        # border
        task = RenderBorder(context, self.grid)
        task.settings = {"has_padding": settings["has_padding"], "color": COLORS["border"]}
        self._render(context, [(task.settings, task.render)])
        
        # chars
        task = RenderChars(context, self.grid)
        task.settings = {"has_padding": settings["has_padding"], "color": COLORS["char"]}
        if settings["show_chars"]:
            self._render(context, [(task.settings, task.render)])
        
        # numbers
        task = RenderNumbers(context, self.grid)
        task.settings = {"has_padding": settings["has_padding"], "color": COLORS["number"]}
        if settings["show_numbers"]:
            self._render(context, [(task.settings, task.render)])
    
    def render_location(self, context, x, y, r, g, b):
        def render():
            # -0.5 for coordinates and +1 for size
            # are needed to render seamlessly in PDF
            rx = self.grid_to_screen_x(x, False) - 0.5
            ry = self.grid_to_screen_y(y, False) - 0.5
            context.rectangle(rx, ry, self.tile_size + 1, self.tile_size + 1)
            context.fill()
        settings = {"has_padding": True, "color": (r, g, b)}
        self._render(context, [(settings, render)])
    
    def render_background(self, context):
        def render():
            width = self.grid.width * (self.tile_size + self.line_width)
            height = self.grid.height * (self.tile_size + self.line_width)
            context.rectangle(self.line_width, self.line_width, width, height)
            context.fill()
        settings = {"has_padding": True, "color": COLORS["background"]}
        self._render(context, [(settings, render)])
        
    def _render(self, context, tasks):
        for settings, function in tasks:
            r, g, b = settings["color"]
            context.set_source_rgb(r, g, b)
            
            if settings["has_padding"]:
                context.translate(self.margin_x, self.margin_y)
            function()
            if settings["has_padding"]:
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
            left_x = self.grid_to_screen_x(x)
            right_x = self.grid_to_screen_x(x) + self.tile_size
            if screen_x >= left_x and screen_x < right_x:
                return x
        return -1
        
    def screen_to_grid_y(self, screen_y):
        for y in range(self.grid.height):
            top_y = self.grid_to_screen_y(y)
            bottom_y = self.grid_to_screen_y(y) + self.tile_size
            if screen_y >= top_y and screen_y < bottom_y:
                return y
        return -1
        
    def grid_to_screen_x(self, x, include_padding=True):
        result = x * self.tile_size + (x + 1) * self.line_width
        if include_padding:
            result += self.margin_x
        return result
    
    def grid_to_screen_y(self, y, include_padding=True):
        result = y * self.tile_size + (y + 1) * self.line_width
        if include_padding:
            result += self.margin_y
        return result
            
    def visual_width(self, include_padding=True):
        width = self.get_grid_width()
        if include_padding:
            width += (self.margin_x * 2)
        return width
        
    def visual_height(self, include_padding=True):
        height = self.get_grid_height()
        if include_padding:
            height += (self.margin_y * 2)
        return height
            
    def get_grid_width(self):
        return self.grid.width * (self.tile_size + self.line_width) + self.line_width
        
    def get_grid_height(self):
        return self.grid.height * (self.tile_size + self.line_width) + self.line_width
