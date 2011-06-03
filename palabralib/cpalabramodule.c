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

static PyObject*
cPalabra_search(PyObject *self, PyObject *args) {
    const int length;
    PyObject *constraints;
    PyObject *more_constraints;
    PyObject *indices;
    PyObject *options;
    if (!PyArg_ParseTuple(args, "iOOOO", &length, &constraints, &more_constraints, &indices, &options))
        return NULL;
    if (length <= 0 || length >= MAX_WORD_LENGTH)
        return PyList_New(0);
    char *cons_str = PyString_AS_STRING(constraints);
    const Py_ssize_t n_indices = PyList_Size(indices);
    
    const int HAS_OPTIONS = options != Py_None;
    int OPTION_MIN_SCORE = -9999; // TODO ugly
    if (HAS_OPTIONS) {
        OPTION_MIN_SCORE = (int) PyInt_AsLong(PyDict_GetItem(options, PyString_FromString("min_score")));
    }

    // each of the constraints
    int offsets[length];
    char *cs[length];
    int t;
    int skipped[length];
    for (t = 0; t < length; t++) skipped[t] = 0;
    Sptr results[n_indices][length];
    if (more_constraints != Py_None) {
        for (t = 0; t < length; t++) {
            PyObject *py_cons_str2;
            PyObject* item = PyList_GET_ITEM(more_constraints, (Py_ssize_t) t);
            if (!PyArg_ParseTuple(item, "iO", &offsets[t], &py_cons_str2))
                return NULL;
            cs[t] = PyString_AS_STRING(py_cons_str2);
        }
        Py_ssize_t ii;
        for (ii = 0; ii < n_indices; ii++) {
            const int index = (int) PyInt_AsLong(PyList_GET_ITEM(indices, ii));
            analyze_intersect_slot2(results[ii], skipped, offsets, cs, length, index, OPTION_MIN_SCORE);
        }
    }

    // main word
    PyObject *result = PyList_New(0);
    Py_ssize_t ii;
    for (ii = 0; ii < n_indices; ii++) {
        const int index = (int) PyInt_AsLong(PyList_GET_ITEM(indices, ii));
        PyObject *mwords = PyList_New(0);
        mwords = find_matches(mwords, trees[index][strlen(cons_str)], cons_str);
        Py_ssize_t m;
        for (m = 0; m < PyList_Size(mwords); m++) {
            PyObject* m_item = PyList_GET_ITEM(mwords, m);
            PyObject* word_str;
            const int score;
            if (!PyArg_ParseTuple(m_item, "Oi", &word_str, &score))
                return NULL;
            if (HAS_OPTIONS && score < OPTION_MIN_SCORE)
                continue;
            char *word = PyString_AS_STRING(word_str);
            int valid = 1;
            if (more_constraints != Py_None) {
                valid = 0;
                // TODO refactor with find_candidate
                int is_char_ok[MAX_WORD_LENGTH];
                int i;
                for (i = 0; i < length; i++) {
                    is_char_ok[i] = 0;
                }
                // mark fully filled in intersecting words also as ok
                for (i = 0; i < length; i++) {
                    if (strchr(cs[i], '.') == NULL)
                        is_char_ok[i] = 1;
                }
                Py_ssize_t jj;
                for (jj = 0; jj < n_indices; jj++) {
                    check_intersect(word, cs, length, results[jj], is_char_ok);
                    int n_chars = 0;
                    int j;
                    for (j = 0; j < length; j++) {
                        if (is_char_ok[j]) n_chars++;
                    }
                    if (n_chars == length) {
                        valid = 1;
                        break;
                    }
                }
            }
            PyObject* item = Py_BuildValue("(sib)", word, score, valid);
            PyList_Append(result, item);
            Py_DECREF(item);
        }
    }
    if (more_constraints != Py_None) {
        Py_ssize_t ii;
        for (ii = 0; ii < n_indices; ii++) {
            for (t = 0; t < length; t++) {
                if (skipped[t] == 0 && results[ii][t] != NULL) {
                    PyMem_Free(results[ii][t]->chars);
                    PyMem_Free(results[ii][t]);
                }
            }
        }
    }
    return result;
}

static PyObject*
cPalabra_preprocess_all(PyObject *self, PyObject *args) {
    // make sure each tree is initialized
    int n;
    for (n = 0; n < MAX_WORD_LISTS + 1; n++) {
        int m;
        for (m = 0; m < MAX_WORD_LENGTH; m++) {
            trees[n][m] = NULL;
        }
    }
    return Py_None;
}

