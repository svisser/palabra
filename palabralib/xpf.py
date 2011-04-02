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

from xml import sax
from xml.sax import make_parser

import constants
from grid import Grid
from puzzle import Puzzle
from view import CellStyle

XPF_SUPPORT = 1.0
META_ELEMS = {'Type': 'type'
    , 'Title': 'title'
    , 'Author': 'creator'
    , 'Editor': 'contributor'
    , 'Copyright': 'rights'
    , 'Publisher': 'publisher'
    , 'Date': 'date'}

class XPFContentHandler(sax.ContentHandler):
    def __init__(self, filename):
        self.puzzles = []
        self.filename = filename
        self.metadata = {'Type': 'normal'}
        self.curMetaElement = None
        self.inSizeElement = False
        self.grid = None
        self.inRowElement = False
        self.inRebusElement = False
        self.inShadeElement = False
        self.inClueElement = False
        self.y = -1
        self.styles = {}
        self.rebus = {}
        self.shade = {}
        self.clue = {}
        
    def startElement(self, name, attrs):
        if name == 'Puzzles':
            v = attrs.get('Version', None)
            if v:
                self.xpf_version = float(v)
                if self.xpf_version > XPF_SUPPORT:
                    raise sax.SAXException('version not supported')
        if name in META_ELEMS:
            self.curMetaElement = name
            self.metadata[META_ELEMS[name]] = ''
        if name in ['Rows', 'Cols']:
            self.inSizeElement = True
            self.size = ''
        if name == 'Grid':
            try:
                self.grid = Grid(self.width, self.height)
            except AttributeError:
                raise sax.SAXException('size not there')
        if name == 'Row':
            self.inRowElement = True
            self.row = ''
            self.y += 1
        if name == 'Circle':
            x = int(attrs.get("Col", None)) - 1
            y = int(attrs.get("Row", None)) - 1
            if (x, y) not in self.styles:
                self.styles[x, y] = CellStyle()
            self.styles[x, y].circle = True
        if name == 'Rebus':
            self.rebus['x'] = int(attrs.get("Col", None)) - 1
            self.rebus['y'] = int(attrs.get("Row", None)) - 1
            self.rebus['short'] = attrs.get("Short", None)
            self.rebus['content'] = ''
            self.inRebusElement = True
        if name == 'Shade':
            self.shade['x'] = int(attrs.get("Col", None)) - 1
            self.shade['y'] = int(attrs.get("Row", None)) - 1
            self.shade['color'] = ''
            self.inShadeElement = True
        if name == 'Clue':
            self.clue['x'] = int(attrs.get("Col", None)) - 1
            self.clue['y'] = int(attrs.get("Row", None)) - 1
            self.clue['n'] = int(attrs.get("Num", None)) - 1
            self.clue['dir'] = attrs.get("Dir", None)
            self.clue['ans'] = attrs.get("Ans", None)
            self.clue['content'] = ''
            self.inClueElement = True
            
    def characters(self, ch):
        if self.curMetaElement:
            self.metadata[META_ELEMS[self.curMetaElement]] += ch
        if self.inSizeElement:
            self.size += ch
        if self.inRowElement:
            self.row += ch
        if self.inRebusElement:
            self.rebus['content'] += ch
        if self.inShadeElement:
            self.shade['color'] += ch
        if self.inClueElement:
            self.clue['content'] += ch
            
    def endElement(self, name):
        if self.curMetaElement:
            self.curMetaElement = None
        if self.inSizeElement:
            if name == 'Rows':
                self.width = int(self.size)
            elif name == 'Cols':
                self.height = int(self.size)
            self.inSizeElement = False
        if self.inRowElement:
            for x, c in enumerate(self.row):
                if c == ' ':
                    continue
                elif c == '.':
                    self.grid.set_block(x, self.y, True)
                elif c == '~':
                    self.grid.set_void(x, self.y, True)
                else:
                    self.grid.set_char(x, self.y, c)
            self.inRowElement = False
        if self.inRebusElement:
            print "TODO rebus", self.rebus
            self.rebus = {}
            self.inRebusElement = False
        if self.inShadeElement:
            x = self.shade['x']
            y = self.shade['y']
            if (x, y) not in self.styles:
                self.styles[x, y] = CellStyle()
            if self.shade['color'] == "gray":
                self.shade['color'] = "#808080"
            if self.shade['color'][0] == '#':
                colorhex = self.shade['color'][1:]
                split = (colorhex[0:2], colorhex[2:4], colorhex[4:6])
                rgb = [int((int(d, 16) / 255.0) * 65535) for d in split]
                self.styles[x, y].cell["color"] = tuple(rgb)
            self.shade = {}
            self.inShadeElement = False
        if self.inClueElement:
            x = self.clue['x']
            y = self.clue['y']
            if self.clue['dir'] == 'Across':
                direction = 'across'
            elif self.clue['dir'] == 'Down':
                direction = 'down'
            self.grid.store_clue(x, y, direction, "text", self.clue['content'])
            self.clue = {}
            self.inClueElement = False
        if name == 'Puzzle':
            self.grid.assign_numbers()
            p = Puzzle(self.grid, self.styles)
            p.metadata = self.metadata
            p.type = constants.PUZZLE_XPF
            p.filename = self.filename
            #p.notepad = r_notepad
            self.puzzles.append(p)

def read_xpf(filename):
    handler = XPFContentHandler(filename)
    parser = make_parser()
    parser.setContentHandler(handler)
    parser.parse(filename)
    return handler.puzzles
