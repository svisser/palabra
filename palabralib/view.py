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
import cView

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
        
    def __eq__(self, other):
        if (other is None
            or self.block != other.block
            or self.cell != other.cell
            or self.char != other.char
            or self.number != other.number
            or self.circle != other.circle):
            return False
        return True

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
        
        #self.styles[5, 5] = CellStyle()
        #self.styles[5, 5].cell["color"] = (65535.0, 0, 0)
        #self.grid.set_void(3, 3, True)
        
        # TODO needed?
        self.border = {}
        self.border["width"] = 1
        self.border["color"] = (0, 0, 0)
        self.cell = {}
        self.cell["size"] = 32
        self.line = {}
        self.line["width"] = 1
        self.line["color"] = (0, 0, 0)
        
    def style(self, x=None, y=None):
        if x is not None and y is not None and (x, y) in self.styles:
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
    
    def pdf_configure(self):
        # 595 = PDF width
        size = (595 - ((self.grid.width + 1) * self.properties.line["width"]) - (2 * 24)) / self.grid.width
        self.properties.cell["size"] = min(32, size)
        self.properties.margin_x = 24
        self.properties.margin_y = 24
        
    def pdf_reset(self):
        self.properties.cell["size"] = 32
        self.properties.margin_x = 10
        self.properties.margin_y = 10
        
    def render(self, context, mode=None):
        """
        Render the grid in the current render mode.
        
        The current render mode can be specified as argument
        or it has been specified earlier by a select_mode call.
        """
        if mode is not None:
            self.select_mode(mode)
        cells = list(self.grid.cells())
        self.render_bottom(context, cells)
        self.render_top(context, cells)

    def render_bottom(self, context, cells):
        # background
        def render_rect(r, s):
            context.set_source_rgb(*[c / 65535.0 for c in self.properties.style(r, s).cell["color"]])
            rx = self.properties.grid_to_screen_x(r, False)
            ry = self.properties.grid_to_screen_y(s, False)
            rsize = self.properties.cell["size"]
            # -0.5 for coordinates and +1 for size
            # are needed to render seamlessly in PDF
            context.rectangle(rx - 0.5, ry - 0.5, rsize + 1, rsize + 1)
            context.fill()
        if self.settings["has_padding"]:
            context.translate(self.properties.margin_x, self.properties.margin_y)
        if len(cells) == 1:
            render_rect(*cells[0])
        else:
            style_default = self.properties.style()
        
            x0 = self.properties.grid_to_screen_x(0, False)
            y0 = self.properties.grid_to_screen_y(0, False)
            x1 = self.properties.grid_to_screen_x(self.grid.width - 1, False)
            y1 = self.properties.grid_to_screen_y(self.grid.height - 1, False)
            context.set_source_rgb(*[c / 65535.0 for c in style_default.cell["color"]])
            rsize = self.properties.cell["size"]
            
            # rsize + 1, rsize + 1)
            rwidth = (x1 + rsize + 1) - x0
            rheight = (y1 + rsize + 1) - y0
            
            # -0.5 for coordinates and +1 for size
            # are needed to render seamlessly in PDF
            context.rectangle(x0 - 0.5, y0 - 0.5, rwidth, rheight)
            context.fill()
            
            for p, q in cells:
                if self.properties.style(p, q) != style_default:
                    render_rect(p, q)
        if self.settings["has_padding"]:
            context.translate(-self.properties.margin_x, -self.properties.margin_y)
        
    def render_top(self, context, cells):
        if self.settings["has_padding"]:
            context.translate(self.properties.margin_x, self.properties.margin_y)
            
        pcr = pangocairo.CairoContext(context)
        pcr_layout = pcr.create_layout()
        def _render_pango(r, s, font, content, rx=None, ry=None):
            if rx is None and ry is None:
                rx = self.properties.grid_to_screen_x(r, False) + 1
                ry = self.properties.grid_to_screen_y(s, False)
            pcr_layout.set_markup('''<span font_desc="%s">%s</span>''' % (font, content))
            context.move_to(rx, ry)
            pcr.show_layout(pcr_layout)
        def _render_char(r, s, c):
            xbearing, ybearing, width, height, xadvance, yadvance = context.text_extents(c)
            rx = (self.properties.border["width"] +
                (r + 0.55) * (self.properties.cell["size"] + self.properties.line["width"]) -
                width - self.properties.line["width"] / 2 - abs(xbearing) / 2)
            ry = (self.properties.border["width"] +
                (s + 0.55) * (self.properties.cell["size"] + self.properties.line["width"]) -
                height - self.properties.line["width"] / 2 - abs(ybearing) / 2)
            _render_pango(r, s, self.properties.style(r, s).char["font"], c, rx, ry)

        for p, q in cells:
            style = self.properties.style(p, q)
        
            # char
            if self.settings["show_chars"]:
                context.set_source_rgb(*[c / 65535.0 for c in style.char["color"]])
                c = self.grid.data[q][p]["char"]
                if c != '':
                    _render_char(p, q, c)
                    
            # overlay char
            if self.settings["render_overlays"]:
                # TODO custom color
                context.set_source_rgb(*[c / 65535.0 for c in (65535.0 / 2, 65535.0 / 2, 65535.0 / 2)])
                for r, s, c in self.overlay:
                    if (p, q) == (r, s):
                        _render_char(p, q, c)
            
            # highlights - TODO custom color
            context.set_source_rgb(*[c / 65535.0 for c in (65535.0, 65535.0, 65535.0 / 2)])
            def render_highlights_of_cell(context, p, q, top, bottom, left, right):
                sx = self.properties.grid_to_screen_x(p, False)
                sy = self.properties.grid_to_screen_y(q, False)
                hwidth = int(self.properties.cell["size"] / 8)
                lines = []
                if top:
                    ry = sy + 0.5 * hwidth
                    rdx = self.properties.cell["size"]
                    lines.append((sx, ry, rdx, 0))
                if bottom:
                    ry = sy + self.properties.cell["size"] - 0.5 * hwidth
                    rdx = self.properties.cell["size"]
                    lines.append((sx, ry, rdx, 0))
                if left:
                    rx = sx + 0.5 * hwidth
                    rdy = self.properties.cell["size"]
                    lines.append((rx, sy, 0, rdy))
                if right:
                    rx = sx + self.properties.cell["size"] - 0.5 * hwidth
                    rdy = self.properties.cell["size"]
                    lines.append((rx, sy, 0, rdy))
                
                context.set_line_width(hwidth)
                for rx, ry, rdx, rdy in lines:
                    context.move_to(rx, ry)
                    context.rel_line_to(rdx, rdy)
                    context.stroke()
                context.set_line_width(self.properties.line["width"])
                
            for r, s, direction, length in self.highlights:
                if direction == "across" and r <= p < r + length and s == q:
                    top = bottom = True
                    right = p == (r + length - 1)
                    left = p == r
                    render_highlights_of_cell(context, p, q, top, bottom, left, right)
                elif direction == "down" and s <= q < s + length and r == p:
                    left = right = True
                    top = q == s
                    bottom = q == (s + length - 1)
                    render_highlights_of_cell(context, p, q, top, bottom, left, right)
            # block
            context.set_source_rgb(*[c / 65535.0 for c in style.block["color"]])
            if self.grid.data[q][p]["block"]:
                rx = self.properties.grid_to_screen_x(p, False)
                ry = self.properties.grid_to_screen_y(q, False)
                rsize = self.properties.cell["size"]
                
                if self.properties.style(p, q).block["margin"] != 0:
                    offset = int((self.properties.style(p, q).block["margin"] / 100.0) * self.properties.cell["size"])
                    rx += offset
                    ry += offset
                    rsize -= (2 * offset)
                
                if self.properties.style(p, q).block["margin"] == 0:
                    # -0.5 for coordinates and +1 for size
                    # are needed to render seamlessly in PDF
                    context.rectangle(rx - 0.5, ry - 0.5, rsize + 1, rsize + 1)
                else:                
                    context.rectangle(rx, ry, rsize, rsize)
            context.fill()
            
            # number
            if self.settings["show_numbers"]:
                context.set_source_rgb(*[c / 65535.0 for c in style.number["color"]])
                n = self.grid.data[q][p]["number"]
                if n > 0:
                    font = self.properties.style(p, q).number["font"]
                    _render_pango(p, q, font, str(n))
                    
            # circle
            if style.circle:
                context.set_source_rgb(*[c / 65535.0 for c in style.char["color"]])
                rx = self.properties.grid_to_screen_x(p, False)
                ry = self.properties.grid_to_screen_y(q, False)
                rsize = self.properties.cell["size"]
                context.new_sub_path()
                context.arc(rx + rsize / 2, ry + rsize / 2, rsize / 2, 0, 2 * math.pi)
                context.stroke()
        
        # lines
        screen_xs = self.comp_screen_xs()
        screen_ys = self.comp_screen_ys()
        if len(cells) == 1:
            x, y = cells[0]
            self.render_all_lines_of_cell(context, x, y, screen_xs, screen_ys)
        else:
            for p, q in cells:
                self.render_lines_of_cell(context, p, q, screen_xs, screen_ys)
        if self.settings["has_padding"]:
            context.translate(-self.properties.margin_x, -self.properties.margin_y)
    
    def render_all_lines_of_cell(self, context, x, y, screen_xs, screen_ys):
        """Render the lines that surround a cell (all four sides)."""
        self.render_lines_of_cell(context, x, y, screen_xs, screen_ys)
        for p, q in [(x + 1, y), (x, y + 1), (x + 1, y + 1)]:
            if self.grid.is_valid(p, q):
                self.render_lines_of_cell(context, p, q, screen_xs, screen_ys)
                
    def comp_screen_xs(self):
        d = {}
        # +1 because we also use coords of invalid cells
        for x in xrange(self.grid.width + 1):
            d[x] = self.properties.grid_to_screen_x(x, False)
        return d
        
    def comp_screen_ys(self):
        d = {}
        # +1 because we also use coords of invalid cells
        for y in xrange(self.grid.height + 1):
            d[y] = self.properties.grid_to_screen_y(y, False)
        return d
        
    def render_lines_of_cell(self, context, x, y, screen_xs, screen_ys):
        # lines
        """Render the lines that belong to a cell (top and left line)."""
        def render_line(context, rx, ry, rdx, rdy, bar, border):
            if bar:
                context.set_line_width(self.properties.bar["width"])
            if border:
                color = [c / 65535.0 for c in self.properties.border["color"]]
                context.set_source_rgb(*color)
            context.move_to(rx, ry)
            context.rel_line_to(rdx, rdy)
            context.stroke()
            if border:
                color = [c / 65535.0 for c in self.properties.line["color"]]
                context.set_source_rgb(*color)
            if bar:
                context.set_line_width(self.properties.line["width"])
        
        context.set_source_rgb(*[c / 65535.0 for c in self.properties.line["color"]])
        if not self.grid.lines:
            self.grid.lines = cView.compute_lines(self.grid)
        lines = self.grid.lines[x, y]
        for p, q, ltype, side in lines:
            sx = screen_xs[p]
            sy = screen_ys[q]
            
            lwidth = self.properties.line["width"]
            bwidth = self.properties.border["width"]
            cellsize = self.properties.cell["size"]
            
            bar = (0 <= x < self.grid.width
                and 0 <= y < self.grid.height
                and self.grid.data[y][x]["bar"][ltype])
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
                if not self.grid.is_available(*check) or not self.grid.is_available(x, y):
                    start -= lwidth
            
            if ltype == "left":
                render_line(context, sx + start, sy, 0, cellsize, bar, border)
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
                        return False, self.properties.line["width"]
                    if ((x, y, "left", "normal") in lines
                        or (x, y - 1, "left", "normal") in lines):
                        return False, self.properties.line["width"]
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
                render_line(context, rx, ry, rdx, 0, bar, border)
                if is_lb:
                    rx -= bwidth
                    render_line(context, rx, ry, bwidth, 0, False, True)
                if is_rb:
                    rx += (cellsize + dxl)
                    render_line(context, rx, ry, bwidth, 0, False, True)
        
    def render_warnings_of_cells(self, context, cells):
        """Determine undesired cells."""
        lengths = {}
        starts = {}
        counts = {}
        warnings = []
        for p, q in cells:
            warn = False
            if (p, q) not in counts:
                counts[p, q] = self.grid.get_check_count(p, q)
            if self.settings["warn_unchecked_cells"]:
                # Color cells that are unchecked. Isolated cells are also colored.
                if 0 <= counts[p, q] <= 1:
                    warnings.append((p, q))
                    continue
            if self.settings["warn_consecutive_unchecked"]:
                # Color consecutive (two or more) unchecked cells.
                warn = False
                if 0 <= count <= 1:
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        if (p + dx, q + dy) not in counts:
                            counts[p + dx, q + dy] = self.grid.get_check_count(p + dx, q + dy)
                        if 0 <= counts[p + dx, q + dy] <= 1:
                            warn = True
                            break
                if warn:
                    warnings.append((p, q))
                    continue
            if self.settings["warn_two_letter_words"]:
                # Color words with length two.
                warn = False
                for d in ["across", "down"]:
                    if (p, q, d) in starts:
                        sx, sy = starts[p, q, d]
                    else:
                        sx, sy = self.grid.get_start_word(p, q, d)
                        starts[p, q, d] = sx, sy
                        for zx, zy in self.grid.in_direction(sx, sy, d):
                            starts[zx, zy, d] = sx, sy
                        lengths[sx, sy, d] = self.grid.word_length(sx, sy, d)
                    if lengths[sx, sy, d] == 2:
                        warn = True
                        break
                if warn:
                    warnings.append((p, q))
                    continue
        return warnings
        
    def render_locations(self, context, cells):
        """Render one or more cells."""
        if self.settings["has_padding"]:
            context.translate(self.properties.margin_x, self.properties.margin_y)
        screen_xs = self.comp_screen_xs()
        screen_ys = self.comp_screen_ys()
        for x, y, r, g, b in cells:
            context.set_source_rgb(r, g, b)
            # -0.5 for coordinates and +1 for size
            # are needed to render seamlessly in PDF
            bx = self.properties.grid_to_screen_x(x, False) - 0.5
            by = self.properties.grid_to_screen_y(y, False) - 0.5
            bsize = self.properties.cell["size"] + 1
            context.rectangle(bx, by, bsize, bsize)
            context.fill()
            self.render_all_lines_of_cell(context, x, y, screen_xs, screen_ys)
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
