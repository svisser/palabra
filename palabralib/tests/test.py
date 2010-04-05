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

# In the project directory, run:
#
# python -m palabralib.tests.test

import unittest

#from palabralib.tests.test_action import ActionTestCase, ActionStackTestCase
from palabralib.tests.test_files import FilesTestCase
from palabralib.tests.test_grid import GridTestCase
from palabralib.tests.test_transform import TransformTestCase
from palabralib.tests.test_word import WordTestCase

# ActionTestCase, ActionStackTestCase
cases = [ FilesTestCase
    , GridTestCase
    , TransformTestCase
    , WordTestCase]
suites = [unittest.TestLoader().loadTestsFromTestCase(c) for c in cases]

alltests = unittest.TestSuite(suites)
unittest.TextTestRunner(verbosity=1).run(alltests)
