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

import os
import unittest

import palabralib.constants as constants
import palabralib.preferences as preferences
from palabralib.preferences import (
    DEFAULTS,
    read_config_file,
    write_config_file,
)

class PrefsTestCase(unittest.TestCase):
    LOCATION = "palabralib/tests/test.config.xml"
        
    def tearDown(self):
        if os.path.exists(self.LOCATION):
            os.remove(self.LOCATION)
        preferences.prefs = {}
            
    def _writeRead(self):
        write_config_file(filename=self.LOCATION)
        read_config_file(filename=self.LOCATION)
        
    def testDefaults(self):
        self._writeRead()
        for key, pref in DEFAULTS.items():
            self.assertEquals(preferences.prefs[key], pref.value)
        self.assertEquals(len(preferences.prefs), len(DEFAULTS))
            
    def testBoolPref(self):
        preferences.prefs[constants.PREF_COPY_BEFORE_SAVE] = True
        self._writeRead()
        self.assertEquals(preferences.prefs[constants.PREF_COPY_BEFORE_SAVE], True)
        
    def testIntPref(self):
        preferences.prefs[constants.PREF_INITIAL_HEIGHT] = 27
        self._writeRead()
        self.assertEquals(preferences.prefs[constants.PREF_INITIAL_HEIGHT], 27)
        
    def testColor(self):
        preferences.prefs[constants.COLOR_PRIMARY_SELECTION + "_red"] = 1234
        self._writeRead()
        self.assertEquals(preferences.prefs[constants.COLOR_PRIMARY_SELECTION + "_red"], 1234)
