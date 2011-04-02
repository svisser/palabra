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

int compute_median(int *numbers, const int length) {
    // sort array
    int s0, s1;
    for (s0 = 0; s0 < length; s0++) {
        for (s1 = s0 + 1; s1 < length; s1++) {
            int v0 = numbers[s0];
            int v1 = numbers[s1];
            if (v1 < v0) {
                numbers[s0] = v1;
                numbers[s1] = v0;
            }
        }
    }
    if (length % 2 == 0) {
        return ((numbers[length / 2 - 1] + numbers[length / 2]) / 2);
    }
    return numbers[(length - 1) / 2];
}

// TODO fix hardcoded array length below

int lookup_number(int **arr, int **numbers, const int index, char c) {
    int i;
    for (i = 0; i < MAX_ALPHABET_SIZE; i++) {
        if (arr[index][i] == c) {
            return numbers[index][i];
        }
    }
    return 0;
}

int lookup_array(int **arr, const int index, char c) {
    int i;
    for (i = 0; i < MAX_ALPHABET_SIZE; i++) {
        if (arr[index][i] == 0) {
            return 0;
        }
        if (arr[index][i] == c) {
            return 1;
        }
    }
    return 0;
}

void free_array(int **arr, int total) {
    int a;
    for (a = 0; a < total; a++) {
        free(arr[a]);
        arr[a] = NULL;
    }
    free(arr);
    arr = NULL;
}

int** allocate_array(int length, int depth) {
    int **arr = malloc((int) length * sizeof(int*));
    if (!arr) {
        return NULL;
    }
    int a, b;
    for (a = 0; a < length; a++) {
        arr[a] = malloc(depth * sizeof(int));
        if (!arr[a]) {
            free_array(arr, a);
            return NULL;
        }
        for (b = 0; b < depth; b++) {
            arr[a][b] = 0;
        }
    }
    return arr;
}

