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
from operator import itemgetter

from lxml import etree

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

class ParserError(Exception):
    def __init__(self, prefix, message):
        self.message = ''.join([prefix, ": ", message])

class PalabraParserError(ParserError):
    def __init__(self, message):
        ParserError.__init__(self, "PalabraParserError", message)

def export_puzzle(puzzle, filename, options):
    outputs = filter(lambda key: options["output"][key], options["output"])
    settings = options["settings"]
    if options["format"] == "csv":
        export_to_csv(puzzle, filename, outputs, settings)
    elif options["format"] == "png":
        export_to_png(puzzle, filename, outputs[0], settings)

def read_crossword(filename):
    t = determine_file_type(filename)
    if t == "palabra":
        results = read_palabra(filename)
        if not results:
            raise PalabraParserError(u"No puzzle was found in this file.")
        if len(results) > 1:
            raise PalabraParserError(u"This is a container file instead of a puzzle file.")
    elif t == "xpf":
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
        raise ParserError(u"ParserError", u"This is not an XML file.")
    root = doc.getroot()
    if root.tag == "palabra":
        return "palabra"
    elif root.tag == "Puzzles":
        return 'xpf'
    return None
    
def write_palabra(puzzle, backup=True):
    root = etree.Element("palabra")
    root.set("version", constants.VERSION)
    
    _write_crossword(root, puzzle)
    
    contents = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
    _write_puzzle(puzzle.filename, contents, backup)
    
def read_pattern_file(filename):
    results = read_palabra(filename)
    metadata = {} # TODO
    contents = {}
    for i, p in enumerate(results):
        contents[str(i)] = p.grid
    return (filename, metadata, contents)
    
def write_pattern_file(filename, metadata, contents):
    root = etree.Element("palabra")
    root.set("version", constants.VERSION)

    container = etree.SubElement(root, "container")
    container.set("content", "grid")
    _write_metadata(container, metadata)
    for i, (j, grid) in enumerate(contents.items(), start=1):
        _write_grid(container, grid, str(i))

    contents = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
    f = open(filename, "w")
    f.write(contents)
    f.close()
    
def read_containers(files):
    def load_container(f):
        metadata = {} # TODO
        return f, metadata, read_palabra(f)
    return [load_container(f) for f in files]
    
def write_container(filename, content, data):
    root = etree.Element("palabra")
    root.set("version", constants.VERSION)

    container = etree.SubElement(root, "container")
    container.set("content", content)
    for d in data:
        if content == "crossword":
            _write_crossword(container, d)
        elif content == "grid":
            _write_grid(container, d)

    contents = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
    f = open(filename, "w")
    f.write(contents)
    f.close()

def _write_crossword(parent, puzzle):
    crossword = etree.SubElement(parent, "puzzle")
    crossword.set("type", "crossword")
    _write_metadata(crossword, puzzle.metadata)
    _write_grid(crossword, puzzle.grid)
    for d in ["across", "down"]:
        _write_clues(crossword, puzzle.grid, d)
    e = etree.SubElement(crossword, "notepad")
    e.text = etree.CDATA(puzzle.notepad)

def _read_metadata(metadata):
    m = {}
    for e in metadata:
        m[e.tag[len("{%s}" % DC_NAMESPACE):]] = e.text
    return m
    
def _write_metadata(parent, metadata):
    e = etree.SubElement(parent, "metadata", nsmap={"dc": DC_NAMESPACE})
    for m in DC_SIMPLE_TERMS:
        if m in metadata:
            prop = etree.SubElement(e, "".join(["{%s}" % DC_NAMESPACE, m]))
            prop.text = metadata[m]
    
def _read_cell(e):
    x = int(e.get("x")) - 1
    y = int(e.get("y")) - 1
    c = {}
    c["block"] = e.tag == "block"
    if e.tag == "letter" and e.text is not None:
        c["char"] = e.text
    else:
        c["char"] = ""
    c["clues"] = {}
    c["bar"] = {}
    c["bar"]["top"] = e.get("top-bar") == "true"
    c["bar"]["left"] = e.get("left-bar") == "true"
    c["number"] = 0
    c["void"] = e.tag == "void"
    return x, y, c
    
def _write_cell(parent, x, y, cell):
    if cell["block"]:
        e = etree.SubElement(parent, "block")
    elif cell["void"]:
        e = etree.SubElement(parent, "void")
    else:
        e = etree.SubElement(parent, "letter")
        if len(cell["char"]) > 0:
            e.text = cell["char"]
    e.set("x", str(x + 1))
    e.set("y", str(y + 1))
    if cell["bar"]["top"]:
        e.set("top-bar", "true")
    if cell["bar"]["left"]:
        e.set("left-bar", "true")
    
