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
    int fixed[MAX_WORD_LENGTH]; // 0 = read/write, 1 = read
} Slot;

int count_words(PyObject *words, int length, char *cs) {
    int count = 0;
    Py_ssize_t w;
    PyObject* key = Py_BuildValue("i", length);
    PyObject* words_m = PyDict_GetItem(words, key);
    for (w = 0; w < PyList_Size(words_m); w++) {
        char *word = PyString_AsString(PyList_GetItem(words_m, w));
        if (!check_constraints(word, cs)) {
            continue;
        }
        count++;
    }
    return count;
}

int get_slot_index(Slot *slots, int n_slots, int x, int y, int dir) {
    int s;
    for (s = 0; s < n_slots; s++) {
        if (dir == 0 && slots[s].dir == 0
            && slots[s].x <= x && x < slots[s].x + slots[s].length
            && slots[s].y == y) {
            return s;
        }
        if (dir == 1 && slots[s].dir == 1
            && slots[s].y <= y && y < slots[s].y + slots[s].length
            && slots[s].x == x) {
            return s;
        }
    }
    return -1;
}

// 1 = yes, 0 = no
int can_clear_char(Slot slot) {
    int count = 0;
    int j;
    for (j = 0; j < slot.length; j++) {
        if (slot.cs[j] == CONSTRAINT_EMPTY)
            count++;
    }
    return count > 0;
}

// TODO clear slot at index but leave intersecting words in place
void clear_slot(Slot *slots, int n_slots, int index) {
    Slot slot = slots[index];
    int l = 0;
    for (l = 0; l < slot.length; l++) {
        if (slot.fixed[l] == 1) continue;
        int cx = slot.x + (slot.dir == 0 ? l : 0);
        int cy = slot.y + (slot.dir == 1 ? l : 0);
        int m = get_slot_index(slots, n_slots, cx, cy, slot.dir == 0 ? 1 : 0);
        if (can_clear_char(slots[m]) && slot.cs[l] != CONSTRAINT_EMPTY) {
            printf("%i can be cleared\n", l);
            slot.cs[l] = CONSTRAINT_EMPTY;
        }
    }
}

void analyze_cell(PyObject *words, int length, char *cs, int index, char *result) {
    printf("analyzing at offset %i\n", index);
    char prevChar = *(cs + index);
    *(cs + index) = CONSTRAINT_EMPTY;
    
    int k;
    for (k = 0; k < MAX_ALPHABET_SIZE; k++) {
        result[k] = CONSTRAINT_EMPTY;
    }
    
    Py_ssize_t w;
    PyObject* key = Py_BuildValue("i", length);
    PyObject* words_m = PyDict_GetItem(words, key);
    for (w = 0; w < PyList_Size(words_m); w++) {
        char *word = PyString_AsString(PyList_GetItem(words_m, w));
        if (!check_constraints(word, cs)) {
            continue;
        }
        char c = *(word + index);
        for (k = 0; k < MAX_ALPHABET_SIZE; k++) {
            if (result[k] == c) break;
            if (result[k] == CONSTRAINT_EMPTY && c != prevChar) {
                result[k] = c;
                break;
            }
        }
    }
    *(cs + index) = prevChar;
}

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

        slots[m].count = count_words(words, length, slots[m].cs);
        slots[m].done = 1;
        int j;
        for (j = 0; j < length; j++) {
            slots[m].fixed[j] = slots[m].cs[j] == CONSTRAINT_EMPTY ? 0 : 1;
            if (slots[m].cs[j] == CONSTRAINT_EMPTY) {
                slots[m].done = 0;
            }
        }
        if (slots[m].done) {
            n_done_slots++;
        }
    }
    
    int recent_index = -1;
    PyObject *result = PyList_New(0);
    PyObject *fill = PyList_New(0);
    while (n_done_slots < n_slots) {
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
        
        if (DEBUG) {
            printf("find word for (%i, %i, %s)\n", slots[index].x, slots[index].y, slots[index].dir == 0 ? "across" : "down");
        }
        char* word = find_candidate(words, slots[index].length, slots[index].cs);
        if (word) {
            int affected[slots[index].length];
            int k;
            for (k = 0; k < slots[index].length; k++) {
                affected[k] = -1;
            }
            for (k = 0; k < slots[index].length; k++) {
                char c = word[k];
                char cell_c[2];
                cell_c[0] = toupper(c);
                cell_c[1] = '\0';
                int cx = slots[index].x + (slots[index].dir == 0 ? k : 0);
                int cy = slots[index].y + (slots[index].dir == 1 ? k : 0);
                
                // update the two affected slots
                int d;
                for (d = 0; d < 2; d++) {
                    int indexD = get_slot_index(slots, n_slots, cx, cy, d);
                    if (indexD >= 0) {
                        int offset = d == 0 ? cx - slots[indexD].x : cy - slots[indexD].y;
                        slots[indexD].cs[offset] = c;
                        if (indexD != index)
                            affected[k] = indexD;
                    }
                }
                
                PyObject* cell = Py_BuildValue("(iis)", cx, cy, cell_c);
                PyList_Append(fill, cell);
            }
            // update counts
            slots[index].count = 1;
            for (k = 0; k < slots[index].length; k++) {
                int mm = affected[k];
                // only recompute when a cell is affected and not already completely filled in
                if (mm >= 0 && slots[mm].count > 1) {
                    int prev = slots[mm].count;
                    slots[mm].count = count_words(words, slots[mm].length, slots[mm].cs);
                    printf("slot %i: from %i to %i\n", mm, prev, slots[mm].count);
                    if (slots[mm].count == 0) {
                        int cx = slots[index].x + (slots[index].dir == 0 ? k : 0);
                        int cy = slots[index].y + (slots[index].dir == 1 ? k : 0);
                        printf("ZERO for (%i, %i)\n", cx, cy);
                        char result[MAX_ALPHABET_SIZE];
                        analyze_cell(words, slots[mm].length, slots[mm].cs, slots[mm].dir == 0 ? cx - slots[mm].x : cy - slots[mm].y, result);
                        int l;
                        for (l = 0; l < MAX_ALPHABET_SIZE; l++) {
                            printf("%c", result[l]);
                        }
                        printf("\n");
                    }
                }
            }
        } else {
            printf("No word could be found for (%i, %i, %s)\n", slots[index].x, slots[index].y, slots[index].dir == 0 ? "across" : "down");
            if (recent_index >= 0) {
                printf("About to clear (%i, %i, %s)\n", slots[recent_index].x, slots[recent_index].y, slots[recent_index].dir == 0 ? "across" : "down");
                clear_slot(slots, n_slots, recent_index);
            }
            break;
        }
        
        recent_index = index;
        slots[index].done = 1;
        n_done_slots++;
        if (DEBUG) {
            printf("done: %s (%i, %i, %s)\n", word, slots[index].x, slots[index].y, slots[index].dir == 0 ? "across" : "down");
        }
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
