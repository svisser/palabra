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

#define MAX_WORD_LENGTH 64

// TODO
#define MAX_ALPHABET_SIZE 50

#define DEBUG 0

int debug_checked = 0;

// return 1 in case of error, 0 otherwise
int process_constraints(PyObject* constraints, char *cs) {
    int k;
    for (k = 0; k < MAX_WORD_LENGTH; k++) {
        cs[k] = ' ';
    }
    Py_ssize_t i;
    for (i = 0; i < PyList_Size(constraints); i++) {
        int j;
        const char *c;
        PyObject *item = PyList_GetItem(constraints, i);
        if (!PyArg_ParseTuple(item, "is", &j, &c))
            return 1;
        cs[j] = *c;
    }
    return 0;
}

// return 0 if constraints don't matches, 1 if they do
inline int check_constraints(char *word, char *cs) {
    debug_checked++;
    int i = 0;                
    while (*word != '\0') {
        if (cs[i] != ' ' && *word != cs[i]) {
            return 0;
        }
        word++;
        i++;
    }
    return 1;
}

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

    Py_ssize_t total = more_constraints != Py_None ? PyList_Size(more_constraints) : 0;
    PyObject *result = PyList_New(0);
    
    // process more_constraints
    int **arr = NULL;
    int **n_matches = NULL;
    int skip[total];
    int equalities[total];
    int intersecting_zero_slot = 0;
    int precons_i[total];
    int precons_l[total];
    PyObject *precons_cs[total];
    if (more_constraints != Py_None) {
        // initialize
        Py_ssize_t m;
        for (m = 0; m < total; m++) {
            equalities[m] = -1;
            skip[m] = 0;
        }
        // read more_constraints
        for (m = 0; m < total; m++) {
            const int cons_i;
            const int cons_l;
            PyObject *cons_cs;
            PyObject* cons = PyList_GetItem(more_constraints, m);
            if (!PyArg_ParseTuple(cons, "iiO", &cons_i, &cons_l, &cons_cs))
                return NULL;
            if (!PyList_Check(cons_cs)) {
                PyErr_SetString(PyExc_TypeError, "cWord.search expects a list as third part of intersecting constraints: (i, l, cs).");
                return NULL;
            }
            precons_i[m] = cons_i;
            precons_l[m] = cons_l;
            
            // TODO copy function?
            Py_ssize_t len_cons_cs = PyList_Size(cons_cs);
            PyObject *cons_cs_e = PyList_New(len_cons_cs);
            Py_ssize_t e;
            for (e = 0; e < len_cons_cs; e++) {
                PyList_SetItem(cons_cs_e, e, PyList_GetItem(cons_cs, e));
            }
            precons_cs[m] = cons_cs_e;
        }
        // deterine which of them are exactly equal
        // equalities contains per slot the value -1 for a unique slot
        // or an integer that refers to an earlier slot that is equal to it
        for (m = 1; m < total; m++) {
            Py_ssize_t mm;
            for (mm = m - 1; mm >= 0; mm--) {
                if (precons_i[m] != precons_i[mm]) {
                    continue;
                }
                if (precons_l[m] != precons_l[mm]) {
                    continue;
                }
                const Py_ssize_t len_m = PyList_Size(precons_cs[m]);
                const Py_ssize_t len_mm = PyList_Size(precons_cs[mm]);
                if (len_m != len_mm) {
                    continue;
                }
                int equal = 1;
                Py_ssize_t l;
                for (l = 0; l < len_m; l++) {
                    const int j_m;
                    const char *c_m;
                    PyObject *tuple_m = PyList_GetItem(precons_cs[m], l);
                    if (!PyArg_ParseTuple(tuple_m, "is", &j_m, &c_m))
                        return NULL;
                    const int j_mm;
                    const char *c_mm;
                    PyObject *tuple_mm = PyList_GetItem(precons_cs[mm], l);
                    if (!PyArg_ParseTuple(tuple_mm, "is", &j_mm, &c_mm))
                        return NULL;
                    if (j_m != j_mm || *c_m != *c_mm) {
                        equal = 0;
                        break;
                    }
                }
                // equal? then point the slot at m to the one at mm
                if (equal == 1) {
                    equalities[m] = mm;
                }
            }
        }
        if (DEBUG) {
            printf("equalities\n");
            for (m = 0; m < total; m++) {
                printf("%i %i\n", (int) m, equalities[m]);
            }
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
            // TODO FIXME XXX turn back on, this is only off for median calculations
            /*if (equalities[m] != -1) {
                continue;
            }*/
            
            const int total_m = PyList_Size(precons_cs[m]);
            // if all characters are already filled in for this intersecting entry
            if (total_m == precons_l[m]) {
                if (DEBUG) {
                    printf("entry at %i will be skipped because it's filled in\n", (int) m);
                }
                skip[m] = 1;
                continue;
            }
            
            // convert the python list into an array
            char csm[MAX_WORD_LENGTH];
            int k;
            for (k = 0; k < MAX_WORD_LENGTH; k++) {
                csm[k] = ' ';
            }
            Py_ssize_t i;
            for (i = 0; i < total_m; i++) {
                const int j;
                const char *c;
                PyObject *item = PyList_GetItem(precons_cs[m], i);
                if (!PyArg_ParseTuple(item, "is", &j, &c)) {
                    free_array(arr, total);
                    free_array(n_matches, total);
                    return NULL;
                }
                csm[j] = *c;
            }
            
            // for all intersecting words of the desired length
            // and that match the intersecting constraints,
            // gather all characters that could be placed in the
            // word of the main slot for which we are searching
            Py_ssize_t w;
            PyObject* key = Py_BuildValue("i", precons_l[m]);
            PyObject* words_m = PyDict_GetItem(words, key);
            for (w = 0; w < PyList_Size(words_m); w++) {
                char *word = PyString_AsString(PyList_GetItem(words_m, w));
                if (!check_constraints(word, csm)) {
                    continue;
                }
                const int ivalue = (int) *(word + precons_i[m]);
                int j;
                for (j = 0; j < MAX_ALPHABET_SIZE; j++) {
                    if (arr[m][j] == ivalue) {
                        n_matches[m][j]++;
                        break;
                    }
                    if (arr[m][j] == 0) {
                        arr[m][j] = ivalue;
                        n_matches[m][j]++;
                        break;
                    }
                }
            }
            // if no matches were found and if the word has at least one missing character...
            if (arr[m][0] == 0 && total_m != precons_l[m]) {
                if (DEBUG) {
                    printf("intersecting_zero_slot for: %i\n", (int) m);
                }
                intersecting_zero_slot = 1;
                break;
            }
        }
        
        for (m = 0; m < total; m++) {
            int f;
            for (f = 0; f < MAX_ALPHABET_SIZE; f++) {
                if (arr[m][f] == 0)
                    break;
                if (DEBUG) {
                    printf("%i %c has n matches: %i\n", (int) m, (char) arr[m][f], n_matches[m][f]);
                }
            }
        }
        
        if (DEBUG) {
            int a, b;
            for (a = 0; a < total; a++) {
                for (b = 0; b < MAX_ALPHABET_SIZE; b++) {
                    printf("arr[%i][%i] = %i\n", a, b, arr[a][b]);
                }
            }
        }
    }
    
    // process the constraints of the main slot
    char cs[MAX_WORD_LENGTH];
    if (process_constraints(constraints, cs) == 1) {
        free_array(arr, total);
        free_array(n_matches, total);
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
        int indicator = 0;
        int has_intersecting = intersecting_zero_slot ? 0 : 1;
        if (more_constraints != Py_None && !intersecting_zero_slot) {
            Py_ssize_t m;
            int median[length];
            if (DEBUG) {
                printf("%s ", word);
            }
            for (m = 0; m < total; m++) {
                median[m] = lookup_number(arr, n_matches, m, *(word + m));
                if (DEBUG) {
                    printf("%i ", median[m]);
                }
            }
            indicator = compute_median(median, length);
            if (DEBUG) {
                printf(" - indicator: %i\n", indicator);
            }
            
            for (m = 0; m < total; m++) {
                if (skip[m]) {
                    continue;
                } 
                char cons_c[2];
                cons_c[0] = *(word + m);
                cons_c[1] = '\0';
                
                // use a cache to lookup/store earlier searches
                // the key is:
                // (index of intersecting slot in word
                // , index of intersection in intersecting word, char)
                PyObject* key = Py_BuildValue("(iis)", m, precons_i[m], cons_c);
                if (!PyDict_Contains(cache, key)) {
                    const int index = equalities[m] != -1 ? equalities[m] : (int) m;
                    const int has_matches = lookup_array(arr, index, *(word + m));
                    if (DEBUG && has_matches == 0) {
                        printf("no matches for (%i %i %s)\n", (int) m, (int) precons_i[m], cons_c);
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
        PyObject* r = Py_BuildValue("(sOi)",  word, PyBool_FromLong(has_intersecting), indicator);
        PyList_Append(result, r);
    }
    if (DEBUG) {
        printf("cache size %i\n", (int) PyDict_Size(cache));
        printf("total words checked %i\n", debug_checked);
    }
    debug_checked = 0;
    
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
    return dict;
}

static PyMethodDef methods[] = {
    {"has_matches",  cWord_has_matches, METH_VARARGS, "has_matches"},
    {"search", cWord_search, METH_VARARGS, "search"},
    {"preprocess", cWord_preprocess, METH_VARARGS, "preprocess"},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initcWord(void)
{
    (void) Py_InitModule("cWord", methods);
}