static PyObject*
cPalabra_preprocess(PyObject *self, PyObject *args) {
    PyObject *words;
    const int index;
    if (!PyArg_ParseTuple(args, "Oi", &words, &index))
        return NULL;
    
    // create dict
    // keys = word lengths
    // values = list with words of that length
    // each item has (word, score)
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
        const int word_score;
        if (!PyArg_ParseTuple(word, "Oi", &word_str, &word_score))
            return NULL;
        int length = (int) PyString_GET_SIZE(word_str);
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
        // clear previous tree in case we are rebuilding for this index
        if (trees[index][m] != NULL) {
            free_tree(trees[index][m]);
            PyMem_Free(trees[index][m]);
        }
        trees[index][m] = NULL;
        PyObject *key = Py_BuildValue("i", m);
        PyObject *words = PyDict_GetItem(dict, key);
        const Py_ssize_t len_m = PyList_Size(words);
        Py_ssize_t w;
        for (w = 0; w < len_m; w++) {
            PyObject *w_word = PyList_GET_ITEM(words, w);
            PyObject* w_str;
            const int w_score;
            if (!PyArg_ParseTuple(w_word, "Oi", &w_str, &w_score))
                return NULL;
            char *c_word = PyString_AsString(w_str);
            trees[index][m] = insert1(trees[index][m], c_word, c_word, w_score);
        }
    }
    return dict;
}

static PyObject*
cPalabra_insert_word(PyObject *self, PyObject *args) {
    const int index;
    const int length;
    char *word;
    const int score;
    if (!PyArg_ParseTuple(args, "iisi", &index, &length, &word, &score))
        return NULL;
    trees[index][length] = insert1(trees[index][length], word, word, score);
    return Py_None;
}

