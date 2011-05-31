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
import json
import pango
import pangocairo
from operator import itemgetter
import os

from lxml import etree

import constants
import grid
from grid import Grid
from puzzle import Puzzle
from view import CellStyle, GridView, _relative_to, DEFAULTS
import view

XPF_META_ELEMS = {'Type': 'type'
    , 'Title': constants.META_TITLE
    , 'Author': constants.META_CREATOR
    , 'Editor': constants.META_EDITOR
    , 'Copyright': constants.META_COPYRIGHT
    , 'Publisher': constants.META_PUBLISHER
    , 'Date': constants.META_DATE
}
IPUZ_MY_META_ELEMS = {
    'copyright': constants.META_COPYRIGHT
    , 'publisher': constants.META_PUBLISHER
    , 'title': constants.META_TITLE
    , 'author': constants.META_CREATOR
    , 'editor': constants.META_EDITOR
    , 'date': constants.META_DATE
}
IPUZ_META_ELEMS = [
    "publication", "url", "uniqueid", "intro", "explanation"
    , "annotation", "notes", "difficulty"
]
IPUZ_TECH_ELEMS = [
    "origin", "block", "empty", "styles", "checksum" #, "saved"
]
IPUZ_CROSS_ELEMS = [
    "dimensions", "puzzle", "saved", "solution", "clues"
    , "showenumerations", "clueplacement", "fill", "answer", "answers"
    , "enumeration", "enumerations", "misses"
]

IPUZ_BLOCK_CHAR = '#'
IPUZ_EMPTY_CHAR = 0

class ParserError(Exception):
    def __init__(self, message):
        self.message = message

class XPFParserError(ParserError):
    def __init__(self, message=""):
        ParserError.__init__(self, "XPFParserError: " + message)

class IPUZParserError(ParserError):
    def __init__(self, message=""):
        ParserError.__init__(self, "IPUZParserError: " + message)

def get_real_filename(f):
    return os.path.join(os.path.split(__file__)[0], f)

def export_puzzle(puzzle, filename, options):
    outputs = [k for k in options["output"].keys() if options["output"][k]]
    settings = options["settings"]
    if options["format"] == "csv":
        export_to_csv(puzzle, filename, outputs, settings)
    elif options["format"] == "pdf":
        settings.update({
            "clue_header": {"font": "Sans 10"}
            , "clue": {"font": "Sans 8"}
            , "page_header": {"font": "Sans 10"}
        })
        export_to_pdf(puzzle, filename, outputs, settings)
    elif options["format"] == "png":
        export_to_png(puzzle, filename, outputs[0], settings)

def read_crossword(filename, warnings=True):
    t = determine_file_type(filename)
    if t is None:
        raise ParserError("Palabra was unable to open: " + filename)
    results = FILETYPES[t]['reader'](filename, warnings)
    e_type = FILETYPES[t]['exception']
    if not results:
        raise e_type(u"No puzzle was found in this file.")
    if len(results) > 1:
        raise e_type(u"This is a container file instead of a puzzle file.")
    return results[0]

def determine_file_type(filename):
    t = None
    with open(filename, 'r') as f:
        content = f.read(4)
        if content == 'ipuz':
            t = constants.PUZZLE_IPUZ
    if t is None:
        try:
            doc = etree.parse(filename)
        except etree.XMLSyntaxError:
            raise ParserError(u"This is not a valid Palabra puzzle file.")
        root = doc.getroot()
        if root.tag == "Puzzles":
            t = constants.PUZZLE_XPF
    return t
    
def read_containers(files):
    def load_container(f):
        f = get_real_filename(f)
        if os.path.isfile(f):
            return f, {}, read_xpf(f)
        else:
            # return None as f to indicate 'failure'
            return None, {}, []
    return [load_container(f) for f in files]

def write_containers(patterns):
    for f, meta, puzzles in patterns:
        write_xpf(puzzles, filename=f, compact=True)

def export_to_csv(puzzle, filename, outputs, settings):
    f = open(filename, 'w')
    
    def write_csv_grid(output):
        line = [output, settings["separator"]
            , str(puzzle.grid.width), settings["separator"]
            , str(puzzle.grid.height), "\n"]
        f.write(''.join(line))
        for y in xrange(puzzle.grid.height):
            line = []
            for x in xrange(puzzle.grid.width):
                if puzzle.grid.is_block(x, y):
                    line.append(".")
                else:
                    if output == "grid":
                        line.append(" ")
                    elif output == "solution":
                        char = puzzle.grid.get_char(x, y)
                        if char != "":
                            line.append(char)
                        else:
                            line.append(" ")
                if x < puzzle.grid.width - 1:
                    line.append(settings["separator"])
            line.append("\n")
            f.write(''.join(line))
    
    if "grid" in outputs:
        write_csv_grid("grid")
    if "solution" in outputs:
        write_csv_grid("solution")
    if "clues" in outputs:
        clues = \
            [("across", puzzle.grid.horizontal_clues())
            ,("down", puzzle.grid.vertical_clues())
            ]
            
        for direction, clue_iterable in clues:
            for n, x, y, clue in clue_iterable:
                line = [direction, settings["separator"]
                    , str(n), settings["separator"]]

                try:
                    line.append(clue["text"])
                except KeyError:
                    line.append("")
                line.append(settings["separator"])
                
                try:
                    line.append(clue["explanation"])
                except KeyError:
                    line.append("")
                line.append("\n")
                f.write(''.join(line))
    f.close()

