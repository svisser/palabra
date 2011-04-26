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

typedef struct sparams *SPPtr;
typedef struct sparams {
    int offset;
} SearchParams;

// return 1 if a word exists that matches the constraints, 0 otherwise
static int
cPalabra_calc_has_matches(PyObject *words, const int length, PyObject *constraints) {
    char cs[MAX_WORD_LENGTH];
    if (process_constraints(constraints, cs) == 1)
        return 2;
    Py_ssize_t w;
    for (w = 0; w < PyList_Size(words); w++) {
        PyObject *item = PyList_GetItem(words, w);
        char *word = PyString_AsString(item);
        if (length == PyString_Size(item) && check_constraints(word, cs)) {
            return 1;
        }
    }
    return 0;
}

static PyObject*
cPalabra_has_matches(PyObject *self, PyObject *args)
{
    PyObject *words;
    const int length;
    PyObject *constraints;
    if (!PyArg_ParseTuple(args, "OiO", &words, &length, &constraints))
        return NULL;
    if (!PyList_Check(words)) {
        PyErr_SetString(PyExc_TypeError, "cPalabra.has_matches expects a list as first argument.");
        return NULL;
    }
    if (!PyList_Check(constraints)) {
        PyErr_SetString(PyExc_TypeError, "cPalabra.has_matches expects a list as third argument");
        return NULL;
    }
    int has_matches = cPalabra_calc_has_matches(words, length, constraints);
    if (has_matches == 2)
        return NULL;
    if (has_matches == 1)
        Py_RETURN_TRUE;
    Py_RETURN_FALSE;
}

typedef struct {
    int index;
    int length;
    PyObject* cs;
    int skip; // 0 = ok, 1 = skip in search process
    int equal; // -1 = unique, 0 and up = index in array that this slot is equal to
} IntersectingSlot;

// 1 = equal, 0 = not equal, 2 = error
int is_intersecting_equal(IntersectingSlot s0, IntersectingSlot s1) {
    if (s0.index != s1.index) return 0;
    if (s0.length != s1.length) return 0;
    const Py_ssize_t len_m = PyList_Size(s0.cs);
    const Py_ssize_t len_mm = PyList_Size(s1.cs);
    if (len_m != len_mm) return 0;
    Py_ssize_t l;
    for (l = 0; l < len_m; l++) {
        const int j_m;
        const char *c_m;
        PyObject *tuple_m = PyList_GetItem(s0.cs, l);
        if (!PyArg_ParseTuple(tuple_m, "is", &j_m, &c_m))
            return 2;
        const int j_mm;
        const char *c_mm;
        PyObject *tuple_mm = PyList_GetItem(s1.cs, l);
        if (!PyArg_ParseTuple(tuple_mm, "is", &j_mm, &c_mm))
            return 2;
        if (j_m != j_mm || *c_m != *c_mm)
            return 0;
    }
    return 1;
}

void print(Tptr p, int indent)
{
    if (p == NULL) return;
    if (p->splitchar != 0) {
        int i;
        for (i = 0; i < indent; i++)
        {
            printf(" ");
        }
        printf("%c\n", p->splitchar);
    }
    if (p->lokid != NULL) print(p->lokid, indent + 2);
    if (p->eqkid != NULL) print(p->eqkid, indent + 2);
    if (p->hikid != NULL) print(p->hikid, indent + 2);
}

Tptr insert1(Tptr p, char *s, char *word)
{
    if (p == NULL) {
        p = (Tptr) PyMem_Malloc(sizeof(Tnode));
        p->splitchar = *s;
        p->word = word;
        p->lokid = p->eqkid = p->hikid = 0;
    }
    if (*s < p->splitchar)
        p->lokid = insert1(p->lokid, s, word);
    else if (*s == p->splitchar) {
        if (*s != 0)
            p->eqkid = insert1(p->eqkid, ++s, word);
    } else
        p->hikid = insert1(p->hikid, s, word);
    return p;
}

