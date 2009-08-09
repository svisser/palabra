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
    , "warn_consecutive_unchecked": False
    , "warn_unchecked_cells": False
    , "warn_two_letter_words": False
}
SETTINGS_EDITOR = {
    "has_padding": True
    , "show_chars": True
    , "show_numbers": False
    , "warn_consecutive_unchecked": True
    , "warn_unchecked_cells": True
    , "warn_two_letter_words": True
}
SETTINGS_EMPTY = {
    "has_padding": False
    , "show_chars": False
    , "show_numbers": True
    , "warn_consecutive_unchecked": False
    , "warn_unchecked_cells": False
    , "warn_two_letter_words": False
}
SETTINGS_SOLUTION = {
    "has_padding": False
    , "show_chars": True
    , "show_numbers": True
    , "warn_consecutive_unchecked": False
    , "warn_unchecked_cells": False
    , "warn_two_letter_words": False
}
custom_settings = {}

class GridViewProperties:
    def __init__(self, grid):
        self.grid = grid
        
        # 0.5 for sharp lines
        self.origin_x = 0.5
        self.origin_y = 0.5
        self.margin_x = 10
        self.margin_y = 10
        
        self.block = {}
        self.block["color"] = (0, 0, 0)
        self.block["margin"] = 0
        
        self.border = {}
        self.border["width"] = 1
        self.border["color"] = (0, 0, 0)
        
        self.cell = {}
        self.cell["color"] = (65535, 65535, 65535)
        self.cell["size"] = 32
        
        self.char = {}
        self.char["color"] = (0, 0, 0)
        self.char["font"] = "Sans 12"
        
        self.line = {}
        self.line["width"] = 1
        self.line["color"] = (0, 0, 0)
        
        self.number = {}
        self.number["color"] = (0, 0, 0)
        self.number["font"] = "Sans 7"
        
    def grid_to_screen_x(self, x, include_padding=True):
        result = self.border["width"] + x * (self.cell["size"] + self.line["width"])
        if include_padding:
            result += self.margin_x
        return result
        
    def grid_to_screen_y(self, y, include_padding=True):
        result = self.border["width"] + y * (self.cell["size"] + self.line["width"])
        if include_padding:
            result += self.margin_y
        return result
        
    def screen_to_grid_x(self, screen_x):
        for x in range(self.grid.width):
            left_x = self.grid_to_screen_x(x)
            right_x = self.grid_to_screen_x(x) + self.cell["size"]
            if screen_x >= left_x and screen_x < right_x:
                return x
        return -1
        
    def screen_to_grid_y(self, screen_y):
        for y in range(self.grid.height):
            top_y = self.grid_to_screen_y(y)
            bottom_y = self.grid_to_screen_y(y) + self.cell["size"]
            if screen_y >= top_y and screen_y < bottom_y:
                return y
        return -1
        
    def visual_width(self, include_padding=True):
        width = (2 * self.border["width"] + self.grid.width * self.cell["size"]
            + (self.grid.width - 1) * self.line["width"])
        if include_padding:
            width += (self.margin_x * 2)
        return width
    
    def visual_height(self, include_padding=True):
        height = (2 * self.border["width"] + self.grid.height * self.cell["size"]
            + (self.grid.height - 1) * self.line["width"])
        if include_padding:
            height += (self.margin_y * 2)
        return height
        
    def get_grid_width(self):
        return self.border["width"] + self.grid.width * (self.cell["size"] + self.line["width"])
        
    def get_grid_height(self):
        return self.border["width"] + self.grid.height * (self.cell["size"] + self.line["width"])

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
        
        if self.settings["show_chars"]:
            self.render_chars(context)

        if self.settings["show_numbers"]:
            self.render_numbers(context)
            
    def render_warnings(self, context, r, g, b):
        if self.settings["warn_unchecked_cells"]:
            self._render_unchecked_cell_warnings(context, r, g, b)
            
        if self.settings["warn_consecutive_unchecked"]:
            self._render_consecutive_unchecked_warnings(context, r, g, b)
        
        if self.settings["warn_two_letter_words"]:
            self._render_two_letter_warnings(context, r, g, b)
            
    def _render_consecutive_unchecked_warnings(self, context, r, g, b):
        def check_word(direction, x, y):
            cells = []
            for p, q in self.grid.in_direction(direction, x, y):
                if 0 <= self.grid.get_check_count(p, q) <= 1:
                    cells.append((p, q))
                else:
                    if len(cells) > 1:
                        for x, y in cells:
                            self.render_location(context, x, y, r, g, b)
                    cells = []
        
        for n, x, y in self.grid.horizontal_words():
            check_word("across", x, y)
        for n, x, y in self.grid.vertical_words():
            check_word("down", x, y)
            
    def _render_unchecked_cell_warnings(self, context, r, g, b):
        for x, y in self.grid.cells():
            if 0 <= self.grid.get_check_count(x, y) <= 1:
                self.render_location(context, x, y, r, g, b)
            
    def _render_two_letter_warnings(self, context, r, g, b):
        for n, x, y in self.grid.horizontal_words():
            if self.grid.word_length(x, y, "across") == 2:
                self.render_horizontal_line(context, x, y, r, g, b)
        for n, x, y in self.grid.vertical_words():
            if self.grid.word_length(x, y, "down") == 2:
                self.render_vertical_line(context, x, y, r, g, b)
        
    def render_blocks(self, context):
        def render(context, grid, props):
            for x, y in grid.cells():
                if grid.is_block(x, y):
                    rx = props.grid_to_screen_x(x, False)
                    ry = props.grid_to_screen_y(y, False)
                    rwidth = props.cell["size"]
                    rheight = props.cell["size"]
                    
                    if props.block["margin"] == 0:
                        # -0.5 for coordinates and +1 for size
                        # are needed to render seamlessly in PDF
                        rx -= 0.5
                        ry -= 0.5
                        rwidth += 1
                        rheight += 1
                    else:
                        rx += props.block["margin"]
                        ry += props.block["margin"]
                        rwidth -= (2 * props.block["margin"])
                        rheight -= (2 * props.block["margin"])
                    context.rectangle(rx, ry, rwidth, rheight)
            context.fill()
        color = map(lambda x: x / 65535.0, self.properties.block["color"])
        self._render(context, render, color=color)
        
    def render_lines(self, context):
        def render(context, grid, props):
            context.set_line_width(props.line["width"])
            
            sx = props.border["width"] + props.cell["size"] + 0.5 * props.line["width"]
            sy = props.border["width"]
            line_length = props.get_grid_height() - props.line["width"]
            context.move_to(sx, sy)
            for i in range(grid.width - 1):
                context.rel_line_to(0, line_length)
                context.rel_move_to(props.cell["size"] + props.line["width"], -line_length)
                
            sx = props.border["width"]
            sy = props.border["width"] + props.cell["size"] + 0.5 * props.line["width"]
            line_length = props.get_grid_width() - props.line["width"]
            context.move_to(sx, sy)
            for j in range(grid.height - 1):
                context.rel_line_to(line_length, 0)
                context.rel_move_to(-line_length, props.cell["size"] + props.line["width"])
            context.stroke()
        color = map(lambda x: x / 65535.0, self.properties.line["color"])
        self._render(context, render, color=color)
        
    def render_border(self, context):
        def render(context, grid, props):
            context.set_line_width(props.border["width"])
            x = 0.5 * props.border["width"]
            y = 0.5 * props.border["width"]
            width = props.get_grid_width() - props.line["width"]
            height = props.get_grid_height() - props.line["width"]
            context.rectangle(x, y, width, height)
            context.stroke()
        color = map(lambda x: x / 65535.0, self.properties.border["color"])
        self._render(context, render, color=color)
        
    def render_horizontal_line(self, context, x, y, r, g, b):
        def render(context, grid, props):
            a = grid.in_direction("across", x, y)
            b = grid.in_direction("across", x, y, reverse=True)
            for p, q in chain(a, b):
                rx = props.grid_to_screen_x(p, False)
                ry = props.grid_to_screen_y(y, False)
                context.rectangle(rx, ry, props.cell["size"], props.cell["size"])
            context.fill()
        self._render(context, render, color=(r, g, b))
        
    def render_vertical_line(self, context, x, y, r, g, b):
        def render(context, grid, props):
            a = grid.in_direction("down", x, y)
            b = grid.in_direction("down", x, y, reverse=True)
            for p, q in chain(a, b):
                rx = props.grid_to_screen_x(x, False)
                ry = props.grid_to_screen_y(q, False)
                context.rectangle(rx, ry, props.cell["size"], props.cell["size"])
            context.fill()
        self._render(context, render, color=(r, g, b))
        
    def render_chars(self, context):
        def render(context, grid, props):
            for x, y in grid.cells():
                c = grid.get_char(x, y)
                if c != '':
                    self._render_char(context, props, x, y, c)
        color = map(lambda x: x / 65535.0, self.properties.char["color"])
        self._render(context, render, color=color)
        
    def render_numbers(self, context):
        def render(context, grid, props):
            for n, x, y in grid.words(False):
                self._render_number(context, props, x, y, n)
        color = map(lambda x: x / 65535.0, self.properties.number["color"])
        self._render(context, render, color=color)
    
    def render_location(self, context, x, y, r, g, b):
        def render(context, grid, props):
            # -0.5 for coordinates and +1 for size
            # are needed to render seamlessly in PDF
            rx = props.grid_to_screen_x(x, False) - 0.5
            ry = props.grid_to_screen_y(y, False) - 0.5
            context.rectangle(rx, ry, props.cell["size"] + 1, props.cell["size"] + 1)
            context.fill()
        self._render(context, render, color=(r, g, b))
    
    def render_background(self, context):
        def render(context, grid, props):
            x = props.border["width"]
            y = props.border["width"]
            width = props.get_grid_width() - props.line["width"]
            height = props.get_grid_height() - props.line["width"]
            context.rectangle(x, y, width, height)
            context.fill()
        color = map(lambda x: x / 65535.0, self.properties.cell["color"])
        self._render(context, render, color=color)
        
    def _render_pango(self, context, x, y, font, content):
        pcr = pangocairo.CairoContext(context)
        layout = pcr.create_layout()
        layout.set_markup('''<span font_desc="%s">%s</span>''' % (font, content))
        context.save()
        context.move_to(x, y)
        pcr.show_layout(layout)
        context.restore()
        
    def _render_char(self, context, props, x, y, c):
        xbearing, ybearing, width, height, xadvance, yadvance = context.text_extents(c)
                    
        rx = (props.border["width"] +
            (x + 0.55) * (props.cell["size"] + props.line["width"]) -
            width - props.line["width"] / 2 - abs(xbearing) / 2)
        ry = (props.border["width"] +
            (y + 0.55) * (props.cell["size"] + props.line["width"]) -
            height - props.line["width"] / 2 - abs(ybearing) / 2)
        self._render_pango(context, rx, ry, props.char["font"], c)
        
    def _render_number(self, context, props, x, y, n):
        rx = props.grid_to_screen_x(x, False) + 1
        ry = props.grid_to_screen_y(y, False)
        self._render_pango(context, rx, ry, props.number["font"], str(n))
            
    def _render(self, context, render, **args):
        r, g, b = args["color"]
        context.set_source_rgb(r, g, b)
        
        if self.settings["has_padding"]:
            context.translate(self.properties.margin_x, self.properties.margin_y)
        
        render(context, self.grid, self.properties)
        
        if self.settings["has_padding"]:
            context.translate(-self.properties.margin_x, -self.properties.margin_y)
        
    def refresh_horizontal_line(self, drawing_area, y):
        self._refresh(drawing_area, [(x, y) for x in xrange(self.grid.width)])
        
    def refresh_vertical_line(self, drawing_area, x):
        self._refresh(drawing_area, [(x, y) for y in xrange(self.grid.height)])
        
    def refresh_location(self, drawing_area, x, y):
        self._refresh(drawing_area, [(x, y)])
        
    def _refresh(self, drawing_area, cells):
        for x, y in cells:
            rx = self.properties.grid_to_screen_x(x)
            ry = self.properties.grid_to_screen_y(y)
            size = self.properties.cell["size"]
            drawing_area.queue_draw_area(rx, ry, size, size)
            
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