def compute_header(puzzle, header, page_n=None):
    if page_n is not None:
        code = constants.META_CODES[constants.META_PAGE_NUMBER]
        return header.replace(code, str(page_n + 1))
    for key, code in constants.META_CODES.items():
        if key == constants.META_PAGE_NUMBER:
            continue
        if key in puzzle.metadata:
            header = header.replace(code, puzzle.metadata[key])
        elif key in constants.META_EXPORT_VALUES:
            if key == constants.META_FILENAME:
                if puzzle.filename is not None:
                    value = os.path.basename(puzzle.filename)
                else:
                    value = constants.META_CODES[key]
            elif key == constants.META_FILEPATH:
                if puzzle.filename is not None:
                    value = puzzle.filename
                else:
                    value = constants.META_CODES[key]
            elif key == constants.META_WIDTH:
                value = str(puzzle.grid.width)
            elif key == constants.META_HEIGHT:
                value = str(puzzle.grid.height)
            elif key == constants.META_N_WORDS:
                value = str(puzzle.grid.count_words())
            elif key == constants.META_N_BLOCKS:
                value = str(puzzle.grid.count_blocks())
            header = header.replace(code, value)
    return header
    
class PangoCairoTable():
    def __init__(self, columns, margin):
        self.columns = columns
        self.margin = margin
        
    def render_rows(self, context, rows, height, offset=0):
        y = 0
        for i, (r_1, r_2) in enumerate(rows[offset:]):
            if y >= height:
                return True, offset + i
            r_y = self.render(context, 0, y, r_1, wrap=True)
            if r_2 is not None:
                self.render(context, 2, y, r_2)
            y += r_y #(r_y / 2) # TODO why divide by 2
        return True, None
        
    def render(self, context, x, y, text, wrap=False):
        pcr = pangocairo.CairoContext(context)
        layout = pcr.create_layout()
        if wrap:
            layout.set_width(pango.SCALE * self.columns[x])
            layout.set_wrap(pango.WRAP_WORD_CHAR)
        layout.set_markup(text)
        r_x = sum(self.columns[0:x])
        context.move_to(self.margin[0] + r_x, self.margin[1] + y)
        pcr.show_layout(layout)
        w, h = layout.get_pixel_size()
        return h
                    
