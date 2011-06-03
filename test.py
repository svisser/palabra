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

# In the project directory, run:
#
# python test.py
#
# To run coverage tests, run:
#
# coverage run test.py
# coverage html

import unittest

from palabralib.tests.test_action import ActionTestCase
from palabralib.tests.test_clue import ClueTestCase
from palabralib.tests.test_editor import EditorTestCase
from palabralib.tests.test_files import FilesTestCase
from palabralib.tests.test_grid import GridTestCase, PuzzleTestCase
from palabralib.tests.test_pattern import PatternTestCase
from palabralib.tests.test_prefs import PrefsTestCase
from palabralib.tests.test_transform import TransformTestCase
from palabralib.tests.test_view import ViewTestCase
from palabralib.tests.test_word import WordTestCase
from palabralib.tests.test_word2 import WordTestCase2

cases = [ ActionTestCase
    , ClueTestCase
    , GridTestCase
    , PuzzleTestCase
    , EditorTestCase
    , FilesTestCase
    , PatternTestCase
    , PrefsTestCase
    , TransformTestCase
    , ViewTestCase
    , WordTestCase
    , WordTestCase2
]
suites = [unittest.TestLoader().loadTestsFromTestCase(c) for c in cases]

alltests = unittest.TestSuite(suites)
unittest.TextTestRunner(verbosity=1).run(alltests)
