#!/usr/bin/env python
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

try:
    import pygtk
    pygtk.require("2.0")
    import gtk
except (ImportError, AssertionError):
    print "PyGTK 2.8 or higher is required for this application."
    raise SystemExit

from palabra.gui import PalabraWindow
from palabra.preferences import read_config_file

if __name__ == "__main__":
    try:
        read_config_file()
        palabra = PalabraWindow()
        palabra.show_all()
        gtk.main()
        #import pstats
        #import cProfile
        #cProfile.run('gtk.main()', 'fooprof')
        #p = pstats.Stats('fooprof')
        #p.sort_stats('cumulative').print_stats()#20)
    except KeyboardInterrupt:
        import sys
        sys.exit("ERROR: Interrupted by user")
else:
    raise ImportError("Palabra cannot be imported.")
