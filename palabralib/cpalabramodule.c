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

static PyObject*
cPalabra_search(PyObject *self, PyObject *args) {
    const int length;
    PyObject *constraints;
    PyObject *more_constraints;
    PyObject *indices;
    if (!PyArg_ParseTuple(args, "iOOO", &length, &constraints, &more_constraints, &indices))
        return NULL;
    if (length <= 0 || length >= MAX_WORD_LENGTH)
        return PyList_New(0);
    char *cons_str = PyString_AS_STRING(constraints);
    
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

    // main word
    PyObject *result = PyList_New(0);
    Py_ssize_t ii;
    for (ii = 0; ii < PyList_Size(indices); ii++) {
        const int index = (int) PyInt_AsLong(PyList_GET_ITEM(indices, ii));
        
        PyObject *mwords = PyList_New(0);
        mwords = find_matches(mwords, trees[index][strlen(cons_str)], cons_str);
        Py_ssize_t m;
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
    const int index;
    if (!PyArg_ParseTuple(args, "Oi", &words, &index))
        return NULL;
    
    // create dict (keys are word lengths, each item is a list with words of that length)
    PyObject* dict = PyDict_New();
    PyObject* keys[MAX_WORD_LENGTH];
    int l;
    for (l = 0; l < MAX_WORD_LENGTH; l++) {
        keys[l] = Py_BuildValue("i", l);
        PyObject *ws = PyList_New(0);
        PyDict_SetItem(dict, keys[l], ws);
        Py_DECREF(ws);
        Py_DECREF(keys[l]);
    }
    Py_ssize_t w;
    for (w = 0; w < PyList_Size(words); w++) {
        PyObject* word = PyList_GET_ITEM(words, w);
        PyObject* word_str;
        const int word_rank;
        if (!PyArg_ParseTuple(word, "Oi", &word_str, &word_rank))
            return NULL;
        int length = (int) PyString_GET_SIZE(word_str);
        if (length <= 0 || length >= MAX_WORD_LENGTH)
            continue;
        PyObject* key = keys[length];
        // PyDict_GetItem eats ref
        PyList_Append(PyDict_GetItem(dict, key), word_str);
    }

    // build ternary search trees per word length
    // TODO insert in random order for best performance
    int m;
    for (m = 0; m < MAX_WORD_LENGTH; m++) {
        trees[index][m] = NULL;
        PyObject *key = Py_BuildValue("i", m);
        PyObject *words = PyDict_GetItem(dict, key);
        const Py_ssize_t len_m = PyList_Size(words);
        Py_ssize_t w;
        for (w = 0; w < len_m; w++) {
            char *word = PyString_AsString(PyList_GET_ITEM(words, w));
            trees[index][m] = insert1(trees[index][m], word, word);
        }
    }
    return dict;
}

static PyObject*
cPalabra_postprocess(PyObject *self, PyObject *args) {
    int i;
    for (i = 0; i < MAX_WORD_LISTS + 1; i++) {
        int m;
        for (m = 0; m < MAX_WORD_LENGTH; m++) {
            if (trees[i][m] != NULL) {
                free_tree(trees[i][m]);
                free(trees[i][m]);
            }
        }
    }
    return Py_None;
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
    PyObject *result = PyList_New(0);
    PyObject *best_fill = NULL;
    int best_n_done_slots = 0;
    while (attempts < 25000) {
        int index = -1;
        if (attempts == 0 || n_done_slots == 0) {
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
        //printf("Candidate: %s (%i %i %i)\n", word, slot->x, slot->y, slot->dir);
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
            is_word_ok = 0;
            if (DEBUG) {
                printf("no word found\n");
            }
            if (n_done_slots > 0) {
                //printf("About to backtrack\n");            
                if (n_done_slots > best_n_done_slots) {
                    best_n_done_slots = n_done_slots;
                    Py_XDECREF(best_fill);
                    best_fill = gather_fill(cgrid, width, height);
                    //printf("NEW BEST FILL: %i\n", best_n_done_slots);
                }
                int c;
                for (c = 0; c < n_slots; c++) {
                    if (order[c] < 0) break;
                    //printf("(%i: %i %i %i) ", c, slots[order[c]].x, slots[order[c]].y, slots[order[c]].dir);
                }
                //printf("\n");
                //printf("Calling backtrack for %i %i %i\n", slots[index].x, slots[index].y, slots[index].dir);
                int cleared = backtrack(words, cgrid, width, height, slots, n_slots, order, n_done_slots, index);
                if (cleared == 0) {
                    printf("NOTHING WAS CLEARED\n");
                    break;
                }
                if (cleared < 0) {
                    break;
                }
                //int c;
                for (c = n_done_slots; c >= n_done_slots - cleared; c--) {
                    order[c] = -1;
                }
                n_done_slots -= cleared;
            }
        }
        //printf("running %i %i\n", attempts, n_done_slots);
        //if (attempts > 0 && n_done_slots == 0) break;
        if (attempts % 1000 == 0) printf("%i\n", attempts);
        
        if (is_word_ok) {
            slot->done = 1;
            order[n_done_slots] = index;
            n_done_slots++;
            //printf("Filled in: %s (%i %i %i)\n", word, slot->x, slot->y, slot->dir);
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