def _read_grid(e):
    width = int(e.get("width"))
    height = int(e.get("height"))
    grid = Grid(width, height)
    for c in e:
        x, y, data = _read_cell(c)
        if grid.is_valid(x, y):
            grid.set_cell(x, y, data)
        else:
            print "".join(["Warning: Invalid cell encountered: ", str((x + 1, y + 1))])
    return grid
    
def _write_grid(parent, grid, id=None):
    e = etree.SubElement(parent, "grid")
    if id:
        e.set("id", id)
    e.set("width", str(grid.width))
    e.set("height", str(grid.height))
    for x, y in grid.cells():
        _write_cell(e, x, y, grid.cell(x, y))
    
def _read_clue(e):
    x = int(e.get("x")) - 1
    y = int(e.get("y")) - 1
    c = {}
    for prop in e:
        if prop.text is not None:
            c[prop.tag] = prop.text
    return x, y, c
    
def _write_clue(parent, x, y, clue):
    e = etree.SubElement(parent, "clue")
    for prop in ["text", "explanation"]:
        if prop in clue:
            p = etree.SubElement(e, prop)
            p.text = clue[prop]
    e.set("x", str(x + 1))
    e.set("y", str(y + 1))
    
def _read_clues(e):
    return (e.get("direction"), [_read_clue(c) for c in e])

def _write_clues(parent, grid, direction):
    e = etree.SubElement(parent, "clues")
    e.set("direction", direction)
    for x, y in grid.cells():
        clues = grid.cell(x, y)["clues"]
        if direction in clues:
            _write_clue(e, x, y, clues[direction])

def _parse_statistics(e):
    stats = {}
    for prop in e:
        if prop.tag == "block-count":
            stats["block_count"] = int(prop.text)
        elif prop.tag == "word-count":
            stats["word_count"] = int(prop.text)
    return stats
        
def export_grid(elem, grid, include_statistics=False):
    grid_elem = etree.SubElement(elem, "grid")
    grid_elem.set("width", str(grid.width))
    grid_elem.set("height", str(grid.height))

    if include_statistics:
        stats_elem = etree.SubElement(grid_elem, "statistics")
        prop = etree.SubElement(stats_elem, "block-count")
        prop.text = str(grid.count_blocks())
        prop = etree.SubElement(stats_elem, "word-count")
        prop.text = str(grid.count_words())
    
    for y in range(grid.height):
        for x in range(grid.width):
            cell = etree.SubElement(grid_elem, "cell")
            cell.set("x", str(x + 1))
            cell.set("y", str(y + 1))
            if grid.is_block(x, y):
                cell.set("type", "block")
            elif grid.get_char(x, y) != "":
                cell.set("content", grid.get_char(x, y))
        
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
                    
def export_to_pdf(puzzle, filename):
    paper_size = gtk.PaperSize(gtk.PAPER_NAME_A4)
    width = paper_size.get_width(gtk.UNIT_POINTS)
    height = paper_size.get_height(gtk.UNIT_POINTS)
    
    surface = cairo.PDFSurface(filename, width, height)
    context = cairo.Context(surface)
    
    puzzle.view.render(context, constants.VIEW_MODE_EMPTY)
    context.show_page()
    puzzle.view.render(context, constants.VIEW_MODE_SOLUTION)
    context.show_page()
    
    surface.finish()
    
def export_to_png(puzzle, filename, output, settings):
    width = puzzle.view.properties.visual_width(False)
    height = puzzle.view.properties.visual_height(False)
    
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)

    context = cairo.Context(surface)
    context.rectangle(0, 0, width, height)
    
    r, g, b = puzzle.view.properties.cell["color"]
    context.set_source_rgb(r / 65535.0, g / 65535.0, b / 65535.0)
    context.fill()
    
    if output == "grid":
        puzzle.view.render(context, constants.VIEW_MODE_EMPTY)
    elif output == "solution":
        puzzle.view.render(context, constants.VIEW_MODE_SOLUTION)
    
    surface.write_to_png(filename)
    surface.finish()
    
#####

