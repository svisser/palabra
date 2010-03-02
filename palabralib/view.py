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
import gtk
from itertools import *
import math
import pango
import pangocairo

import constants

SETTINGS_PREVIEW = {
    "has_padding": True
    , "show_chars": False
    , "show_numbers": False
    , "render_overlays": False
    , "warn_consecutive_unchecked": False
    , "warn_unchecked_cells": False
    , "warn_two_letter_words": False
    , "warn_blacklist": False
}
SETTINGS_EDITOR = {
    "has_padding": True
    , "show_chars": True
    , "show_numbers": False
    , "render_overlays": True
    , "warn_consecutive_unchecked": True
    , "warn_unchecked_cells": True
    , "warn_two_letter_words": True
    , "warn_blacklist": True
}
SETTINGS_EMPTY = {
    "has_padding": False
    , "show_chars": False
    , "show_numbers": True
    , "render_overlays": False
    , "warn_consecutive_unchecked": False
    , "warn_unchecked_cells": False
    , "warn_two_letter_words": False
    , "warn_blacklist": False
}
SETTINGS_SOLUTION = {
    "has_padding": False
    , "show_chars": True
    , "show_numbers": True
    , "render_overlays": False
    , "warn_consecutive_unchecked": False
    , "warn_unchecked_cells": False
    , "warn_two_letter_words": False
    , "warn_blacklist": False
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
        
        self.bar = {}
        self.bar["width"] = 5
        
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
    
    def apply_appearance(self, appearance):
        cell_color = appearance["cell"]["color"]
        cell_red = cell_color.red
        cell_green = cell_color.green
        cell_blue = cell_color.blue
        
        line_color = appearance["line"]["color"]
        line_red = line_color.red
        line_green = line_color.green
        line_blue = line_color.blue
        
        border_color = appearance["border"]["color"]
        border_red = border_color.red
        border_green = border_color.green
        border_blue = border_color.blue
        
        block_color = appearance["block"]["color"]
        block_red = block_color.red
        block_green = block_color.green
        block_blue = block_color.blue
        
        char_color = appearance["char"]["color"]
        char_red = char_color.red
        char_green = char_color.green
        char_blue = char_color.blue
        
        number_color = appearance["number"]["color"]
        number_red = number_color.red
        number_green = number_color.green
        number_blue = number_color.blue
        
        self.block["color"] = (block_red, block_green, block_blue)
        self.border["color"] = (border_red, border_green, border_blue)
        self.char["color"] = (char_red, char_green, char_blue)
        self.cell["color"] = (cell_red, cell_green, cell_blue)
        self.line["color"] = (line_red, line_green, line_blue)
        self.number["color"] = (number_red, number_green, number_blue)
        
        self.border["width"] = appearance["border"]["width"]
        self.line["width"] = appearance["line"]["width"]
        self.block["margin"] = appearance["block"]["margin"]
        self.cell["size"] = appearance["cell"]["size"]
    
    def grid_to_screen_x(self, x, include_padding=True):
        """Return the x-coordinate of the cell's upper-left corner."""
        result = self.border["width"] + x * (self.cell["size"] + self.line["width"])
        if include_padding:
            result += self.margin_x
        return result
        
    def grid_to_screen_y(self, y, include_padding=True):
        """Return the y-coordinate of the cell's upper-left corner."""
        result = self.border["width"] + y * (self.cell["size"] + self.line["width"])
        if include_padding:
            result += self.margin_y
        return result
        
    def screen_to_grid_x(self, screen_x):
        """
        Return the x-coordinate of the cell based on the x-coordinate on screen.
        """
        for x in range(self.grid.width):
            left_x = self.grid_to_screen_x(x)
            right_x = self.grid_to_screen_x(x) + self.cell["size"]
            if screen_x >= left_x and screen_x < right_x:
                return x
        return -1
        
    def screen_to_grid_y(self, screen_y):
        """
        Return the y-coordinate of the cell based on the y-coordinate on screen.
        """
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
        """Return the width of the grid."""
        w = 2 * self.border["width"]
        w += self.grid.width * self.cell["size"]
        w += (self.grid.width - 1) * self.line["width"]
        return w
        
    def get_grid_height(self):
        """Return the height of the grid."""
        h = 2 * self.border["width"]
        h += self.grid.height * self.cell["size"]
        h += (self.grid.height - 1) * self.line["width"]
        return h

class GridView:
    def __init__(self, grid):
        self.grid = grid
        self.properties = GridViewProperties(self.grid)
        self.select_mode(constants.VIEW_MODE_EDITOR)
        
        self.overlay = []
        
    def select_mode(self, mode):
        """Select the render mode for future render calls."""
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
        
    def render(self, context, area, mode=None):
        """
        Render the grid in the current render mode.
        
        The current render mode can be specified as argument
        or it has been specified earlier by a select_mode call.
        """
        if mode is not None:
            self.select_mode(mode)
            
        self.render_blocks(context, area)
        self.render_lines(context, area)
        
        if self.settings["show_chars"]:
            self.render_chars(context, area)

        if self.settings["show_numbers"]:
            self.render_numbers(context, area)
            
        if self.settings["render_overlays"]:
            self.render_overlay_chars(context, area)

    def render_bottom(self, context, x, y):
        # background
        def render(context, grid, props):
            bx = props.grid_to_screen_x(x, False)
            by = props.grid_to_screen_y(y, False)
            bsize = props.cell["size"]
            i = gtk.gdk.Rectangle(bx, by, bsize, bsize)
            
            # -0.5 for coordinates and +1 for size
            # are needed to render seamlessly in PDF
            context.rectangle(i.x - 0.5, i.y - 0.5, i.width + 1, i.height + 1)
            context.fill()
        r, g, b = map(lambda x: x / 65535.0, self.properties.cell["color"])
        self._render(context, render, color=(r, g, b))
        
    def render_top(self, context, x, y):
        # char
        def render(context, grid, props):
            c = grid.get_char(x, y)
            if c != '':
                self._render_char(context, props, x, y, c)
        color = map(lambda x: x / 65535.0, self.properties.char["color"])
        self._render(context, render, color=color)
        
        # overlay char
        def render(context, grid, props):
            for p, q, c in self.overlay:
                if (x, y) == (p, q):
                    self._render_char(context, props, x, y, c)
        color = map(lambda x: x / 65535.0, (65535.0 / 2, 65535.0 / 2, 65535.0 / 2))
        if self.settings["render_overlays"]:
            self._render(context, render, color=color)
        
        # block
        def render(context, grid, props):
            if grid.is_block(x, y):
                rx = props.grid_to_screen_x(x, False)
                ry = props.grid_to_screen_y(y, False)
                rwidth = props.cell["size"]
                rheight = props.cell["size"]
                
                if props.block["margin"] != 0:
                    offset = int((props.block["margin"] / 100.0) * props.cell["size"])
                    rx += offset
                    ry += offset
                    rwidth -= (2 * offset)
                    rheight -= (2 * offset)
                
                i = gtk.gdk.Rectangle(rx, ry, rwidth, rheight)
                if props.block["margin"] == 0:
                    # -0.5 for coordinates and +1 for size
                    # are needed to render seamlessly in PDF
                    context.rectangle(i.x - 0.5, i.y - 0.5, i.width + 1, i.height + 1)
                else:                
                    context.rectangle(i.x, i.y, i.width, i.height)
            context.fill()
        color = map(lambda x: x / 65535.0, self.properties.block["color"])
        self._render(context, render, color=color)
        
        self.render_all_lines_of_cell(context, x, y)
            
        # number
        # TODO slow
        #def render(context, grid, props):
        #    for n, p, q in grid.words(False):
        #        if (x, y) == (p, q):
        #            self._render_number(context, props, x, y, n)
        #color = map(lambda x: x / 65535.0, self.properties.number["color"])
        #if self.settings["show_numbers"]:
        #    self._render(context, render, color=color)
        
    def render_lines_of_cell(self, context, x, y):
        # lines
        """Render the internal lines of the grid (i.e., all lines except the border)."""
        def render_line(context, props, rx, ry, rdx, rdy, bar, border):
            if bar:
                context.set_line_width(props.bar["width"])
            if border:
                r, g, b = map(lambda x: x / 65535.0, props.border["color"])
                context.set_source_rgb(r, g, b)
            context.move_to(rx, ry)
            context.rel_line_to(rdx, rdy)
            context.stroke()
            if bar:
                context.set_line_width(props.line["width"])
            if border:
                r, g, b = map(lambda x: x / 65535.0, props.line["color"])
                context.set_source_rgb(r, g, b)
                
        def get_adjustments(lines, props, x, y):
            def get_delta(x, y, side_no_extend, side_extend):
                """
                Determine the delta in pixels.
                The delta is at least the normal line width.
                """
                if ((x, y, "left", side_no_extend) in lines
                    or (x, y - 1, "left", side_no_extend) in lines):
                    return props.line["width"]
                elems = [(x, y, "left", "normal"), (x, y - 1, "left", "normal")]
                if True in map(lambda e: e in lines, elems):
                    return props.line["width"]
                elems = [(x, y, "left", side_extend), (x, y - 1, "left", side_extend)]
                if True in map(lambda e: e in lines, elems):
                    return props.border["width"]
                return 0
            dx_left = get_delta(x, y, "innerborder", "outerborder")
            dx_right = get_delta(x + 1, y, "outerborder", "innerborder")
            return (dx_left, dx_right)
        
        def render(context, grid, props):
            context.set_line_width(props.line["width"])
            
            lines = grid.lines_of_cell(x, y)
            for p, q, ltype, side in lines:
                sx = props.grid_to_screen_x(p, False)
                sy = props.grid_to_screen_y(q, False)
                
                bar = grid.is_valid(x, y) and grid.has_bar(x, y, ltype)
                border = "border" in side
                if ltype == "top":
                    rx = sx
                    if side == "normal":
                        context.set_line_width(props.line["width"])
                        ry = sy - 0.5 * props.line["width"]
                        rdx = props.cell["size"]
                    elif border:
                        context.set_line_width(props.border["width"])
                        if side == "outerborder":
                            ry = sy - 0.5 * props.border["width"]
                        elif side == "innerborder":
                            ry = sy + 0.5 * props.border["width"]
                            if not grid.is_available(x, y + 1):
                                ry -= props.line["width"]
                        rdx = props.cell["size"]
                        
                    # adjust horizontal lines to fill empty spaces in corners
                    dxl, dxr = get_adjustments(lines, props, x, y)
                    rx -= dxl
                    rdx += dxl
                    rdx += dxr
                        
                    render_line(context, props, rx, ry, rdx, 0, bar, border)
                elif ltype == "left":
                    if side == "normal":
                        context.set_line_width(props.line["width"])
                        rx = sx - 0.5 * props.line["width"]
                        rdy = props.cell["size"]
                        
                    elif border:
                        context.set_line_width(props.border["width"])
                        if side == "outerborder":
                            rx = sx - 0.5 * props.border["width"]
                        elif side == "innerborder":
                            rx = sx + 0.5 * props.border["width"]
                            if not grid.is_available(x + 1, y):
                                rx -= props.line["width"]
                        rdy = props.cell["size"]
                    render_line(context, props, rx, sy, 0, rdy, bar, border)
        color = map(lambda x: x / 65535.0, self.properties.line["color"])
        self._render(context, render, color=color)
            
    def render_blacklist(self, context, area, r, g, b, blacklist):
        """Render blacklisted words in the specified color."""
        if not self.settings["warn_blacklist"]:
            return
        def gather_segments(word, sx, sy, direction):
            segments = []
            segment = {"word": "", "cells": []}
            dx = 1 if direction == "across" else 0
            dy = 1 if direction == "down" else 0
            for i, c in enumerate(word):
                if c != "?":
                    p = sx + i * dx
                    q = sy + i * dy
                    segment["word"] = segment["word"] + c
                    segment["cells"] = segment["cells"] + [(p, q)]
                else:
                    if len(segment["cells"]):
                        segments.append(segment)
                    segment = {"word": "", "cells": []}
            if len(segment["cells"]):
                segments.append(segment)
            return segments
        def check_word(x, y, direction):
            sx, sy = self.grid.get_start_word(x, y, direction)
            word = self.grid.gather_word(x, y, direction, "?")
            segments = gather_segments(word, sx, sy, direction)
            cells = []
            for s in segments:
                word = "".join(map(lambda c: c.lower(), s["word"]))
                badwords = blacklist.get_substring_matches(word)
                for i in xrange(len(word)):
                    for bad in badwords:
                        if word[i:i + len(bad)] == bad:
                            cells += s["cells"][i:i + len(bad)]
            return cells                    
        a = []
        d = []
        for n, x, y in self.grid.horizontal_words():
            a += check_word(x, y, "across")
        for n, x, y in self.grid.vertical_words():
            d += check_word(x, y, "down")
        for x, y in a:
            self.render_location(context, area, x, y, r, g, b)
        for x, y in d:
            self.render_location(context, area, x, y, r, g, b)
            
    def render_warnings(self, context, area, r, g, b):
        """Render undesired cells in the specified color."""
        if self.settings["warn_unchecked_cells"]:
            self._render_unchecked_cell_warnings(context, area, r, g, b)
            
        if self.settings["warn_consecutive_unchecked"]:
            self._render_consecutive_unchecked_warnings(context, area, r, g, b)
        
        if self.settings["warn_two_letter_words"]:
            self._render_two_letter_warnings(context, area, r, g, b)
            
    def _render_consecutive_unchecked_warnings(self, context, area, r, g, b):
        """Color consecutive (two or more) unchecked cells."""
        checks = {}
        for x, y in self.grid.cells():
            checks[x, y] = self.grid.get_check_count(x, y)
        def is_consecutive_unchecked(x, y):
            if checks[x, y] < 0 or checks[x, y] > 1:
                return False
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                if (x + dx, y + dy) in checks and 0 <= checks[x + dx, y + dy] <= 1:
                    return True
        cells = filter(lambda p: is_consecutive_unchecked(*p), self.grid.cells())
        for x, y in cells:
            self.render_location(context, area, x, y, r, g, b)
            
    def _render_unchecked_cell_warnings(self, context, area, r, g, b):
        """Color cells that are unchecked. Isolated cells are also colored."""
        for x, y in self.grid.cells():
            if 0 <= self.grid.get_check_count(x, y) <= 1:
                self.render_location(context, area, x, y, r, g, b)
            
    def _render_two_letter_warnings(self, context, area, r, g, b):
        """Color words with length two."""
        for n, x, y in self.grid.horizontal_words():
            if self.grid.word_length(x, y, "across") == 2:
                #self.render_horizontal_line(context, area, x, y, r, g, b)
                self.render_line(context, None, x, y, "across", r, g, b)
        for n, x, y in self.grid.vertical_words():
            if self.grid.word_length(x, y, "down") == 2:
                self.render_line(context, None, x, y, "down", r, g, b)
                #self.render_vertical_line(context, area, x, y, r, g, b)
        
    def render_blocks(self, context, area):
        """Render all blocks of the grid."""
        def render(context, grid, props):
            for x, y in grid.cells():
                if grid.is_block(x, y):
                    rx = props.grid_to_screen_x(x, False)
                    ry = props.grid_to_screen_y(y, False)
                    rwidth = props.cell["size"]
                    rheight = props.cell["size"]
                    
                    if props.block["margin"] != 0:
                        offset = int((props.block["margin"] / 100.0) * props.cell["size"])
                        rx += offset
                        ry += offset
                        rwidth -= (2 * offset)
                        rheight -= (2 * offset)
                    
                    i = gtk.gdk.Rectangle(rx, ry, rwidth, rheight)
                    if props.block["margin"] == 0:
                        # -0.5 for coordinates and +1 for size
                        # are needed to render seamlessly in PDF
                        context.rectangle(i.x - 0.5, i.y - 0.5, i.width + 1, i.height + 1)
                    else:                
                        context.rectangle(i.x, i.y, i.width, i.height)
            context.fill()
        color = map(lambda x: x / 65535.0, self.properties.block["color"])
        self._render(context, render, color=color)
        
    def render_lines(self, context, area):
        """Render the internal lines of the grid (i.e., all lines except the border)."""
        def render_line(context, props, rx, ry, rdx, rdy, bar, border):
            if bar:
                context.set_line_width(props.bar["width"])
            if border:
                r, g, b = map(lambda x: x / 65535.0, props.border["color"])
                context.set_source_rgb(r, g, b)
            context.move_to(rx, ry)
            context.rel_line_to(rdx, rdy)
            context.stroke()
            if bar:
                context.set_line_width(props.line["width"])
            if border:
                r, g, b = map(lambda x: x / 65535.0, props.line["color"])
                context.set_source_rgb(r, g, b)
                
        def get_adjustments(lines, props, x, y):
            def get_delta(x, y, side_no_extend, side_extend):
                """
                Determine the delta in pixels.
                The delta is at least the normal line width.
                """
                if ((x, y, "left", side_no_extend) in lines
                    or (x, y - 1, "left", side_no_extend) in lines):
                    return props.line["width"]
                elems = [(x, y, "left", "normal"), (x, y - 1, "left", "normal")]
                if True in map(lambda e: e in lines, elems):
                    return props.line["width"]
                elems = [(x, y, "left", side_extend), (x, y - 1, "left", side_extend)]
                if True in map(lambda e: e in lines, elems):
                    return props.border["width"]
                return 0
            dx_left = get_delta(x, y, "innerborder", "outerborder")
            dx_right = get_delta(x + 1, y, "outerborder", "innerborder")
            return (dx_left, dx_right)
        
        def render(context, grid, props):
            context.set_line_width(props.line["width"])
            
            lines = grid.lines()
            for x, y, ltype, side in lines:
                sx = props.grid_to_screen_x(x, False)
                sy = props.grid_to_screen_y(y, False)
                
                # overestimate to accommodate for cells that are near the border of the puzzle
                bx = sx - props.line["width"] - props.border["width"]
                by = sy - props.line["width"] - props.border["width"]
                bsize = props.cell["size"] + 2 * props.border["width"] + 2 * props.line["width"]
                
                i = gtk.gdk.Rectangle(bx, by, bsize, bsize)
                
                # only render when cell intersects the specified area
                bar = grid.is_valid(x, y) and grid.has_bar(x, y, ltype)
                border = "border" in side
                if ltype == "top":
                    rx = sx
                    if side == "normal":
                        context.set_line_width(props.line["width"])
                        ry = sy - 0.5 * props.line["width"]
                        rdx = props.cell["size"]
                    elif border:
                        context.set_line_width(props.border["width"])
                        if side == "outerborder":
                            ry = sy - 0.5 * props.border["width"]
                        elif side == "innerborder":
                            ry = sy + 0.5 * props.border["width"]
                            if not grid.is_available(x, y):
                                ry -= props.line["width"]
                        rdx = props.cell["size"]
                        
                    # adjust horizontal lines to fill empty spaces in corners
                    dxl, dxr = get_adjustments(lines, props, x, y)
                    rx -= dxl
                    rdx += dxl
                    rdx += dxr
                        
                    render_line(context, props, rx, ry, rdx, 0, bar, border)
                elif ltype == "left":
                    if side == "normal":
                        context.set_line_width(props.line["width"])
                        rx = sx - 0.5 * props.line["width"]
                        rdy = props.cell["size"]
                        
                    elif border:
                        context.set_line_width(props.border["width"])
                        if side == "outerborder":
                            rx = sx - 0.5 * props.border["width"]
                        elif side == "innerborder":
                            rx = sx + 0.5 * props.border["width"]
                            if not grid.is_available(x, y):
                                rx -= props.line["width"]
                        rdy = props.cell["size"]
                    render_line(context, props, rx, sy, 0, rdy, bar, border)
        color = map(lambda x: x / 65535.0, self.properties.line["color"])
        self._render(context, render, color=color)
        
    def render_line(self, context, area, x, y, direction, r, g, b):
        """Render a sequence of cells."""
        v0 = self.grid.in_direction(direction, x, y)
        v1 = self.grid.in_direction(direction, x, y, reverse=True)
        for p, q in chain(v0, v1):
            self.render_location(context, area, p, q, r, g, b)
            self.render_char(context, p, q)
        
    def render_chars(self, context, area):
        """Render the letters of the grid."""
        def render(context, grid, props):
            for x, y in grid.cells():
                c = grid.get_char(x, y)
                if c != '':
                    self._render_char(context, props, x, y, c)
        color = map(lambda x: x / 65535.0, self.properties.char["color"])
        self._render(context, render, color=color)          
        
    def render_overlay_chars(self, context, area):
        def render(context, grid, props):
            for x, y, c in self.overlay:
                self._render_char(context, props, x, y, c)
        color = map(lambda x: x / 65535.0, (65535.0 / 2, 65535.0 / 2, 65535.0 / 2))
        self._render(context, render, color=color)
        
    def render_numbers(self, context, area):
        """Render the word numbers of the grid."""
        def render(context, grid, props):
            for n, x, y in grid.words(False):
                self._render_number(context, props, x, y, n)
        color = map(lambda x: x / 65535.0, self.properties.number["color"])
        self._render(context, render, color=color)
    
    def render_location(self, context, area, x, y, r, g, b):
        """Render a cell."""
        def render(context, grid, props):
            bx = props.grid_to_screen_x(x, False)
            by = props.grid_to_screen_y(y, False)
            bsize = props.cell["size"]
            i = gtk.gdk.Rectangle(bx, by, bsize, bsize)
            
            # -0.5 for coordinates and +1 for size
            # are needed to render seamlessly in PDF
            context.rectangle(i.x - 0.5, i.y - 0.5, i.width + 1, i.height + 1)
            context.fill()
        self._render(context, render, color=(r, g, b))
        
        self.render_all_lines_of_cell(context, x, y)
        
    def render_all_lines_of_cell(self, context, x, y):
        self.render_lines_of_cell(context, x, y)
        if self.grid.is_valid(x + 1, y):
            self.render_lines_of_cell(context, x + 1, y)
        if self.grid.is_valid(x, y + 1):
            self.render_lines_of_cell(context, x, y + 1)
        if self.grid.is_valid(x + 1, y + 1):
            self.render_lines_of_cell(context, x + 1, y + 1)
    
    def render_background(self, context, area):
        """Render the background of all cells of the grid."""
        def render(context, grid, props):
            bwidth = self.properties.get_grid_width()
            bheight = self.properties.get_grid_height()
            
            i = gtk.gdk.Rectangle(0, 0, bwidth, bheight)
            context.rectangle(i.x, i.y, i.width, i.height)
            context.fill()
        color = map(lambda x: x / 65535.0, self.properties.cell["color"])
        self._render(context, render, color=color)
        
    def _render_pango(self, context, x, y, font, content):
        """Render the content at (x, y) using the specified font description."""
        pcr = pangocairo.CairoContext(context)
        layout = pcr.create_layout()
        layout.set_markup('''<span font_desc="%s">%s</span>''' % (font, content))
        context.save()
        context.move_to(x, y)
        pcr.show_layout(layout)
        context.restore()
        
    def _render_char(self, context, props, x, y, c):
        """Render a letter c at the specified coordinates (x, y)."""
        xbearing, ybearing, width, height, xadvance, yadvance = context.text_extents(c)
                    
        rx = (props.border["width"] +
            (x + 0.55) * (props.cell["size"] + props.line["width"]) -
            width - props.line["width"] / 2 - abs(xbearing) / 2)
        ry = (props.border["width"] +
            (y + 0.55) * (props.cell["size"] + props.line["width"]) -
            height - props.line["width"] / 2 - abs(ybearing) / 2)
        self._render_pango(context, rx, ry, props.char["font"], c)
        
    def _render_number(self, context, props, x, y, n):
        """Render a number n at the specified coordinates (x, y)."""
        rx = props.grid_to_screen_x(x, False) + 1
        ry = props.grid_to_screen_y(y, False)
        self._render_pango(context, rx, ry, props.number["font"], str(n))
            
    def _render(self, context, render, **args):
        """Perform the rendering function render with the given arguments."""
        r, g, b = args["color"]
        context.set_source_rgb(r, g, b)
        
        if self.settings["has_padding"]:
            context.translate(self.properties.margin_x, self.properties.margin_y)
        
        render(context, self.grid, self.properties)
        
        if self.settings["has_padding"]:
            context.translate(-self.properties.margin_x, -self.properties.margin_y)
        
    def refresh_horizontal_line(self, drawing_area, y):
        """Redraw a horizontal sequence of cells at the specified y-coordinate."""
        self._refresh(drawing_area, [(x, y) for x in xrange(self.grid.width)])
        
    def refresh_vertical_line(self, drawing_area, x):
        """Redraw a vertical sequence of cells at the specified x-coordinate."""
        self._refresh(drawing_area, [(x, y) for y in xrange(self.grid.height)])
        
    def refresh_line(self, drawing_area, x, y, direction):
        """Redraw a sequence of cells in the given direction at the specified coordinates."""
        if direction == "across":
            self.refresh_horizontal_line(drawing_area, y)
        elif direction == "down":
            self.refresh_vertical_line(drawing_area, x)
        
    def refresh_location(self, drawing_area, x, y):
        """Refresh the cell at the specified coordinates."""
        self._refresh(drawing_area, [(x, y)])
        
    def _refresh(self, drawing_area, cells):
        for x, y in cells:
            rx = self.properties.grid_to_screen_x(x)
            ry = self.properties.grid_to_screen_y(y)
            size = self.properties.cell["size"]
            drawing_area.queue_draw_area(rx, ry, size, size)
            
    # needs manual queue_draw() on drawing_area afterwards
    def refresh_visual_size(self, drawing_area):
        """Recalculate the visual width and height and resize the drawing area."""
        visual_width = self.properties.visual_width()
        visual_height = self.properties.visual_height()
        drawing_area.set_size_request(visual_width, visual_height)
