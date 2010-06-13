/* This file is part of Palabra

   Copyright (C) 2009 - 2010 Simeon Visser

   Palabra is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.
  
   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

#include <Python.h>

// 0 = false, 1 = true
int calc_is_available(PyObject *grid, int x, int y) {
    int width = (int) PyInt_AsLong(PyObject_GetAttrString(grid, "width"));
    int height = (int) PyInt_AsLong(PyObject_GetAttrString(grid, "height"));
    
    if (!(0 <= x && x < width && 0 <= y && y < height))
        return 0;
    
    PyObject* data = PyObject_GetAttr(grid, PyString_FromString("data"));
    PyObject* col = PyObject_GetItem(data, PyInt_FromLong(y));
    PyObject* cell = PyObject_GetItem(col, PyInt_FromLong(x));
    
    int is_block = PyObject_IsTrue(PyObject_GetItem(cell, PyString_FromString("block")));
    if (is_block != 0)
        return 0;
    int is_void = PyObject_IsTrue(PyObject_GetItem(cell, PyString_FromString("void")));
    if (is_void != 0)
        return 0;
    return 1;
}

static PyObject*
cGrid_is_available(PyObject *self, PyObject *args) {
    PyObject *grid;
    const int x;
    const int y;
    if (!PyArg_ParseTuple(args, "Oii", &grid, &x, &y))
        return NULL;
    int available = calc_is_available(grid, x, y);
    if (available == 0)
        Py_RETURN_FALSE;
    Py_RETURN_TRUE;
}

/*
n = 1
for x, y in self.cells():
    if self.is_start_word(x, y):
        self.data[y][x]["number"] = n
        n += 1
    else:
        self.data[y][x]["number"] = 0
*/
static PyObject*
cGrid_assign_numbers(PyObject *self, PyObject *args) {
    PyObject *grid;
    if (!PyArg_ParseTuple(args, "O", &grid))
        return NULL;
    int width = (int) PyInt_AsLong(PyObject_GetAttrString(grid, "width"));
    int height = (int) PyInt_AsLong(PyObject_GetAttrString(grid, "height"));
    
    PyObject* data = PyObject_GetAttr(grid, PyString_FromString("data"));
    
    int n = 1;
    int x;
    int y;
    for (y = 0; y < height; y++) {
        for (x = 0; x < width; x++) {
            PyObject* col = PyObject_GetItem(data, PyInt_FromLong(y));
            PyObject* cell = PyObject_GetItem(col, PyInt_FromLong(x));
            
            PyObject* key = PyString_FromString("number");
            if (1 == 1) {
                PyDict_SetItem(cell, key, PyInt_FromLong(n));
                n++;
            } else {
                PyDict_SetItem(cell, key, PyInt_FromLong(0));
            }
        }
    }
    Py_RETURN_NONE;
}

static PyMethodDef methods[] = {
    {"is_available",  cGrid_is_available, METH_VARARGS, "is_available"},
    {"assign_numbers", cGrid_assign_numbers, METH_VARARGS, "assign_numbers"},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initcGrid(void)
{
    (void) Py_InitModule("cGrid", methods);
}
