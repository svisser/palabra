import os
import sys

if sys.version_info < (2, 7):
    sys.exit("ERROR: Python 2.7 is required to run Palabra.")

from setuptools import setup
from distutils.core import Extension
import palabralib.constants as constants

ext_modules = [
    Extension('cPalabra', sources=[
        'palabralib/cpalabramodule.c',
        'palabralib/cpalabra.c'
    ])
]

# see http://pypi.python.org/pypi?%3Aaction=list_classifiers
CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Environment :: X11 Applications :: GTK",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: GNU General Public License (GPL)",
    "Operating System :: POSIX :: Linux",
    "Natural Language :: English",
    "Programming Language :: C",
    "Programming Language :: Python :: 2.7",
    "Topic :: Games/Entertainment :: Puzzle Games",
]

PACKAGE_DATA = [
    'xml/patterns.xml',
    'resources/icon1.png',
    'resources/icon2.png',
]

def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()


setup(name="palabra",
    version=constants.VERSION,
    license="GNU General Public License (GPL)",
    author="Simeon Visser",
    author_email="simeonvisser@gmail.com",
    description="A free crossword editor",
    long_description=read('README'),
    url=constants.WEBSITE,
    requires=['lxml'],
    packages=['palabralib'],
    package_dir={'palabralib': 'palabralib'},
    package_data={'palabralib': PACKAGE_DATA},
    entry_points={'console_scripts':['palabra = palabralib.gui:main']},
    classifiers=CLASSIFIERS,
    include_dirs=['palabralib'],
    zip_safe=False,
    ext_modules=ext_modules,
)
