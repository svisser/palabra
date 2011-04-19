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
import pango
import pangocairo
from operator import itemgetter
import os

from lxml import etree

import cGrid
import constants
import grid
from grid import Grid
from puzzle import Puzzle
from view import CellStyle, GridView

DC_NAMESPACE = "http://purl.org/dc/elements/1.1/"
DC_SIMPLE_TERMS = ["title"
    , "creator"
    , "subject"
    , "description"
    , "publisher"
    , "contributor"
    , "date"
    , "type"
    , "format"
    , "identifier"
    , "source"
    , "language"
    , "relation"
    , "coverage"
    , "rights"]

XPF_META_ELEMS = {'Type': 'type'
    , 'Title': 'title'
    , 'Author': 'creator'
    , 'Editor': 'contributor'
    , 'Copyright': 'rights'
    , 'Publisher': 'publisher'
    , 'Date': 'date'}
XPF_META_ELEMS_LIST = [("type", "Type")
    , ("title", "Title")
    , ("creator", "Author")
    , ("contributor", "Editor")
    , ("rights", "Copyright")
    , ("publisher", "Publisher")
    , ("date", "Date")]

class ParserError(Exception):
    def __init__(self, message):
        self.message = message

class XPFParserError(ParserError):
    def __init__(self, message=""):
        ParserError.__init__(self, "XPFParserError: " + message)

def get_real_filename(f):
    return os.path.join(os.path.split(__file__)[0], f)

def export_puzzle(puzzle, filename, options):
    outputs = filter(lambda key: options["output"][key], options["output"])
    settings = options["settings"]
    if options["format"] == "csv":
        export_to_csv(puzzle, filename, outputs, settings)
    elif options["format"] == "pdf":
        export_to_pdf(puzzle, filename, outputs[0], settings)
    elif options["format"] == "png":
        export_to_png(puzzle, filename, outputs[0], settings)

def read_crossword(filename):
    t = determine_file_type(filename)
    if t is None:
        raise ParserError("Palabra was unable to open: " + filename)
    if t == "xpf":
        results = read_xpf(filename)
        if not results:
            raise XPFParserError(u"No puzzle was found in this file.")
        if len(results) > 1:
            raise XPFParserError(u"This is a container file instead of a puzzle file.")
    return results[0]

def determine_file_type(filename):
    try:
        doc = etree.parse(filename)
    except etree.XMLSyntaxError:
        raise ParserError(u"This is not an XML file.")
    root = doc.getroot()
    if root.tag == "Puzzles":
        return 'xpf'
    return None
    
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
                    
def export_to_pdf(puzzle, filename, output, settings):
    paper_size = gtk.PaperSize(gtk.PAPER_NAME_A4)
    width = paper_size.get_width(gtk.UNIT_POINTS)
    height = paper_size.get_height(gtk.UNIT_POINTS)
    surface = cairo.PDFSurface(filename, width, height)
    context = cairo.Context(surface)
    def pdf_header():
        header = puzzle.metadata["title"] if "title" in puzzle.metadata else "(nameless)"
        if "creator" in puzzle.metadata:
            header += (" / " + puzzle.metadata["creator"])
        pcr = pangocairo.CairoContext(context)
        layout = pcr.create_layout()
        layout.set_markup('''<span font_desc="Sans 10">%s</span>''' % header)
        context.save()
        context.move_to(20, 20)
        pcr.show_layout(layout)
        context.restore()
        context.translate(0, 24)
    if output == "grid":
        pdf_header()
        puzzle.view.pdf_configure()
        puzzle.view.render(context, constants.VIEW_MODE_EXPORT_PDF_PUZZLE)
        puzzle.view.pdf_reset()
        context.show_page()
        def show_clue_page_compact():
            content = []
            for caption, direction in [("Across", "across"), ("Down", "down")]:
                content += ['''<span font_desc="Sans 10">%s</span>\n<span font_desc="Sans 8">''' % caption]
                for n, x, y, clue in puzzle.grid.clues(direction):
                    try:
                        txt = clue["text"]
                    except KeyError:
                        txt = '''<span color="#ff0000">(missing clue)</span>'''
                    txt = txt.replace("&", "&amp;")
                    content += [''' <b>%s</b> %s''' % (str(n), txt)]
                content += ["</span>\n\n"]
            rx, ry = 20, 20
            pcr = pangocairo.CairoContext(context)
            layout = pcr.create_layout()
            layout.set_width(pango.SCALE * 500)
            layout.set_wrap(pango.WRAP_WORD_CHAR)
            layout.set_markup(''.join(content))
            context.save()
            context.move_to(20, 36)
            pcr.show_layout(layout)
            context.restore()
            context.show_page()
        show_clue_page_compact()
    elif output == "solution":
        pdf_header()
        puzzle.view.pdf_configure()
        puzzle.view.render(context, constants.VIEW_MODE_EXPORT_PDF_SOLUTION)
        puzzle.view.pdf_reset()
        context.show_page()
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