int analyze(int offset, Sptr result, Tptr p, char *s, char *cs)
{
    if (!p) return 0;
    int n = 0;
    if (*s == '.' || *s < p->splitchar)
        n += analyze(offset, result, p->lokid, s, cs);
    if (*s == '.' || *s == p->splitchar)
        if (p->splitchar && *s)
            n += analyze(offset, result, p->eqkid, s + 1, cs);
    if (*s == 0 && p->splitchar == 0) {
        n += 1;
        char intersect_char = *(cs + offset);
        if (intersect_char == '.') {
            char c = *(p->word + offset);
            int m;
            for (m = 0; m < MAX_ALPHABET_SIZE; m++) {
                if (result->chars[m] == c)
                    break;
                if (result->chars[m] == ' ') {
                    result->chars[m] = c;
                    break;
                }
            }
        } else {
            result->chars[0] = intersect_char;
        }
    }
    if (*s == '.' || *s > p->splitchar)
        n += analyze(offset, result, p->hikid, s, cs);
    result->n_matches = n;
    return n;
}

Sptr analyze_intersect_slot(int offset, char *cs) {
    if (!trees[strlen(cs)]) {
        return NULL;
    }
    Sptr result;
    result = (Sptr) PyMem_Malloc(sizeof(SearchResult));
    if (!result) {
        return NULL; //PyErr_NoMemory(); TODO fix
    }
    result->chars = PyMem_Malloc(MAX_ALPHABET_SIZE * sizeof(char));
    if (!result->chars) {
        PyMem_Free(result);
        return NULL; //PyErr_NoMemory(); TODO fix
    }
    int c;
    for (c = 0; c < MAX_ALPHABET_SIZE; c++) {
        result->chars[c] = ' ';
    }
    analyze(offset, result, trees[strlen(cs)], cs, cs);
    return result;
}

void analyze_intersect_slot2(Sptr *results, int *skipped, int *offsets, char **cs, int length) {
    int t;
    for (t = 0; t < length; t++) {
        int skip = -1;
        int s;
        for (s = 0; s < t; s++) {
            if (strcmp(cs[s], cs[t]) == 0) {
                skip = s;
                break;
            }
        }
        if (skip < 0) {
            results[t] = analyze_intersect_slot(offsets[t], cs[t]);
        } else {
            skipped[t] = 1;
            results[t] = results[skip];
        }
    }
}

static PyObject*
cPalabra_search(PyObject *self, PyObject *args) {
    PyObject *words;
    const int length;
    PyObject *constraints;
    PyObject *more_constraints;
    if (!PyArg_ParseTuple(args, "OiOO", &words, &length, &constraints, &more_constraints))
        return NULL;
    if (length <= 0 || length >= MAX_WORD_LENGTH)
        return PyList_New(0);
    char *cons_str = PyString_AS_STRING(constraints);
    // main word
    PyObject *mwords = PyList_New(0);
    mwords = find_matches(mwords, trees[strlen(cons_str)], cons_str);
    
    // each of the constraints
    int offsets[length];
    char *cs[length];
    int t;
    int skipped[length];
    for (t = 0; t < length; t++) skipped[t] = 0;
    Sptr results[length];
    if (more_constraints != Py_None) {
        for (t = 0; t < length; t++) {
            PyObject *py_cons_str2;
            PyObject* item = PyList_GET_ITEM(more_constraints, (Py_ssize_t) t);
            if (!PyArg_ParseTuple(item, "iO", &offsets[t], &py_cons_str2))
                return NULL;
            cs[t] = PyString_AS_STRING(py_cons_str2);
        }
        analyze_intersect_slot2(results, skipped, offsets, cs, length);
    }
    
    Py_ssize_t m;
    PyObject *result = PyList_New(0);
    for (m = 0; m < PyList_Size(mwords); m++) {
        char *word = PyString_AS_STRING(PyList_GET_ITEM(mwords, m));
        int valid = 1;
        if (more_constraints != Py_None) {
            valid = check_intersect(word, cs, length, results);
        }
        PyObject* py_intersect = PyBool_FromLong(valid);
        PyObject* item = Py_BuildValue("(sO)", word, py_intersect);
        Py_DECREF(py_intersect);
        PyList_Append(result, item);
        Py_DECREF(item);
    }
    if (more_constraints != Py_None) {
        for (t = 0; t < length; t++) {
            if (skipped[t] == 0 && results[t] != NULL) {
                PyMem_Free(results[t]->chars);
                PyMem_Free(results[t]);
            }
        }
    }
    return result;
}

