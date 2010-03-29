
import sys

if sys.version_info < (2, 4):
    sys.exit("ERROR: Python 2.4 is required to run Palabra.")

from distutils.core import setup, Extension

module1 = Extension('cWord', sources = ['clib/cwordmodule.c'])

setup(name="palabra"
    , version="0.1"
    , license="GNU General Public License (GPL)"
    , author="Simeon Visser"
    , author_email="simeonvisser@gmail.com"
    , description="A crossword editor"
    , url="http://bitbucket.org/svisser/palabra"
    , packages=['palabralib']
    , scripts=['palabra']
    # see http://pypi.python.org/pypi?%3Aaction=list_classifiers
    , classifiers=[ 
        "Development Status :: 4 - Beta"
        , "Environment :: X11 Applications :: GTK"
        , "Intended Audience :: End Users/Desktop"
        , "License :: OSI Approved :: GNU General Public License (GPL)"
        , "Operating System :: POSIX :: Linux" # for now
        , "Programming Language :: Python"
        , "Topic :: Games/Entertainment :: Puzzle Games"
        ]
    , ext_modules = [module1]
    )
