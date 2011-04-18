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

typedef struct tnode *Tptr;
typedef struct tnode {
    char splitchar;
    char *word;
    Tptr lokid, eqkid, hikid;
} Tnode;

typedef struct sresult *Sptr;
typedef struct sresult {
    int n_matches;
    char *chars;
} SearchResult;

typedef struct sparams *SPPtr;
typedef struct sparams {
    int length;
    int offset;
} SearchParams;

Tptr trees[MAX_WORD_LENGTH];

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

// TODO return C object
PyObject* find_matches(PyObject *list, Tptr p, char *s)
{
    if (!p) return list;
    if (*s == '.' || *s < p->splitchar)
        find_matches(list, p->lokid, s);
    if (*s == '.' || *s == p->splitchar)
        if (p->splitchar && *s)
            find_matches(list, p->eqkid, s + 1);
    if (*s == 0 && p->splitchar == 0) {
        PyList_Append(list, PyString_FromString(p->word));
    }
    if (*s == '.' || *s > p->splitchar)
        find_matches(list, p->hikid, s);
    return list;
}

int analyze(SPPtr params, Sptr result, Tptr p, char *s, char *cs)
{
    if (!p) return 0;
    int n = 0;
    if (*s == '.' || *s < p->splitchar)
        n += analyze(params, result, p->lokid, s, cs);
    if (*s == '.' || *s == p->splitchar)
        if (p->splitchar && *s)
            n += analyze(params, result, p->eqkid, s + 1, cs);
    if (*s == 0 && p->splitchar == 0) {
        n += 1;
        char intersect_char = *(cs + params->offset);
        if (intersect_char == '.') {
            char c = *(p->word + params->offset);
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
        n += analyze(params, result, p->hikid, s, cs);
    result->n_matches = n;
    return n;
}

static PyObject*
cWord_search(PyObject *self, PyObject *args) {
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
    int intersections[length];
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
                SPPtr params;
                params = (SPPtr) PyMem_Malloc(sizeof(SearchParams));
                if (!params)
                    return PyErr_NoMemory();
                params->length = length;
                params->offset = offsets[t];

                Sptr result;
                result = (Sptr) PyMem_Malloc(sizeof(SearchResult));
                if (!result) {
                    PyMem_Free(params);
                    return PyErr_NoMemory();
                }
                result->chars = PyMem_Malloc(MAX_ALPHABET_SIZE * sizeof(char));
                if (!result->chars) {
                    PyMem_Free(result);
                    PyMem_Free(params);
                    return PyErr_NoMemory();
                }
                int c;
                for (c = 0; c < MAX_ALPHABET_SIZE; c++) {
                    result->chars[c] = ' ';
                }
                if (!trees[strlen(cs[t])]) {
                    intersections[t] = 0;
                    results[t] = NULL;
                } else {
                    intersections[t] = analyze(params, result, trees[strlen(cs[t])], cs[t], cs[t]);
                    results[t] = result;
                }
                PyMem_Free(params);
            } else {
                skipped[t] = 1;
                intersections[t] = intersections[skip];
                results[t] = results[skip];
            }
        }
    }
    
    Py_ssize_t m;
    PyObject *result = PyList_New(0);
    for (m = 0; m < PyList_Size(mwords); m++) {
        char *word = PyString_AS_STRING(PyList_GET_ITEM(mwords, m));
        int valid = 1;
        if (more_constraints != Py_None) {
            int zero_slot = 0;
            int n_chars = 0;
            int c;
            for (c = 0; c < length; c++) {
                zero_slot = 0 == intersections[c];
                if (zero_slot) {
                    break;
                }
                if (strchr(cs[c], '.') == NULL) {
                    n_chars += 1;
                    continue;
                }
                int m;
                for (m = 0; m < MAX_ALPHABET_SIZE; m++) {
                    if (results[c]->chars[m] == ' ') break;
                    if (results[c]->chars[m] == *(word + c)) {
                        n_chars += 1;
                        break;
                    }
                }
            }
            valid = !zero_slot && (n_chars == length);
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
    {"preprocess", cWord_preprocess, METH_VARARGS, "preprocess"},
    {"postprocess", cWord_postprocess, METH_VARARGS, "postprocess"},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initcWord(void)
{
    (void) Py_InitModule("cWord", methods);
}
