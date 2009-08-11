
import sys

from distutils.core import setup

if sys.version < '2.4':
    print "Python 2.4 is required to run Palabra."
else:
    setup(name="palabra"
        , version="0.1"
        , license="GNU General Public License"
        , author="Simeon Visser"
        , author_email="simeonvisser@gmail.com"
        , description="A crossword editor"
        , url="http://bitbucket.org/svisser/palabra"
        , packages=['palabra']
        , requires=['gtk', 'pygtk (>=2.8)', 'lxml']
        )