// return 1 if a word exists that matches the constraints, 0 otherwise
static int
cWord_calc_has_matches(PyObject *words, const int length, PyObject *constraints) {
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
cWord_has_matches(PyObject *self, PyObject *args)
{
    PyObject *words;
    const int length;
    PyObject *constraints;
    if (!PyArg_ParseTuple(args, "OiO", &words, &length, &constraints))
        return NULL;
    if (!PyList_Check(words)) {
        PyErr_SetString(PyExc_TypeError, "cWord.has_matches expects a list as first argument.");
        return NULL;
    }
    if (!PyList_Check(constraints)) {
        PyErr_SetString(PyExc_TypeError, "cWord.has_matches expects a list as third argument");
        return NULL;
    }
    int has_matches = cWord_calc_has_matches(words, length, constraints);
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


#include <stdio.h>
#include <stdlib.h>

typedef struct tnode *Tptr;
typedef struct tnode {
    char splitchar;
    char *word;
    Tptr lokid, eqkid, hikid;
} Tnode;

Tptr trees[MAX_WORD_LENGTH];

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

// TODO release memory afterwards
Tptr insert1(Tptr p, char *s, char *word)
{
    if (p == 0) {
        p = (Tptr) malloc(sizeof(Tnode));
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

void search2(Tptr p, char *s)
{
    if (!p) return;
    if (*s == '.' || *s < p->splitchar)
        search2(p->lokid, s);
    if (*s == '.' || *s == p->splitchar)
        if (p->splitchar && *s)
            search2(p->eqkid, s + 1);
    if (*s == 0 && p->splitchar == 0)
        printf("%s\n", p->word);
    if (*s == '.' || *s > p->splitchar)
        search2(p->hikid, s);
}

// TODO return C object
PyObject* search3(PyObject *list, Tptr p, char *s)
{
    if (!p) return list;
    if (*s == '.' || *s < p->splitchar)
        search3(list, p->lokid, s);
    if (*s == '.' || *s == p->splitchar)
        if (p->splitchar && *s)
            search3(list, p->eqkid, s + 1);
    if (*s == 0 && p->splitchar == 0) {
        PyList_Append(list, PyString_FromString(p->word));
    }
    if (*s == '.' || *s > p->splitchar)
        search3(list, p->hikid, s);
    return list;
}

int count_matches(Tptr p, char *s)
{
    if (!p) return 0;
    int result = 0;
    if (*s == '.' || *s < p->splitchar)
        result += count_matches(p->lokid, s);
    if (*s == '.' || *s == p->splitchar)
        if (p->splitchar && *s)
            result += count_matches(p->eqkid, s + 1);
    if (*s == 0 && p->splitchar == 0)
        result += 1;
    if (*s == '.' || *s > p->splitchar)
        result += count_matches(p->hikid, s);
    return result;
}

int main(int argc, const char* argv[])
{
    /*Tptr root;
    root = insert1(root, "simeon", "simeon");
    root = insert1(root, "simone", "simone");
    print(root, 0);
    search2(root, "s....e");*/
    return 0;
}

static PyObject*
cWord_search2(PyObject *self, PyObject *args) {
    PyObject *words;
    const int length;
    PyObject *constraints;
    PyObject *more_constraints;
    if (!PyArg_ParseTuple(args, "OiOO", &words, &length, &constraints, &more_constraints))
        return NULL;
    char *cons_str = PyString_AsString(constraints);
    
    // main word
    PyObject *mwords = PyList_New(0);
    mwords = search3(mwords, trees[strlen(cons_str)], cons_str);
    
    // each of the constraints
    int intersections[length];
    int lengths[length];
    int t;
    for (t = 0; t < length; t++) {
        int index;
        PyObject *py_cons_str2;
        PyObject* item = PyList_GetItem(more_constraints, (Py_ssize_t) t);
        if (!PyArg_ParseTuple(item, "iO", &index, &py_cons_str2))
            return NULL;
        
        char *cons_str2 = PyString_AsString(py_cons_str2);
        lengths[t] = strlen(cons_str2);
        
        int skip = 0;
        int s;
        for (s = 0; s < t; s++) {
            if (lengths[s] == lengths[t]) {
                skip = s;
                break;
            }
        }
        
        if (skip == 0) {
            intersections[t] = count_matches(trees[lengths[t]], cons_str2);
        } else {
            intersections[t] = intersections[s];
        }
    }
    
    int zero_slot = 0;
    int z;
    for (z = 0; z < length; z++) {
        if (0 == intersections[z]) {
            zero_slot = 1;
            break;
        }
    }
    
    Py_ssize_t m;
    PyObject *result = PyList_New(0);
    for (m = 0; m < PyList_Size(mwords); m++) {
        char *word = PyString_AsString(PyList_GetItem(mwords, m));
        PyObject* py_intersect = PyBool_FromLong(!zero_slot);
        PyObject* r = Py_BuildValue("(sOi)",  word, py_intersect, 0);
        PyList_Append(result, r);
    }
    return result;
}

static PyObject*
cWord_search(PyObject *self, PyObject *args) {
    PyObject *words;
    const int length;
    PyObject *constraints;
    PyObject *more_constraints;
    if (!PyArg_ParseTuple(args, "OiOO", &words, &length, &constraints, &more_constraints))
        return NULL;
    if (!PyDict_Check(words)) {
        PyErr_SetString(PyExc_TypeError, "cWord.search expects a dict as first argument.");
        return NULL;
    }
    if (!PyList_Check(constraints)) {
        PyErr_SetString(PyExc_TypeError, "cWord.search expects a list as third argument.");
        return NULL;
    }
    if (more_constraints != Py_None && !PyList_Check(more_constraints)) {
        PyErr_SetString(PyExc_TypeError, "cWord.search expects a list as fourth argument.");
        return NULL;
    }

    const int total = more_constraints != Py_None ? length : 0;
    PyObject *result = PyList_New(0);
    
    // process more_constraints
    int **arr = NULL;
    int **n_matches = NULL;
    int intersecting_zero_slot = 0;
    IntersectingSlot slots[total];
    if (more_constraints != Py_None) {
        // initialize and read more_constraints
        Py_ssize_t m;
        for (m = 0; m < total; m++) {
            slots[m].equal = -1;
            slots[m].skip = 0;
            PyObject* item = PyList_GetItem(more_constraints, m);
            if (!PyArg_ParseTuple(item, "iiO", &slots[m].index, &slots[m].length, &slots[m].cs))
                return NULL;
            if (!PyList_Check(slots[m].cs)) {
                PyErr_SetString(PyExc_TypeError, "cWord.search expects a list as third part of intersecting constraints: (i, l, cs).");
                return NULL;
            }
        }
        // deterine which of them are exactly equal
        // equalities contains per slot the value -1 for a unique slot
        // or an integer that refers to an earlier slot that is equal to it
        for (m = 1; m < total; m++) {
            Py_ssize_t mm;
            for (mm = m - 1; mm >= 0; mm--) {
                // equal? then point the slot at m to the one at mm
                int equal = is_intersecting_equal(slots[m], slots[mm]);
                if (equal == 2) return NULL;
                if (equal == 1) {
                    slots[m].equal = mm;
                }
            }
        }
        if (DEBUG) {
            printf("equalities: {");
            for (m = 0; m < total; m++) {
                if (slots[m].equal == -1) {
                    printf("new");
                } else {
                    printf("equal(%i)", slots[m].equal);
                }
                if (m < total - 1) {
                    printf(", ");
                }
            }
            printf("}\n");
        }
        
        // allocate space for the list of characters (stored as ints)
        arr = allocate_array(total, MAX_ALPHABET_SIZE);
        if (!arr)
            return NULL;
        n_matches = allocate_array(total, MAX_ALPHABET_SIZE);
        if (!n_matches) {
            free_array(arr, total);
            return NULL;
        }
        
        // gather possible characters that could be part of the
        // main slot, at each intersecting slot
        for (m = 0; m < total; m++) {
            // we encountered a slot that is equal to a previous one
            // just copy calculated values for median later on
            if (slots[m].equal != -1) {
                int j;
                for (j = 0; j < MAX_ALPHABET_SIZE; j++) {
                    arr[m][j] = arr[slots[m].equal][j];
                    n_matches[m][j] = n_matches[slots[m].equal][j];
                }
                continue;
            }
            
            const int total_m = PyList_Size(slots[m].cs);
            // if all characters are already filled in for this intersecting entry
            if (total_m == slots[m].length) {
                if (DEBUG) {
                    printf("entry at %i will be skipped because it's filled in\n", (int) m);
                }
                slots[m].skip = 1;
                continue;
            }
            
            // convert the python list into an array
            char csm[MAX_WORD_LENGTH];
            if (process_constraints(slots[m].cs, csm) == 1) {
                free_array(arr, total);
                free_array(n_matches, total);
                return NULL;
            }
            
            // for all intersecting words of the desired length
            // and that match the intersecting constraints,
            // gather all characters that could be placed in the
            // word of the main slot for which we are searching
            Py_ssize_t w;
            PyObject* key = Py_BuildValue("i", slots[m].length);
            PyObject* words_m = PyDict_GetItem(words, key);
            for (w = 0; w < PyList_Size(words_m); w++) {
                char *word = PyString_AsString(PyList_GetItem(words_m, w));
                if (!check_constraints(word, csm)) {
                    continue;
                }
                const int ivalue = (int) *(word + slots[m].index);
                int j;
                for (j = 0; j < MAX_ALPHABET_SIZE; j++) {
                    if (arr[m][j] == 0) {
                        arr[m][j] = ivalue;
                    }
                    if (arr[m][j] == ivalue) {
                        n_matches[m][j]++;
                        break;
                    }
                }
            }
            // if no matches were found and if the word has at least one missing character...
            if (arr[m][0] == 0 && total_m != slots[m].length) {
                if (DEBUG) {
                    printf("intersecting_zero_slot for: %i\n", (int) m);
                }
                intersecting_zero_slot = 1;
                break;
            }
        }
        if (DEBUG) {
            for (m = 0; m < total; m++) {
                int f;
                for (f = 0; f < MAX_ALPHABET_SIZE; f++) {
                    if (arr[m][f] == 0)
                        break;
                    printf("%i %c has n matches: %i\n", (int) m, (char) arr[m][f], n_matches[m][f]);
                }
            }
            int a, b;
            printf("arr = {");
            for (a = 0; a < total; a++) {
                printf("%i: {", a);
                for (b = 0; b < MAX_ALPHABET_SIZE; b++) {
                    if (arr[a][b] != 0) {
                        //printf("%i: %c", b, arr[a][b]);
                        printf("%c", arr[a][b]);
                        if (b < MAX_ALPHABET_SIZE - 1 && arr[a][b + 1] != 0) {
                            printf(", ");
                        }
                    }
                }
                printf("}");
                if (a < total - 1) {
                    printf(",\n");
                }
            }
            printf("}\n");
        }
    }
    
    // process the constraints of the main slot
    char cs[MAX_WORD_LENGTH];
    if (process_constraints(constraints, cs) == 1) {
        if (more_constraints != Py_None) {
            free_array(arr, total);
            free_array(n_matches, total);
        }
        return NULL;
    }

    // process words
    PyObject* cache = PyDict_New();
    PyObject* key = Py_BuildValue("i", length);
    PyObject* words_main = PyDict_GetItem(words, key);
    Py_ssize_t w;
    for (w = 0; w < PyList_Size(words_main); w++) {
        char *word = PyString_AsString(PyList_GetItem(words_main, w));
        if (!check_constraints(word, cs)) {
            continue;
        }
        int indicator = 0, indicator2 = 0;
        int has_intersecting = intersecting_zero_slot ? 0 : 1;
        if (more_constraints != Py_None && !intersecting_zero_slot) {
            Py_ssize_t m;
            int median[total];
            for (m = 0; m < total; m++) {
                median[m] = lookup_number(arr, n_matches, m, *(word + m));
            }
            indicator = compute_median(median, length);
            for (m = 0; m < total; m++) {
                if (median[m] < indicator) {
                    indicator2 += (indicator - median[m]);
                }
            }
            if (DEBUG & DEBUG_WORDS) {
                printf("%s ", word);
                for (m = 0; m < total; m++) {
                    printf("%i ", median[m]);
                }
                printf("- indicators: (%i, %i)\n", indicator, indicator2);
            }
            
            for (m = 0; m < total; m++) {
                if (slots[m].skip) {
                    continue;
                } 
                char cons_c[2];
                cons_c[0] = *(word + m);
                cons_c[1] = '\0';
                
                // use a cache to lookup/store earlier searches
                // the key is:
                // (index of intersecting slot in word
                // , index of intersection in intersecting word, char)
                PyObject* key = Py_BuildValue("(iis)", m, slots[m].index, cons_c);
                if (!PyDict_Contains(cache, key)) {
                    const int index = slots[m].equal != -1 ? slots[m].equal : (int) m;
                    const int has_matches = lookup_array(arr, index, *(word + m));
                    if (DEBUG && has_matches == 0) {
                        printf("no matches for (%i %i %s)\n", (int) m, (int) slots[m].index, cons_c);
                    }
                    PyDict_SetItem(cache, key, PyInt_FromLong(has_matches));
                }
                PyObject* value = PyDict_GetItem(cache, key);
                if (!PyInt_AsLong(value)) {
                    has_intersecting = 0;
                    break;
                }
            }
        }
        const int w_indicator = indicator + (-1 * indicator2);
        PyObject* py_intersect = PyBool_FromLong(has_intersecting);
        PyObject* r = Py_BuildValue("(sOi)",  word, py_intersect, w_indicator);
        PyList_Append(result, r);
    }
    if (DEBUG) {
        printf("cache size %i\n", (int) PyDict_Size(cache));
        //printf("total words checked %i\n", debug_checked);
    }
    //debug_checked = 0;
    
    if (more_constraints != Py_None) {
        free_array(arr, total);
        free_array(n_matches, total);
    }
    return result;
}

static PyObject*
cWord_preprocess(PyObject *self, PyObject *args) {
    PyObject *words;
    if (!PyArg_ParseTuple(args, "O", &words))
        return NULL;
    
    // create dict (keys are word lengths, each item is a list with words of that length)
    PyObject* dict = PyDict_New();
    PyObject* keys[MAX_WORD_LENGTH];
    int l;
    for (l = 0; l < MAX_WORD_LENGTH; l++) {
        keys[l] = Py_BuildValue("i", l);
        PyDict_SetItem(dict, keys[l], PyList_New(0));
    }
    Py_ssize_t w;
    for (w = 0; w < PyList_Size(words); w++) {
        PyObject* word = PyList_GetItem(words, w);
        PyObject* key = keys[(int) PyString_Size(word)];
        PyList_Append(PyDict_GetItem(dict, key), word);
    }
    
    // build ternary search trees per word length
    int m;
    for (m = 0; m < MAX_WORD_LENGTH; m++) {
        Tptr root;
        trees[m] = root;
        trees[m] = insert1(trees[m], "", "");
        
        Py_ssize_t w;
        PyObject *words = PyDict_GetItem(dict, Py_BuildValue("i", m));
        for (w = 0; w < PyList_Size(words); w++) {
            char *word = PyString_AsString(PyList_GetItem(words, w));
            trees[m] = insert1(trees[m], word, word);
        }
    }
    return dict;
}

void free_tree(Tptr p) {
    if (p->lokid != NULL) {
        free_tree(p->lokid);
        free(p->lokid);
        p->lokid = NULL;
    }
    if (p->eqkid != NULL) {
        free_tree(p->eqkid);
        free(p->eqkid);
        p->eqkid = NULL;
    }
    if (p->hikid != NULL) {
        free_tree(p->hikid);
        free(p->hikid);
        p->hikid = NULL;
    }
}

static PyObject*
cWord_postprocess(PyObject *self, PyObject *args) {
    int m;
    for (m = 0; m < MAX_WORD_LENGTH; m++) {
        free_tree(trees[m]);
        free(trees[m]);
    }
    return Py_None;
}

static PyMethodDef methods[] = {
    {"has_matches",  cWord_has_matches, METH_VARARGS, "has_matches"},
    {"search", cWord_search, METH_VARARGS, "search"},
    {"search2", cWord_search2, METH_VARARGS, "search2"},
    {"preprocess", cWord_preprocess, METH_VARARGS, "preprocess"},
    {"postprocess", cWord_postprocess, METH_VARARGS, "postprocess"},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initcWord(void)
{
    (void) Py_InitModule("cWord", methods);
}