# http://www.xwordinfo.com/XPF/
def read_xpf(filename):
    # TODO check validity coordinates
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
            print "Warning: skipping a child of Puzzles that is not a Puzzle."
            continue
        r_meta = {}
        r_width = None
        r_height = None
        r_grid = None
        r_notepad = ""
        r_styles = {}
        for child in puzzle:
            if child.tag in XPF_META_ELEMS:
                r_meta[XPF_META_ELEMS[child.tag]] = child.text
            elif child.tag == "Size":
                for d in child:
                    if d.tag == "Rows":
                        r_height = int(d.text)
                    elif d.tag == "Cols":
                        r_width = int(d.text)
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
                        print "Warning: skipping a child of Grid that is not a Row."
                        continue
                    if not row.text or len(row.text) < r_width:
                        print "Warning: skipping a row with missing content."
                        continue
                    for x, c in enumerate(row.text):
                        if c == '.':
                            r_grid.set_block(x, y, True)
                        elif c == '~':
                            r_grid.set_void(x, y, True)
                        else:
                            r_grid.set_char(x, y, c if c != ' ' else '')
                    y += 1
            elif child.tag == "Circles":
                for circle in child:
                    if circle.tag != "Circle":
                        print "Warning: skipping a child of Circles that is not a Circle."
                        continue
                    a_row = circle.get("Row")
                    a_col = circle.get("Col")
                    if not (a_row and a_col):
                        print "Warning: skipping a child of Circles with missing content."
                        continue
                    x = int(a_col) - 1
                    y = int(a_row) - 1
                    if (x, y) not in r_styles:
                        r_styles[x, y] = CellStyle()
                    r_styles[x, y].circle = True
            elif child.tag == "RebusEntries":
                for rebus in child:
                    if rebus.tag != "Rebus":
                        print "Warning: skipping a child of RebusEntries that is not a Rebus."
                        continue
                    a_row = rebus.get("Row")
                    a_col = rebus.get("Col")
                    a_short = rebus.get("Short")
                    content = rebus.text
                    if not (a_row and a_row and a_short and content):
                        print "Warning: skipping a child of RebusEntries with missing content."
                        continue
                    x = int(a_col) - 1
                    y = int(a_row) - 1
                    print "TODO - rebus found:", x, y, a_short, content
            elif child.tag == "Shades":
                for shade in child:
                    if shade.tag != "Shade":
                        print "Warning: skipping a child of Shades that is not a Shade."
                        continue
                    a_row = shade.get("Row")
                    a_col = shade.get("Col")
                    if not (a_row and a_col and shade.text):
                        print "Warning: skipping a child of Shades with missing content."
                        continue
                    x = int(a_col) - 1
                    y = int(a_row) - 1
                    if (x, y) not in r_styles:
                        r_styles[x, y] = CellStyle()
                    if shade.text == "gray":
                        shade.text = "#808080"
                    if shade.text[0] == '#':
                        colorhex = shade.text[1:]
                        split = (colorhex[0:2], colorhex[2:4], colorhex[4:6])
                        rgb = [int((int(d, 16) / 255.0) * 65535) for d in split]
                        r_styles[x, y].cell["color"] = tuple(rgb)
            elif child.tag == "Clues":
                for clue in child:
                    if clue.tag != "Clue":
                        print "Warning: skipping a child of Clues that is not a Clue."
                        continue
                    a_row = clue.get("Row")
                    a_col = clue.get("Col")
                    a_num = clue.get("Num")
                    a_dir = clue.get("Dir")
                    a_ans = clue.get("Ans")
                    if not (a_row and a_col and a_dir):
                        print "Warning: skipping a child of Clues with missing content."
                        continue
                    x = int(a_col) - 1
                    y = int(a_row) - 1
                    dirs = {"Across": "across", "Down": "down"}
                    if a_dir not in dirs:
                        print "Warning: skipping a clue with a direction that is not across or down."
                        continue
                    if not clue.text:
                        #print "Warning: skipping clue without text."
                        continue
                    r_grid.store_clue(x, y, dirs[a_dir], "text", clue.text)
            elif child.tag == "Notepad":
                r_notepad = child.text
        # TODO modify when arbitrary number schemes are implemented
        r_grid.assign_numbers()
        p = Puzzle(r_grid, r_styles)
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

def _write_xpf_xml(root, puzzle, compact=False):
    main = etree.SubElement(root, "Puzzle")
    
    for dc, e in XPF_META_ELEMS_LIST:
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
        default = puzzle.view.properties.default    
        styles = puzzle.view.properties.styles
        circles = [cell for cell in styles if styles[cell].circle != default.circle]
        if circles:
            circles.sort(key=itemgetter(0, 1))
            ecircles = etree.SubElement(main, "Circles")
            for x, y in circles:
                ecircle = etree.SubElement(ecircles, "Circle")
                ecircle.set("Row", str(y + 1))
                ecircle.set("Col", str(x + 1))
        shades = [cell for cell in styles if styles[cell].cell["color"] != default.cell["color"]]
        if shades:
            shades.sort(key=itemgetter(0, 1))
            eshades = etree.SubElement(main, "Shades")
            for x, y in shades:
                eshade = etree.SubElement(eshades, "Shade")
                eshade.set("Row", str(y + 1))
                eshade.set("Col", str(x + 1))
                def to_hex(value):
                    hv = hex(int(value / 65535.0 * 255))[2:]
                    return hv if len(hv) == 2 else '0' + hv
                text = '#' + ''.join([to_hex(v) for v in styles[x, y].cell["color"]])
                eshade.text = text
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
FILETYPES['keys'] = [constants.PUZZLE_XPF]
FILETYPES[constants.PUZZLE_XPF] = {
    'description': u"XPF puzzle files"
    , 'pattern': u".xml"
    , 'writer': write_xpf
}