def read_palabra(filename):
    results = []
    try:
        doc = etree.parse(filename)
    except etree.XMLSyntaxError:
        raise PalabraParserError(u"No valid XML syntax.")
    palabra = doc.getroot()
    if palabra.tag != "palabra":
        raise PalabraParserError(u"No root element called palabra found.")
    version = palabra.get("version")
    if not version:
        raise PalabraParserError(u"Palabra version number not specified.")
    if version > constants.VERSION:
        contents = [
            u"This file was created in a newer version of Palabra ("
            , str(version)
            , u")\n"
            , "You are running Palabra "
            , str(constants.VERSION)
            , u".\nPlease upgrade your version of Palabra to open this file."
            ]
        raise PalabraParserError(u"".join(contents))
    def parse_metadata(element):
        meta = {}
        for m in element:
            term = m.tag[len("{%s}" % DC_NAMESPACE):]
            if term not in DC_SIMPLE_TERMS:
                print "Warning: skipping a non-DC metadata term: ", term
                continue
            meta[term] = m.text
        return meta
    def parse_cell_coordinate(cell, skip, attr, name):
        coord = cell.get(attr)
        if not coord:
            print "".join([u"Warning: skipping ", skip, " with no ", name, "-coordinate."])
            return None
        if not coord.isdigit():
            print "".join([u"Warning: skipping ", skip, " with invalid ", name, "-coordinate."])
            return None
        if int(coord) - 1 < 0:
            print "".join([u"Warning: skipping ", skip, " with invalid ", name, "-coordinate."])
            return None
        return int(coord) - 1
    def parse_grid(element):
        def parse_grid_size(attr, name):
            width = element.get(attr)
            if not width:
                msg = "".join([name, u" attribute of grid not specified."])
                raise PalabraParserError(msg)
            if not width.isdigit():
                msg = "".join([name, u" attribute of grid is not a number."])
                raise PalabraParserError(msg)
            if int(width) < 1:
                msg = "".join([name, u" of grid must be at least one cell."])
                raise PalabraParserError(msg)
            return int(width)
        width = parse_grid_size("width", u"Width")
        height = parse_grid_size("height", u"Height")
        grid = Grid(width, height)
        for cell in element:
            if cell.tag not in ["block", "letter", "void"]:
                print u"Warning: skipping cell with invalid type."
                continue
            x = parse_cell_coordinate(cell, "cell", "x", "x")
            if x is None:
                continue
            y = parse_cell_coordinate(cell, "cell", "y", "y")
            if y is None:
                continue
            if not grid.is_valid(x, y):
                print "Warning: skipping cell with invalid coordinates."
                continue
            data = {}
            data["block"] = cell.tag == "block"
            if cell.tag == "letter" and cell.text is not None:
                data["char"] = cell.text
            else:
                data["char"] = ""
            data["clues"] = {}
            data["bar"] = {}
            data["bar"]["top"] = cell.get("top-bar") == "true"
            data["bar"]["left"] = cell.get("left-bar") == "true"
            data["number"] = 0
            data["void"] = cell.tag == "void"
            grid.set_cell(x, y, data)
        return grid
    def parse_clues(element, grid):
        dir = element.get("direction")
        if not dir:
            print u"Warning: skipping clues element with no direction specified."
            return
        if dir not in ["across", "down"]:
            print u"Warning: skipping clues element with invalid direction."
            return
        for clue in element:
            if clue.tag != "clue":
                print "Warning: skipping child of clues that is not a clue."
                continue
            x = parse_cell_coordinate(clue, "clue", "x", "x")
            if x is None:
                continue
            y = parse_cell_coordinate(clue, "clue", "y", "y")
            if y is None:
                continue
            if not grid.is_valid(x, y):
                print "Warning: skipping clue with invalid coordinates."
                continue
            data = {}
            for prop in clue:
                if prop.tag not in ["text", "explanation"]:
                    print "Warning: skipping child of clue that is not text or explanation."
                    continue
                if prop.text is not None:
                    data[prop.tag] = prop.text
            grid.cell(x, y)["clues"][dir] = data
    for puzzle in palabra:
        if puzzle.tag != "puzzle":
            print "Warning: skipping a child of palabra that is not a puzzle."
            continue
        type = puzzle.get("type")
        if not type:
            raise PalabraParserError(u"Type of puzzle not specified.")
        if type != "crossword":
            raise PalabraParserError("".join([u"This type of puzzle (", type, ") not supported."]))
        r_meta = {}
        r_grid = None
        r_notepad = ""
        for child in puzzle:
            if child.tag == "metadata":
                r_meta = parse_metadata(child)
            elif child.tag == "grid":
                r_grid = parse_grid(child)
            elif child.tag == "clues":
                if r_grid is None:
                    raise PalabraParserError(u"Unable to process clues: grid does not exist.")
                parse_clues(child, r_grid)
            elif child.tag == "notepad":
                r_notepad = child.text
        # TODO modify when arbitrary number schemes are implemented
        r_grid.assign_numbers()
        p = Puzzle(r_grid)
        p.metadata = r_meta
        p.type = constants.PUZZLE_PALABRA
        p.notepad = r_notepad
        results.append(p)
    return results

