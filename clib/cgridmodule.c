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
#include "cpalabra.h"

// 0 = false, 1 = true
int calc_is_available(PyObject *grid, int x, int y) {
    int width = (int) PyInt_AsLong(PyObject_GetAttrString(grid, "width"));
    int height = (int) PyInt_AsLong(PyObject_GetAttrString(grid, "height"));
    
    if (!(0 <= x && x < width && 0 <= y && y < height))
        return 0;
    
    PyObject* data = PyObject_GetAttrString(grid, "data");
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
    if (calc_is_available(grid, x, y) == 0)
        Py_RETURN_FALSE;
    Py_RETURN_TRUE;
}

/*
def is_start_word(self, x, y, direction=None):
    """Return True when a word begins in the cell (x, y)."""
    
    if not self.is_available(x, y):
        return False
    for d in ([direction] if direction else ["across", "down"]):
        if d == "across":
            bdx, bdy, adx, ady, bar_side = -1, 0, 1, 0, "left"
        elif d == "down":
            bdx, bdy, adx, ady, bar_side = 0, -1, 0, 1, "top"
        
        before = not self.is_available(x + bdx, y + bdy) or self.has_bar(x, y, bar_side)
        after = self.is_available(x + adx, y + ady) and not self.has_bar(x + adx, y + ady, bar_side)
        if before and after:
            return True
    return False
*/

// 0 = false, 1 = true
int calc_is_start_word(PyObject *grid, int x, int y) {
    int available = calc_is_available(grid, x, y);
    if (available == 0)
        return 0;
    
    PyObject *bar_str = PyString_FromString("bar");
    PyObject *side_left = PyString_FromString("left");
    PyObject *side_top = PyString_FromString("top");
    
    // 0 = across, 1 = down
    int e;
    for (e = 0; e < 2; e++) {
        int bdx = e == 0 ? -1 : 0;
        int bdy = e == 0 ? 0 : -1;
        int adx = e == 0 ? 1 : 0;
        int ady = e == 0 ? 0 : 1;
        PyObject *side = e == 0 ? side_left : side_top;
        
        // both conditions of after
        if (calc_is_available(grid, x + adx, y + ady) == 0)
            continue;
        PyObject* data = PyObject_GetAttrString(grid, "data");
        PyObject* col = PyObject_GetItem(data, PyInt_FromLong(y + ady));
        PyObject* cell = PyObject_GetItem(col, PyInt_FromLong(x + adx));
        PyObject* bars = PyObject_GetItem(cell, bar_str);
        if (PyObject_IsTrue(PyObject_GetItem(bars, side)) == 1)
            continue;
        
        // both conditions of before
        if (calc_is_available(grid, x + bdx, y + bdy) == 0)
            return 1;
        col = PyObject_GetItem(data, PyInt_FromLong(y));
        cell = PyObject_GetItem(col, PyInt_FromLong(x));
        bars = PyObject_GetItem(cell, bar_str);
        if (PyObject_IsTrue(PyObject_GetItem(bars, side)) == 1)
            return 1;
    }
    return 0;
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
    
    PyObject* data = PyObject_GetAttrString(grid, "data");
    
    int n = 1;
    int x;
    int y;
    for (y = 0; y < height; y++) {
        for (x = 0; x < width; x++) {
            PyObject* col = PyObject_GetItem(data, PyInt_FromLong(y));
            PyObject* cell = PyObject_GetItem(col, PyInt_FromLong(x));
            
            PyObject* key = PyString_FromString("number");
            if (calc_is_start_word(grid, x, y) == 1) {
                PyDict_SetItem(cell, key, PyInt_FromLong(n));
                n++;
            } else {
                PyDict_SetItem(cell, key, PyInt_FromLong(0));
            }
        }
    }
    Py_RETURN_NONE;
}

typedef struct {
    int x;
    int y;
    int dir; // 0 = across, 1 = down
    int length;
    int count;
    int done; // {0, 1}
    char cs[MAX_WORD_LENGTH];
    //PyObject* cs;
} Slot;