def export_to_pdf(puzzle, filename, outputs, settings):
    paper_size = gtk.PaperSize(gtk.PAPER_NAME_A4)
    width = paper_size.get_width(gtk.UNIT_POINTS)
    height = paper_size.get_height(gtk.UNIT_POINTS)
    mm_unit = width / paper_size.get_width(gtk.UNIT_MM)
    
    margin_left = settings["margin_left"] * mm_unit
    margin_right = settings["margin_right"] * mm_unit
    margin_top = settings["margin_top"] * mm_unit
    margin_bottom = settings["margin_bottom"] * mm_unit
    c_width = width - margin_left - margin_right
    c_height = height - margin_top - margin_bottom
    
    surface = cairo.PDFSurface(filename, width, height)
    context = cairo.Context(surface)
    def pdf_header(header):
        p_h = settings["page_header"]
        pcr = pangocairo.CairoContext(context)
        layout = pcr.create_layout()
        text = ['<span font_desc="', p_h["font"], '">', header, "</span>"]
        layout.set_markup(''.join(text))
        context.move_to(margin_left, margin_top)
        pcr.show_layout(layout)
        w, h = layout.get_pixel_size()
        return h
    def produce_clues(clue_break=False, answers=False, reduce_to_rows=False):
        content = {"clue_markup": {}, "clues": {}}
        c_h = settings["clue_header"]
        c_h_font = c_h["font"]
        c_h_bold = settings["clue_header_bold"]
        c_h_italic = settings["clue_header_italic"]
        c_h_under = settings["clue_header_underline"]
        c_c = settings["clue"]
        c_c_font = c_c["font"]
        has_bold_number = settings["clue_number_bold"]
        has_number_period = settings["clue_number_period"]
        has_clue_length = settings["clue_length"]
        grid = puzzle.grid
        word_length = grid.word_length
        gather_word = grid.gather_word
        clues = grid.clues
        for d in ["across", "down"]:
            c_h_txt = settings["clue_header_" + d]
            content["clue_header_" + d] = ''.join(['''<span font_desc="''', c_h_font, '''">'''
                , ("<b>" if c_h_bold else '')
                , ("<i>" if c_h_italic else '')
                , ("<u>" if c_h_under else '')
                , c_h_txt
                , ("</u>" if c_h_under else '')
                , ("</i>" if c_h_italic else '')
                , ("</b>" if c_h_bold else '')
                , '''</span>'''])
            content["clue_markup"][d] = '<span font_desc="' + c_c_font + '">'
            content["clues"][d] = []
            for n, x, y, clue in clues(d):
                clue_txt = []
                try:
                    txt = clue["text"]
                except KeyError:
                    txt = '<span color="#ff0000">(missing clue)</span>'
                if "&" in txt:
                    txt = txt.replace("&", "&amp;")
                if has_bold_number:
                    clue_txt += ["<b>"]
                clue_txt += [str(n)]
                if has_number_period:
                    clue_txt += ['.']
                if has_bold_number:
                    clue_txt += ["</b>"]
                clue_txt += [' ', txt]
                if has_clue_length:
                    clue_txt += [" (", str(word_length(x, y, d)), ")"]
                if clue_break:
                    clue_txt += ["\n"]
                result = ''.join(clue_txt)
                if answers:
                    result = (result, gather_word(x, y, d))
                content["clues"][d].append(result)
        if reduce_to_rows:
            rows = []
            for d in ["across", "down"]:
                rows.append((content["clue_header_" + d], None))
                for clue, answer in content["clues"][d]:
                    pre = content["clue_markup"][d]
                    post = "</span>"
                    clue = ''.join([pre, clue, post])
                    answer = ''.join([pre, answer, post])
                    rows.append((clue, answer))
            return rows
        return content
    def show_clues_columns(content, columns):
        stream = dict([(d, content["clues"][d]) for d in ["across", "down"]])
        a_count, d_count = len(stream["across"]), len(stream["down"])
        r_columns = []
        offset = 0
        incl_a_header = False
        incl_d_header = False
        clue_header_across = content["clue_header_across"]
        clue_header_down = content["clue_header_down"]
        clue_markup_across = content["clue_markup"]["across"]
        clue_markup_down = content["clue_markup"]["down"]
        stream_across = stream["across"]
        stream_down = stream["down"]
        for page, x, y, w, h in columns:
            pcr = pangocairo.CairoContext(context)
            layout = pcr.create_layout()
            layout.set_width(pango.SCALE * w)
            layout.set_wrap(pango.WRAP_WORD_CHAR)
            lay_get_pixel_size = layout.get_pixel_size
            lay_set_markup = layout.set_markup
            text = ''
            done = False
            totally_done = False
            count = 32
            step_size = 32
            while not done:
                has_a_header = False
                has_d_header = False
                a_clues = []
                d_clues = []
                if offset > a_count:
                    d_start = offset - a_count
                    d_clues = stream_down[d_start:d_start + count]
                else:
                    a_c = a_count - offset
                    if count <= a_c:
                        a_clues = stream_across[offset:offset + count]
                    else:
                        a_clues = stream_across[offset:a_count]
                        d_clues = stream_down[0:count - a_c]
                col = []
                if offset == 0 and not incl_a_header:
                    col.append(clue_header_across + "\n")
                    has_a_header = True
                if a_clues:
                    col.append(clue_markup_across)
                    col.extend(a_clues)
                    col.append("</span>\n")
                if d_clues:
                    if not incl_d_header:
                        col.append(clue_header_down + "\n")
                        has_d_header = True
                    col.append(clue_markup_down)
                    col.extend(d_clues)
                    col.append("</span>")
                text = ''.join(col)
                lay_set_markup(text)
                l_w, l_h = lay_get_pixel_size()
                n_clues = len(a_clues + d_clues)
                if l_h <= h:
                    if offset + n_clues == a_count + d_count:
                        done = True
                        totally_done = True
                    else:
                        count += step_size
                elif l_h > h:
                    step_size /= 2
                    count -= step_size
                    if step_size == 1:
                        offset += n_clues
                        done = True
            r_columns.append((page, x, y, w, h, text))
            if has_a_header:
                incl_a_header = True
            if has_d_header:
                incl_d_header = True
            if totally_done:
                break
        pages = []
        for p, x, y, w, h, text in r_columns:
            if p not in pages:
                pages.append(p)
        def render_page(page, header_delta=None):
            for p, x, y, w, h, text in r_columns:
                if p != page:
                    continue
                context.move_to(x, y)
                pcr = pangocairo.CairoContext(context)
                layout = pcr.create_layout()
                layout.set_width(pango.SCALE * w)
                layout.set_wrap(pango.WRAP_WORD_CHAR)
                layout.set_markup(text)
                pcr.show_layout(layout)
            return True, None
        return [(render_page, p) for p in pages]
    def gen_columns(col_width
        , padding=None
        , grid_w=None
        , grid_h=None
        , position=None
        , header_delta=None):
        clue_placement = settings["clue_placement"]
        n_columns = settings["n_columns"]
        page = 0
        x, y = margin_left, margin_top
        pos_x, pos_y = position
        while True:
            for n in xrange(n_columns):
                col_height = c_height - header_delta
                col_x = x + n * col_width + n * padding
                col_y = y
                shrink = False
                if page == 0:
                    if clue_placement == "below":
                        shrink = True
                    elif clue_placement == "wrap":
                        shrink = (col_x < pos_x + grid_w
                            and col_x + col_width > pos_x
                            and col_y < pos_y + grid_h
                            and col_y + col_height > pos_y)
                if shrink:
                    col_height -= (grid_h + padding)
                    col_y += (grid_h + padding)
                yield page, col_x, col_y, col_width, col_height
            page += 1
    def adjust_grid_props(align, cell_size=7):
        padding = int(c_width * settings["column_spacing"] / 100)
        n_columns = settings["n_columns"]
        col_width = int((c_width - ((n_columns - 1) * padding)) / n_columns)
        props = puzzle.view.properties
        prevs = {
            ("cell", "size"): props["cell", "size"]
            , "margin": props.margin
        }
        props["cell", "size"] = cell_size * mm_unit
        grid_w, grid_h = props.visual_size(False)
        if align == "right":
            position = width - margin_right - grid_w, margin_top
        elif align == "center":
            position = margin_left + (c_width - grid_w) / 2, margin_top
        elif align == "left":
            position = margin_left, margin_top
        return col_width, prevs, grid_w, grid_h, position, padding
    def produce_puzzle(mode, prevs, position, add_clues=False):
        def render_puzzle(header_delta=None):
            puzzle.view.properties.margin = position
            puzzle.view.render(context, mode)
            puzzle.view.pdf_reset(prevs)
            return (not add_clues), None
        return [(render_puzzle, None)]
    p_h_include = settings["page_header_include"]
    p_h_all = settings["page_header_include_all"]
    page_n = 0
    header = compute_header(puzzle, settings["page_header_text"])
    GRID_ALIGNMENT = {"puzzle": settings["align"]
        , "grid": "center"
        , "solution": "center"
    }
    CELL_SIZE = {"puzzle": settings["cell_size_puzzle"]
        , "grid": settings["cell_size_puzzle"]
        , "solution": settings["cell_size_solution"]
    }
    RENDER_MODE = {
        "puzzle": constants.VIEW_MODE_EXPORT_PDF_PUZZLE
        , "grid": constants.VIEW_MODE_EXPORT_PDF_PUZZLE
        , "solution": constants.VIEW_MODE_EXPORT_PDF_SOLUTION
    }
    def compute_funcs(header_delta):
        if o in ["puzzle", "grid", "solution"]:
            grid_props = adjust_grid_props(GRID_ALIGNMENT[o], CELL_SIZE[o])
            funcs = produce_puzzle(RENDER_MODE[o], grid_props[1], grid_props[4], o == "puzzle")
        if o == "puzzle":
            columns = gen_columns(grid_props[0]
                , grid_props[5], grid_props[2], grid_props[3]
                , grid_props[4], header_delta)
            funcs += show_clues_columns(produce_clues(clue_break=True), columns)
        elif o == "answers":
            rows = produce_clues(clue_break=True, answers=True, reduce_to_rows=True)
            w1 = int((settings["answers_clue_width"] / 100.0) * c_width)
            w2 = int((settings["answers_clue_sep"] / 100.0) * c_width)
            w3 = c_width - w1 - w2
            table = PangoCairoTable([w1, w2, w3], margin=(margin_left, margin_top))
            def render_table(offset, header_delta):
                return table.render_rows(context, rows, c_height - header_delta, offset)
            funcs = [(render_table, 0)]
        return funcs
    for o in outputs:
        funcs = None
        done = False
        count = 0
        while not done:
            context.save()
            header_delta = 0
            if p_h_include and (True if p_h_all else page_n == 0):
                header_height = pdf_header(compute_header(puzzle, header, page_n))
                header_delta = header_height + 10
                context.translate(0, header_delta)
            if funcs is None:
                funcs = compute_funcs(header_delta)
            todo = funcs[count:]
            for f, f_args in todo:
                count += 1
                r, new_arg = f(f_args, header_delta) if f_args is not None else f(header_delta)
                if new_arg is not None:
                    funcs.append((f, new_arg))
                if not r:
                    continue
                context.show_page()
                page_n += 1
                break
            context.restore()
            done = count == len(funcs)
    surface.finish()
    
