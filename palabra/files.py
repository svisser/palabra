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

import grid
from grid import (
    Grid,
    GridView,
)
from puzzle import (
    Puzzle,
)

PALABRA_VERSION = "0.1"

def import_puzzle(filename):
    try:
        tree = etree.parse(filename)
    except etree.XMLSyntaxError:
        return None
    palabra = tree.getroot()
    if palabra.tag != "palabra":
        return None
    
    version = palabra.get("version")
        
    puzzle = palabra[0]
    if puzzle.tag != "puzzle":
        return None
    
    data = {}
    for e in puzzle:
        if e.tag == "grid":
            data["grid"] = parse_grid(e)
        elif e.tag == "clues":
            direction = e.get("direction")
            if direction is None:
                continue
                
            clues = parse_clues(e, direction)
            
            data[direction + "_clues"] = clues
            
    puzzle = Puzzle(data["grid"])
    for x, y, direction in data["across_clues"]:
        puzzle.grid.cell(x, y)["clues"]["across"] = data["across_clues"][x, y, direction]
    for x, y, direction in data["down_clues"]:
        puzzle.grid.cell(x, y)["clues"]["down"] = data["down_clues"][x, y, direction]
    return puzzle
            
def parse_grid(e):
    width = e.get("width")
    height = e.get("height")
    if width is None or height is None:
        return None
        
    width = int(width)
    height = int(height)
    
    grid = Grid(width, height)
    for cell in e:
        if cell.tag == "cell":
            cell_data = _parse_cell(cell)
            x, y, c = cell_data
            if c is not None:
                grid.set_cell(x, y, c)

    return grid
    
def _parse_statistics(e):
    stats = {}
    for prop in e:
        if prop.tag == "block-count":
            stats["block_count"] = int(prop.text)
        elif prop.tag == "word-count":
            stats["word_count"] = int(prop.text)
    return stats
    
def _parse_cell(e):
    x = e.get("x")
    y = e.get("y")
    if x is None or y is None:
        return None
        
    x = int(x) - 1
    y = int(y) - 1
    
    cell = {}
    
    content = e.get("content")
    ctype = e.get("type")
    cell["block"] = ctype == "block"
    if not cell["block"] and content is not None:
        cell["char"] = content
    else:
        cell["char"] = ""
    cell["clues"] = {}
    return x, y, cell
    
def parse_clues(e, direction):
    clues = {}
    for clue in e:
        if clue.tag != "clue":
            continue
        
        x = clue.get("x")
        y = clue.get("y")
        
        if x is None or y is None:
            continue
        
        text = None
        explanation = None
        for prop in clue:
            if prop.tag == "text":
                text = prop.text
            elif prop.tag == "explanation":
                explanation = prop.text
                
        if text is None and explanation is None:
            continue

        x = int(x) - 1
        y = int(y) - 1
        
        clues[x, y, direction] = {}
        if text != None:
            clues[x, y, direction]["text"] = text
        if explanation != None:
            clues[x, y, direction]["explanation"] = explanation
    return clues
        
def export_puzzle(puzzle):
    palabra = etree.Element("palabra")
    palabra.set("version", PALABRA_VERSION)
    
    puzzle_elem = etree.SubElement(palabra, "puzzle")
    puzzle_elem.set("type", "crossword")
    
    export_metadata(puzzle_elem, puzzle.metadata)
    export_grid(puzzle_elem, puzzle.grid)
    export_clues(puzzle_elem, puzzle.grid)

    contents = etree.tostring(palabra
        , xml_declaration=True
        , encoding="UTF-8"
        , pretty_print=True)
    file = open(puzzle.filename, "w")
    file.write(contents)
    
def export_metadata(puzzle_elem, metadata):
    metadata_elem = etree.SubElement(puzzle_elem, "metadata")

    title = etree.SubElement(metadata_elem, "title")
    try:
        title.text = metadata["title"]
    except KeyError:
        pass
    
    author = etree.SubElement(metadata_elem, "author")
    try:
        author.text = metadata["author"]
    except KeyError:
        pass
        
    copyright = etree.SubElement(metadata_elem, "copyright")
    try:
        copyright.text = metadata["copyright"]
    except KeyError:
        pass
        
    description = etree.SubElement(metadata_elem, "description")
    try:
        description.text = metadata["description"]
    except KeyError:
        pass
    
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

def export_clues(elem, grid):
    across_clues = etree.SubElement(elem, "clues")
    across_clues.set("direction", "across")
    down_clues = etree.SubElement(elem, "clues")
    down_clues.set("direction", "down")
    
    clues = \
        [(across_clues, grid.horizontal_clues())
        ,(down_clues, grid.vertical_clues())
        ]
    for elem, clue_iterable in clues:
        for n, x, y, clue in clue_iterable:
            clue_elem = etree.SubElement(elem, "clue")
            clue_elem.set("x", str(x + 1))
            clue_elem.set("y", str(y + 1))
            
            for key, value in clue.items():
                prop = etree.SubElement(clue_elem, key)
                prop.text = value

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
        result["grid"] = parse_grid(grid_elem)
            
    return result

def export_template(grid, filename):
    palabra = etree.Element("palabra")
    palabra.set("version", PALABRA_VERSION)
    
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
    
def export_to_csv(puzzle, filename, options):
    f = open(filename, 'w')
    
    clues = \
        [("across", puzzle.grid.horizontal_clues())
        ,("down", puzzle.grid.vertical_clues())
        ]
        
    for direction, clue_iterable in clues:
        for n, x, y, clue in clue_iterable:
            line = [direction, options["separator"]]

            try:
                line.append(clue["text"])
            except KeyError:
                line.append("")
            line.append(options["separator"])
            
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
    
    view = GridView(puzzle.grid)
    view.update_view(context, grid.VIEW_MODE_EMPTY)
    
    context.show_page()
    
    view.update_view(context, grid.VIEW_MODE_SOLUTION)
    
    context.show_page()
    
    surface.finish()
    
def export_to_png(puzzle, filename, view_mode=grid.VIEW_MODE_EMPTY):
    view = GridView(puzzle.grid)
    width = view.visual_width(False)
    height = view.visual_height(False)
    
    surface = canvas = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    context = cairo.Context(surface)
    
    context.rectangle(0, 0, width, height)
    context.set_source_rgb(1, 1, 1)
    context.fill()
    
    view.update_view(context, view_mode)
    
    surface.write_to_png(filename)
    
    surface.finish()