static PyObject*
cPalabra_preprocess(PyObject *self, PyObject *args) {
    PyObject *words;
    if (!PyArg_ParseTuple(args, "O", &words))
        return NULL;
    
    // create dict (keys are word lengths, each item is a list with words of that length)
    PyObject* dict = PyDict_New();
    PyObject* keys[MAX_WORD_LENGTH];
    int l;
    for (l = 0; l < MAX_WORD_LENGTH; l++) {
        keys[l] = Py_BuildValue("i", l);
        PyObject *words = PyList_New(0);
        PyDict_SetItem(dict, keys[l], words);
        Py_DECREF(words);
        Py_DECREF(keys[l]);
    }
    Py_ssize_t w;
    for (w = 0; w < PyList_Size(words); w++) {
        PyObject* word = PyList_GET_ITEM(words, w);
        int length = (int) PyString_GET_SIZE(word);
        if (length <= 0 || length >= MAX_WORD_LENGTH)
            continue;
        PyObject* key = keys[length];
        // PyDict_GetItem eats ref
        PyList_Append(PyDict_GetItem(dict, key), word);
    }

    // build ternary search trees per word length
    // TODO insert in random order for best performance
    int m;
    for (m = 0; m < MAX_WORD_LENGTH; m++) {
        trees[m] = NULL;
        PyObject *key = Py_BuildValue("i", m);
        PyObject *words = PyDict_GetItem(dict, key);
        const Py_ssize_t len_m = PyList_Size(words);
        Py_ssize_t w;
        for (w = 0; w < len_m; w++) {
            char *word = PyString_AsString(PyList_GET_ITEM(words, w));
            trees[m] = insert1(trees[m], word, word);
        }
    }
    return dict;
}

void free_tree(Tptr p) {
    if (!p) return;
    if (p->lokid != NULL) {
        free_tree(p->lokid);
        PyMem_Free(p->lokid);
        p->lokid = NULL;
    }
    if (p->eqkid != NULL) {
        free_tree(p->eqkid);
        PyMem_Free(p->eqkid);
        p->eqkid = NULL;
    }
    if (p->hikid != NULL) {
        free_tree(p->hikid);
        PyMem_Free(p->hikid);
        p->hikid = NULL;
    }
}

