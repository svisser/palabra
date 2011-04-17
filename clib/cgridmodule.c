/* This file is part of Palabra

   Copyright (C) 2009 - 2011 Simeon Visser

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

typedef struct Cell {
    int top_bar; // {0,1}
    int left_bar; // {0,1}
    int block; // {0,1}
    char c;
    int number;
    int empty; // {0,1}
    int fixed; // {0,1} 0 = read/write, 1 = read
} Cell;

typedef struct Slot {
    int x;
    int y;
    int dir; // 0 = across, 1 = down
    int length;
    int count;
    int done; // {0, 1}
    int offset;
} Slot;

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
    PyObject *py_width = PyObject_GetAttrString(grid, "width");
    int width = (int) PyInt_AsLong(py_width);
    Py_DECREF(py_width);
    PyObject *py_height = PyObject_GetAttrString(grid, "height");
    int height = (int) PyInt_AsLong(py_height);
    Py_DECREF(py_height);
    
    PyObject* data = PyObject_GetAttrString(grid, "data");
    
    int n = 1;
    int x;
    int y;
    for (y = 0; y < height; y++) {
        for (x = 0; x < width; x++) {
            PyObject *py_y = PyInt_FromLong(y);
            PyObject* col = PyObject_GetItem(data, py_y);
            Py_DECREF(py_y);
            PyObject *py_x = PyInt_FromLong(x);
            PyObject* cell = PyObject_GetItem(col, py_x);
            Py_DECREF(py_x);
            
            PyObject* key = PyString_FromString("number");
            if (calc_is_start_word(grid, x, y) == 1) {
                PyObject *py_n = PyInt_FromLong(n);
                PyDict_SetItem(cell, key, py_n);
                Py_DECREF(py_n);
                n++;
            } else {
                PyObject *py_zero = PyInt_FromLong(0);
                PyDict_SetItem(cell, key, py_zero);
                Py_DECREF(py_zero);
            }
            Py_DECREF(key);
        }
    }
    Py_DECREF(data);
    Py_RETURN_NONE;
}

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
        Slot slot = slots[s];
        if (dir == slot.dir) {
            int match_across = (dir == 0 && x>= slot.x
                && x < slot.x + slot.length && slot.y == y);
            int match_down = (dir == 1 && y >= slot.y
                && y < slot.y + slot.length && slot.x == x);
            if (match_across || match_down) {
                return s;
            }
        }
    }
    return -1;
}

// 1 = yes, 0 = no
int can_clear_char(Cell *cgrid, int width, int height, Slot slot) {
    int j;
    for (j = 0; j < slot.length; j++) {
        int cx = slot.x + (slot.dir == 0 ? j : 0);
        int cy = slot.y + (slot.dir == 1 ? j : 0);
        if (cgrid[cx + cy * height].c == CONSTRAINT_EMPTY)
            return 1;
    }
    return 0;
}

void clear_slot(Cell *cgrid, int width, int height, Slot *slots, int n_slots, int index) {
    Slot slot = slots[index];
    int l;
    for (l = 0; l < slot.length; l++) {
        if (cgrid[slot.x + slot.y * height].fixed == 1) continue;
        int cx = slot.x + (slot.dir == 0 ? l : 0);
        int cy = slot.y + (slot.dir == 1 ? l : 0);
        int m = get_slot_index(slots, n_slots, cx, cy, slot.dir == 0 ? 1 : 0);
        
        Cell *cell = &cgrid[cx + cy * height];
        if (can_clear_char(cgrid, width, height, slots[m]) && cell->c != CONSTRAINT_EMPTY) {
            cell->c = CONSTRAINT_EMPTY;
        }
    }
}

// 0 = false, 1 = true
int is_intersecting(Slot *slot1, Slot *slot2) {
    if (slot1->dir == slot2->dir) return 0;
    if (slot1->dir == 0) {
        return (slot2->x >= slot1->x && slot2->x < slot1->x + slot1->length
            && slot1->y >= slot2->y && slot1->y < slot2->y + slot2->length);
    } else if (slot1->dir == 1) {
        return (slot1->x >= slot2->x && slot1->x < slot2->x + slot2->length
            && slot2->y >= slot1->y && slot2->y < slot1->y + slot1->length);
    }
    return 0;
}

int is_valid(int x, int y, int width, int height) {
    return x >= 0 && y >= 0 && x < width && y < height;
}

int is_available(Cell *cgrid, int width, int height, int x, int y) {
    return cgrid[x + y * height].block == 0
        && cgrid[x + y * height].empty == 0
        && is_valid(x, y, width, height);
}

char* get_constraints(Cell *cgrid, int width, int height, Slot *slot) {
    char* cs = malloc(slot->length * sizeof(char));
    if (!cs) {
        return NULL;
    }
    int dx = slot->dir == 0 ? 1 : 0;
    int dy = slot->dir == 1 ? 1 : 0;
    int x = slot->x;
    int y = slot->y;
    int count = 0;
    while (is_available(cgrid, width, height, x, y)) {
        cs[count] = cgrid[x + y * height].c;
        if (dx == 1 && is_valid(x + dx, y, width, height) && cgrid[(x + dx) + y * height].left_bar == 1)
            break;
        if (dy == 1 && is_valid(x, y + dy, width, height) && cgrid[x + (y + dy) * height].top_bar == 1)
            break;
        x += dx;
        y += dy;
        count++;
    }
    return cs;
}

int determine_count(PyObject *words, Cell *cgrid, int width, int height, Slot *slot) {
    int prev = slot->count;
    char *ds = get_constraints(cgrid, width, height, slot);
    if (!ds) {
        printf("Warning: determine_count failed to obtain constraints.\n");
        return -1;
    }
    int count = count_words(words, slot->length, ds);
    if (DEBUG && count == 0) {
        printf("WARNING: slot (%i, %i, %i): from %i to %i\n", slot->x, slot->y, slot->dir, prev, count);
    }
    free(ds);
    return count;
}

// return = number of slots cleared
int backtrack(PyObject *words, Cell *cgrid, int width, int height, Slot *slots, int n_slots, int* order, int index) {
    int cleared = 0;
    int s;
    int iindex = -1;
    for (s = index; s >= 0; s--) {
        Slot *slot = &slots[order[s]];
        if (is_intersecting(slot, &slots[index])) {
            iindex = order[s];
            break;
        }
    }
    if (iindex >= 0) {
        if (DEBUG) {
            printf("Blanking between (%i, %i, %s) and (%i, %i, %s)\n"
                , (&slots[iindex])->x, (&slots[iindex])->y, (&slots[iindex])->dir == 0 ? "across" : "down"
                , (&slots[index])->x, (&slots[index])->y, (&slots[index])->dir == 0 ? "across" : "down" );
            printf("Indices: %i %i\n", iindex, index);
        }
        for (s = index; s >= iindex; s--) {
            cleared++;
            int blank = order[s];
            Slot *bslot = &slots[blank];
            if (DEBUG) {
                printf("Blanking: %i %i %i %i (%i, %i, %s)\n", s, blank, index, iindex, bslot->x, bslot->y, bslot->dir == 0 ? "across" : "down");
            }
            clear_slot(cgrid, width, height, slots, n_slots, blank);
            bslot->count = determine_count(words, cgrid, width, height, bslot);
            bslot->done = 0;
            if (blank > iindex) bslot->offset = 0;
            if (blank == iindex) bslot->offset++;
        }
    }
    int j;
    for (j = 0; j < n_slots; j++) {
        printf("%i ", order[j]);
    }
    printf("\n");
    return cleared;
}

PyObject* gather_fill(Cell *cgrid, int width, int height) {
    int x;
    int y;
    PyObject *fill = PyList_New(0);
    for (y = 0; y < height; y++) {
        for (x = 0; x < width; x++) {
            Cell *cell = &cgrid[x + y * height];
            if (cell->fixed == 1 || cell->c == CONSTRAINT_EMPTY) continue;
            char cell_c[2];
            cell_c[0] = toupper(cell->c);
            cell_c[1] = '\0';
            PyList_Append(fill, Py_BuildValue("(iis)", x, y, cell_c));
        }
    }
    return fill;
}

static PyObject*
cGrid_fill(PyObject *self, PyObject *args) {
    PyObject *grid;
    PyObject *words;
    PyObject *meta;
    if (!PyArg_ParseTuple(args, "OOO", &grid, &words, &meta))
        return NULL;
        
    int width = (int) PyInt_AsLong(PyObject_GetAttrString(grid, "width"));
    int height = (int) PyInt_AsLong(PyObject_GetAttrString(grid, "height"));
    PyObject* data = PyObject_GetAttrString(grid, "data");
    
    int x;
    int y;
    Cell cgrid[width * height];
    for (y = 0; y < height; y++) {
        for (x = 0; x < width; x++) {
            PyObject* col = PyObject_GetItem(data, PyInt_FromLong(y));
            PyObject* cell = PyObject_GetItem(col, PyInt_FromLong(x));
            PyObject* block_obj = PyObject_GetItem(cell, PyString_FromString("block"));
            PyObject* char_obj = PyObject_GetItem(cell, PyString_FromString("char"));
            PyObject* empty_obj = PyObject_GetItem(cell, PyString_FromString("void"));
            PyObject* number_obj = PyObject_GetItem(cell, PyString_FromString("number"));
            int is_block = PyObject_IsTrue(block_obj);
            int is_empty = PyObject_IsTrue(empty_obj);
            char* c_str = PyString_AsString(char_obj);
            int number = PyInt_AsLong(number_obj);
            int index = x + y * height;
            cgrid[index].top_bar = 0;
            cgrid[index].left_bar = 0;
            cgrid[index].block = is_block;
            cgrid[index].c = strlen(c_str) > 0 ? c_str[0] : CONSTRAINT_EMPTY;
            cgrid[index].number = number;
            cgrid[index].empty = is_empty;
            cgrid[index].fixed = cgrid[index].c == CONSTRAINT_EMPTY ? 0 : 1;
        }
    }

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
        char *cs = get_constraints(cgrid, width, height, &slots[m]);
        if (!cs) {
            printf("Warning: fill failed to obtain constraints.\n");
            return NULL;
        }
        slots[m].count = count_words(words, length, cs);
        slots[m].done = 1;
        slots[m].offset = 0;
        int j;
        for (j = 0; j < length; j++) {
            if (cs[j] == CONSTRAINT_EMPTY) {
                slots[m].done = 0;
            }
        }
        if (slots[m].done) {
            n_done_slots++;
        }
        free(cs);
    }
    
    int order[n_slots];
    int o;
    for (o = 0; o < n_slots; o++) {
        order[o] = -1;
    }
    
    int attempts = 0;
    PyObject *result = PyList_New(0);
    while (attempts < 10000) {
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
        Slot *slot = &slots[index];
        if (index < 0) {
            if (DEBUG) {
                printf("BREAKING - SHOULD NOT OCCUR\n");
            }
            break;
        }
        if (DEBUG) {
            printf("Searching word for (%i, %i, %s) at index %i: ", slot->x, slot->y, slot->dir == 0 ? "across" : "down", index);
        }
        char *cs = get_constraints(cgrid, width, height, slot);
        if (!cs) {
            printf("Warning: fill failed to obtain constraints.\n");
            return NULL;
        }
        
        int is_word_ok = 1;
        char* word = find_candidate(words, slot->length, cs, slot->offset);
        if (word) {
            if (DEBUG) {
                printf("%s (%i)\n", word, slot->offset);
            }
            int affected[slot->length];
            int k;
            for (k = 0; k < slot->length; k++) {
                // mark the affected slot of the modified cell
                affected[k] = -1;
                int cx = slot->x + (slot->dir == 0 ? k : 0);
                int cy = slot->y + (slot->dir == 1 ? k : 0);
                int dir = slot->dir == 0 ? 1 : 0;
                int indexD = get_slot_index(slots, n_slots, cx, cy, dir);
                if (indexD >= 0 && indexD != index) {
                    affected[k] = indexD;
                }
            }
            // update counts for affected slots
            slot->count = 1;
            if (DEBUG) {
                printf("before updating affected\n");
            }
            for (k = 0; k < slot->length; k++) {
                if (affected[k] >= 0) {
                    int cx = slot->x + (slot->dir == 0 ? k : 0);
                    int cy = slot->y + (slot->dir == 1 ? k : 0);
                    int is_empty = cgrid[cx + cy * height].c == CONSTRAINT_EMPTY;
                    cgrid[cx + cy * height].c = word[k];
                    int count = determine_count(words, cgrid, width, height, &slots[affected[k]]);
                    if (is_empty) {
                        cgrid[cx + cy * height].c = CONSTRAINT_EMPTY;
                    }
                    if (count == 0) {
                        is_word_ok = 0;
                        if (DEBUG) {
                            printf("WARNING: an intersecting slot has 0!!!\n");
                        }
                    }
                }
            }
            if (is_word_ok) {
                if (DEBUG) {
                    printf("before updating cells\n");
                }
                for (k = 0; k < slot->length; k++) {
                    int cx = slot->x + (slot->dir == 0 ? k : 0);
                    int cy = slot->y + (slot->dir == 1 ? k : 0);
                    cgrid[cx + cy * height].c = word[k];
                    int count = determine_count(words, cgrid, width, height, &slots[affected[k]]);
                    (&slots[affected[k]])->count = count;
                }
            } else {
                slot->offset += 1;
                if (DEBUG) {
                    printf("WORD IS NOT OK (%i %i %i) %i\n", slot->x, slot->y, slot->dir, slot->offset);
                }
            }
        } else {
            if (DEBUG) {
                printf("no word found\n");
            }
            if (n_done_slots > 0) {
                int cleared = backtrack(words, cgrid, width, height, slots, n_slots, order, n_done_slots);
                if (cleared < 0) {
                    break;
                }
                int c;
                for (c = n_done_slots; c >= n_done_slots - cleared; c--) {
                    order[c] = -1;
                }
                printf("subtracting %i\n", cleared);
                n_done_slots -= cleared;
            }
        }
        
        free(cs);
        
        if (is_word_ok) {
            slot->done = 1;
            order[n_done_slots] = index;
            printf("n_done_slots = %i and incrementing\n", n_done_slots);
            n_done_slots++;
        }
        attempts++;
    }
    
    PyObject *fill = gather_fill(cgrid, width, height);
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
