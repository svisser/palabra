#include <Python.h>

#define MAX_WORD_LENGTH 64

#define DEBUG 0

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

int check_constraints(PyObject* string, char *cs) {
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

static PyObject *
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

// TODO refactor

static PyObject *
cWord_search(PyObject *self, PyObject *args) {
    PyObject *words;
    const int length;
    PyObject *constraints;
    PyObject *more_constraints;
    if (!PyArg_ParseTuple(args, "OiOO", &words, &length, &constraints, &more_constraints))
        return NULL;
    if (!PyList_Check(words)) {
        PyErr_SetString(PyExc_TypeError, "cWord.search expects a list as first argument.");
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
    
    int intersecting_zero_slot = 0;
    int precons_i[total];
    int precons_l[total];
    PyObject *precons_cs[total];
    PyObject *precons_words[total];
    if (more_constraints != Py_None) {
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
                if (equal == 1) {
                    equalities[mm] = m;
                }
            }
        }
        if (DEBUG) {
            printf("equalities");
            for (m = 0; m < total; m++) {
                printf("%i %i\n", (int) m, equalities[m]);
            }
        }
        for (m = 0; m < total; m++) {
            if (equalities[m] >= 0) {
                precons_words[m] = precons_words[equalities[m]];
                continue;
            }
        
            precons_words[m] = PyList_New(0);
            
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
                if (!PyArg_ParseTuple(item, "is", &j, &c))
                    return NULL;
                csm[j] = *c;
            }
        
            if (DEBUG) {
                printf("building list for %i\n", (int) m);
            }
            Py_ssize_t w;
            for (w = 0; w < PyList_Size(words); w++) {
                PyObject *word = PyList_GetItem(words, w);
                Py_ssize_t size = PyString_Size(word);
                if (precons_l[m] == size && check_constraints(word, csm)) {
                    PyList_Append(precons_words[m], word);
                }
            }
            if (DEBUG) {
                printf("list size %i\n", (int) PyList_Size(precons_words[m]));
            }
            if (PyList_Size(precons_words[m]) == 0) {
                if (DEBUG) {
                    printf("no words\n");
                }
                intersecting_zero_slot = 1;
                break;
            }
        }
        /*for (m = 0; m < total; m++) {
            if (precons_words[m] != NULL) {
                printf("%i %i\n", (int) m, (int) PyList_Size(precons_words[m]));
            }
        }*/
    }
    
    char cs[MAX_WORD_LENGTH];
    if (process_constraints(constraints, cs) == 1)
        return NULL;
    
    PyObject* cache = PyDict_New();

    Py_ssize_t w;
    for (w = 0; w < PyList_Size(words); w++) {
        PyObject *item = PyList_GetItem(words, w);
        Py_ssize_t size = PyString_Size(item);
        if (length == size && check_constraints(item, cs)) {
            char *word = PyString_AsString(item);
            int has_intersecting = 1;
            if (intersecting_zero_slot) {
                has_intersecting = 0;
            }
            if (more_constraints != Py_None && !intersecting_zero_slot) {
                Py_ssize_t m;
                for (m = 0; m < PyList_Size(more_constraints); m++) {
                    char *it_word = PyString_AsString(item);
                    it_word += m;
                    char *cons_c = it_word;
                    
                    char cons_cc[2];
                    strncpy(cons_cc, cons_c, 1);
                    cons_cc[1] = '\0';
                    
                    PyObject* key;
                    key = Py_BuildValue("(iis)", m, precons_i[m], cons_cc);
                    if (!PyDict_Contains(cache, key)) {
                        PyObject* tuple;
                        tuple = Py_BuildValue("(is)", precons_i[m], cons_cc);
                        PyList_SetItem(precons_cs[m], PyList_Size(precons_cs[m]) - 1, tuple);
                        int has_matches = cWord_calc_has_matches(precons_words[m], precons_l[m], precons_cs[m]);
                        if (has_matches == 2)
                            return NULL;
                        if (has_matches == 0 && DEBUG) {
                            printf("no matches for (%i %i %s) in %i words\n", (int) m, (int) precons_i[m], cons_cc, (int) PyList_Size(precons_words[m]));
                        }
                        PyDict_SetItem(cache, key, PyInt_FromLong(has_matches));
                    }
                    PyObject* value;
                    value = PyDict_GetItem(cache, key);
                    if (!PyInt_AsLong(value)) {
                        has_intersecting = 0;
                        break;
                    }
                }
            }
            PyObject* res_tuple;
            res_tuple = Py_BuildValue("(sO)",  word, PyBool_FromLong(has_intersecting));
            PyList_Append(result, res_tuple);
        }
    }
    if (DEBUG) {
        printf("cache size %i\n", (int) PyDict_Size(cache));
    }
    return result;
}

static PyMethodDef methods[] = {
    {"has_matches",  cWord_has_matches, METH_VARARGS, "has_matches"},
    {"search", cWord_search, METH_VARARGS, "search"},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initcWord(void)
{
    (void) Py_InitModule("cWord", methods);
}