static PyObject*
cPalabra_postprocess(PyObject *self, PyObject *args) {
    int m;
    for (m = 0; m < MAX_WORD_LENGTH; m++) {
        free_tree(trees[m]);
        free(trees[m]);
    }
    return Py_None;
}

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
    Py_ssize_t offset;
    PyObject *words;
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
cPalabra_is_available(PyObject *self, PyObject *args) {
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
cPalabra_assign_numbers(PyObject *self, PyObject *args) {
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
        if (cgrid[slot.x + slot.y * height].fixed == 1)
            continue;
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
    // TODO reduce these malloc calls
    char* cs = PyMem_Malloc(slot->length * sizeof(char) + 1);
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
    cs[slot->length] = '\0';
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
    PyMem_Free(ds);
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
            if (blank < 0) {
                // no word was actually filled in so skip
                continue;
            }
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
    /*int j;
    for (j = 0; j < n_slots; j++) {
        printf("%i ", order[j]);
    }
    printf("\n");*/
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

inline int find_initial_slot(Slot *slots, int n_slots, int option_start) {
    int index = -1;
    if (option_start == FILL_START_AT_ZERO) {
        index = 0;
    } else if (option_start == FILL_START_AT_SELECTION) {
        // TODO
    } else if (option_start == FILL_START_AT_AUTO) {
        // find most-constrained slot
        int m;
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
    }
    return index;
}

inline int find_slot(Slot *slots, int n_slots, int* order) {
    // find most-constrained slot that is connected to a previously filled in slot
    int index = -1;
    int o;
    for (o = 0; o < n_slots; o++) {
        if (order[o] < 0) break;
        int count = -1;
        
        int n_done = 0;
        
        int l;
        for (l = 0; l < slots[order[o]].length; l++) {
            int m;
            for (m = 0; m < n_slots; m++) {
                if (order[o] == m) continue;
                if (slots[m].done) continue;
                if (is_intersecting(&slots[order[o]], &slots[m])) {
                    if (slots[order[o]].dir == 0 && (slots[m].x - slots[order[o]].x == l)) {
                        index = m;
                        break;
                    } else if (slots[order[o]].dir == 1 && (slots[m].y - slots[order[o]].y == l)) {
                        index = m;
                        break;
                    }
                }
            }
            if (index >= 0) break;
        }
        if (index >= 0) break;
    }
    return index;
}

static PyObject*
cPalabra_fill(PyObject *self, PyObject *args) {
    PyObject *grid;
    PyObject *words;
    PyObject *meta;
    PyObject *options;
    if (!PyArg_ParseTuple(args, "OOOO", &grid, &words, &meta, &options))
        return NULL;
        
    const int OPTION_START = (int) PyInt_AsLong(PyDict_GetItem(options, PyString_FromString("start")));

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
        PyObject *s_words;
        if (!PyArg_ParseTuple(item, "iiiiOO", &x, &y, &dir, &length, &constraints, &s_words))
            return NULL;
        slots[m].x = x;
        slots[m].y = y;
        slots[m].dir = dir;
        slots[m].length = length;
        slots[m].words = s_words;
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
        PyMem_Free(cs);
    }
    
    int order[n_slots];
    int o;
    for (o = 0; o < n_slots; o++) {
        order[o] = -1;
    }
    
    int attempts = 0;
    int backtracked = 0;
    PyObject *result = PyList_New(0);
    PyObject *best_fill = NULL;
    int best_n_done_slots = 0;
    while (attempts < 5000) {
        int index = -1;
        if (n_done_slots == 0) {
            index = find_initial_slot(slots, n_slots, OPTION_START);
        } else {
            index = find_slot(slots, n_slots, order);
        }
        if (index < 0) break;
        Slot *slot = &slots[index];
        if (DEBUG) {
            printf("Searching word for (%i, %i, %s) at index %i: ", slot->x, slot->y, slot->dir == 0 ? "across" : "down", index);
        }
        char *cs = get_constraints(cgrid, width, height, slot);
        if (!cs) {
            printf("Warning: fill failed to obtain constraints.\n");
            return NULL;
        }
        
        char *cs_i[slot->length];
        int offsets[slot->length];
        for (m = 0; m < n_slots; m++) {
            if (is_intersecting(slot, &slots[m])) {
                int index = 0;
                int offset = 0;
                if (slot->dir == 0) {
                    index = slots[m].x - slot->x;
                    offset = slot->y - slots[m].y;
                } else {
                    index = (&slots[m])->y - slot->y;
                    offset = slot->x - (&slots[m])->x;
                }
                offsets[index] = offset;
                cs_i[index] = get_constraints(cgrid, width, height, &slots[m]);
            }
        }
        int skipped[slot->length];
        int t;
        for (t = 0; t < slot->length; t++) {
            skipped[t] = 0;
        }
        Sptr results[slot->length];
        analyze_intersect_slot2(results, skipped, offsets, cs_i, slot->length);
        
        int is_word_ok = 1;
        char* word = find_candidate(cs_i, results, slot->words, slot->length, cs, slot->offset);
        PyMem_Free(cs);
        for (m = 0; m < slot->length; m++) {
            if (cs_i[m]) {
                PyMem_Free(cs_i[m]);
            }
        }
        
        for (t = 0; t < slot->length; t++) {
            if (skipped[t] == 0 && results[t] != NULL) {
                PyMem_Free(results[t]->chars);
                PyMem_Free(results[t]);
            }
        }
        
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
                if (n_done_slots > best_n_done_slots) {
                    best_n_done_slots = n_done_slots;
                    Py_XDECREF(best_fill);
                    best_fill = gather_fill(cgrid, width, height);
                    printf("NEW BEST FILL: %i\n", best_n_done_slots);
                }
                backtracked++;
                int cleared = backtrack(words, cgrid, width, height, slots, n_slots, order, n_done_slots);
                if (cleared < 0) {
                    break;
                }
                int c;
                for (c = n_done_slots; c >= n_done_slots - cleared; c--) {
                    order[c] = -1;
                }
                n_done_slots -= cleared;
            }
        }
        
        if (is_word_ok) {
            slot->done = 1;
            order[n_done_slots] = index;
            printf("n_done_slots = %i - (%i %i %i), %s\n", n_done_slots, slot->x, slot->y, slot->dir, word);
            n_done_slots++;
        }
        attempts++;
    }
    if (best_fill != NULL) {
        PyList_Append(result, best_fill);
        Py_DECREF(best_fill);
    }
    return result;
}

