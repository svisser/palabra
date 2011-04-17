
IS_DEVELOPMENT = False

import sys

if sys.version_info < (2, 4):
    sys.exit("ERROR: Python 2.4 is required to run Palabra.")

from distutils.core import setup, Extension
import palabralib.constants as constants

def create_ext(e):
    name = 'c' + e.capitalize()
    sources = ['palabralib/c' + e + 'module.c', 'palabralib/cpalabra.c']
    return name, sources
EXTS = [create_ext(e) for e in ['grid', 'view', 'word']]
ext_modules = [Extension(n, sources=s) for n, s in EXTS]

setup(name="palabra"
    , version=constants.VERSION
    , license="GNU General Public License (GPL)"
    , author="Simeon Visser"
    , author_email="simeonvisser@gmail.com"
    , description="A crossword editor"
    , url=constants.WEBSITE
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
    , ext_modules=ext_modules)
if IS_DEVELOPMENT:
    import os
    
    # TODO correct?
    import distutils.util
    platform = (distutils.util.get_platform()
        + '-' + str(sys.version_info[0]) + '.' + str(sys.version_info[1]))
    
    # TODO ugly
    import glob
    dirs = glob.glob('build/lib.*')
    if len(dirs) == 0:
        print "ERROR! No lib.* directory found in /build directory"
    else:
        for name, sources in EXTS:
            f = name + '.so'
            path = 'palabralib/' + f
            if os.path.exists(path):
                os.remove(path)
            os.rename(''.join(['build/', dirs[0][6:], '/', f]), path)