static PyObject*
cPalabra_postprocess(PyObject *self, PyObject *args) {
    int i;
    for (i = 0; i < MAX_WORD_LISTS + 1; i++) {
        if (trees[i] == NULL) continue;
        int m;
        for (m = 0; m < MAX_WORD_LENGTH; m++) {
            if (trees[i][m] != NULL) {
                free_tree(trees[i][m]);
                PyMem_Free(trees[i][m]);
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
    const int OPTION_NICE = (int) PyInt_AsLong(PyDict_GetItem(options, PyString_FromString("nice")));
    const int OPTION_DUPLICATE = (int) PyInt_AsLong(PyDict_GetItem(options, PyString_FromString("duplicate")));
    const int NICE_COUNT = (int) PyInt_AsLong(PyDict_GetItem(options, PyString_FromString("nice_count")));

    const int width = (int) PyInt_AsLong(PyObject_GetAttrString(grid, "width"));
    const int height = (int) PyInt_AsLong(PyObject_GetAttrString(grid, "height"));
    PyObject* data = PyObject_GetAttrString(grid, "data");
    
    const int OUTPUT_DEBUG = 0;
    
    int x;
    int y;
    Cell cgrid[width * height];
    for (y = 0; y < height; y++) {
        for (x = 0; x < width; x++) {
            PyObject* col = PyObject_GetItem(data, PyInt_FromLong(y));
            PyObject* cell = PyObject_GetItem(col, PyInt_FromLong(x));
            PyObject* block_obj = PyObject_GetItem(cell, PyString_FromString("block"));
            PyObject* empty_obj = PyObject_GetItem(cell, PyString_FromString("void"));
            PyObject* number_obj = PyObject_GetItem(cell, PyString_FromString("number"));
            const int is_block = PyObject_IsTrue(block_obj);
            const int is_empty = PyObject_IsTrue(empty_obj);
            const int number = PyInt_AsLong(number_obj);
            const int index = x + y * width;
            cgrid[index].top_bar = 0;
            cgrid[index].left_bar = 0;
            cgrid[index].block = is_block;
            cgrid[index].c = CONSTRAINT_EMPTY; // chars are read later
            cgrid[index].number = number;
            cgrid[index].empty = is_empty;
            cgrid[index].fixed = 0;
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
        
        Py_ssize_t c_i;
        for (c_i = 0; c_i < PyList_Size(constraints); c_i++) {
            PyObject *item = PyList_GET_ITEM(constraints, c_i);
            const int offset;
            const char *c_c;
            if (!PyArg_ParseTuple(item, "is", &offset, &c_c))
                return NULL;
            int cx = x + (dir == DIR_ACROSS ? offset : 0);
            int cy = y + (dir == DIR_DOWN ? offset : 0);
            const int index = cx + cy * width;
            cgrid[index].c = c_c[0];
            cgrid[index].fixed = 1;
        }
        
        slots[m].cs = PyMem_Malloc(length * sizeof(char) + 1);
        if (!slots[m].cs) {
            printf("Warning: fill failed to obtain constraints.\n");
            return NULL;
        }
        get_constraints_i(cgrid, width, height, &slots[m], slots[m].cs);
        slots[m].count = count_words(words, length, slots[m].cs);
        slots[m].done = 1;
        slots[m].offset = 0;
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
    
    int order[n_slots];
    int o;
    for (o = 0; o < n_slots; o++) {
        order[o] = -1;
    }
    
    int attempts = 0;
    PyObject *result = PyList_New(0);
    PyObject *best_fill = NULL;
    int best_n_done_slots = 0;
    while (attempts < 1000) {
        int index = -1;
        if (OPTION_NICE) {
            index = find_nice_slot(words, slots, n_slots, width, height, order);
        } else if (attempts == 0 || n_done_slots == 0) {
            index = find_initial_slot(slots, n_slots, OPTION_START);
        } else {
            index = find_slot(slots, n_slots, order);
        }
        if (index < 0) break;
        Slot *slot = &slots[index];
        if (DEBUG) {
            printf("Searching word for (%i, %i, %s, %i) at index %i: \n", slot->x, slot->y, slot->dir == 0 ? "across" : "down", slot->count, index);
        }
        get_constraints_i(cgrid, width, height, slot, slot->cs);
        
        char *cs_i[slot->length];
        for (m = 0; m < slot->length; m++) {
            cs_i[m] = NULL;
        }
        int offsets[slot->length];
        Sptr results[slot->length];
        int skipped[slot->length];
        int t;
        for (t = 0; t < slot->length; t++) {
            skipped[t] = 0;
            results[t] = NULL;
        }
        if (!OPTION_NICE) {
            for (m = 0; m < n_slots; m++) {
                if (is_intersecting(slot, &slots[m])) {
                    int index = 0;
                    int offset = 0;
                    if (slot->dir == DIR_ACROSS) {
                        index = slots[m].x - slot->x;
                        offset = slot->y - slots[m].y;
                    } else {
                        index = (&slots[m])->y - slot->y;
                        offset = slot->x - (&slots[m])->x;
                    }
                    cs_i[index] = PyMem_Malloc(slots[m].length * sizeof(char) + 1);
                    offsets[index] = offset;
                    get_constraints_i(cgrid, width, height, &slots[m], cs_i[index]);
                }
            }
            // TODO index
            // TODO min_score
            analyze_intersect_slot2(results, skipped, offsets, cs_i, slot->length, 0, -9999);
        }
        
        int is_word_ok = 1;
        
        /*int s;
        for (s = 0; s < n_slots; s++) {
            printf("%i %i %i (%i), ", slots[s].x, slots[s].y, slots[s].dir, slots[s].offset);
        }*/
        
        //printf("Trying for %i %i %i\n", slot->x, slot->y, slot->dir);
        char* word = find_candidate(cs_i, results, slot, slot->cs, OPTION_NICE, slot->offset);
        //if (word) printf("before %s at %i %i %i from %i\n", word, slot->x, slot->y, slot->dir, slot->offset);
        if (0) {
            PyObject *val = Py_BuildValue("(ssiiii)", "before", word, slot->x, slot->y, slot->dir, slot->offset);
            PyList_Append(result, val);
            Py_DECREF(val);
        }
        
        if (word && OPTION_DUPLICATE) {
            int duplicates[n_slots];
            for (t = 0; t < n_slots; t++) {
                duplicates[t] = 0;
            }
            while (1) {
                int added_offset = 0;
                int next = 0;
                for (t = 0; t < n_slots; t++) {
                    if (!slots[t].done) continue;
                    if (duplicates[t]) added_offset++;
                    char *word_t = get_constraints(cgrid, width, height, &slots[t]);
                    if (word_t && strcmp(word, word_t) == 0) {
                        PyMem_Free(word_t);
                        duplicates[t] = 1;
                        added_offset++;
                        word = find_candidate(cs_i, results, slot, slot->cs, OPTION_NICE, slot->offset + added_offset);
                        next = word != NULL;
                        break;
                    }
                }
                if (!next) break;
            }
        }
        //if (word) printf("after %s at %i %i %i from %i\n", word, slot->x, slot->y, slot->dir, slot->offset);
        if (0 && word) {
            PyObject *val = Py_BuildValue("(ssiiii)", "after", word, slot->x, slot->y, slot->dir, slot->offset);
            PyList_Append(result, val);
            Py_DECREF(val);
        }
        
        for (m = 0; m < slot->length; m++) {
            if (cs_i[m] != NULL) {
                PyMem_Free(cs_i[m]);
            }
        }
        
        for (t = 0; t < slot->length; t++) {
            if (skipped[t] == 0 && results[t] != NULL) {
                PyMem_Free(results[t]->chars);
                PyMem_Free(results[t]);
            }
        }
        
        int is_backtrack = 0;
        if (!word) {
            is_backtrack = 1;
        }
        if (word) {
            int affected[slot->length];
            int k;
            for (k = 0; k < slot->length; k++) {
                // mark the affected slot of the modified cell
                affected[k] = -1;
                int cx = slot->x + (slot->dir == DIR_ACROSS ? k : 0);
                int cy = slot->y + (slot->dir == DIR_DOWN ? k : 0);
                int dir = slot->dir == DIR_ACROSS ? 1 : 0;
                int indexD = get_slot_index(slots, n_slots, cx, cy, dir);
                if (indexD >= 0 && indexD != index) {
                    affected[k] = indexD;
                }
            }
            // update counts for affected slots
            slot->count = 1;
            for (k = 0; k < slot->length; k++) {
                if (affected[k] >= 0) {
                    int cx = slot->x + (slot->dir == DIR_ACROSS ? k : 0);
                    int cy = slot->y + (slot->dir == DIR_DOWN ? k : 0);
                    int is_empty = cgrid[cx + cy * width].c == CONSTRAINT_EMPTY;
                    cgrid[cx + cy * width].c = word[k];
                    int count = determine_count(words, cgrid, width, height, &slots[affected[k]]);
                    if (is_empty) {
                        cgrid[cx + cy * width].c = CONSTRAINT_EMPTY;
                    }
                    // words are not ok when intersecting slot has nothing
                    if (!OPTION_NICE && count == 0) {
                        is_backtrack = 1;
                    }
                }
            }
            if (!is_backtrack) {
                for (k = 0; k < slot->length; k++) {
                    int cx = slot->x + (slot->dir == DIR_ACROSS ? k : 0);
                    int cy = slot->y + (slot->dir == DIR_DOWN ? k : 0);
                    cgrid[cx + cy * width].c = word[k];
                    if (affected[k] >= 0) {
                        int count = determine_count(words, cgrid, width, height, &slots[affected[k]]);
                        (&slots[affected[k]])->count = count;
                        // if an intersecting slot is not yet done, reset
                        // offset because constraints have changed.
                        if (!slots[affected[k]].done) {
                            (&slots[affected[k]])->offset = 0;
                        }
                    }
                }
            }
        }
        if (is_backtrack) {
            //printf("Backtracking\n");
            is_word_ok = 0;
            if (n_done_slots > 0) {
                if (OPTION_NICE ? n_done_slots == NICE_COUNT : n_done_slots > best_n_done_slots) {
                    best_n_done_slots = n_done_slots;
                    Py_XDECREF(best_fill);
                    best_fill = gather_fill(cgrid, width, height);
                }
                int c;
                for (c = 0; c < n_slots; c++) {
                    if (order[c] < 0) break;
                }
                int cleared = backtrack(words, cgrid, width, height, slots, n_slots, order, n_done_slots, index);
                //assert cleared > 0
                for (c = n_done_slots; c >= n_done_slots - cleared; c--) {
                    order[c] = -1;
                }
                n_done_slots -= cleared;
            }
        }
        if (OUTPUT_DEBUG) {
            PyObject *val = gather_fill(cgrid, width, height);
            PyList_Append(result, val);
            Py_DECREF(val);
        }
        if (is_word_ok) {
            slot->done = 1;
            order[n_done_slots] = index;
            n_done_slots++;
            //printf("Filled in: %s (%i %i %i)\n", word, slot->x, slot->y, slot->dir);
        }
        if (OPTION_NICE && n_done_slots == NICE_COUNT) break;
        attempts++;
    }
    if (best_fill == NULL && (OPTION_NICE ? n_done_slots == NICE_COUNT : 1)) {
        best_fill = gather_fill(cgrid, width, height);
    }
    if (best_fill != NULL) {
        PyList_Append(result, best_fill);
        Py_DECREF(best_fill);
    }
    for (m = 0; m < n_slots; m++) {
        PyMem_Free(slots[m].cs);
    }
    return result;
}

static PyObject*
cPalabra_compute_lines(PyObject *self, PyObject *args) {
    // left lines must be returned before top lines (needed for compute_render_lines)
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
            
            // e == 0 (left) or e == 1 (top)
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

static PyObject*
cPalabra_compute_render_lines(PyObject *self, PyObject *args) {
    PyObject *grid;
    PyObject *data;
    PyObject *cells;
    PyObject *grid_lines;
    PyObject *all_lines;
    PyObject *sx;
    PyObject *sy;
    const int line_width;
    const int border_width;
    const float cell_size;
    if (!PyArg_ParseTuple(args, "OOOOOOOiif", &grid, &data, &cells, &grid_lines, &all_lines
        , &sx, &sy, &line_width, &border_width, &cell_size))
        return NULL;
    PyObject* result = PyList_New(0);
    
    const int width = (int) PyInt_AsLong(PyObject_GetAttrString(grid, "width"));
    const int height = (int) PyInt_AsLong(PyObject_GetAttrString(grid, "height"));
    
    Py_ssize_t a;
    Py_ssize_t n_lines = PyList_Size(all_lines);
    int all_x[n_lines];
    int all_y[n_lines];
    char *all_t[n_lines];
    char *all_s[n_lines];
    for (a = 0; a < n_lines; a++) {
        PyObject *v_item = PyList_GetItem(all_lines, a);
        const int v_x;
        const int v_y;
        PyObject *v_ltype;
        PyObject *v_side;
        if (!PyArg_ParseTuple(v_item, "iiOO", &v_x, &v_y, &v_ltype, &v_side))
            return NULL;
        all_x[a] = v_x;
        all_y[a] = v_y;
        all_t[a] = PyString_AsString(v_ltype);
        all_s[a] = PyString_AsString(v_side);
    }

    Py_ssize_t c;
    for (c = 0; c < PyList_Size(cells); c++) {
        PyObject *cell = PyList_GetItem(cells, c);
        const int x;
        const int y;
        if (!PyArg_ParseTuple(cell, "ii", &x, &y))
            return NULL;
        PyObject *cell_lines = PyDict_GetItem(grid_lines, cell);
        
        int has_left_border_line = 0;
        int has_right_border_line = 0;
        
        // peek at cell to the right to see if there's a border
        Py_ssize_t m;
        for (m = 0; m < n_lines; m++) {
            if (all_x[m] == x + 1
                && all_y[m] == y
                && strcmp(all_t[m], "left") == 0
                && strcmp(all_s[m], "innerborder") == 0) {
                has_right_border_line = 1;
                break;
            }
        }

        Py_ssize_t l;
        for (l = 0; l < PyList_Size(cell_lines); l++) {
            PyObject *line = PyList_GetItem(cell_lines, l);
            const int p;
            const int q;
            PyObject *ltype;
            PyObject *side;
            if (!PyArg_ParseTuple(line, "iiOO", &p, &q, &ltype, &side))
                return NULL;
            char *str_ltype = PyString_AsString(ltype);
            char *str_side = PyString_AsString(side);
            
            PyObject *py_p = PyInt_FromLong(p);
            PyObject *py_q = PyInt_FromLong(q);
            PyObject *py_sx_p = PyObject_GetItem(sx, py_p);
            PyObject *py_sy_q = PyObject_GetItem(sy, py_q);
            Py_DECREF(py_p);
            Py_DECREF(py_q);
            const float sx_p = (float) PyFloat_AsDouble(py_sx_p);
            const float sy_q = (float) PyFloat_AsDouble(py_sy_q);
            int bar = 0 <= x && x < width && 0 <= y && y < height;
            if (bar) {
                PyObject *py_y = PyInt_FromLong(y);
                PyObject* col = PyObject_GetItem(data, py_y);
                Py_DECREF(py_y);
                PyObject *py_x = PyInt_FromLong(x);
                PyObject* cell = PyObject_GetItem(col, py_x);
                Py_DECREF(py_x);
                PyObject *py_bar = PyString_FromString("bar");
                PyObject *item = PyObject_GetItem(cell, py_bar);
                Py_DECREF(py_bar);
                PyObject *b_item = PyObject_GetItem(item, ltype);
                Py_DECREF(item);
                bar = PyObject_IsTrue(b_item);
                Py_DECREF(b_item);
            }            
            const int l_is_normal = strcmp(str_side, "normal") == 0;
            const int l_is_outer = strcmp(str_side, "outerborder") == 0;
            const int l_is_inner = strcmp(str_side, "innerborder") == 0;
            const int l_is_top = strcmp(str_ltype, "top") == 0;
            const int l_is_left = strcmp(str_ltype, "left") == 0;
            const int l_is_border = l_is_outer || l_is_inner;
            
            float start = 0;
            if (l_is_normal) {
                start = -0.5 * line_width;
            } else if (l_is_outer) {
                start = -0.5 * border_width;
            } else if (l_is_inner) {
                start = 0.5 * border_width;
                int check_x = 0;
                int check_y = 0;
                if (l_is_top) {
                    check_x = x;
                    check_y = y + 1;
                } else if (l_is_left) {
                    check_x = x + 1;
                    check_y = y;
                }
                if (calc_is_available(grid, check_x, check_y) == 0 ||
                    calc_is_available(grid, x, y) == 0) {
                    start -= line_width;
                }
            }
            if (l_is_left) {
                has_left_border_line = l_is_border;
                PyObject* r = Py_BuildValue("(ffifiii)", sx_p + start, sy_q, 0, cell_size, bar, l_is_border, 0);
                PyList_Append(result, r);
                Py_DECREF(r);
            } else if (l_is_top) {
                int is_lb = 1;
                int is_rb = 1;
                // TODO refactor
                int x1_y1_left_outerborder = 0;
                int x1_y_left_outerborder = 0;
                int x_y1_left_innerborder = 0;
                int x_y_left_innerborder = 0;
                int x_y_left_outerborder = 0;
                int xm1_y_top_innerborder = 0;
                int x_ym1_left_outerborder = 0;
                int xm1_y_top_outerborder = 0;
                int x1_y_left_innerborder = 0;
                int x1_y_top_innerborder = 0;
                int x1_y_top_outerborder = 0;
                int x1_ym1_left_innerborder = 0;
                int x1_ym1_left_outerborder = 0;
                int x_ym1_left_innerborder = 0;
                Py_ssize_t v;
                for (v = 0; v < n_lines; v++) {
                    const int v_x = all_x[v];
                    const int v_y = all_y[v];
                    const int is_outerborder = strcmp(all_s[v], "outerborder") == 0;
                    const int is_innerborder = strcmp(all_s[v], "innerborder") == 0;
                    const int is_left = strcmp(all_t[v], "left") == 0;
                    if (v_x == x + 1 && v_y == y - 1 && is_outerborder && is_left)
                        x1_y1_left_outerborder = 1;
                    if (v_x == x + 1 && v_y == y && is_outerborder && is_left)
                        x1_y_left_outerborder = 1;
                    if (v_x == x && v_y == y - 1 && is_innerborder && is_left)
                        x_y1_left_innerborder = 1;
                    if (v_x == x && v_y == y && is_innerborder && is_left)
                        x_y_left_innerborder = 1;
                    if (v_x == x && v_y == y && is_outerborder && is_left)
                        x_y_left_outerborder = 1;
                    if (v_x == x - 1 && v_y == y && is_innerborder && !is_left)
                        xm1_y_top_innerborder = 1;
                    if (v_x == x - 1 && v_y == y && is_outerborder && !is_left)
                        xm1_y_top_outerborder = 1;
                    if (v_x == x && v_y == y - 1 && is_outerborder && is_left)
                        x_ym1_left_outerborder = 1;
                    if (v_x == x + 1 && v_y == y && is_innerborder && is_left)
                        x1_y_left_innerborder = 1;
                    if (v_x == x + 1 && v_y == y && is_innerborder && !is_left)
                        x1_y_top_innerborder = 1;
                    if (v_x == x + 1 && v_y == y && is_outerborder && !is_left)
                        x1_y_top_outerborder = 1;
                    if (v_x == x + 1 && v_y == y - 1 && is_innerborder && is_left)
                        x1_ym1_left_innerborder = 1;
                    if (v_x == x + 1 && v_y == y - 1 && is_outerborder && is_left)
                        x1_ym1_left_outerborder = 1;
                    if (v_x == x && v_y == y - 1 && is_innerborder && is_left)
                        x_ym1_left_innerborder = 1;
                }
                // exclude cases in which lb or rb is not needed
                if (x1_y1_left_outerborder || x1_y_left_outerborder) is_rb = 0;
                if (x_y1_left_innerborder || x_y_left_innerborder) is_lb = 0;
                
                // corners on left side
                if (xm1_y_top_innerborder && x_y_left_outerborder) is_lb = 0;
                if (xm1_y_top_outerborder && x_ym1_left_outerborder) is_lb = 0;
                
                // corners on right side
                if (x1_y_left_innerborder && x1_y_top_innerborder) is_rb = 0;
                if (x1_ym1_left_innerborder && x1_y_top_outerborder) is_rb = 0;
                
                float rx = sx_p;
                float ry = sy_q + start;
                float rdx = cell_size;
                // extend borders to make them fit in the corners
                if (l_is_border) {
                    if (x_y_left_innerborder || x_ym1_left_innerborder) {
                        rx -= line_width;
                        rdx += line_width;
                    }
                    if (x1_ym1_left_outerborder || x1_y_left_outerborder) {
                        rdx += line_width;
                    }
                }
                PyObject* r = Py_BuildValue("(fffiiii)", rx, ry, rdx, 0, bar, l_is_border, 0);
                PyList_Append(result, r);
                Py_DECREF(r);
                // lines that are sticking out (could be normal lines or borders)
                // these are marked as 'special'
                if (is_lb) {
                    int is_border = l_is_border || has_left_border_line;
                    PyObject *r1 = Py_BuildValue("(ffiiiii)"
                        , sx_p - border_width, sy_q + start, border_width, 0, 0, is_border, 1);
                    PyList_Append(result, r1);
                    Py_DECREF(r1);
                }
                if (is_rb) {
                    int is_border = l_is_border || has_right_border_line;
                    PyObject *r2 = Py_BuildValue("(ffiiiii)"
                        , sx_p + cell_size, sy_q + start, border_width, 0, 0, is_border, 1);
                    PyList_Append(result, r2);
                    Py_DECREF(r2);
                }
            }
        }
    }
    return result;
}

static PyObject*
cPalabra_compute_distances(PyObject *self, PyObject *args) {
    /* NO LONGER UPDATED:
    def compute_distance(w):
        places = 0
        for i, c in enumerate(w):
            l = cs[x, y, d][i][1]
            l_i = cs[x, y, d][i][0]
            for j, item in enumerate(a[l][l_i]):
                if item[0] == c:
                    places += j
                    break
        return places
    data = [(w, compute_distance(w)) for w in words]
    */
    PyObject *words;
    PyObject *cs;
    PyObject *counts;
    PyObject *key;
    if (!PyArg_ParseTuple(args, "OOOO", &words, &cs, &counts, &key))
        return NULL;
        
    PyObject *py_lengths[MAX_WORD_LENGTH];
    int m;
    for (m = 0; m < MAX_WORD_LENGTH; m++) {
        py_lengths[m] = PyInt_FromLong(m);
    }
    
    PyObject *result = PyList_New(0);
    Py_ssize_t w;
    for (w = 0; w < PyList_GET_SIZE(words); w++) {
        int count = 0;
        char *word = PyString_AS_STRING(PyList_GET_ITEM(words, w));
        int i;
        for (i = 0; i < strlen(word); i++) {
            char c = *(word + i);
            PyObject *cs_item = PyDict_GetItem(cs, key);
            PyObject *cs_item_i = PyList_GET_ITEM(cs_item, i);
            PyObject *py_l = PyTuple_GET_ITEM(cs_item_i, 1);
            PyObject *py_l_i = PyTuple_GET_ITEM(cs_item_i, 0);
            const int l = (int) PyInt_AS_LONG(py_l);
            const int l_i = (int) PyInt_AS_LONG(py_l_i);
            
            PyObject *a_l = PyDict_GetItem(counts, py_lengths[l]);
            PyObject *a_l_i = PyDict_GetItem(a_l, py_lengths[l_i]);
            
            int occurs = 0;
            int j;
            for (j = 0; j < PyList_GET_SIZE(a_l_i); j++) {
                PyObject *item = PyList_GET_ITEM(a_l_i, j);
                PyObject *py_c = PyTuple_GET_ITEM(item, 0);
                char *c_c = PyString_AS_STRING(py_c);
                if (c == *c_c) {
                    count += j;
                    // TODO use number of times that character occurs as well
                    occurs = 1;
                    break;
                }
            }
            // penalize score if character does not occur at all
            if (!occurs) {
                count += PyList_GET_SIZE(a_l_i);
            }
        }
        PyObject* item = Py_BuildValue("(si)", word, count);
        PyList_Append(result, item);
        Py_DECREF(item);
    }
    for (m = 0; m < MAX_WORD_LENGTH; m++) {
        Py_DECREF(py_lengths[m]);
    }
    return result;
}

static PyObject*
cPalabra_compute_counts(PyObject *self, PyObject *args) {
    /*
    a = {}
    for l in words:
        a[l] = {}
        for i in xrange(l):
            a[l][i] = {}
        for w in words[l]:
            for i, c in enumerate(w):
                if c not in a[l][i]:
                    a[l][i][c] = 1
                else:
                    a[l][i][c] += 1
    */
    PyObject *words;
    if (!PyArg_ParseTuple(args, "O", &words))
        return NULL;
    PyObject *result = PyDict_New();
    int l;
    for (l = 0; l < MAX_WORD_LENGTH; l++) {
        PyObject *key = PyInt_FromLong(l);
        PyObject *a_l = PyDict_New();
        PyDict_SetItem(result, key, a_l);
        int m;
        for (m = 0; m < MAX_WORD_LENGTH; m++) {
            PyObject *key2 = PyInt_FromLong(m);
            PyObject *a_l_i = PyDict_New();
            PyDict_SetItem(a_l, key2, a_l_i);
            Py_DECREF(key2);
            Py_DECREF(a_l_i);
        }
        char *a_chars[l];
        int *a_counts[l];
        for (m = 0; m < l; m++) {
            a_chars[m] = malloc(sizeof(char) * MAX_ALPHABET_SIZE);
            a_counts[m] = malloc(sizeof(int) * MAX_ALPHABET_SIZE);
            int k;
            for (k = 0; k < MAX_ALPHABET_SIZE; k++) {
                a_chars[m][k] = -1;
                a_counts[m][k] = 0;
            }
        }
        PyObject *l_words = PyDict_GetItem(words, key);
        Py_ssize_t w;
        for (w = 0; w < PyList_Size(l_words); w++) {
            PyObject* item = PyList_GET_ITEM(l_words, w);
            PyObject* word_str;
            const int word_score;
            if (!PyArg_ParseTuple(item, "Oi", &word_str, &word_score))
                return NULL;
            char *word = PyString_AsString(word_str);
            int i;
            for (i = 0; i < strlen(word); i++) {
                char c = *(word + i);
                int j;
                for (j = 0; j < MAX_ALPHABET_SIZE; j++) {
                    if (a_chars[i][j] == -1) {
                        a_chars[i][j] = c;
                        a_counts[i][j] = 1;
                        break;
                    } else if (a_chars[i][j] == c) {
                        a_counts[i][j] += 1;
                        break;
                    }
                }
            }
        }
        for (m = 0; m < l; m++) {
            PyObject *key_m = PyInt_FromLong(m);
            PyObject *a_l_i = PyDict_GetItem(a_l, key_m);
            int k;
            for (k = 0; k < MAX_ALPHABET_SIZE; k++) {
                if (a_chars[m][k] == -1) break;
                char str[2];
                str[0] = a_chars[m][k];
                str[1] = '\0';
                PyObject *py_c = PyString_FromString(str);
                PyObject *py_count = PyInt_FromLong(a_counts[m][k]);
                PyDict_SetItem(a_l_i, py_c, py_count);
                Py_DECREF(py_c);
                Py_DECREF(py_count);
            }
        }
        for (m = 0; m < l; m++) {
            free(a_chars[m]);
            free(a_counts[m]);
        }
        Py_DECREF(key);
        Py_DECREF(a_l);
    }
    return result;
}

int read_counts(char *counts_c, int *counts_i, PyObject *counts) {
    Py_ssize_t n_counts = PyList_Size(counts);
    int i;
    for (i = 0; i < n_counts; i++) {
        PyObject *c_item = PyList_GetItem(counts, i);
        char *c_c;
        const int c_i;
        if (!PyArg_ParseTuple(c_item, "si", &c_c, &c_i))
            return 0;
        counts_c[i] = c_c[0];
        counts_i[i] = c_i;
    }
    return 1;
}

static PyObject*
cPalabra_get_contained_words(PyObject *self, PyObject *args) {
    const int index;
    const int length;
    PyObject *counts;
    const int counts_length;
    if (!PyArg_ParseTuple(args, "iiOi", &index, &length, &counts, &counts_length))
        return NULL;
    char counts_c[counts_length];
    int counts_i[counts_length];
    if (!read_counts(counts_c, counts_i, counts))
        return NULL;
    
    char cons_str[length + 1];
    int i;
    for (i = 0; i < length; i++) {
        cons_str[i] = '.';
    }
    cons_str[length] = '\0';
    PyObject *result = PyList_New(0);
    PyObject *mwords = PyList_New(0);
    mwords = find_matches(mwords, trees[index][length], cons_str);
    Py_ssize_t m;
    for (m = 0; m < PyList_Size(mwords); m++) {
        char *word = PyString_AS_STRING(PyList_GET_ITEM(mwords, m));
        int ok = 0;
        for (i = 0; i < counts_length; i++) {
            int count = 0;
            int j;
            for (j = 0; j < strlen(word); j++) {
                if (word[j] == counts_c[i]) count++;
            }
            if (count >= counts_i[i]) {
                ok++;
            }
        }
        if (ok == counts_length) {
            PyObject *py_word = PyString_FromString(word);
            PyList_Append(result, py_word);
            Py_DECREF(py_word);
        }
    }
    return result;
}

static PyObject*
cPalabra_verify_contained_words(PyObject *self, PyObject *args) {
    const int index;
    PyObject *pairs;
    if (!PyArg_ParseTuple(args, "iO", &index, &pairs))
        return NULL;
    int test = 0;    
    PyObject *result = PyList_New(0);
    Py_ssize_t p;
    for (p = 0; p < PyList_Size(pairs); p++) {
        PyObject *pair = PyList_GET_ITEM(pairs, p);
        PyObject *w1;
        PyObject *w2;
        if (!PyArg_ParseTuple(pair, "OO", &w1, &w2))
            return NULL;
        char *w1_word = PyString_AsString(w1);
        char *w2_word = PyString_AsString(w2);
        
        test++;
        PyObject *res = find_matches_i(index, w2_word);
        Py_ssize_t mm;
        for (mm = 0; mm < PyList_Size(res); mm++) {
            char *mm_word = PyString_AS_STRING(PyList_GET_ITEM(res, mm));
            PyObject* item = Py_BuildValue("(ss)", w1_word, mm_word);
            PyList_Append(result, item);
            Py_DECREF(item);
        }
        if (test == 1000) break;
    }
    printf("TEST %i\n", test);
    return result;
}

static PyObject*
cPalabra_update_score(PyObject *self, PyObject *args) {
    PyObject *word;
    const int word_length;
    const int score;
    const int wlist_index;
    if (!PyArg_ParseTuple(args, "Oiii", &word, &word_length, &score, &wlist_index))
        return NULL;
    update_score(trees[wlist_index][word_length], PyString_AsString(word), score);
    return Py_None;
}

static PyMethodDef methods[] = {
    {"search", cPalabra_search, METH_VARARGS, "search"},
    {"preprocess", cPalabra_preprocess, METH_VARARGS, "preprocess"},
    {"preprocess_all", cPalabra_preprocess_all, METH_VARARGS, "preprocess_all"},
    {"postprocess", cPalabra_postprocess, METH_VARARGS, "postprocess"},
    {"is_available",  cPalabra_is_available, METH_VARARGS, "is_available"},
    {"assign_numbers", cPalabra_assign_numbers, METH_VARARGS, "assign_numbers"},
    {"fill", cPalabra_fill, METH_VARARGS, "fill"},
    {"compute_lines",  cPalabra_compute_lines, METH_VARARGS, "compute_lines"},
    {"compute_render_lines", cPalabra_compute_render_lines, METH_VARARGS, "compute_render_lines"},
    {"compute_distances", cPalabra_compute_distances, METH_VARARGS, "compute_distances"},
    {"compute_counts", cPalabra_compute_counts, METH_VARARGS, "compute_counts"},
    {"get_contained_words", cPalabra_get_contained_words, METH_VARARGS, "get_contained_words"},
    {"verify_contained_words", cPalabra_verify_contained_words, METH_VARARGS, "verify_contained_words"},
    {"update_score", cPalabra_update_score, METH_VARARGS, "update_score"},
    {"insert_word", cPalabra_insert_word, METH_VARARGS, "insert_word"},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initcPalabra(void)
{
    (void) Py_InitModule("cPalabra", methods);
}