static PyObject*
cPalabra_compute_lines(PyObject *self, PyObject *args) {
    PyObject *grid;
    if (!PyArg_ParseTuple(args, "O", &grid))
        return NULL;
    PyObject *py_width = PyObject_GetAttrString(grid, "width");
    int width = (int) PyInt_AsLong(py_width);
    Py_DECREF(py_width);
    PyObject *py_height = PyObject_GetAttrString(grid, "height");
    int height = (int) PyInt_AsLong(py_height);
    Py_DECREF(py_height);
    
    PyObject* lines = PyDict_New();
    
    PyObject* str_data = PyString_FromString("data");
    PyObject* data = PyObject_GetAttr(grid, str_data);
    Py_DECREF(str_data);
    int x = 0;
    int y = 0;
    int e = 0;
    for (y = 0; y < height; y++) {
        for (x = 0; x < width; x++) {
            PyObject *result = PyList_New(0);
            
            // is_void
            PyObject* py_y = PyInt_FromLong(y);
            PyObject* col = PyObject_GetItem(data, py_y);
            Py_DECREF(py_y);
            PyObject* py_x = PyInt_FromLong(x);
            PyObject* cell = PyObject_GetItem(col, py_x);
            Py_DECREF(py_x);
            PyObject *py_void = PyString_FromString("void");
            PyObject *item = PyObject_GetItem(cell, py_void);
            int v0 = PyObject_IsTrue(item);
            Py_DECREF(item);
            Py_DECREF(py_void);
            
            for (e = 0; e < 2; e++) {
                int dx = e == 0 ? -1 : 0;
                int dy = e == 0 ? 0 : -1;
                
                int nx = x + dx;
                int ny = y + dy;
                if (0 <= nx && nx < width && 0 <= ny && ny < height) {
                    // is_void
                    PyObject *py_ny = PyInt_FromLong(ny);
                    PyObject* col = PyObject_GetItem(data, py_ny);
                    Py_DECREF(py_ny);
                    PyObject *py_nx = PyInt_FromLong(nx);
                    PyObject* cell = PyObject_GetItem(col, py_nx);
                    Py_DECREF(py_nx);
                    PyObject *py_void = PyString_FromString("void");
                    PyObject *item = PyObject_GetItem(cell, py_void);
                    Py_DECREF(py_void);
                    Py_DECREF(cell);
                    Py_DECREF(col);
                    int v1 = PyObject_IsTrue(item);
                    Py_DECREF(item);
                    if (v0 == 0 || v1 == 0) {
                        PyObject* r = NULL;
                        if (v0 == 1 && v1 == 0) {
                            r = Py_BuildValue("(iiss)",  x, y, e == 0 ? "left" : "top", "innerborder");
                        } else if (v0 == 0 && v1 == 1) {
                            r = Py_BuildValue("(iiss)",  x, y, e == 0 ? "left" : "top", "outerborder");
                        } else {
                            r = Py_BuildValue("(iiss)",  x, y, e == 0 ? "left" : "top", "normal");
                        }
                        PyList_Append(result, r);
                        Py_DECREF(r);
                    }
                } else if (v0 == 0) {
                    PyObject* r = Py_BuildValue("(iiss)",  x, y, e == 0 ? "left" : "top", "outerborder");
                    PyList_Append(result, r);
                    Py_DECREF(r);
                }
            }
            if (y == height - 1) {
                // is_void
                PyObject *py_y = PyInt_FromLong(height - 1);
                PyObject* col = PyObject_GetItem(data, py_y);
                Py_DECREF(py_y);
                PyObject *py_x = PyInt_FromLong(x);
                PyObject* cell = PyObject_GetItem(col, py_x);
                Py_DECREF(py_x);
                PyObject *py_void = PyString_FromString("void");
                PyObject *item = PyObject_GetItem(cell, py_void);
                Py_DECREF(py_void);
                Py_DECREF(cell);
                Py_DECREF(col);
                int v = PyObject_IsTrue(item);
                Py_DECREF(item);
                if (v == 0) {
                    PyObject* r = Py_BuildValue("(iiss)",  x, height, "top", "innerborder");
                    PyList_Append(result, r);
                    Py_DECREF(r);
                }
            }
            if (x == width - 1) {
                // is_void
                PyObject *py_y = PyInt_FromLong(y);
                PyObject* col = PyObject_GetItem(data, py_y);
                Py_DECREF(py_y);
                PyObject *py_x = PyInt_FromLong(width - 1);
                PyObject* cell = PyObject_GetItem(col, py_x);
                Py_DECREF(py_x);
                PyObject *py_void = PyString_FromString("void");
                PyObject *item = PyObject_GetItem(cell, py_void);
                Py_DECREF(py_void);
                Py_DECREF(cell);
                Py_DECREF(col);
                int v = PyObject_IsTrue(item);
                Py_DECREF(item);
                if (v == 0) {
                    PyObject* r = Py_BuildValue("(iiss)",  width, y, "left", "innerborder");
                    PyList_Append(result, r);
                    Py_DECREF(r);
                }
            }
            PyObject* key = Py_BuildValue("(ii)", x, y);
            PyDict_SetItem(lines, key, result);
            Py_DECREF(key);
            Py_DECREF(result);
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
    {"has_matches",  cPalabra_has_matches, METH_VARARGS, "has_matches"},
    {"search", cPalabra_search, METH_VARARGS, "search"},
    {"preprocess", cPalabra_preprocess, METH_VARARGS, "preprocess"},
    {"postprocess", cPalabra_postprocess, METH_VARARGS, "postprocess"},
    {"is_available",  cPalabra_is_available, METH_VARARGS, "is_available"},
    {"assign_numbers", cPalabra_assign_numbers, METH_VARARGS, "assign_numbers"},
    {"fill", cPalabra_fill, METH_VARARGS, "fill"},
    {"compute_lines",  cPalabra_compute_lines, METH_VARARGS, "compute_lines"},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initcPalabra(void)
{
    (void) Py_InitModule("cPalabra", methods);
}