class XPFParserError(ParserError):
    def __init__(self, message=""):
        ParserError.__init__(self, "XPFParserError", message)

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
            if child.tag == "Title":
                r_meta["title"] = child.text
            elif child.tag == "Author":
                r_meta["creator"] = child.text
            elif child.tag == "Editor":
                r_meta["contributor"] = child.text
            elif child.tag == "Copyright":
                r_meta["rights"] = child.text
            elif child.tag == "Publisher":
                r_meta["publisher"] = child.text
            elif child.tag == "Date":
                r_meta["date"] = child.text
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
                x, y = 0, 0
                for row in child:
                    if row.tag != "Row":
                        print "Warning: skipping a child of Grid that is not a Row."
                        continue
                    content = row.text
                    for i, c in enumerate(content):
                        if c == '.':
                            r_grid.set_block(x + i, y, True)
                        else:
                            r_grid.set_char(x + i, y, c)
                    y += 1
            elif child.tag == "Circles":
                for circle in child:
                    if circle.tag != "Circle":
                        print "Warning: skipping a child of Circles that is not a Circle."
                        continue
                    a_row = circle.get("Row")
                    a_col = circle.get("Col")
                    if a_row is None:
                        print "Warning: skipping a child of Circles without a Row."
                        continue
                    if a_col is None:
                        print "Warning: skipping a child of Circles without a Col."
                        continue
                    x = int(a_col) - 1
                    y = int(a_row) - 1
                    if (x, y) not in r_styles:
                        r_styles[x, y] = CellStyle()
                    r_styles[x, y].circle = True
            elif child.tag == "RebusEntries":
                pass # TODO
            elif child.tag == "Shades":
                for shade in child:
                    if shade.tag != "Shade":
                        print "Warning: skipping a child of Shades that is not a Shade."
                        continue
                    a_row = shade.get("Row")
                    a_col = shade.get("Col")
                    if a_row is None:
                        print "Warning: skipping a child of Shades without a Row."
                        continue
                    if a_col is None:
                        print "Warning: skipping a child of Shades without a Col."
                        continue
                    x = int(a_col) - 1
                    y = int(a_row) - 1
                    if shade.text:
                        if (x, y) not in r_styles:
                            r_styles[x, y] = CellStyle()
                        if shade.text[0] == '#':
                            colorhex = shade.text[1:]
                            split = (colorhex[0:2], colorhex[2:4], colorhex[4:6])
                            rgb = [int((int(d, 16) / 255.0) * 65535) for d in split]
                            r_styles[x, y].cell["color"] = tuple(rgb)
                        else:
                            print "TODO", shade.text
                    else:
                        print "Warning: Skipping a child of Shades with no content."
                        continue
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
                    if a_row is not None and a_col is not None and a_dir is not None:
                        x = int(a_col) - 1
                        y = int(a_row) - 1
                        if a_dir == "Across":
                            direction = "across"
                        elif a_dir == "Down":
                            direction = "down"
                        else:
                            print "Warning: skipping a clue with a direction that is not across or down."
                            continue
                        r_grid.store_clue(x, y, direction, "text", clue.text)
            elif child.tag == "Notepad":
                r_notepad = child.text
        # TODO modify when arbitrary number schemes are implemented
        r_grid.assign_numbers()
        p = Puzzle(r_grid, r_styles)
        p.metadata = r_meta
        p.type = constants.PUZZLE_XPF
        p.notepad = r_notepad
        results.append(p)
    return results
    
def write_xpf(puzzle, backup=True):
    root = etree.Element("Puzzles")
    main = etree.SubElement(root, "Puzzle")
    
    elems = [("title", "Title")
        , ("creator", "Author")
        , ("contributor", "Editor")
        , ("publisher", "Publisher")
        , ("date", "Date")]
    for dc, e in elems:
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
        c = cell["char"]
        return c if c else ' '

    egrid = etree.SubElement(main, "Grid")
    for y in xrange(puzzle.grid.height):
        erow = etree.SubElement(egrid, "Row")
        chars = [calc_char(x, y) for x in xrange(puzzle.grid.width)]
        erow.text = ''.join(chars)
    
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
    for d in ["across", "down"]:
        for n, x, y, word, clue, explanation in puzzle.grid.gather_words(d):
            eclue = etree.SubElement(clues, "Clue")
            eclue.set("Row", str(y + 1))
            eclue.set("Col", str(x + 1))
            eclue.set("Num", str(n))
            dshow = {"across": "Across", "down": "Down"}[d]
            eclue.set("Dir", dshow)
            eclue.set("Ans", word)
            eclue.text = clue
    
    contents = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
    _write_puzzle(puzzle.filename, contents, backup)
    
def _write_puzzle(filename, contents, backup=True):
    """
    Store the contents in the specified file. If a file in that location
    already exists and backup is True, a copy will be made before saving.
    """
    if backup:
        try:
            import os
            if os.path.isfile(filename):
                import shutil
                shutil.copy2(filename, "".join([filename, "~"]))
        except IOError:
            print "Warning: Failed to create a backup copy before saving."
    f = open(filename, "w")
    f.write(contents)
    f.close()