def export_to_png(puzzle, filename, output, settings):
    width, height = puzzle.view.properties.visual_size(False)
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    context = cairo.Context(surface)
    context.rectangle(0, 0, width, height)
    modes = {"grid": constants.VIEW_MODE_EMPTY, "solution": constants.VIEW_MODE_SOLUTION}
    puzzle.view.render(context, modes[output])
    surface.write_to_png(filename)
    surface.finish()

# http://www.ipuz.org/    
def read_ipuz(filename, warnings=True):
    results = []
    content = None
    with open(filename, 'r') as f:
        content = f.read()
        content = content.strip('\n')
    if content is not None:
        data = json.loads(content[5:-1])
        keys = data.keys()
        if "version" not in keys:
            raise IPUZParserError(u"Mandatory version element missing in ipuz file.")
        if "kind" not in keys:
            raise IPUZParserError(u"Mandatory kind element missing in ipuz file.")
        n_kinds = len(data["kind"])
        if n_kinds == 0:
            raise IPUZParserError(u"Mandatory kind element has no content.")
        if n_kinds > 1:
            raise IPUZParserError(u"Mandatory kind element has more than one puzzle kind.")
        kind = data["kind"][0]
        if kind != "http://ipuz.org/crossword#1":
            raise IPUZParserError(u"This type of puzzle (" + kind + ") is not supported.")
        r_meta = {}
        r_width = None
        r_height = None
        r_grid = None
        r_notepad = ""
        r_styles = {}
        r_gstyles = {}
        r_number_mode = constants.NUMBERING_AUTO
        for m in IPUZ_MY_META_ELEMS:
            if m in data:
                r_meta[IPUZ_MY_META_ELEMS[m]] = data[m]
        for m in IPUZ_META_ELEMS:
            if m in data:
                r_meta[m] = data[m]
        c_block = IPUZ_BLOCK_CHAR
        c_empty = IPUZ_EMPTY_CHAR
        for t in IPUZ_TECH_ELEMS:
            if t in data:
                if t == "block":
                    r_meta[t] = c_block = data[t]
                elif t == "empty":
                    r_meta[t] = c_empty = data[t]
                else:
                    pass # TODO
        for e in IPUZ_CROSS_ELEMS:
            if e in data:
                if e == "dimensions":
                    r_width = data[e]["width"]
                    r_height = data[e]["height"]
                elif e == "puzzle":
                    assert r_width >= 0
                    assert r_height >= 0
                    r_grid = Grid(r_width, r_height)
                    x, y = 0, 0
                    for row in data[e]:
                        for x, c in enumerate(row):
                            if isinstance(c, dict):
                                if "style" in c:
                                    style = c["style"]
                                    if "shapebg" in style:
                                        if style["shapebg"] == "circle":
                                            if (x, y) not in r_styles:
                                                r_styles[x, y] = CellStyle()
                                            r_styles[x, y]["circle"] = True
                                    if "color" in style:
                                        if (x, y) not in r_styles:
                                            r_styles[x, y] = CellStyle()
                                        rgb = hex_to_color('#' + style["color"])
                                        r_styles[x, y]["cell", "color"] = rgb
                                    if "colortext" in style:
                                        if (x, y) not in r_styles:
                                            r_styles[x, y] = CellStyle()
                                        rgb = hex_to_color(style["colortext"])
                                        r_styles[x, y]["char", "color"] = rgb
                                if "cell" in c:
                                    c = c["cell"]
                                    # fall-through
                            if c == None:
                                r_grid.set_void(x, y, True)
                            elif c == c_block:
                                r_grid.set_block(x, y, True)
                            elif c == c_empty:
                                pass
                        y += 1
                elif e == "solution":
                    assert r_grid is not None
                    x, y = 0, 0
                    for row in data[e]:
                        for x, c in enumerate(row):
                            if isinstance(c, list) or isinstance(c, dict):
                                print "TODO"
                            elif c is not None and c != c_block and c != c_empty:
                                r_grid.set_char(x, y, c)
                        y += 1
                elif e == "clues":
                    assert r_grid is not None
                    clues = {}
                    for md, d in [("across", "Across"), ("down", "Down")]:
                        if d in data[e]:
                            for n, clue in data[e][d]:
                                clues[n, md] = clue
        if r_number_mode == constants.NUMBERING_AUTO:
            r_grid.assign_numbers()
        for d in ["across", "down"]:
            for n, x, y in r_grid.words_by_direction(d):
                if (n, d) in clues:
                    r_grid.store_clue(x, y, d, "text", clues[n, d])
        p = Puzzle(r_grid, r_styles, r_gstyles)
        p.metadata = r_meta
        p.type = constants.PUZZLE_IPUZ
        p.filename = filename
        p.notepad = r_notepad
        results.append(p)
    return results

