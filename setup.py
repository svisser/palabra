
import sys

if sys.version_info < (2, 4):
    sys.exit("ERROR: Python 2.4 is required to run Palabra.")

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup
from distutils.core import Extension
import palabralib.constants as constants

def create_ext(e):
    name = 'c' + e.capitalize()
    sources = ['palabralib/c' + e + 'module.c', 'palabralib/cpalabra.c']
    return name, sources
EXTS = [create_ext(e) for e in ['grid', 'view', 'word']]
ext_modules = [Extension(n, sources=s) for n, s in EXTS]

# see http://pypi.python.org/pypi?%3Aaction=list_classifiers
classifiers = [ 
"Development Status :: 4 - Beta"
, "Environment :: X11 Applications :: GTK"
, "Intended Audience :: End Users/Desktop"
, "License :: OSI Approved :: GNU General Public License (GPL)"
, "Operating System :: POSIX :: Linux" # for now
, "Natural Language :: English"
, "Programming Language :: C"
, "Programming Language :: Python :: 2.6"
, "Topic :: Games/Entertainment :: Puzzle Games"
]

setup(name="palabra"
    , version=constants.VERSION
    , license="GNU General Public License (GPL)"
    , author="Simeon Visser"
    , author_email="simeonvisser@gmail.com"
    , description="A crossword editor"
    , url=constants.WEBSITE
    , requires=['lxml']
    , packages=['palabralib']
    , package_data={'': ['xml/patterns.xml']}
    , entry_points={'console_scripts':['palabra = palabra']}
    , classifiers=classifiers
    , include_dirs=['palabralib']
    , ext_modules=ext_modules)
