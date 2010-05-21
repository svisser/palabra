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
    PyObject *width;
    char attr0[6];
    // TODO
    attr0[0] = 'w';
    attr0[1] = 'i';
    attr0[2] = 'd';
    attr0[3] = 't';
    attr0[4] = 'h';
    attr0[5] = '\0';
    const char *attr0_p = attr0;
    width = PyObject_GetAttrString(grid, attr0_p);
    int i_width = (int) PyInt_AsLong(width);
    
    PyObject *height;
    char attr1[7];
    attr1[0] = 'h';
    attr1[1] = 'e';
    attr1[2] = 'i';
    attr1[3] = 'g';
    attr1[4] = 'h';
    attr1[5] = 't';
    attr1[6] = '\0';
    const char *attr1_p = attr1;
    height = PyObject_GetAttrString(grid, attr1_p);
    int i_height = (int) PyInt_AsLong(height);
    
    PyObject* lines = PyDict_New();
    
    int x = 0;
    int y = 0;
    int e = 0;
    for (y = 0; y < i_height; y++) {
        for (x = 0; x < i_width; x++) {
            PyObject *result = PyList_New(0);
            
            char m_is_void[8] = { 'i', 's', '_', 'v', 'o', 'i', 'd', '\0' };
            int v0 = PyObject_IsTrue(PyObject_CallMethod(grid, m_is_void, "(ii)", x, y));
            
            for (e = 0; e < 2; e++) {
                int dx = e == 0 ? -1 : 0;
                int dy = e == 0 ? 0 : -1;
                char edge[e == 0 ? 5 : 4];
                if (e == 0) {
                    edge[0] = 'l';
                    edge[1] = 'e';
                    edge[2] = 'f';
                    edge[3] = 't';
                    edge[4] = '\0';
                } else {
                    edge[0] = 't';
                    edge[1] = 'o';
                    edge[2] = 'p';
                    edge[3] = '\0';
                }
                
                char m_is_valid[9] = { 'i', 's', '_', 'v', 'a', 'l', 'i', 'd', '\0' };
                PyObject* b = PyObject_CallMethod(grid, m_is_valid, "(ii)", x + dx, y + dy);
                if (PyObject_IsTrue(b) == 1) {
                    int v1 = PyObject_IsTrue(PyObject_CallMethod(grid, m_is_void, "(ii)", x + dx, y + dy));
                    if (v0 == 0 || v1 == 0) {
                        PyObject* r = NULL;
                        if (v0 == 1 && v0 == 0) {
                            char side[12] = { 'i', 'n', 'n', 'e', 'r', 'b', 'o', 'r', 'd', 'e', 'r', '\0' };
                            r = Py_BuildValue("(iiss)",  x, y, edge, side);
                        } else if (v0 == 0 && v1 == 1) {
                            char side[12] = { 'o', 'u', 't', 'e', 'r', 'b', 'o', 'r', 'd', 'e', 'r', '\0' };
                            r = Py_BuildValue("(iiss)",  x, y, edge, side);
                        } else {
                            char side[7] = { 'n', 'o', 'r', 'm', 'a', 'l', '\0' };
                            r = Py_BuildValue("(iiss)",  x, y, edge, side);
                        }
                        PyList_Append(result, r);
                    }
                } else if (v0 == 0) {
                    char side[12] = { 'o', 'u', 't', 'e', 'r', 'b', 'o', 'r', 'd', 'e', 'r', '\0' };
                    PyObject* r = Py_BuildValue("(iiss)",  x, y, edge, side);
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
