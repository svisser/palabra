# This file is part of Palabra
#
# Copyright (C) 2009 - 2011 Simeon Visser
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
SETTINGS_EXPORT_PDF_PUZZLE = {
    "has_padding": True
    , "show_chars": False
    , "show_numbers": True
    , "render_overlays": False
    , "warn_consecutive_unchecked": False
    , "warn_unchecked_cells": False
    , "warn_two_letter_words": False
    , "warn_blacklist": False
}
SETTINGS_EXPORT_PDF_SOLUTION = {
    "has_padding": True
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
        self.circle = False

class GridViewProperties:
    def __init__(self, grid, styles=None):
        self.grid = grid
        
        # 0.5 for sharp lines
        self.origin_x = 0.5
        self.origin_y = 0.5
        self.margin_x = 10
        self.margin_y = 10
        
        self.default = CellStyle()
        self.styles = styles if styles else {}
        
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
        
    def visual_size(self, include_padding=True):
        """
        Return the visual size, possibly including padding, as shown on screen.
        """
        width = 2 * self.border["width"]
        width += self.grid.width * self.cell["size"]
        width += (self.grid.width - 1) * self.line["width"]
        if include_padding:
            width += (2 * self.margin_x)
        height = 2 * self.border["width"]
        height += self.grid.height * self.cell["size"]
        height += (self.grid.height - 1) * self.line["width"]
        if include_padding:
            height += (2 * self.margin_y)
        return width, height

class GridView:
    def __init__(self, grid, styles=None):
        self.grid = grid
        self.properties = GridViewProperties(grid, styles)
        self.select_mode(constants.VIEW_MODE_EDITOR)
        
        self.overlay = []
        self.highlights = []
        
    def style(self, x, y):
        return self.properties.style(x, y)
        
    def select_mode(self, mode):
        """Select the render mode for future render calls."""
        self.settings = {}
        self.mode = mode
        if mode == constants.VIEW_MODE_EDITOR:
            self.settings.update(SETTINGS_EDITOR)
            self.settings.update(custom_settings)
        elif mode == constants.VIEW_MODE_EMPTY:
            self.settings.update(SETTINGS_EMPTY)
        elif mode == constants.VIEW_MODE_PREVIEW:
            self.settings.update(SETTINGS_PREVIEW)
        elif mode == constants.VIEW_MODE_SOLUTION:
            self.settings.update(SETTINGS_SOLUTION)
        elif mode == constants.VIEW_MODE_EXPORT_PDF_PUZZLE:
            self.settings.update(SETTINGS_EXPORT_PDF_PUZZLE)
        elif mode == constants.VIEW_MODE_EXPORT_PDF_SOLUTION:
            self.settings.update(SETTINGS_EXPORT_PDF_SOLUTION)
        
    def render(self, context, mode=None):
        """
        Render the grid in the current render mode.
        
        The current render mode can be specified as argument
        or it has been specified earlier by a select_mode call.
        """
        if mode is not None:
            self.select_mode(mode)
        if (self.mode == constants.VIEW_MODE_EXPORT_PDF_PUZZLE
            or self.mode == constants.VIEW_MODE_EXPORT_PDF_SOLUTION):
            # 595 = PDF width
            size = (595 - ((self.grid.width + 1) * self.properties.line["width"]) - (2 * 24)) / self.grid.width
            self.properties.cell["size"] = min(32, size)
            self.properties.margin_x = 24
            self.properties.margin_y = 24
        for x, y in self.grid.cells():
            self.render_bottom(context, x, y)
            self.render_top(context, x, y)
        if (self.mode == constants.VIEW_MODE_EXPORT_PDF_PUZZLE
            or self.mode == constants.VIEW_MODE_EXPORT_PDF_SOLUTION):
            self.properties.cell["size"] = 32
            self.properties.margin_x = 10
            self.properties.margin_y = 10

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
        color = [c / 65535.0 for c in self.style(x, y).cell["color"]]
        self._render(context, render, color=color)
        
    def render_top(self, context, x, y):
        # char
        def render(context, grid, props):
            c = grid.get_char(x, y)
            if c != '':
                self._render_char(context, props, x, y, c)
        if self.settings["show_chars"]:
            color = [c / 65535.0 for c in self.style(x, y).char["color"]]
            self._render(context, render, color=color)
        
        # overlay char
        def render(context, grid, props):
            for p, q, c in self.overlay:
                if (x, y) == (p, q):
                    self._render_char(context, props, x, y, c)
        # TODO custom color
        if self.settings["render_overlays"]:
            color = [c / 65535.0 for c in (65535.0 / 2, 65535.0 / 2, 65535.0 / 2)]
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
        color = [c / 65535.0 for c in (65535.0, 65535.0, 65535.0 / 2)]
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
        color = [c / 65535.0 for c in self.style(x, y).block["color"]]
        self._render(context, render, color=color)
        
        self.render_all_lines_of_cell(context, x, y)
            
        # number
        def render(context, grid, props):
            n = grid.cell(x, y)["number"]
            if n > 0:
                self._render_number(context, props, x, y, n)
        if self.settings["show_numbers"]:
            color = [c / 65535.0 for c in self.style(x, y).number["color"]]
            self._render(context, render, color=color)
            
        # circle
        def render(context, grid, props):
            rx = props.grid_to_screen_x(x, False)
            ry = props.grid_to_screen_y(y, False)
            rsize = props.cell["size"]
            context.new_sub_path()
            context.arc(rx + rsize / 2, ry + rsize / 2, rsize / 2, 0, 2 * math.pi)
            context.stroke()
        if self.style(x, y).circle:
            color = [c / 65535.0 for c in self.style(x, y).char["color"]]
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
                color = [c / 65535.0 for c in props.border["color"]]
                context.set_source_rgb(*color)
            context.move_to(rx, ry)
            context.rel_line_to(rdx, rdy)
            context.stroke()
            if border:
                color = [c / 65535.0 for c in props.line["color"]]
                context.set_source_rgb(*color)
            if bar:
                context.set_line_width(props.line["width"])
        
        def render(context, grid, props):
            lines = grid.get_lines(x, y)
            for p, q, ltype, side in lines:
                sx = props.grid_to_screen_x(p, False)
                sy = props.grid_to_screen_y(q, False)
                
                lwidth = props.line["width"]
                bwidth = props.border["width"]
                cellsize = props.cell["size"]
                
                bar = grid.is_valid(x, y) and grid.has_bar(x, y, ltype)
                border = "border" in side
                if side == "normal":
                    context.set_line_width(lwidth)
                elif border:
                    context.set_line_width(bwidth)
                
                if side == "normal":
                    start = -0.5 * lwidth
                elif side == "outerborder":
                    start = -0.5 * bwidth
                elif side == "innerborder":
                    start = 0.5 * bwidth
                    if ltype == "top":
                        check = x, y + 1
                    elif ltype == "left":
                        check = x + 1, y
                    if not grid.is_available(*check) or not grid.is_available(x, y):
                        start -= lwidth
                
                if ltype == "left":
                    render_line(context, props, sx + start, sy, 0, cellsize, bar, border)
                elif ltype == "top":
                    rx = sx
                    ry = sy + start
                    rdx = cellsize
                    
                    def get_delta(x, y, side_no_extend, side_extend):
                        """
                        Determine the delta in pixels.
                        The delta is at least the normal line width.
                        """
                        if ((x, y, "left", side_no_extend) in lines
                            or (x, y - 1, "left", side_no_extend) in lines):
                            return False, props.line["width"]
                        if ((x, y, "left", "normal") in lines
                            or (x, y - 1, "left", "normal") in lines):
                            return False, props.line["width"]
                        if ((x, y, "left", side_extend) in lines
                            or (x, y - 1, "left", side_extend) in lines):
                            return True, 0
                        return False, 0
                    is_lb, dxl = get_delta(x, y, "innerborder", "outerborder")
                    is_rb, dxr = get_delta(x + 1, y, "outerborder", "innerborder")
                    
                    # adjust horizontal lines to fill empty spaces in corners
                    rx -= dxl
                    rdx += dxl
                    rdx += dxr
                    render_line(context, props, rx, ry, rdx, 0, bar, border)
                    if is_lb:
                        rx -= bwidth
                        render_line(context, props, rx, ry, bwidth, 0, False, True)
                    if is_rb:
                        rx += (cellsize + dxl)
                        render_line(context, props, rx, ry, bwidth, 0, False, True)
        color = [c / 65535.0 for c in self.properties.line["color"]]
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
            # -0.5 for coordinates and +1 for size
            # are needed to render seamlessly in PDF
            bx = props.grid_to_screen_x(x, False) - 0.5
            by = props.grid_to_screen_y(y, False) - 0.5
            bsize = props.cell["size"] + 1
            
            context.rectangle(bx, by, bsize, bsize)
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
        context.set_source_rgb(*args["color"])
        
        if self.settings["has_padding"]:
            context.translate(self.properties.margin_x, self.properties.margin_y)
        render(context, self.grid, self.properties)
        if self.settings["has_padding"]:
            context.translate(-self.properties.margin_x, -self.properties.margin_y)
            
    # needs manual queue_draw() on drawing_area afterwards
    def refresh_visual_size(self, drawing_area):
        """Recalculate the visual width and height and resize the drawing area."""
        drawing_area.set_size_request(*self.properties.visual_size())

class GridPreview(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self)
        
        self.view = None
        self.preview_surface = None
        self.preview_pattern = None
        
        label = gtk.Label()
        label.set_alignment(0, 0)
        label.set_markup("<b>Preview</b>")
        
        self.drawing_area = gtk.DrawingArea()
        self.drawing_area.connect("expose_event", self.on_expose_event)
        
        self.scrolled_window = gtk.ScrolledWindow(None, None)
        self.scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scrolled_window.add_with_viewport(self.drawing_area)
        
        self.pack_start(label, False, False, 6)
        self.pack_start(self.scrolled_window, True, True, 0)
        
    def display(self, grid):
        self.view = GridView(grid)
        self.preview_surface = None
        self.refresh()
        
    def refresh(self):
        if self.view is not None:
            self.view.properties.cell["size"] = 12
            self.view.refresh_visual_size(self.drawing_area)
            self.drawing_area.queue_draw()
        
    def clear(self):
        self.view = None
        self.preview_surface = None
        self.drawing_area.queue_draw()
        
    def on_expose_event(self, drawing_area, event):
        if self.view is not None:
            if not self.preview_surface:
                width, height = self.view.properties.visual_size(True)
                self.preview_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
                self.preview_pattern = cairo.SurfacePattern(self.preview_surface)
                context = cairo.Context(self.preview_surface)
                self.view.render(context, constants.VIEW_MODE_PREVIEW)
            context = drawing_area.window.cairo_create()
            context.set_source(self.preview_pattern)
            context.paint()

            #import pstats
            #import cProfile
            #cProfile.runctx('self.view.render(context, constants.VIEW_MODE_PREVIEW)', globals(), locals(), filename='fooprof')
            #p = pstats.Stats('fooprof')
            #p.sort_stats('time').print_stats(20)
            #self.view.render(context, constants.VIEW_MODE_PREVIEW)
