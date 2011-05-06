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
import math
import pango
import pangocairo

import constants
import cPalabra

SETTINGS_PREVIEW = {
    "has_padding": True
    , "show_chars": True
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
SETTINGS_PREVIEW_CELL = {
    "has_padding": True
    , "show_chars": False
    , "show_numbers": True
    , "render_overlays": False
    , "warn_consecutive_unchecked": False
    , "warn_unchecked_cells": False
    , "warn_two_letter_words": False
    , "warn_blacklist": False
}
SETTINGS_PREVIEW_SOLUTION = {
    "has_padding": True
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

DEFAULTS = {
    ("bar", "width"): 3,
    ("border", "width"): 1,
    ("border", "color"): (0, 0, 0),
    ("cell", "size"): 32,
    ("line", "width"): 1,
    ("line", "color"): (0, 0, 0)
}
def _relative_to(key, p, d=DEFAULTS):
    return str(int(d[key] * p)) + "px"
DEFAULTS_CELL = {
    ("block", "color"): (0, 0, 0),
    ("block", "margin"): 0,
    ("char", "color"): (0, 0, 0),
    ("char", "font"): "Sans",
    ("char", "size"): (64, _relative_to(("cell", "size"), 0.64)),
    ("cell", "color"): (65535, 65535, 65535),
    ("number", "color"): (0, 0, 0),
    ("number", "font"): "Sans",
    ("number", "size"): (32, _relative_to(("cell", "size"), 0.32)),
    "circle": False
}
DEFAULTS.update(DEFAULTS_CELL)

class CellStyle:
    def __init__(self):
        self._data = {}
        self._data.update(DEFAULTS_CELL)
        
    def __getitem__(self, key):
        return self._data[key]
        
    def __setitem__(self, key, value):
        self._data[key] = value
        
    def __eq__(self, other):
        return other is not None and self._data == other._data
        
    def __ne__(self, other):
        return not self.__eq__(other)

class GridViewProperties:
    def __init__(self, grid, styles=None, gstyles=None):
        self.grid = grid
        self.margin = 10, 10
        
        self.styles = styles if styles else {}
        self._data = {}
        self._data.update(DEFAULTS)
        if gstyles:
            for key, value in gstyles.items():
                self[key] = value
                
    def __setitem__(self, key, value):
        self._data[key] = value
        if key == ("cell", "size"):
            for k in [("char", "size"), ("number", "size")]:
                s = self._data[k]
                self._data[k] = (s[0], _relative_to(("cell", "size"), s[0] / 100.0, d=self._data))
            
    def __getitem__(self, key):
        return self._data[key]
        
    def update(self, x, y, items):
        for k, v in items:
            if self[k] != v:
                if (x, y) not in self.styles:
                    self.styles[x, y] = CellStyle()
                self.styles[x, y][k] = v
            else:
                if (x, y) in self.styles and self.styles[x, y][k] != v:
                    self.styles[x, y][k] = v
        default = self.style()
        if (x, y) in self.styles:
            for k, v in self.styles[x, y]._data.items():
                if self.styles[x, y][k] != default[k]:
                    break
            else:
                del self.styles[x, y]
        
    def style(self, x=None, y=None):
        if x is not None and y is not None and (x, y) in self.styles:
            return self.styles[x, y]
        # TODO ugly
        default = CellStyle()
        default._data.update(self._data)
        return default
        
    def get_non_defaults(self):
        props = [("Bar", "Width", ("bar", "width"))
            , ("Border", "Width", ("border", "width"))
            , ("Border", "Color", ("border", "color"))
            , ("Cell", "Size", ("cell", "size"))
            , ("Line", "Width", ("line", "width"))
            , ("Line", "Color", ("line", "color"))
            , ("Block", "Color", ("block", "color"))
            , ("Block", "Margin", ("block", "margin"))
            , ("Char", "Color", ("char", "color"))
            , ("Cell", "Color", ("cell", "color"))
            , ("Number", "Color", ("number", "color"))
            , ("Char", "Size", ("char", "size"))
            , ("Number", "Size", ("number", "size"))
        ]
        visuals = {}
        for elem, attr, key in props:
            value = self[key]
            if value != DEFAULTS[key]:
                if key in [("char", "size"), ("number", "size")]:
                    value = value[0]
                if elem not in visuals:
                    visuals[elem] = [(attr, value)]
                else:
                    visuals[elem].append((attr, value))
        return visuals
    
    def grid_to_screen(self, x=None, y=None, include_padding=True):
        """
        Return the x-coordinate and/or y-coordinate of the cell's upper-left corner.
        """
        border_width = self["border", "width"]
        cell_size = self["cell", "size"]
        line_width = self["line", "width"]
        dsize = cell_size + line_width
        if x is not None:
            sx = border_width + x * dsize + (self.margin[0] if include_padding else 0)
        if y is not None:
            sy = border_width + y * dsize + (self.margin[1] if include_padding else 0)
        if x is not None and y is not None:
            return sx, sy
        elif x is not None:
            return sx
        elif y is not None:
            return sy
        return None
        
    def screen_to_grid(self, screen_x, screen_y):
        """
        Return the coordinates of the cell based on the coordinates on screen.
        """
        i, j = -1, -1
        to_screen = self.grid_to_screen
        size = self["cell", "size"]
        for x in xrange(self.grid.width):
            sx = to_screen(x=x)
            if sx <= screen_x < sx + size:
                i = x
                break
        for y in xrange(self.grid.height):
            sy = to_screen(y=y)
            if sy <= screen_y < sy + size:
                j = y
                break
        return i, j
        
    def visual_size(self, include_padding=True):
        """
        Return the visual size, possibly including padding, as shown on screen.
        """
        border_width = self["border", "width"]
        cell_size = self["cell", "size"]
        line_width = self["line", "width"]
        g_w, g_h = self.grid.size
        w = 2 * border_width + (g_w * cell_size) + (g_w - 1) * line_width
        h = 2 * border_width + (g_h * cell_size) + (g_h - 1) * line_width
        if include_padding:
            w += (2 * self.margin[0])
            h += (2 * self.margin[1])
        return w, h

class GridView:
    def __init__(self, grid, styles=None, gstyles=None):
        self.grid = grid
        self.properties = GridViewProperties(grid, styles, gstyles)
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
        elif mode == constants.VIEW_MODE_PREVIEW_CELL:
            self.settings.update(SETTINGS_PREVIEW_CELL)
        elif mode == constants.VIEW_MODE_PREVIEW_SOLUTION:
            self.settings.update(SETTINGS_PREVIEW_SOLUTION)
    
    def pdf_reset(self, prevs):
        self.properties["cell", "size"] = prevs["cell", "size"]
        self.properties.margin = prevs["margin"]
        
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
        has_padding = self.settings["has_padding"]
        props = self.properties
        # background
        def render_rect(r, s):
            context.set_source_rgb(*[c / 65535.0 for c in props.style(r, s)["cell", "color"]])
            rx, ry = props.grid_to_screen(r, s, False)
            rsize = props["cell", "size"]
            # -0.5 for coordinates and +1 for size
            # are needed to render seamlessly in PDF
            context.rectangle(rx - 0.5, ry - 0.5, rsize + 1, rsize + 1)
            context.fill()
        if has_padding:
            context.translate(*props.margin)
        if len(cells) < self.grid.width * self.grid.height:
            for p, q in cells:
                render_rect(p, q)
        else:
            default = props.style()
            style = props.style
        
            x0, y0 = props.grid_to_screen(0, 0, False)
            x1, y1 = props.grid_to_screen(self.grid.width - 1, self.grid.height - 1, False)
            context.set_source_rgb(*[c / 65535.0 for c in default["cell", "color"]])
            rsize = props["cell", "size"]
            
            # rsize + 1, rsize + 1)
            rwidth = (x1 + rsize + 1) - x0
            rheight = (y1 + rsize + 1) - y0
            
            # -0.5 for coordinates and +1 for size
            # are needed to render seamlessly in PDF
            context.rectangle(x0 - 0.5, y0 - 0.5, rwidth, rheight)
            context.fill()
            
            styles = props.styles
            for p, q in cells:
                if (p, q) not in styles:
                    continue
                if styles[p, q]._data != default._data:
                    render_rect(p, q)
        if has_padding:
            mx, my = props.margin
            context.translate(-1 * mx, -1 * my)
        
    def render_top(self, context, cells):
        data = self.grid.data
        props = self.properties
        if self.settings["has_padding"]:
            context.translate(*props.margin)
        cur_color = None
        
        default = props._data
        styles = props.styles
        
        screen_xs, screen_ys = self.comp_screen()
        pcr = pangocairo.CairoContext(context)
        pcr_layout = pcr.create_layout()
        def _render_pango(r, s, font, content, rx=None, ry=None):
            if rx is None and ry is None:
                rx = screen_xs[r] + 1
                ry = screen_ys[s]
            pcr_layout.set_markup('''<span font_desc="%s">%s</span>''' % (font, content))
            context.move_to(rx, ry)
            pcr.show_layout(pcr_layout)
        def _render_char(r, s, c, extents):
            xbearing, ybearing, width, height, xadvance, yadvance = extents[c]
            border_width = props["border", "width"]
            size = props["cell", "size"]
            line_width = props["line", "width"]
            rx = (border_width +
                (r + 0.55) * (size + line_width) -
                width - line_width / 2 - abs(xbearing) / 2)
            ry = (border_width +
                (s + 0.55) * (size + line_width) -
                height - line_width / 2 - abs(ybearing) / 2)
            if (r, s) in styles:
                style = styles[r, s]
                char_font = style["char", "font"]
                char_size = style["char", "size"]
            else:
                char_font = default["char", "font"]
                char_size = default["char", "size"]
            _render_pango(r, s, char_font + " " + char_size[1], c, rx, ry)

        # chars and overlay chars
        n_chars, o_chars = [], []
        if self.settings["show_chars"]:
            n_chars = [(p, q, data[q][p]["char"]) for p, q in cells if data[q][p]["char"] != '']
        if self.settings["render_overlays"]:
            o_chars = [(p, q, c) for p, q in cells for r, s, c in self.overlay if (p, q) == (r, s)]
        extents = {}
        for p, q, c in (n_chars + o_chars):
            if c not in extents:
                extents[c] = context.text_extents(c)
        for p, q, c in n_chars:
            color = styles[p, q]["char", "color"] if (p, q) in styles else default["char", "color"]
            if color != cur_color:
                cur_color = color
                context.set_source_rgb(*[cc / 65535.0 for cc in color])
            _render_char(p, q, c, extents)
        for p, q, c in o_chars:
            # TODO custom color
            color = (65535.0 / 2, 65535.0 / 2, 65535.0 / 2)
            if color != cur_color:
                cur_color = color
                context.set_source_rgb(*[cc / 65535.0 for cc in color])
            _render_char(p, q, c, extents)
        
        cell_size = props["cell", "size"]
        line_width = props["line", "width"]
        
        # highlights
        for p, q in cells:
            # TODO custom color
            color = (65535.0, 65535.0, 65535.0 / 2)
            if color != cur_color:
                cur_color = color
                context.set_source_rgb(*[c / 65535.0 for c in color])
            hwidth = int(cell_size / 8)
            context.set_line_width(hwidth)
            for r, s, direction, length in self.highlights:
                top, bottom, left, right = None, None, None, None
                if direction == "across" and r <= p < r + length and s == q:
                    top = bottom = True
                    right = p == (r + length - 1)
                    left = p == r
                elif direction == "down" and s <= q < s + length and r == p:
                    left = right = True
                    top = q == s
                    bottom = q == (s + length - 1)
                sx = screen_xs[p]
                sy = screen_ys[q]
                lines = []
                if top:
                    lines.append((sx, sy + 0.5 * hwidth, cell_size, 0))
                if bottom:
                    lines.append((sx, sy + cell_size - 0.5 * hwidth, cell_size, 0))
                if left:
                    lines.append((sx + 0.5 * hwidth, sy, 0, cell_size))
                if right:
                    lines.append((sx + cell_size - 0.5 * hwidth, sy, 0, cell_size))
                for rx, ry, rdx, rdy in lines:
                    context.move_to(rx, ry)
                    context.rel_line_to(rdx, rdy)
                    context.stroke()
            context.set_line_width(line_width)
        # block
        for p, q in cells:
            color = styles[p, q]["block", "color"] if (p, q) in styles else default["block", "color"]
            if color != cur_color:
                cur_color = color
                context.set_source_rgb(*[c / 65535.0 for c in color])
            if data[q][p]["block"]:
                rx = screen_xs[p]
                ry = screen_ys[q]
                rsize = cell_size
                margin = styles[p, q]["block", "margin"] if (p, q) in styles else default["block", "margin"]
                if margin == 0:
                    # -0.5 for coordinates and +1 for size
                    # are needed to render seamlessly in PDF
                    context.rectangle(rx - 0.5, ry - 0.5, rsize + 1, rsize + 1)
                else:
                    offset = int((margin / 100.0) * rsize)
                    rsize -= (2 * offset)
                    context.rectangle(rx + offset, ry + offset, rsize, rsize)
                context.fill()
        
        # number
        if self.settings["show_numbers"]:
            numbers = [(p, q) for p, q in cells if data[q][p]["number"] > 0]
            for p, q in numbers:
                if (p, q) in styles:
                    style = styles[p, q]
                    color = style["number", "color"]
                    font = style["number", "font"] + " " + style["number", "size"][1]
                else:
                    color = default["number", "color"]
                    font = default["number", "font"] + " " + default["number", "size"][1]
                if color != cur_color:
                    cur_color = color
                    context.set_source_rgb(*[c / 65535.0 for c in color])
                _render_pango(p, q, font, str(data[q][p]["number"]))

        # circle
        for p, q in cells:
            if (p, q) in styles:
                has_circle = styles[p, q]["circle"]
            else:
                has_circle = default["circle"]
            if has_circle:
                if (p, q) in styles:
                    color = styles[p, q]["block", "color"]
                else:
                    color = default["block", "color"]
                if color != cur_color:
                    cur_color = color
                    context.set_source_rgb(*[c / 65535.0 for c in color])
                context.set_line_width(line_width)
                rsize = cell_size
                rx = screen_xs[p] + rsize / 2
                ry = screen_ys[q] + rsize / 2
                context.new_sub_path()
                context.arc(rx, ry, rsize / 2, 0, 2 * math.pi)
                context.stroke()
        
        # lines
        if len(cells) < self.grid.width * self.grid.height:
            cls = [c for c in cells]
            for x, y in cells:
                cls += self.grid.neighbors(x, y, diagonals=True)
            self.render_lines_of_cells(context, set(cls), screen_xs, screen_ys)
        else:
            self.render_lines_of_cells(context, cells, screen_xs, screen_ys)
        if self.settings["has_padding"]:
            mx, my = props.margin
            context.translate(-1 * mx, -1 * my)
    
    def render_all_lines_of_cell(self, context, x, y, screen_xs, screen_ys):
        """Render the lines that surround a cell (all four sides)."""
        cells = [(x, y)] + list(self.grid.neighbors(x, y, diagonals=True))
        self.render_lines_of_cells(context, cells, screen_xs, screen_ys)
                
    def comp_screen(self):
        """Compute screen coordinates of cells."""
        to_screen = self.properties.grid_to_screen
        xx, yy = {}, {}
        # +1 because we also use coords of invalid cells
        for x in xrange(self.grid.width + 1):
            xx[x] = to_screen(x=x, include_padding=False)
        for y in xrange(self.grid.height + 1):
            yy[y] = to_screen(y=y, include_padding=False)
        return xx, yy

    def render_lines_of_cells(self, context, cells, screen_xs, screen_ys):
        # lines
        """Render the lines that belong to a cell (top and left line)."""
        ctx_move_to = context.move_to
        ctx_rel_line_to = context.rel_line_to
        ctx_stroke = context.stroke
        ctx_set_line_width = context.set_line_width
        ctx_set_source_rgb = context.set_source_rgb
        props = self.properties
        props_line_width = props["line", "width"]
        props_border_width = props["border", "width"]
        props_bar_width = props["bar", "width"]
        props_cell_size = props["cell", "size"]
        props_line_color = props["line", "color"]
        props_border_color = props["border", "color"]
        grid = self.grid
        width = grid.width
        height = grid.height
        data = grid.data
        is_available = grid.is_available
        
        if not grid.lines:
            grid.lines = cPalabra.compute_lines(grid)
            grid.v_lines = []
            for v in grid.lines.values():
                grid.v_lines.extend(v)
        v_lines = grid.v_lines
        the_lines = cPalabra.compute_render_lines(grid
            , data
            , list(cells)
            , grid.lines
            , grid.v_lines
            , screen_xs
            , screen_ys
            , props_line_width
            , props_border_width
            , props_cell_size)
        #the_lines = []
        for x, y in []: #cells:
            lines = self.grid.lines[x, y]
            test = []
            for p, q, ltype, side in lines:
                sx = screen_xs[p]
                sy = screen_ys[q]
                bar = (0 <= x < self.grid.width
                    and 0 <= y < self.grid.height
                    and self.grid.data[y][x]["bar"][ltype])
                border = "border" in side
                
                if side == "normal":
                    start = -0.5 * props_line_width
                elif side == "outerborder":
                    start = -0.5 * props_border_width
                elif side == "innerborder":
                    start = 0.5 * props_border_width
                    if ltype == "top":
                        check = x, y + 1
                    elif ltype == "left":
                        check = x + 1, y
                    if not self.grid.is_available(*check) or not self.grid.is_available(x, y):
                        start -= props_line_width
                
                if ltype == "left":
                    test.append((sx + start, sy, 0, props_cell_size, bar, border))
                elif ltype == "top":
                    ry = sy + start
                    
                    is_lb, dxl = False, 0
                    if ((x, y, "left", "outerborder") in v_lines
                        or (x, y - 1, "left", "outerborder") in v_lines):
                        is_lb, dxl = True, 0
                    if ((x, y, "left", "innerborder") in v_lines
                        or (x, y - 1, "left", "innerborder") in v_lines
                        or (x, y, "left", "normal") in v_lines
                        or (x, y - 1, "left", "normal") in v_lines):
                        is_lb, dxl = False, props_line_width
                    is_rb, dxr = False, 0
                    if ((x + 1, y, "left", "innerborder") in v_lines
                        or (x + 1, y - 1, "left", "innerborder") in v_lines):
                        is_rb, dxr = True, 0
                    if ((x + 1, y, "left", "outerborder") in v_lines
                        or (x + 1, y - 1, "left", "outerborder") in v_lines
                        or (x + 1, y, "left", "normal") in v_lines
                        or (x + 1, y - 1, "left", "normal") in v_lines):
                        is_rb, dxr = False, props_line_width
                    
                    # adjust horizontal lines to fill empty spaces in corners
                    test.append((sx - dxl, ry, props_cell_size + dxl + dxr, 0, bar, border))
                    if is_lb:
                        test.append((sx - dxl - props_border_width, ry, props_border_width, 0, False, True))
                    if is_rb:
                        test.append((sx + props_cell_size, ry, props_border_width, 0, False, True))
            #r = cPalabra.compute_render_lines(grid
            #    , data
            #    , list([(x, y)])
            #    , grid.lines
            #    , grid.v_lines
            #    , screen_xs
            #    , screen_ys
            #    , props_line_width
            #    , props_border_width
            #    , props_cell_size)
            #rr = [(rx, ry, rdx, rdy, True if bar == 1 else False, True if border == 1 else False) for rx, ry, rdx, rdy, bar, border in r]
            #if test != rr:
            #    for i in xrange(len(test)):
            #        print ">>", x, y, test[i], rr[i]
            #    print ">>", x, y, test
            #    print ">>", x, y, rr
            #the_lines.extend(test)
        # bars - TODO property bar width
        ctx_set_line_width(props_bar_width)
        for rx, ry, rdx, rdy, bar, border in the_lines:
            if bar:
                ctx_move_to(rx, ry)
                ctx_rel_line_to(rdx, rdy)
        ctx_stroke()
        # lines
        ctx_set_line_width(props_line_width)
        ctx_set_source_rgb(*[c / 65535.0 for c in props_line_color])
        for rx, ry, rdx, rdy, bar, border in the_lines:
            if not bar and not border:
                ctx_move_to(rx, ry)
                ctx_rel_line_to(rdx, rdy)
        ctx_stroke()
        # borders
        ctx_set_line_width(props_border_width)
        ctx_set_source_rgb(*[c / 65535.0 for c in props_border_color])
        for rx, ry, rdx, rdy, bar, border in the_lines:
            if border:
                ctx_move_to(rx, ry)
                ctx_rel_line_to(rdx, rdy)
        ctx_stroke()
        
    def render_warnings_of_cells(self, context, cells):
        """Determine undesired cells."""
        lengths = {}
        starts = {}
        warn_unchecked = self.settings["warn_unchecked_cells"]
        warn_consecutive = self.settings["warn_consecutive_unchecked"]
        warn_two_letter = self.settings["warn_two_letter_words"]
        check_count = self.grid.get_check_count
        if warn_unchecked or warn_consecutive:
            counts = self.grid.get_check_count_all()
        if warn_two_letter:
            get_start_word = self.grid.get_start_word
            in_direction = self.grid.in_direction
            word_length = self.grid.word_length
        for p, q in cells:
            if warn_unchecked:
                # Color cells that are unchecked. Isolated cells are also colored.
                if 0 <= counts[p, q] <= 1:
                    yield p, q
                    continue
            if warn_consecutive:
                # Color consecutive (two or more) unchecked cells.
                warn = False
                if 0 <= counts[p, q] <= 1:
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        if not (0 <= p + dx < self.grid.width
                            and 0 <= q + dy < self.grid.height):
                            continue
                        if 0 <= counts[p + dx, q + dy] <= 1:
                            warn = True
                            break
                if warn:
                    yield p, q
                    continue
            if warn_two_letter:
                # Color words with length two.
                warn = False
                for d in ["across", "down"]:
                    if (p, q, d) in starts:
                        sx, sy = starts[p, q, d]
                    else:
                        sx, sy = get_start_word(p, q, d)
                        starts[p, q, d] = sx, sy
                        for zx, zy in in_direction(sx, sy, d):
                            starts[zx, zy, d] = sx, sy
                        lengths[sx, sy, d] = word_length(sx, sy, d)
                    if lengths[sx, sy, d] == 2:
                        warn = True
                        break
                if warn:
                    yield p, q
                    continue
        
    def render_locations(self, context, cells):
        """Render one or more cells."""
        has_padding = self.settings["has_padding"]
        if has_padding:
            context.translate(*self.properties.margin)
        screen_xs, screen_ys = self.comp_screen()
        for x, y, r, g, b in cells:
            context.set_source_rgb(r, g, b)
            # -0.5 for coordinates and +1 for size
            # are needed to render seamlessly in PDF
            bx = screen_xs[x] - 0.5
            by = screen_ys[y] - 0.5
            bsize = self.properties["cell", "size"] + 1
            context.rectangle(bx, by, bsize, bsize)
            context.fill()
            self.render_all_lines_of_cell(context, x, y, screen_xs, screen_ys)
        if has_padding:
            mx, my = self.properties.margin
            context.translate(-1 * mx, -1 * my)
        
    # needs manual queue_draw() on drawing_area afterwards
    def refresh_visual_size(self, drawing_area):
        """Recalculate the visual width and height and resize the drawing area."""
        drawing_area.set_size_request(*self.properties.visual_size())

class GridPreview(gtk.VBox):
    def __init__(self
        , mode=constants.VIEW_MODE_PREVIEW
        , header="Preview"):
        gtk.VBox.__init__(self)
        self.magnify = False
        self.view = None
        self.preview_surface = None
        self.preview_pattern = None
        self.render_mode = mode
        
        label = gtk.Label()
        label.set_alignment(0, 0)
        label.set_markup(''.join(["<b>", header, "</b>"]))
        
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
        
    def refresh(self, force=False):
        if force:
            self.preview_surface = None
        if self.view is not None:
            self.view.properties["cell", "size"] = 128 if self.magnify else 16
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
                self.view.render(context, self.render_mode)
            context = drawing_area.window.cairo_create()
            context.set_source(self.preview_pattern)
            context.paint()
