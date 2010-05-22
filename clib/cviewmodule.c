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

// TODO add failure checking

static PyObject*
cView_compute_lines(PyObject *self, PyObject *args) {
    PyObject *grid;
    if (!PyArg_ParseTuple(args, "O", &grid))
        return NULL;
    int width = (int) PyInt_AsLong(PyObject_GetAttrString(grid, "width"));
    int height = (int) PyInt_AsLong(PyObject_GetAttrString(grid, "height"));
    
    PyObject* lines = PyDict_New();
    
    PyObject* data = PyObject_GetAttr(grid, PyString_FromString("data"));
    int x = 0;
    int y = 0;
    int e = 0;
    for (y = 0; y < height; y++) {
        for (x = 0; x < width; x++) {
            PyObject *result = PyList_New(0);
            
            // is_void
            PyObject* col = PyObject_GetItem(data, PyInt_FromLong(y));
            PyObject* cell = PyObject_GetItem(col, PyInt_FromLong(x));
            int v0 = PyObject_IsTrue(PyObject_GetItem(cell, PyString_FromString("void")));
            
            for (e = 0; e < 2; e++) {
                int dx = e == 0 ? -1 : 0;
                int dy = e == 0 ? 0 : -1;
                
                int nx = x + dx;
                int ny = y + dy;
                if (0 <= nx && nx < width && 0 <= ny && ny < height) {
                    // is_void
                    PyObject* col = PyObject_GetItem(data, PyInt_FromLong(ny));
                    PyObject* cell = PyObject_GetItem(col, PyInt_FromLong(nx));
                    int v1 = PyObject_IsTrue(PyObject_GetItem(cell, PyString_FromString("void")));
                    if (v0 == 0 || v1 == 0) {
                        PyObject* r = NULL;
                        if (v0 == 1 && v0 == 0) {
                            r = Py_BuildValue("(iiss)",  x, y, e == 0 ? "left" : "top", "innerborder");
                        } else if (v0 == 0 && v1 == 1) {
                            r = Py_BuildValue("(iiss)",  x, y, e == 0 ? "left" : "top", "outerborder");
                        } else {
                            r = Py_BuildValue("(iiss)",  x, y, e == 0 ? "left" : "top", "normal");
                        }
                        PyList_Append(result, r);
                    }
                } else if (v0 == 0) {
                    PyObject* r = Py_BuildValue("(iiss)",  x, y, e == 0 ? "left" : "top", "outerborder");
                    PyList_Append(result, r);
                }
            }
            if (y == height - 1) {
                // is_void
                PyObject* col = PyObject_GetItem(data, PyInt_FromLong(height - 1));
                PyObject* cell = PyObject_GetItem(col, PyInt_FromLong(x));
                int v = PyObject_IsTrue(PyObject_GetItem(cell, PyString_FromString("void")));
                if (v == 0) {
                    PyObject* r = Py_BuildValue("(iiss)",  x, height, "top", "innerborder");
                    PyList_Append(result, r);
                }
            }
            if (x == width - 1) {
                // is_void
                PyObject* col = PyObject_GetItem(data, PyInt_FromLong(y));
                PyObject* cell = PyObject_GetItem(col, PyInt_FromLong(width - 1));
                int v = PyObject_IsTrue(PyObject_GetItem(cell, PyString_FromString("void")));
                if (v == 0) {
                    PyObject* r = Py_BuildValue("(iiss)",  width, y, "left", "innerborder");
                    PyList_Append(result, r);
                }
            }
            
            PyObject* key = Py_BuildValue("(ii)", x, y);
            PyDict_SetItem(lines, key, result);
        }
    }
    
    /*
    """Return the lines of a cell (uses nonexistent cells for outer lines)."""
        lines = []
        for edge, (dx, dy) in [("left", (-1, 0)), ("top", (0, -1))]:
            if self.is_valid(x + dx, y + dy):
                v0 = self.is_void(x, y)
                v1 = self.is_void(x + dx, y + dy)
                if not (v0 and v1):
                    side = "normal"
                    if v0 and not v1:
                        side = "innerborder"
                    elif not v0 and v1:
                        side = "outerborder"
                    lines.append((x, y, edge, side))
            elif not self.is_void(x, y):
                lines.append((x, y, edge, "outerborder"))
                
        # also include lines at the bottom and the right
        if y == self.height - 1:
            if not self.is_void(x, self.height - 1):
                lines.append((x, self.height, "top", "innerborder"))
        if x == self.width - 1:
            if not self.is_void(self.width - 1, y):
                lines.append((self.width, y, "left", "innerborder"))
        return lines
    */
    // TODO
    return lines;
}

static PyMethodDef methods[] = {
    {"compute_lines",  cView_compute_lines, METH_VARARGS, "compute_lines"},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initcView(void)
{
    (void) Py_InitModule("cView", methods);
}