def write_ipuz(puzzle, backup=True):
    contents = {}
    contents["origin"] = "Palabra " + constants.VERSION
    contents["version"] = "http://ipuz.org/v1"
    contents["kind"] = ["http://ipuz.org/crossword#1"]
    meta = puzzle.metadata
    for dc, e in [(b, a) for a, b in IPUZ_MY_META_ELEMS.items()]:
        if dc in meta:
            contents[e] = meta[dc]
    c_block = meta["block"] if "block" in meta else IPUZ_BLOCK_CHAR
    c_empty = meta["empty"] if "empty" in meta else IPUZ_EMPTY_CHAR
    for k, v in [("block", c_block), ("empty", c_empty)]:
        if k in meta:
            contents[k] = v
    for e in IPUZ_META_ELEMS:
        if e in meta:
            contents[e] = meta[e]
    props = puzzle.view.properties
    styles = props.styles
    diffs = {}
    for key in ["circle", ("cell", "color"), ("char", "color")]:
        diffs[key] = [c for c in styles if styles[c][key] != props[key]]
    puz = []
    width = puzzle.grid.width
    height = puzzle.grid.height
    contents["dimensions"] = {"width": width, "height": height}
    for y in xrange(height):
        row = []
        for x in xrange(width):
            n = puzzle.grid.data[y][x]["number"]
            if n != 0:
                cell = n
            elif puzzle.grid.data[y][x]["block"]:
                cell = c_block
            elif puzzle.grid.data[y][x]["void"]:
                cell = None
            else:
                cell = c_empty
            style = {}
            if (x, y) in diffs["circle"]:
                style["shapebg"] = "circle"
            if (x, y) in diffs["cell", "color"]:
                color = color_to_hex(styles[x, y]["cell", "color"], include=False)
                style["color"] = color
            if (x, y) in diffs["char", "color"]:
                color = color_to_hex(styles[x, y]["char", "color"], include=False)
                style["colortext"] = color
            if style:
                row.append({"cell": cell, "style": style})
            else:
                row.append(cell)
        puz.append(row)
    contents["puzzle"] = puz
    clues = {}
    for d, ipuz_d in [("across", "Across"), ("down", "Down")]:
        clues[ipuz_d] = []
        for n, x, y, data in puzzle.grid.clues(d):
            if "text" in data:
                clues[ipuz_d].append([n, data["text"]])
    contents["clues"] = clues
    solution = []
    for y in xrange(height):
        row = []
        for x in xrange(width):
            if puzzle.grid.data[y][x]["block"]:
                row.append(c_block)
            elif puzzle.grid.data[y][x]["void"]:
                row.append(None)
            else:
                 c = puzzle.grid.data[y][x]["char"]
                 if c != '':
                    row.append(c)
                 else:
                    row.append(c_empty)
        solution.append(row)
    contents["solution"] = solution
    contents = ''.join(['ipuz(', json.dumps(contents), ')'])
    _write_puzzle(puzzle.filename, contents, backup)

