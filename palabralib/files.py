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

from lxml import etree

import constants
import grid
from grid import Grid
from puzzle import Puzzle
from view import GridView

XML_SCHEMA_CROSSWORD = "xml/crossword.xsd"

class ParserError(Exception):
    pass
    
class InvalidFileError(ParserError):
    pass

def export_puzzle(puzzle, filename, options):
    outputs = filter(lambda key: options["output"][key], options["output"])
    settings = options["settings"]
    if options["format"] == "csv":
        export_to_csv(puzzle, filename, outputs, settings)
    elif options["format"] == "png":
        export_to_png(puzzle, filename, outputs[0], settings)

def read_crossword(filename):
    try:
        doc = etree.parse(filename)
    except etree.XMLSyntaxError:
        raise InvalidFileError
    xmlschema = etree.XMLSchema(etree.parse(XML_SCHEMA_CROSSWORD))
    try:
        xmlschema.assertValid(doc)
    except etree.DocumentInvalid:
        raise InvalidFileError
    
    root = doc.getroot()
    version = root.get("version")
    for e in root[0]:
        if e.tag == "metadata":
            metadata = _read_metadata(e)
        elif e.tag == "grid":
            grid = _read_grid(e)
        elif e.tag == "clues":
            direction, clues = _read_clues(e)
            for x, y, data in clues:
                grid.cell(x, y)["clues"][direction] = data
    puzzle = Puzzle(grid)
    puzzle.metadata = metadata
    return puzzle
    
def write_crossword_to_xml(puzzle):
    root = etree.Element("palabra")
    root.set("version", constants.VERSION)
    
    crossword = etree.SubElement(root, "crossword")
    _write_metadata(crossword, puzzle.metadata)
    _write_grid(crossword, puzzle.grid)
    for d in ["across", "down"]:
        _write_clues(crossword, puzzle.grid, d)
    
    contents = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
    f = open(puzzle.filename, "w")
    f.write(contents)
    f.close()

def _read_metadata(metadata):
    m = {}
    for e in metadata:
        m[e.tag] = e.text
    return m
    
def _write_metadata(parent, metadata):
    e = etree.SubElement(parent, "metadata")
    for m in ["title", "author", "copyright", "description"]:
        prop = etree.SubElement(e, m)
        if m in metadata:
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
        grid.set_cell(*_read_cell(c))
    return grid
    
def _write_grid(parent, grid):
    e = etree.SubElement(parent, "grid")
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

def import_template(filename, index):
    try:
        tree = etree.parse(filename)
    except etree.XMLSyntaxError:
        return None
    palabra = tree.getroot()
    version = palabra.get("version")
    
    try:
        template = parse_template(palabra[index], True)
        if template is not None:
            return template["grid"]
    except IndexError:
        return None
        
def import_templates(filename):
    try:
        tree = etree.parse(filename)
    except etree.XMLSyntaxError:
        return []
    palabra = tree.getroot()
    version = palabra.get("version")
    
    templates = []
    for template in palabra:
        t = parse_template(template)
        if t is not None:
            templates.append((t, filename))
    return templates
        
def parse_template(template, include_grid=False):
    result = {}
    
    metadata = template.find("metadata")
    
    grid_elem = template.find("grid")
    if grid_elem is None:
        return None

    width = grid_elem.get("width")
    height = grid_elem.get("height")
    if width is None or height is None:
        return None

    result["width"] = int(width)
    result["height"] = int(height)
    
    stats_elem = grid_elem.find("statistics")
    if stats_elem is None:
        return None

    result.update(_parse_statistics(stats_elem))
    
    if "block_count" in result:
        size = result["width"] * result["height"]
        result["letter_count"] = size - result["block_count"]
    
    if include_grid:
        result["grid"] = read_grid(grid_elem)
            
    return result

def export_template(grid, filename):
    palabra = etree.Element("palabra")
    palabra.set("version", constants.VERSION)
    
    template = etree.SubElement(palabra, "template")
    template.set("type", "crossword")
    
    meta_elem = etree.SubElement(template, "metadata")

    source = etree.SubElement(meta_elem, "source")
        
    export_grid(template, grid, True)

    contents = etree.tostring(palabra
        , xml_declaration=True
        , encoding="UTF-8"
        , pretty_print=True)
    file = open(filename, "w")
    file.write(contents)
    
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
        puzzle.view.render(context, None, constants.VIEW_MODE_EMPTY)
    elif output == "solution":
        puzzle.view.render(context, None, constants.VIEW_MODE_SOLUTION)
    
    surface.write_to_png(filename)
    surface.finish()
