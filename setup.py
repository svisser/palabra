
import sys

if sys.version_info < (2, 6):
    sys.exit("ERROR: Python 2.6 is required to run Palabra.")

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
CLASSIFIERS = [ 
"Development Status :: 5 - Production/Stable"
, "Environment :: X11 Applications :: GTK"
, "Intended Audience :: End Users/Desktop"
, "License :: OSI Approved :: GNU General Public License (GPL)"
, "Operating System :: POSIX :: Linux" # for now
, "Natural Language :: English"
, "Programming Language :: C"
, "Programming Language :: Python :: 2.6"
, "Topic :: Games/Entertainment :: Puzzle Games"
]

PACKAGE_DATA = [
'xml/patterns.xml',
'resources/icon1.png',
'resources/icon2.png'
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
    , package_dir={'palabralib': 'palabralib'}
    , package_data={'palabralib': PACKAGE_DATA}
    , entry_points={'console_scripts':['palabra = palabralib.gui:main']}
    , classifiers=CLASSIFIERS
    , include_dirs=['palabralib']
    , zip_safe=False
    , ext_modules=ext_modules)
