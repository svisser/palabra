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

import gtk
import os
from collections import namedtuple

from lxml import etree

import action
import constants
import grid

import ConfigParser

ColorScheme = namedtuple('ColorScheme', ['title'
    , 'primary_selection'
    , 'primary_active'
    , 'secondary_active'
    , 'current_word'
    , 'highlight'
])
_SCHEME_YELLOW = ColorScheme("Yellow"
    , (65535, 65535, 16383)
    , (65535, 65535, 16383)
    , (65535, 65535, 49152)
    , (65535, 65535, 49152)
    , (65535, 65535, 16383)
)
_SCHEME_RED = ColorScheme("Red"
    , (65535, 16383, 16383)
    , (65535, 16383, 16383)
    , (65535, 49152, 49152)
    , (65535, 49152, 49152)
    , (65535, 16383, 16383)
)
_SCHEME_GREEN = ColorScheme("Green"
    , (16383, 65535, 16383)
    , (16383, 65535, 16383)
    , (49152, 65535, 49152)
    , (49152, 65535, 49152)
    , (16383, 65535, 16383)
)
_SCHEME_BLUE = ColorScheme("Blue"
    , (16383, 16383, 65535)
    , (16383, 16383, 65535)
    , (49152, 49152, 65535)
    , (49152, 49152, 65535)
    , (16383, 16383, 65535)
)
_SCHEME_PURPLE = ColorScheme("Purple"
    , (65535, 16383, 65535)
    , (65535, 16383, 65535)
    , (65535, 49152, 65535)
    , (65535, 49152, 65535)
    , (65535, 16383, 65535)
)
_SCHEME_CYAN = ColorScheme("Cyan"
    , (16383, 65535, 65535)
    , (16383, 65535, 65535)
    , (49152, 65535, 65535)
    , (49152, 65535, 65535)
    , (16383, 65535, 65535)
)
_SCHEME_ORANGE = ColorScheme("Orange"
    , (65535, 32767, 16383)
    , (65535, 32767, 16383)
    , (65535, 49152, 16383)
    , (65535, 49152, 16383)
    , (65535, 32767, 16383)
)

COLORS = [('yellow', _SCHEME_YELLOW)
    , ('red', _SCHEME_RED)
    , ('green', _SCHEME_GREEN)
    , ('blue', _SCHEME_BLUE)
    , ('purple', _SCHEME_PURPLE)
    , ('cyan', _SCHEME_CYAN)
    , ('orange', _SCHEME_ORANGE)
]
D_COLORS = dict(COLORS)

prefs = {}

Preference = namedtuple('Preference', ['value', 'eval', 'type', 'itemtype'])
PreferenceFile = namedtuple('PreferenceFile', ['path', 'name'])

_COLOR_ATTRS = [
    (constants.COLOR_PRIMARY_SELECTION, 'primary_selection')
    , (constants.COLOR_PRIMARY_ACTIVE, 'primary_active')
    , (constants.COLOR_SECONDARY_ACTIVE, 'secondary_active')
    , (constants.COLOR_CURRENT_WORD, 'current_word')
    , (constants.COLOR_HIGHLIGHT, 'highlight')
]
_OTHER_COLOR_PREFS = [
    (constants.COLOR_WARNING, (65535, 49152, 49152))
]
_INT_PREFS = [
    (constants.PREF_INITIAL_HEIGHT, 15)
    , (constants.PREF_INITIAL_WIDTH, 15)
#    , (constants.PREF_UNDO_STACK_SIZE, 50)    
]
for k, color in (_COLOR_ATTRS + _OTHER_COLOR_PREFS):
    if isinstance(color, tuple):
        r, g, b = color
    else:
        r, g, b = getattr(D_COLORS["yellow"], color)
    _INT_PREFS.extend([(k + "_red", r), (k + "_green", g), (k + "_blue", b)])
_BOOL_PREFS = [
    (constants.PREF_COPY_BEFORE_SAVE, False)
#    , (constants.PREF_UNDO_FINITE_STACK, True)
]
_FILE_PREFS = [
    (constants.PREF_WORD_FILES, [PreferenceFile("/usr/share/dict/words", "Default")])
    , (constants.PREF_PATTERN_FILES, [])
]

DEFAULTS = {}
for code, b in _BOOL_PREFS:
    DEFAULTS[code] = Preference(b, lambda s: "True" in s, "bool", None)
for code, n in _INT_PREFS:
    DEFAULTS[code] = Preference(n, int, "int", None)
for code, files in _FILE_PREFS:
    result = []
    for f in files:
        result.append({"path": {"type": "str", "value": f.path}
            , "name": {"type": "str", "value": f.name}
        })
    DEFAULTS[code] = Preference(result, list, "list", "file")

def read_config_file(filename=constants.CONFIG_FILE_LOCATION, warnings=True):
    """
    Read the user's configuration file if it exists.
    Otherwise, use default values.
    """
    def parse_list(elem):
        values = []
        for c in elem:
            if c.get("type") == "file":
                value = {}
                for c2 in c:
                    d = {"type": c2.get("type"), "value": c2.text}
                    value[c2.get("name")] = d
            values.append(value)
        return values
    props = {}
    try:
        doc = etree.parse(filename)
        root = doc.getroot()
        version = root.get("version")
        for p in root:
            t = p.get("type")
            name = p.get("name")
            if t in ["int", "bool"]:
                props[name] = p.text
            elif t == "list":
                props[name] = parse_list(p)
    except (etree.XMLSyntaxError, IOError):
        if warnings:
            print "Warning: No configuration file found, using defaults instead."
    for key, pref in DEFAULTS.items():
        prefs[key] = pref.eval(props[key]) if key in props else pref.value

def write_config_file(filename=constants.CONFIG_FILE_LOCATION):
    """
    Write the user's configuration file with the user's preferences or default values.
    """
    root = etree.Element("palabra-preferences")
    root.set("version", constants.VERSION)
    keys = DEFAULTS.keys()
    keys.sort()
    for key in keys:
        pref = DEFAULTS[key]
        e = etree.SubElement(root, "preference")
        e.set("type", pref.type)
        e.set("name", key)
        data = prefs[key] if key in prefs else pref.value
        if pref.type in ["int", "bool"]:
            e.text = str(data)
        elif pref.type == "list":
            for v in data:
                f = etree.SubElement(e, "preference-item")
                f.set("type", pref.itemtype)
                if pref.itemtype == "file":
                    for k0, v0 in v.items():
                        g = etree.SubElement(f, "preference-item")
                        g.set("name", k0)
                        g.set("type", v0["type"])
                        g.text = v0["value"]
    if not os.path.isdir(constants.APPLICATION_DIRECTORY):
        os.mkdir(constants.APPLICATION_DIRECTORY)
    contents = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
    with open(filename, "w") as f:
        f.write(contents)

def read_pref_color(key, divide=True):
    if divide:
        r = prefs[key + "_red"] / 65535.0
        g = prefs[key + "_green"] / 65535.0
        b = prefs[key + "_blue"] / 65535.0
    else:
        r = prefs[key + "_red"]
        g = prefs[key + "_green"]
        b = prefs[key + "_blue"]
    return r, g, b
