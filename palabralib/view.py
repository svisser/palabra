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

class CellStyle:
    def __init__(self):
        self.block = {}
        self.block["color"] = (0, 0, 0)
        self.block["margin"] = 0
        self.cell = {}
        self.cell["color"] = (65535, 65535, 65535)
        self.char = {}
        self.char["color"] = (0, 0, 0)
        self.char["font"] = "Sans 12"
        self.number = {}
        self.number["color"] = (0, 0, 0)
        self.number["font"] = "Sans 7"

class GridViewProperties:
    def __init__(self, grid):
        self.grid = grid
        
        # 0.5 for sharp lines
        self.origin_x = 0.5
        self.origin_y = 0.5
        self.margin_x = 10
        self.margin_y = 10
        
        self.default = CellStyle()
        self.styles = {}
        
        self.bar = {}
        self.bar["width"] = 5
        self.border = {}
        self.border["width"] = 1
        self.border["color"] = (0, 0, 0)
        self.cell = {}
        self.cell["size"] = 32
        self.line = {}
        self.line["width"] = 1
        self.line["color"] = (0, 0, 0)
        
    def style(self, x, y):
        if (x, y) in self.styles:
            return self.styles[x, y]
        return self.default
    
    def apply_appearance(self, appearance):
        self.default.block["color"] = appearance["block"]["color"]
        self.border["color"] = appearance["border"]["color"]
        self.default.char["color"] = appearance["char"]["color"]
        self.default.cell["color"] = appearance["cell"]["color"]
        self.line["color"] = appearance["line"]["color"]
        self.default.number["color"] = appearance["number"]["color"]
        
        self.border["width"] = appearance["border"]["width"]
        self.line["width"] = appearance["line"]["width"]
        self.default.block["margin"] = appearance["block"]["margin"]
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
        for x in xrange(self.grid.width):
            sx = self.grid_to_screen_x(x)
            if sx <= screen_x < sx + self.cell["size"]:
                return x
        return -1
        
    def screen_to_grid_y(self, screen_y):
        """
        Return the y-coordinate of the cell based on the y-coordinate on screen.
        """
        for y in xrange(self.grid.height):
            sy = self.grid_to_screen_y(y)
            if sy <= screen_y < sy + self.cell["size"]:
                return y
        return -1
       
    def visual_width(self, include_padding=True):
        """
        Return the visual width, possibly including padding, as shown on screen.
        """
        width = self.get_grid_width()
        if include_padding:
            width += (2 * self.margin_x)
        return width
    
    def visual_height(self, include_padding=True):
        """
        Return the visual height, possibly including padding, as shown on screen.
        """
        height = self.get_grid_height()
        if include_padding:
            height += (2 * self.margin_y)
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
        self.highlights = []
        
    def style(self, x, y):
        return self.properties.style(x, y)
        
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
        
    def render(self, context, mode=None):
        """
        Render the grid in the current render mode.
        
        The current render mode can be specified as argument
        or it has been specified earlier by a select_mode call.
        """
        if mode is not None:
            self.select_mode(mode)
        for x, y in self.grid.cells():
            self.render_bottom(context, x, y)
            self.render_top(context, x, y)

    def render_bottom(self, context, x, y):
        # background
        def render(context, grid, props):
            rx = props.grid_to_screen_x(x, False)
            ry = props.grid_to_screen_y(y, False)
            rsize = props.cell["size"]
            
            # -0.5 for coordinates and +1 for size
            # are needed to render seamlessly in PDF
            context.rectangle(rx - 0.5, ry - 0.5, rsize + 1, rsize + 1)
            context.fill()
        color = map(lambda x: x / 65535.0, self.style(x, y).cell["color"])
        self._render(context, render, color=color)
        
    def render_top(self, context, x, y):
        # char
        def render(context, grid, props):
            c = grid.get_char(x, y)
            if c != '':
                self._render_char(context, props, x, y, c)
        color = map(lambda x: x / 65535.0, self.style(x, y).char["color"])
        self._render(context, render, color=color)
        
        # overlay char
        def render(context, grid, props):
            for p, q, c in self.overlay:
                if (x, y) == (p, q):
                    self._render_char(context, props, x, y, c)
        color = map(lambda x: x / 65535.0, (65535.0 / 2, 65535.0 / 2, 65535.0 / 2))
        if self.settings["render_overlays"]:
            self._render(context, render, color=color)
        
        # highlights
        def render(context, grid, props):
            def render_highlights_of_cell(context, p, q, top, bottom, left, right):
                sx = props.grid_to_screen_x(p, False)
                sy = props.grid_to_screen_y(q, False)
                hwidth = int(props.cell["size"] / 8)
                lines = []
                if top:
                    ry = sy + 0.5 * hwidth
                    rdx = props.cell["size"]
                    lines.append((sx, ry, rdx, 0))
                if bottom:
                    ry = sy + props.cell["size"] - 0.5 * hwidth
                    rdx = props.cell["size"]
                    lines.append((sx, ry, rdx, 0))
                if left:
                    rx = sx + 0.5 * hwidth
                    rdy = props.cell["size"]
                    lines.append((rx, sy, 0, rdy))
                if right:
                    rx = sx + props.cell["size"] - 0.5 * hwidth
                    rdy = props.cell["size"]
                    lines.append((rx, sy, 0, rdy))
                
                context.set_line_width(hwidth)
                for rx, ry, rdx, rdy in lines:
                    context.move_to(rx, ry)
                    context.rel_line_to(rdx, rdy)
                    context.stroke()
                context.set_line_width(props.line["width"])
                
            for p, q, direction, length in self.highlights:
                if direction == "across" and p <= x < p + length and q == y:
                    top = bottom = True
                    right = x == (p + length - 1)
                    left = x == p
                    render_highlights_of_cell(context, x, y, top, bottom, left, right)
                elif direction == "down" and q <= y < q + length and p == x:
                    left = right = True
                    top = y == q
                    bottom = y == (q + length - 1)
                    render_highlights_of_cell(context, x, y, top, bottom, left, right)
        # TODO custom color
        color = map(lambda x: x / 65535.0, (65535.0, 65535.0, 65535.0 / 2))
        self._render(context, render, color=color)
        
        # block
        def render(context, grid, props):
            if grid.is_block(x, y):
                rx = props.grid_to_screen_x(x, False)
                ry = props.grid_to_screen_y(y, False)
                rsize = props.cell["size"]
                
                if props.style(x, y).block["margin"] != 0:
                    offset = int((props.style(x, y).block["margin"] / 100.0) * props.cell["size"])
                    rx += offset
                    ry += offset
                    rsize -= (2 * offset)
                
                if props.style(x, y).block["margin"] == 0:
                    # -0.5 for coordinates and +1 for size
                    # are needed to render seamlessly in PDF
                    context.rectangle(rx - 0.5, ry - 0.5, rsize + 1, rsize + 1)
                else:                
                    context.rectangle(rx, ry, rsize, rsize)
            context.fill()
        color = map(lambda x: x / 65535.0, self.style(x, y).block["color"])
        self._render(context, render, color=color)
        
        self.render_all_lines_of_cell(context, x, y)
            
        # number
        def render(context, grid, props):
            n = grid.cell(x, y)["number"]
            if n > 0:
                self._render_number(context, props, x, y, n)
        color = map(lambda x: x / 65535.0, self.style(x, y).number["color"])
        if self.settings["show_numbers"]:
            self._render(context, render, color=color)
    
    def render_all_lines_of_cell(self, context, x, y):
        """Render the lines that surround a cell (all four sides)."""
        self.render_lines_of_cell(context, x, y)
        for p, q in [(x + 1, y), (x, y + 1), (x + 1, y + 1)]:
            if self.grid.is_valid(p, q):
                self.render_lines_of_cell(context, p, q)
        
    def render_lines_of_cell(self, context, x, y):
        # lines
        """Render the lines that belong to a cell (top and left line)."""
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
                    return False, props.line["width"]
                elems = [(x, y, "left", "normal"), (x, y - 1, "left", "normal")]
                if True in [e in lines for e in elems]:
                    return False, props.line["width"]
                elems = [(x, y, "left", side_extend), (x, y - 1, "left", side_extend)]
                if True in [e in lines for e in elems]:
                    return True, 0 #props.border["width"]
                return False, 0
            is_left_border, dx_left = get_delta(x, y, "innerborder", "outerborder")
            is_right_border, dx_right = get_delta(x + 1, y, "outerborder", "innerborder")
            return (dx_left, dx_right, is_left_border, is_right_border)
        
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
                    dxl, dxr, is_lb, is_rb = get_adjustments(lines, props, x, y)
                    rx -= dxl
                    rdx += dxl
                    rdx += dxr
                    render_line(context, props, rx, ry, rdx, 0, bar, border)
                    if is_lb:
                        rx -= props.border["width"]
                        rdx = props.border["width"]
                        render_line(context, props, rx, ry, rdx, 0, False, True)
                    if is_rb:
                        rx += (props.cell["size"] + dxl)
                        rdx = props.border["width"]
                        render_line(context, props, rx, ry, rdx, 0, False, True)
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
            
    def render_warnings_of_cell(self, context, x, y, r, g, b):
        """Render undesired cell in the specified color."""
        count = self.grid.get_check_count(x, y)
        if self.settings["warn_unchecked_cells"]:
            # Color cells that are unchecked. Isolated cells are also colored.
            if 0 <= count <= 1:
                self.render_location(context, x, y, r, g, b)
        if self.settings["warn_consecutive_unchecked"]:
            # Color consecutive (two or more) unchecked cells.
            if 0 <= count <= 1:
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    if 0 <= self.grid.get_check_count(x + dx, y + dy) <= 1:
                        self.render_location(context, x, y, r, g, b)
        if self.settings["warn_two_letter_words"]:
            # Color words with length two.
            for d in ["across", "down"]:
                sx, sy = self.grid.get_start_word(x, y, d)
                if self.grid.word_length(sx, sy, d) == 2:
                    self.render_location(context, x, y, r, g, b)
        
    def render_location(self, context, x, y, r, g, b):
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
        self._render_pango(context, rx, ry, props.style(x, y).char["font"], c)
        
    def _render_number(self, context, props, x, y, n):
        """Render a number n at the specified coordinates (x, y)."""
        rx = props.grid_to_screen_x(x, False) + 1
        ry = props.grid_to_screen_y(y, False)
        self._render_pango(context, rx, ry, props.style(x, y).number["font"], str(n))
            
    def _render(self, context, render, **args):
        """Perform the rendering function render with the given arguments."""
        r, g, b = args["color"]
        context.set_source_rgb(r, g, b)
        
        if self.settings["has_padding"]:
            context.translate(self.properties.margin_x, self.properties.margin_y)
        render(context, self.grid, self.properties)
        if self.settings["has_padding"]:
            context.translate(-self.properties.margin_x, -self.properties.margin_y)
            
    # needs manual queue_draw() on drawing_area afterwards
    def refresh_visual_size(self, drawing_area):
        """Recalculate the visual width and height and resize the drawing area."""
        visual_width = self.properties.visual_width()
        visual_height = self.properties.visual_height()
        drawing_area.set_size_request(visual_width, visual_height)