static PyObject*
cGrid_fill(PyObject *self, PyObject *args) {
    PyObject *grid;
    PyObject *words;
    PyObject *meta;
    if (!PyArg_ParseTuple(args, "OOO", &grid, &words, &meta))
        return NULL;

    // store information per slot
    int n_done_slots = 0;
    Py_ssize_t n_slots = PyList_Size(meta);
    Slot slots[n_slots];
    Py_ssize_t m;
    for (m = 0; m < n_slots; m++) {
        PyObject *item = PyList_GetItem(meta, m);
        const int x;
        const int y;
        const int dir;
        const int length;
        PyObject *constraints;
        if (!PyArg_ParseTuple(item, "iiiiO", &x, &y, &dir, &length, &constraints))
            return NULL;
        slots[m].x = x;
        slots[m].y = y;
        slots[m].dir = dir;
        slots[m].length = length;
        if (process_constraints(constraints, slots[m].cs) == 1)
            return NULL;

        int count = 0;
        Py_ssize_t w;
        PyObject* key = Py_BuildValue("i", length);
        PyObject* words_m = PyDict_GetItem(words, key);
        for (w = 0; w < PyList_Size(words_m); w++) {
            char *word = PyString_AsString(PyList_GetItem(words_m, w));
            if (!check_constraints(word, slots[m].cs)) {
                continue;
            }
            count++;
        }
        slots[m].count = count;
        slots[m].done = 1;
        int j;
        for (j = 0; j < length; j++) {
            if (slots[m].cs[j] == CONSTRAINT_EMPTY) {
                slots[m].done = 0;
            }
        }
        if (slots[m].done) {
            n_done_slots++;
        }
    }
    
    PyObject *result = PyList_New(0);
    PyObject *fill = PyList_New(0);
    while (n_done_slots != n_slots) {
        int index = -1;
        for (m = 0; m < n_slots; m++) {
            if (!slots[m].done) {
                index = m;
                break;
            }
        }
        for (m = 0; m < n_slots; m++) {
            if (slots[m].count < slots[index].count && !slots[m].done) {
                index = m;
            }
        }
        
        printf("find word for (%i, %i, %i)\n", slots[index].x, slots[index].y, slots[index].dir);
        char* word = find_candidate(words, slots[index].length, slots[index].cs);
        if (word) {
            int k;
            for (k = 0; k < slots[index].length; k++) {
                char c = word[k];
                char cell_c[2];
                cell_c[0] = toupper(c);
                cell_c[1] = '\0';
                int cx = slots[index].x + (slots[index].dir == 0 ? k : 0);
                int cy = slots[index].y + (slots[index].dir == 1 ? k : 0);
                
                // update the two affected slots
                int m;
                for (m = 0; m < n_slots; m++) {
                    if (slots[m].dir == 0 && slots[m].x <= cx
                        && cx <= slots[m].x + slots[m].length && slots[m].y == cy) {
                        slots[m].cs[cx - slots[m].x] = c;
                    }
                    if (slots[m].dir == 1 && slots[m].y <= cy
                        && cy <= slots[m].y + slots[m].length && slots[m].x == cx) {
                        slots[m].cs[cy - slots[m].y] = c;
                    }
                }
                
                PyObject* cell = Py_BuildValue("(iis)", cx, cy, cell_c);
                PyList_Append(fill, cell);
            }
        }
        
        slots[index].done = 1;
        n_done_slots++;
        printf("done: %i %s\n", n_done_slots, word);
    }
    
    PyList_Append(result, fill);
    return result;
}

static PyMethodDef methods[] = {
    {"is_available",  cGrid_is_available, METH_VARARGS, "is_available"},
    {"assign_numbers", cGrid_assign_numbers, METH_VARARGS, "assign_numbers"},
    {"fill", cGrid_fill, METH_VARARGS, "fill"},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initcGrid(void)
{
    (void) Py_InitModule("cGrid", methods);
}
