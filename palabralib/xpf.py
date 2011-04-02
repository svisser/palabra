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

XPF_SUPPORT = 1.0
META_ELEMS = ['Type'
    , 'Title'
    , 'Author'
    , 'Editor'
    , 'Copyright'
    , 'Publisher'
    , 'Date']

class XPFContentHandler(sax.ContentHandler):
    def __init__(self, filename):
        self.puzzles = []
        self.filename = filename
        self.metadata = {'Type': 'normal'}
        self.curMetaElement = None
        self.inSizeElement = False
        self.grid = None
        self.inRowElement = False
        self.y = -1
        
    def startElement(self, name, attrs):
        if name == 'Puzzles':
            v = attrs.get('Version', None)
            if v:
                self.xpf_version = float(v)
                if self.xpf_version > XPF_SUPPORT:
                    raise sax.SAXException('version not supported')
        if name in META_ELEMS:
            self.curMetaElement = name
            self.metadata[name] = ''
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
            
    def characters(self, ch):
        if self.curMetaElement:
            self.metadata[self.curMetaElement] += ch
        if self.inSizeElement:
            self.size += ch
        if self.inRowElement:
            self.row += ch
            
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
        if name == 'Puzzle':
            self.grid.assign_numbers()
            p = Puzzle(self.grid) #r_styles)
            #p.metadata = r_meta
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
