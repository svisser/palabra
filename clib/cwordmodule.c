#include <Python.h>

static int
cWord_calc_has_matches(PyObject *words, const int length, PyObject *constraints) {
    static int calls = 0;
    calls++;
    //printf("%i\n", calls);
    const int MAX_WORD_LENGTH = 64;
    char cs[MAX_WORD_LENGTH];
    int k;
    for (k = 0; k < MAX_WORD_LENGTH; k++) {
        cs[k] = ' ';
    }
    
    Py_ssize_t i;
    for (i = 0; i < PyList_GET_SIZE(constraints); i++) {
        int j;
        const char *c;
        PyObject *item = PyList_GetItem(constraints, i);
        if (!PyArg_ParseTuple(item, "is", &j, &c))
            return 2;
        cs[j] = *c;
    }
    
    Py_ssize_t w;
    Py_ssize_t size;
    for (w = 0; w < PyList_Size(words); w++) {
        PyObject *item = PyList_GetItem(words, w);
        size = PyString_Size(item);
        if (length == size) {
            char *word = PyString_AsString(item);
            int check = 1;
            int i = 0;                
            while (*word != '\0') {
                if (cs[i] != ' ' && *word != cs[i]) {
                    check = 0;
                    break;
                }
                word++;
                i++;
            }
            if (check == 1)
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
    /*
    intersect_failure = False
        cache = {}
        if more_constraints:
            for j, (i, l, cs) in enumerate(more_constraints):
                cache[j] = [w for w, b_i in self.search(l, cs)]
                if not cache[j]:
                    intersect_failure = True
                    break
                
        cache2 = {}
        for word in self.words:
            if len(word) != length:
                continue
            ok = True
            for i, c in constraints:
                if not word[i] == c:
                    ok = False
                    break
            if not ok:
                continue
            intersecting = True
            if intersect_failure:
                intersecting = False
            if more_constraints and not intersect_failure:
                for j, (i, l, cs) in enumerate(more_constraints):
                    unique = (j, i, word[j])
                    if unique not in cache2:
                        cache2[unique] = self.has_matches(l, [(i, word[j])], cache[j])
                    if not cache2[unique]:
                        intersecting = False
                        break
            yield word, intersecting
            */
    const int MAX_WORD_LENGTH = 64;
    char cs[MAX_WORD_LENGTH];
    int k;
    for (k = 0; k < MAX_WORD_LENGTH; k++) {
        cs[k] = ' ';
    }
    
    Py_ssize_t i;
    for (i = 0; i < PyList_GET_SIZE(constraints); i++) {
        int j;
        const char *c;
        PyObject *item = PyList_GET_ITEM(constraints, i);
        if (!PyArg_ParseTuple(item, "is", &j, &c))
            return NULL;
        cs[j] = *c;
    }
    
    Py_ssize_t total = more_constraints != Py_None ? PyList_Size(more_constraints) : 0;
    PyObject *result = PyList_New(0);
    
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
        for (m = 0; m < total; m++) {
            printf("%i %i\n", (int) m, equalities[m]);
        }
        for (m = 0; m < total; m++) {
            if (equalities[m] >= 0) {
                precons_words[m] = precons_words[equalities[m]];
                continue;
            }
        
            precons_words[m] = PyList_New(0);
            
            const int MAX_WORD_LENGTH = 64;
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
        
            Py_ssize_t size;
            Py_ssize_t w;
            printf("building list for %i\n", (int) m);
            for (w = 0; w < PyList_Size(words); w++) {
                PyObject *item = PyList_GetItem(words, w);
                size = PyString_Size(item);
                if (precons_l[m] == size) {
                    char *word = PyString_AsString(item);
                    char *it_word = PyString_AsString(item);
                    int check = 1;
                    int i = 0;                
                    while (*it_word != '\0') {
                        if (csm[i] != ' ' && *it_word != csm[i]) {
                            check = 0;
                            break;
                        }
                        it_word++;
                        i++;
                    }
                    if (check == 1) {
                        //printf("appending (%i) %s\n", (int) m, word);
                        PyList_Append(precons_words[m], item);
                    }
                }
            }
        }
        for (m = 0; m < total; m++) {
            printf("%i %i\n", (int) m, (int) PyList_Size(precons_words[m]));
        }
    }
    
    PyObject* cache = PyDict_New();

    Py_ssize_t size;
    Py_ssize_t w;
    for (w = 0; w < PyList_Size(words); w++) {
        PyObject *item = PyList_GetItem(words, w);
        size = PyString_Size(item);
        if (length == size) {
            char *word = PyString_AsString(item);
            char *it_word = PyString_AsString(item);
            int check = 1;
            int i = 0;                
            while (*it_word != '\0') {
                if (cs[i] != ' ' && *it_word != cs[i]) {
                    check = 0;
                    break;
                }
                it_word++;
                i++;
            }
            if (check == 1) {
                int has_intersecting = 1;
                if (more_constraints != Py_None) {
                    Py_ssize_t m;
                    for (m = 0; m < PyList_Size(more_constraints); m++) {
                        /*unique = (j, i, word[j])
                        if unique not in cache2:
                            cache2[unique] = self.has_matches(l, [(i, word[j])], cache[j])
                        if not cache2[unique]:
                            intersecting = False
                            break*/
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
                            if (has_matches == 0) {
                                printf("no matches for (%i %i %s) in %i words\n", (int) m, (int) precons_i[m], cons_cc, (int) PyList_Size(precons_words[m]));
                            }
                            
                            //if (has_matches == 0) {
                            //    has_intersecting = 0;
                            //    break;
                            //}
                            
                            PyDict_SetItem(cache, key, PyInt_FromLong(has_matches));
                        } else {
                            //printf("cache hit %i %i %c\n", (int) m, (int) precons_i[m], *cons_c);
                        }
                        PyObject* value;
                        value = PyDict_GetItem(cache, key);
                        if (!PyInt_AsLong(value)) {
                            has_intersecting = 0;
                            break;
                        }
                        
                        

                        
                        
                        //if (0){ //has_matches == 0) {
                        //    has_intersecting = 0;
                        //   break;
                        //}
                    }
                }
                
                PyObject* res_tuple;
                res_tuple = Py_BuildValue("(sO)",  word, PyBool_FromLong(has_intersecting));
                
                PyList_Append(result, res_tuple);
                /*
                if more_constraints is not None:
                        filled_constraints = [(l, cs + [(i, word[j])]) for j, (i, l, cs) in enumerate(more_constraints)]
                        
                        for args in filled_constraints:
                            if not self.has_matches(*args):
                                yield word, False
                                break
                        else:
                            yield word, True
                    else:
                        yield word, True
                */
            }
        }
    }
    printf("cache size %i\n", (int) PyDict_Size(cache));
    PyObject* keys = PyDict_Keys(cache);
    Py_ssize_t kv;
    for (kv = 0; kv < PyList_Size(keys); kv++) {
        PyObject* key = PyList_GetItem(keys, kv);
        //key = Py_BuildValue("(iis)", m, precons_i[m], cons_c);
        const int kv_i;
        const int kv_l;
        const char* kv_c;
        if (!PyArg_ParseTuple(key, "iis", &kv_i, &kv_l, &kv_c))
            return NULL;
        
        //PyObject* value = PyDict_GetItem(keys, key);
        //printf("(%i, %i, %s) -\n", kv_i, kv_l, kv_c); //, PyString_AsString(value));
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
