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

class GridViewProperties:
    def __init__(self, grid):
        self.grid = grid
        
        # 0.5 for sharp lines
        self.origin_x = 0.5
        self.origin_y = 0.5
        self.tile_size = 32
        self.margin_x = 10
        self.margin_y = 10
        self.line_width = 1
        
        self.appearance = {}
        self.appearance["colors"] = {
            "background": (1, 1, 1)
            , "border": (0, 0, 0)
            , "block": (0, 0, 0)
            , "line": (0, 0, 0)
            , "char": (0, 0, 0)
            , "number": (0, 0, 0)
        }
        
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

class GridView:
    def __init__(self, grid):
        self.grid = grid
        self.properties = GridViewProperties(self.grid)
        self.select_mode(constants.VIEW_MODE_EDITOR)
        
    def select_mode(self, mode):
        self.settings = {}
        if mode == constants.VIEW_MODE_EDITOR:
            self.settings.update(SETTINGS_EDITOR)
            self.settings.update(custom_settings)
        elif mode == constants.VIEW_MODE_EMPTY:
            self.settings.update(SETTINGS_EMPTY)
        elif mode == constants.VIEW_MODE_PREVIEW:
            self.settings.update(SETTINGS_PREVIEW)
        elif mode == constants.VIEW_MODE_SOLUTION:
            self.settings.update(SETTINGS_SOLUTION)
        
    def render(self, context, mode=constants.VIEW_MODE_EDITOR):
        self.select_mode(mode)
            
        self.render_blocks(context)
        self.render_lines(context)
        self.render_border(context)
        
        # chars
        if self.settings["show_chars"]:
            self.render_chars(context)

        # numbers
        if self.settings["show_numbers"]:
            self.render_numbers(context)
        
    def render_blocks(self, context):
        def render(context, grid, settings):
            for x, y in grid.cells():
                if grid.is_block(x, y):
                    # -0.5 for coordinates and +1 for size
                    # are needed to render seamlessly in PDF
                    rx = settings.grid_to_screen_x(x, False) - 0.5
                    ry = settings.grid_to_screen_y(y, False) - 0.5
                    context.rectangle(rx, ry, settings.tile_size + 1, settings.tile_size + 1)
            context.fill()
        color = self.properties.appearance["colors"]["block"]
        self._render(context, render, color=color)
        
    def render_lines(self, context):
        def render(context, grid, settings):
            context.set_line_width(settings.line_width)
            context.move_to(settings.tile_size + 1.5 * settings.line_width, settings.line_width)
            for i in range(grid.width - 1):
                line_length = settings.get_grid_height() - settings.line_width
                context.rel_line_to(0, line_length)
                context.rel_move_to(settings.tile_size + settings.line_width, -line_length)
                
            context.move_to(settings.line_width, settings.tile_size + 1.5 * settings.line_width)
            for j in range(grid.height - 1):
                line_length = settings.get_grid_width() - settings.line_width
                context.rel_line_to(line_length, 0)
                context.rel_move_to(-line_length, settings.tile_size + settings.line_width)
            context.stroke()
        color = self.properties.appearance["colors"]["line"]
        self._render(context, render, color=color)
        
    def render_border(self, context):
        def render(context, grid, settings):
            context.set_line_width(settings.line_width)
            x = 0.5 * settings.line_width
            y = 0.5 * settings.line_width
            width = settings.get_grid_width() - settings.line_width
            height = settings.get_grid_height() - settings.line_width
            context.rectangle(x, y, width, height)
            context.stroke()
        color = self.properties.appearance["colors"]["border"]
        self._render(context, render, color=color)
        
    def render_horizontal_line(self, context, x, y, r, g, b):
        def render(context, grid, props):
            a = grid.in_direction("across", x, y)
            b = grid.in_direction("across", x, y, reverse=True)
            for p, q in chain(a, b):
                rx = props.grid_to_screen_x(p, False)
                ry = props.grid_to_screen_y(y, False)
                context.rectangle(rx, ry, props.tile_size, props.tile_size)
            context.fill()
        self._render(context, render, color=(r, g, b))
        
    def render_vertical_line(self, context, x, y, r, g, b):
        def render(context, grid, props):
            a = grid.in_direction("down", x, y)
            b = grid.in_direction("down", x, y, reverse=True)
            for p, q in chain(a, b):
                rx = props.grid_to_screen_x(x, False)
                ry = props.grid_to_screen_y(q, False)
                context.rectangle(rx, ry, props.tile_size, props.tile_size)
            context.fill()
        self._render(context, render, color=(r, g, b))
        
    def render_chars(self, context):
        def render(context, grid, settings):
            for x, y in grid.cells():
                c = grid.get_char(x, y)
                if c != '':
                    self._render_char(context, settings, x, y, c)
        color = self.properties.appearance["colors"]["char"]
        self._render(context, render, color=color)
        
    def render_numbers(self, context):
        def render(context, grid, settings):
            for n, x, y in grid.words():
                self._render_number(context, settings, x, y, n)
        color = self.properties.appearance["colors"]["number"]
        self._render(context, render, color=color)
    
    def render_location(self, context, x, y, r, g, b):
        def render(context, grid, settings):
            # -0.5 for coordinates and +1 for size
            # are needed to render seamlessly in PDF
            rx = settings.grid_to_screen_x(x, False) - 0.5
            ry = settings.grid_to_screen_y(y, False) - 0.5
            context.rectangle(rx, ry, settings.tile_size + 1, settings.tile_size + 1)
            context.fill()
        self._render(context, render, color=(r, g, b))
    
    def render_background(self, context):
        def render(context, grid, settings):
            width = grid.width * (settings.tile_size + settings.line_width)
            height = grid.height * (settings.tile_size + settings.line_width)
            context.rectangle(settings.line_width, settings.line_width, width, height)
            context.fill()
        color = self.properties.appearance["colors"]["background"]
        self._render(context, render, color=color)
        
    def _render_pango(self, context, x, y, font, content):
        pcr = pangocairo.CairoContext(context)
        layout = pcr.create_layout()
        layout.set_markup('''<span font_desc="%s">%s</span>''' % (font, content))
        context.save()
        context.move_to(x, y)
        pcr.show_layout(layout)
        context.restore()
        
    def _render_char(self, context, settings, x, y, c):
        xbearing, ybearing, width, height, xadvance, yadvance = context.text_extents(c)
                    
        rx = (settings.line_width +
            (x + 0.55) * (settings.tile_size + settings.line_width) -
            width - settings.line_width / 2 - abs(xbearing) / 2)
        ry = (settings.line_width +
            (y + 0.55) * (settings.tile_size + settings.line_width) -
            height - settings.line_width / 2 - abs(ybearing) / 2)
        self._render_pango(context, rx, ry, "Sans 12", c)
        
    def _render_number(self, context, settings, x, y, n):
        rx = settings.grid_to_screen_x(x, False) + 1
        ry = settings.grid_to_screen_y(y, False)
        self._render_pango(context, rx, ry, "Sans 7", str(n))
            
    def _render(self, context, render, **args):
        r, g, b = args["color"]
        context.set_source_rgb(r, g, b)
        
        if self.settings["has_padding"]:
            context.translate(self.properties.margin_x, self.properties.margin_y)
        
        render(context, self.grid, self.properties)
        
        if self.settings["has_padding"]:
            context.translate(-self.properties.margin_x, -self.properties.margin_y)
        
    def refresh_horizontal_line(self, drawing_area, y):
        self._refresh(drawing_area, self.grid.in_direction("across", 0, y))
        
    def refresh_vertical_line(self, drawing_area, x):
        self._refresh(drawing_area, self.grid.in_direction("down", x, 0))
        
    def refresh_location(self, drawing_area, x, y):
        self._refresh(drawing_area, [(x, y)])
        
    def _refresh(self, drawing_area, cells):
        for x, y in cells:
            rx = self.properties.grid_to_screen_x(x)
            ry = self.properties.grid_to_screen_y(y)
            drawing_area.queue_draw_area(rx, ry, self.properties.tile_size, self.properties.tile_size)
            
    # needs manual queue_draw() on drawing_area afterwards
    def update_visual_size(self, drawing_area):
        visual_width = self.visual_width()
        visual_height = self.visual_height()
        drawing_area.set_size_request(visual_width, visual_height)
            
    def screen_to_grid_x(self, screen_x):
        return self.properties.screen_to_grid_x(screen_x)
        
    def screen_to_grid_y(self, screen_y):
        return self.properties.screen_to_grid_y(screen_y)
        
    def grid_to_screen_x(self, x, include_padding=True):
        return self.properties.grid_to_screen_x(x, include_padding)
    
    def grid_to_screen_y(self, y, include_padding=True):
        return self.properties.grid_to_screen_y(y, include_padding)
            
    def visual_width(self, include_padding=True):
        return self.properties.visual_width(include_padding)
        
    def visual_height(self, include_padding=True):
        return self.properties.visual_height(include_padding)
            
    def get_grid_width(self):
        return self.properties.get_grid_width()
        
    def get_grid_height(self):
        return self.properties.get_grid_height()