# http://www.xwordinfo.com/XPF/
def read_xpf(filename, warnings=True):
    results = []
    try:
        doc = etree.parse(filename)
    except etree.XMLSyntaxError:
        raise XPFParserError(u"No valid XML syntax.")
    puzzles = doc.getroot()
    if puzzles.tag != "Puzzles":
        raise XPFParserError(u"No root element called Puzzles found.")
    version = puzzles.get("Version")
    if version is None:
        raise XPFParserError(u"No version specified for this XPF file. Possible older than v1.0?")
    try:
        version = float(version)
    except ValueError:
        raise XPFParserError("uXPF version is not a valid number")
    if version < 1.0:
        raise XPFParserError("uXPF versions older than 1.0 are not supported.")
    for puzzle in puzzles:
        if puzzle.tag != "Puzzle":
            if warnings:
                print "Warning: skipping a child of Puzzles that is not a Puzzle."
            continue
        r_meta = {}
        r_width = None
        r_height = None
        r_grid = None
        r_notepad = ""
        r_styles = {}
        r_gstyles = {}
        r_number_mode = constants.NUMBERING_AUTO
        for child in puzzle:
            if child.tag in XPF_META_ELEMS:
                r_meta[XPF_META_ELEMS[child.tag]] = child.text
            elif child.tag == "Size":
                for d in child:
                    try:
                        if d.tag == "Rows":
                            r_height = int(d.text)
                        elif d.tag == "Cols":
                            r_width = int(d.text)
                    except ValueError:
                        raise XPFParserError(u"Invalid grid dimensions were specified.")
            elif child.tag == "Grid":
                if r_width is None:
                    raise XPFParserError(u"The number of columns was not specified.")
                if r_height is None:
                    raise XPFParserError(u"The number of rows was not specified.")
                assert r_width >= 0
                assert r_height >= 0
                r_grid = Grid(r_width, r_height)
                y = 0
                for row in child:
                    if row.tag != "Row":
                        if warnings:
                            print "Warning: skipping a child of Grid that is not a Row."
                        continue
                    if not row.text:# or len(row.text) < r_width:
                        if warnings:
                            print "Warning: skipping a row with missing content."
                        continue
                    for x, c in enumerate(row.text):
                        if c == '.':
                            r_grid.data[y][x]["block"] = True
                        elif c == '~':
                            r_grid.data[y][x]["void"] = True
                        else:
                            r_grid.data[y][x]["char"] = c if c != ' ' else ''
                    y += 1
            elif child.tag == "Circles":
                for circle in child:
                    if circle.tag != "Circle":
                        if warnings:
                            print "Warning: skipping a child of Circles that is not a Circle."
                        continue
                    a_row = circle.get("Row")
                    a_col = circle.get("Col")
                    if not (a_row and a_col):
                        if warnings:
                            print "Warning: skipping a child of Circles with missing content."
                        continue
                    try:
                        x = int(a_col) - 1
                        y = int(a_row) - 1
                    except ValueError:
                        if warnings:
                            print "Warning: skipping child of Circles with invalid coordinates."
                        continue
                    if (x, y) not in r_styles:
                        r_styles[x, y] = CellStyle()
                    r_styles[x, y]["circle"] = True
            elif child.tag == "RebusEntries":
                for rebus in child:
                    if rebus.tag != "Rebus":
                        if warnings:
                            print "Warning: skipping a child of RebusEntries that is not a Rebus."
                        continue
                    a_row = rebus.get("Row")
                    a_col = rebus.get("Col")
                    a_short = rebus.get("Short")
                    content = rebus.text
                    if not (a_row and a_row and a_short and content):
                        if warnings:
                            print "Warning: skipping a child of RebusEntries with missing content."
                        continue
                    try:
                        x = int(a_col) - 1
                        y = int(a_row) - 1
                    except ValueError:
                        if warnings:
                            print "Warning: skipping child of RebusEntries with invalid coordinates."
                        continue
                    r_grid.set_rebus(x, y, a_short, content)
            elif child.tag == "Shades":
                for shade in child:
                    if shade.tag != "Shade":
                        if warnings:
                            print "Warning: skipping a child of Shades that is not a Shade."
                        continue
                    a_row = shade.get("Row")
                    a_col = shade.get("Col")
                    if not (a_row and a_col and shade.text):
                        if warnings:
                            print "Warning: skipping a child of Shades with missing content."
                        continue
                    try:
                        x = int(a_col) - 1
                        y = int(a_row) - 1
                    except ValueError:
                        if warnings:
                            print "Warning: skipping a child of Shades with invalid coordinates."
                        continue
                    if (x, y) not in r_styles:
                        r_styles[x, y] = CellStyle()
                    if shade.text == "gray":
                        rgb = (32767, 32767, 32767)
                    elif shade.text[0] == '#':
                        rgb = hex_to_color(shade.text)
                    r_styles[x, y]["cell", "color"] = rgb
            elif child.tag == "Clues":
                for clue in child:
                    if clue.tag != "Clue":
                        if warnings:
                            print "Warning: skipping a child of Clues that is not a Clue."
                        continue
                    a_row = clue.get("Row")
                    a_col = clue.get("Col")
                    a_num = clue.get("Num")
                    a_dir = clue.get("Dir")
                    a_ans = clue.get("Ans")
                    if not (a_row and a_col and a_dir):
                        if warnings:
                            print "Warning: skipping a child of Clues with missing content."
                        continue
                    try:
                        x = int(a_col) - 1
                        y = int(a_row) - 1
                    except ValueError:
                        if warnings:
                            print "Warning: skipping a child of Clues with invalid coordinates."
                        continue
                    dirs = {"Across": "across", "Down": "down"}
                    if a_dir not in dirs:
                        if warnings:
                            print "Warning: skipping a clue with a direction that is not across or down."
                        continue
                    if not clue.text:
                        if warnings:
                            print "Warning: skipping clue without text."
                        continue
                    r_grid.store_clue(x, y, dirs[a_dir], "text", clue.text)
            elif child.tag == "Notepad":
                r_notepad = child.text
            elif child.tag == "Palabra":
                version = child.get("Version")
                if version > constants.VERSION:
                    # for now, don't try
                    if warnings:
                        print "Warning: Palabra-specific puzzle content was not loaded as it was made in a newer version of Palabra."
                    continue
                for c in child:
                    if c.tag == "Explanation":
                        a_row = c.get("Row")
                        a_col = c.get("Col")
                        a_dir = c.get("Dir")
                        if not (a_row and a_col and a_dir):
                            if warnings:
                                print "Warning: skipping Explanation with missing content"
                            continue
                        try:
                            x = int(a_col) - 1
                            y = int(a_row) - 1
                        except ValueError:
                            if warnings:
                                print "Warning: skipping Explanation with invalid coordinates."
                            continue
                        dirs = {"Across": "across", "Down": "down"}
                        if a_dir not in dirs:
                            if warnings:
                                print "Warning: skipping Explanation with a direction that is not across or down."
                            continue
                        if not c.text:
                            if warnings:
                                print "Warning: skipping explanation without text."
                            continue
                        r_grid.store_clue(x, y, dirs[a_dir], "explanation", c.text)
                    elif c.tag == "Style":
                        for s in c:
                            if s.tag == "Bar":
                                width = s.get("Width")
                                if width is not None:
                                    r_gstyles["bar", "width"] = int(width)
                            elif s.tag == "Border":
                                width = s.get("Width")
                                if width is not None:
                                    r_gstyles["border", "width"] = int(width)
                                color = s.get("Color")
                                if color is not None:
                                    r_gstyles["border", "color"] = hex_to_color(color)
                            elif s.tag == "Cell":
                                size = s.get("Size")
                                if size is not None:
                                    r_gstyles["cell", "size"] = int(size)
                                color = s.get("Color")
                                if color is not None:
                                    r_gstyles["cell", "color"] = hex_to_color(color)
                            elif s.tag == "Line":
                                width = s.get("Width")
                                if width is not None:
                                    r_gstyles["line", "width"] = int(width)
                                color = s.get("Color")
                                if color is not None:
                                    r_gstyles["line", "color"] = hex_to_color(color)
                            elif s.tag == "Block":
                                color = s.get("Color")
                                if color is not None:
                                    r_gstyles["block", "color"] = hex_to_color(color)
                                margin = s.get("Margin")
                                if margin is not None:
                                    r_gstyles["block", "margin"] = int(margin)
                            elif s.tag == "Char":
                                color = s.get("Color")
                                if color is not None:
                                    r_gstyles["char", "color"] = hex_to_color(color)
                                size = s.get("Size")
                                if size is not None:
                                    s_s = int(size)
                                    s_k = ("cell", "size")
                                    s_d = {s_k: (r_gstyles[s_k] if s_k in r_gstyles else DEFAULTS[s_k])}
                                    s_r = _relative_to(s_k, s_s / 100.0, d=s_d)
                                    r_gstyles["char", "size"] = (s_s, s_r)
                            elif s.tag == "Number":
                                color = s.get("Color")
                                if color is not None:
                                    r_gstyles["number", "color"] = hex_to_color(color)
                                size = s.get("Size")
                                if size is not None:
                                    s_s = int(size)
                                    s_k = ("cell", "size")
                                    s_d = {s_k: (r_gstyles[s_k] if s_k in r_gstyles else DEFAULTS[s_k])}
                                    s_r = _relative_to(s_k, s_s / 100.0, d=s_d)
                                    r_gstyles["number", "size"] = (s_s, s_r)
        if r_number_mode == constants.NUMBERING_AUTO:
            r_grid.assign_numbers()
        p = Puzzle(r_grid, r_styles, r_gstyles)
        p.metadata = r_meta
        p.type = constants.PUZZLE_XPF
        p.filename = filename
        p.notepad = r_notepad
        results.append(p)
    return results
    
