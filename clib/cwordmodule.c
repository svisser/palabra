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
int check_constraints(PyObject* string, char *cs) {
    debug_checked++;
    char *word = PyString_AsString(string);
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

void free_array(int **arr, int total) {
    int a;
    for (a = 0; a < total; a++) {
        free(arr[a]);
        arr[a] = NULL;
    }
    free(arr);
    arr = NULL;
}

// return 1 if a word exists that matches the constraints, 0 otherwise
static int
cWord_calc_has_matches(PyObject *words, const int length, PyObject *constraints) {
    char cs[MAX_WORD_LENGTH];
    if (process_constraints(constraints, cs) == 1)
        return 2;
    Py_ssize_t w;
    for (w = 0; w < PyList_Size(words); w++) {
        PyObject *word = PyList_GetItem(words, w);
        if (length == PyString_Size(word) && check_constraints(word, cs)) {
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
    if (more_constraints != Py_None) {
        if (!PyList_Check(more_constraints)) {
            PyErr_SetString(PyExc_TypeError, "cWord.search expects a list as fourth argument.");
            return NULL;
        }
    }

    Py_ssize_t total = more_constraints != Py_None ? PyList_Size(more_constraints) : 0;
    PyObject *result = PyList_New(0);
    
    // process more_constraints
    int **arr = NULL;
    int intersecting_zero_slot = 0;
    int precons_i[total];
    int precons_l[total];
    PyObject *precons_cs[total];
    if (more_constraints != Py_None) {
        // read more_constraints
        Py_ssize_t m;
        for (m = 0; m < total; m++) {
            PyObject* cons = PyList_GetItem(more_constraints, m);
            const int cons_i;
            const int cons_l;
            PyObject *cons_cs;
            if (!PyArg_ParseTuple(cons, "iiO", &cons_i, &cons_l, &cons_cs))
                return NULL;
            if (!PyList_Check(cons_cs)) {
                PyErr_SetString(PyExc_TypeError, "cWord.search expects a list as third part of intersecting constraints: (i, l, cs).");
                return NULL;
            }
            PyObject *cons_cs_e = PyList_New(PyList_Size(cons_cs) + 1);
            Py_ssize_t e;
            for (e = 0; e < PyList_Size(cons_cs); e++) {
                PyList_SetItem(cons_cs_e, e, PyList_GetItem(cons_cs, e));
            }
            precons_i[m] = cons_i;
            precons_l[m] = cons_l;
            precons_cs[m] = cons_cs_e;
        }
        // deterine which of them are exactly equal
        // equalities contains per slot the value -1 for a unique slot
        // or an integer that refers to an earlier slot that is equal to it
        int equalities[total];
        for (m = 0; m < total; m++) {
            equalities[m] = -1;
        }
        for (m = 0; m < total; m++) {
            Py_ssize_t mm;
            for (mm = m + 1; mm < total; mm++) {
                int equal = 0;
                if (precons_i[m] == precons_i[mm] && precons_l[m] == precons_l[mm]) {
                    Py_ssize_t ml = PyList_Size(precons_cs[m]);
                    Py_ssize_t mml = PyList_Size(precons_cs[mm]);
                    if (ml == mml) {
                        Py_ssize_t l;
                        equal = 1;
                        for (l = 0; l < ml - 1; l++) {
                            int j_m;
                            const char *c_m;
                            PyObject *tuple_m = PyList_GetItem(precons_cs[m], l);
                            if (!PyArg_ParseTuple(tuple_m, "is", &j_m, &c_m))
                                return NULL;
                            int j_mm;
                            const char *c_mm;
                            PyObject *tuple_mm = PyList_GetItem(precons_cs[mm], l);
                            if (!PyArg_ParseTuple(tuple_mm, "is", &j_mm, &c_mm))
                                return NULL;
                            if (j_m != j_mm || *c_m != *c_mm) {
                                equal = 0;
                                break;
                            }
                        }
                    }
                }
                // equal? then point the slot at mm to the one at m
                if (equal == 1) {
                    equalities[mm] = m;
                }
            }
        }
        if (DEBUG) {
            printf("equalities\n");
            for (m = 0; m < total; m++) {
                printf("%i %i\n", (int) m, equalities[m]);
            }
        }
        
        arr = malloc((int) total * sizeof(int*));
        if (!arr) {
            return NULL;
        }
        int a;
        int b;
        for (a = 0; a < total; a++) {
            arr[a] = malloc(MAX_ALPHABET_SIZE * sizeof(int));
            if (!arr[a]) {
                free_array(arr, a);
                return NULL;
            }
            for (b = 0; b < MAX_ALPHABET_SIZE; b++) {
                arr[a][b] = 0;
            }
        }
        
        for (m = 0; m < total; m++) {
            char csm[MAX_WORD_LENGTH];
            int k;
            for (k = 0; k < MAX_WORD_LENGTH; k++) {
                csm[k] = ' ';
            }
            
            Py_ssize_t i;
            for (i = 0; i < PyList_Size(precons_cs[m]) - 1; i++) {
                int j;
                const char *c;
                PyObject *item = PyList_GetItem(precons_cs[m], i);
                if (!PyArg_ParseTuple(item, "is", &j, &c)) {
                    free_array(arr, total);
                    return NULL;
                }
                csm[j] = *c;
            }
            
            PyObject* key;
            key = Py_BuildValue("i", precons_l[m]);
            
            PyObject* words_m = PyDict_GetItem(words, key);
            
            Py_ssize_t w;
            for (w = 0; w < PyList_Size(words_m); w++) {
                PyObject *word = PyList_GetItem(words_m, w);
                if (check_constraints(word, csm)) {
                    char *it_word = PyString_AsString(word);
                    it_word += precons_i[m];
                    char *cons_c = it_word;
                    
                    int j;
                    for (j = 0; j < MAX_ALPHABET_SIZE; j++) {
                        int ivalue = (int) *cons_c;
                        if (arr[m][j] == ivalue) {
                            break;
                        }
                        if (arr[m][j] == 0) {
                            arr[m][j] = ivalue;
                            break;
                        }
                    }
                }
            }
            if (arr[m][0] == 0) {
                if (DEBUG) {
                    printf("intersecting_zero_slot\n");
                }
                intersecting_zero_slot = 1;
                break;
            }
        }
        
        if (DEBUG) {
            for (a = 0; a < total; a++) {
                for (b = 0; b < MAX_ALPHABET_SIZE; b++) {
                    printf("arr[%i][%i] = %i\n", a, b, arr[a][b]);
                }
            }
        }
    }
    
    char cs[MAX_WORD_LENGTH];
    if (process_constraints(constraints, cs) == 1) {
        free_array(arr, total);
        return NULL;
    }
    
    PyObject* cache = PyDict_New();

    // process words    
    Py_ssize_t w;
    PyObject* key = Py_BuildValue("i", length);
    PyObject* words_main = PyDict_GetItem(words, key);
    for (w = 0; w < PyList_Size(words_main); w++) {
        PyObject *item = PyList_GetItem(words_main, w);
        if (check_constraints(item, cs)) {
            char *word = PyString_AsString(item);
            int has_intersecting = intersecting_zero_slot ? 0 : 1;
            if (more_constraints != Py_None && !intersecting_zero_slot) {
                Py_ssize_t m;
                for (m = 0; m < PyList_Size(more_constraints); m++) {
                    char *it_word = PyString_AsString(item);
                    it_word += m;
                    char *cons_c = it_word;
                    
                    char cons_cc[2];
                    strncpy(cons_cc, cons_c, 1);
                    cons_cc[1] = '\0';
                    
                    // use a cache to lookup/store earlier searches
                    // the key is:
                    // (index of intersecting slot in word
                    // , index of intersection in intersecting word, char)
                    PyObject* key;
                    key = Py_BuildValue("(iis)", m, precons_i[m], cons_cc);
                    if (!PyDict_Contains(cache, key)) {
                        int has_matches = 0;
                        int b;
                        for (b = 0; b < MAX_ALPHABET_SIZE; b++) {
                            if (arr[m][b] == 0) {
                                break;
                            }
                            if (arr[m][b] == ((int) *cons_c)) {
                                has_matches = 1;
                                break;
                            }
                        }
                        
                        if (has_matches == 2) {
                            free_array(arr, total);
                            return NULL;
                        }
                        if (has_matches == 0 && DEBUG) {
                            printf("no matches for (%i %i %s)\n", (int) m, (int) precons_i[m], cons_cc);
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
            PyObject* r = Py_BuildValue("(sO)",  word, PyBool_FromLong(has_intersecting));
            PyList_Append(result, r);
        }
    }
    if (DEBUG) {
        printf("cache size %i\n", (int) PyDict_Size(cache));
        printf("total words checked %i\n", debug_checked);
    }
    debug_checked = 0;
    
    if (more_constraints != Py_None) {
        free_array(arr, total);
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