def write_xpf(content, backup=True, filename=None, compact=False):
    """Accepts a Puzzle object or a list of Puzzle objects."""
    root = etree.Element("Puzzles")
    root.set("Version", "1.0")
    if isinstance(content, Puzzle):
        contents = _write_xpf_xml(root, content)
        _write_puzzle(content.filename, contents, backup)
    elif isinstance(content, list):
        for p in content:
            _write_xpf_xml(root, p, compact)
        contents = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
        _write_puzzle(filename, contents, backup)

def color_to_hex(color, include=True):
    def to_hex(value):
        hv = hex(int(value / 65535.0 * 255))[2:]
        return hv if len(hv) == 2 else '0' + hv
    hx = ''.join([to_hex(v) for v in color])
    if include:
        return '#' + hx
    return hx
    
def hex_to_color(colorhex):
    o = 0 if len(colorhex) == 6 else 1 # len = 6 or 7
    split = (colorhex[o:o + 2], colorhex[o + 2:o + 4], colorhex[o + 4:o + 6])
    return tuple([int((int(d, 16) / 255.0) * 65535) for d in split])

def _write_xpf_xml(root, puzzle, compact=False):
    main = etree.SubElement(root, "Puzzle")
    
    for dc, e in [(b, a) for a, b in XPF_META_ELEMS.items()]:
        if dc in puzzle.metadata and puzzle.metadata[dc]:
            child = etree.SubElement(main, e)
            child.text = puzzle.metadata[dc]
    size = etree.SubElement(main, "Size")
    rows = etree.SubElement(size, "Rows")
    rows.text = str(puzzle.grid.height)
    cols = etree.SubElement(size, "Cols")
    cols.text = str(puzzle.grid.width)
    
    def calc_char(x, y):
        cell = puzzle.grid.cell(x, y)
        if cell["block"]:
            return '.'
        if cell["void"]:
            return '~'
        c = cell["char"]
        return c if c else ' '

    egrid = etree.SubElement(main, "Grid")
    for y in xrange(puzzle.grid.height):
        erow = etree.SubElement(egrid, "Row")
        chars = [calc_char(x, y) for x in xrange(puzzle.grid.width)]
        erow.text = ''.join(chars)
    
    if not compact:
        props = puzzle.view.properties
        styles = props.styles
        circles = [cell for cell in styles if styles[cell]["circle"] != props["circle"]]
        if circles:
            circles.sort(key=itemgetter(0, 1))
            ecircles = etree.SubElement(main, "Circles")
            for x, y in circles:
                ecircle = etree.SubElement(ecircles, "Circle")
                ecircle.set("Row", str(y + 1))
                ecircle.set("Col", str(x + 1))
        shades = [cell for cell in styles if styles[cell]["cell", "color"] != props["cell", "color"]]
        if shades:
            shades.sort(key=itemgetter(0, 1))
            eshades = etree.SubElement(main, "Shades")
            for x, y in shades:
                eshade = etree.SubElement(eshades, "Shade")
                eshade.set("Row", str(y + 1))
                eshade.set("Col", str(x + 1))
                eshade.text = color_to_hex(styles[x, y]["cell", "color"])
        rebus = [cell for cell in puzzle.grid.cells() if puzzle.grid.has_rebus(*cell)]
        if rebus:
            entries = etree.SubElement(main, "RebusEntries")
            for x, y in rebus:
                erebus = etree.SubElement(entries, "Rebus")
                erebus.set("Row", str(y + 1))
                erebus.set("Col", str(x + 1))
                item = puzzle.grid.cell(x, y)["rebus"]
                erebus.set("Short", item[0])
                erebus.text = item[1]
        clues = etree.SubElement(main, "Clues")
        for n, x, y, d, word, clue, explanation in puzzle.grid.gather_words():
            eclue = etree.SubElement(clues, "Clue")
            eclue.set("Row", str(y + 1))
            eclue.set("Col", str(x + 1))
            eclue.set("Num", str(n))
            eclue.set("Dir", {"across": "Across", "down": "Down"}[d])
            eclue.set("Ans", word)
            if clue:
                eclue.text = clue
        e = etree.SubElement(main, "Notepad")
        e.text = etree.CDATA(puzzle.notepad)
        
        epal = etree.SubElement(main, "Palabra")
        epal.set("Version", constants.VERSION)
        for n, x, y, d, word, clue, explanation in puzzle.grid.gather_words():
            if explanation:
                eexp = etree.SubElement(epal, "Explanation")
                eexp.set("Row", str(y + 1))
                eexp.set("Col", str(x + 1))
                eexp.set("Num", str(n))
                eexp.set("Dir", {"across": "Across", "down": "Down"}[d])
                eexp.text = explanation
        visuals = puzzle.view.properties.get_non_defaults()
        if visuals:
            estyle = etree.SubElement(epal, "Style")
            for i, items in visuals.items():
                evisual = etree.SubElement(estyle, i)
                for attr, value in items:
                    text = str(value)
                    if attr == "Color":
                        text = color_to_hex(value)
                    evisual.set(attr, text)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8")
    
def _write_puzzle(filename, contents, backup=True):
    """
    Store the contents in the specified file. If a file in that location
    already exists and backup is True, a copy will be made before saving.
    """
    if backup:
        try:
            if os.path.isfile(filename):
                import shutil
                shutil.copy2(filename, "".join([filename, "~"]))
        except IOError:
            print "Warning: Failed to create a backup copy before saving."
    with open(filename, "w") as f:
        f.write(contents)
    
FILETYPES = {}
FILETYPES['keys'] = [constants.PUZZLE_XPF, constants.PUZZLE_IPUZ]
FILETYPES[constants.PUZZLE_XPF] = {
    'description': u"XPF puzzle files"
    , 'pattern': u".xml"
    , 'reader': read_xpf
    , 'writer': write_xpf
    , 'exception': XPFParserError
}
FILETYPES[constants.PUZZLE_IPUZ] = {
    'description': u"ipuz puzzle files"
    , 'pattern': u".ipuz"
    , 'reader': read_ipuz
    , 'writer': write_ipuz
    , 'exception': IPUZParserError
}
