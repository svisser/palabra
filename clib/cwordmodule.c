#include <Python.h>

static int
cWord_calc_has_matches(PyObject *words, const int length, PyObject *constraints) {
    Py_ssize_t numCs = PyList_GET_SIZE(constraints);
    if (numCs == 0) {
        Py_ssize_t w;
        Py_ssize_t size;
        for (w = 0; w < PyList_Size(words); w++) {
            PyObject *item = PyList_GetItem(words, w);
            size = PyString_Size(item);
            if (length == size)
                return 1;
        }
    } else {
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
    
    Py_ssize_t total = 0;
    PyObject *result = PyList_New(0);

    Py_ssize_t size;
    Py_ssize_t w;
    for (w = 0; w < PyList_Size(words); w++) {
        PyObject *item = PyList_GetItem(words, w);
        size = PyString_Size(item);
        if (length == size) {
            char *word = PyString_AsString(item);
            //printf("%s", word);
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
                //PyObject* rword;
                //rword = Py_BuildValue("s", word);
                int has_intersecting = 1;
                if (more_constraints != Py_None) {
                    Py_ssize_t m;
                    for (m = 0; m < PyList_Size(more_constraints); m++) {
                        PyObject* cons = PyList_GetItem(more_constraints, m);
                        
                        const int cons_i;
                        const int cons_l;
                        PyObject *cons_cs;
                        
                        if (!PyArg_ParseTuple(cons, "iiO", &cons_i, &cons_l, &cons_cs))
                            return NULL;
                            
                        PyObject *cons_cs_e = PyList_New(PyList_Size(cons_cs) + 1);
                        Py_ssize_t e;
                        for (e = 0; e < PyList_Size(cons_cs); e++) {
                            PyList_SetItem(cons_cs_e, e, PyList_GetItem(cons_cs, e));
                        }
                        PyObject* tuple;
                        char *it_word = PyString_AsString(item);
                        it_word += m;
                        char *cons_c = it_word;
                        tuple = Py_BuildValue("(is)", cons_i, cons_c);
                        PyList_SetItem(cons_cs_e, e, tuple);
                        
                        int has_matches = cWord_calc_has_matches(words, cons_l, cons_cs_e);
                        if (has_matches == 2)
                            return NULL;
                        if (has_matches == 0) {
                            has_intersecting = 0;
                            break;
                        }
                    }
                }
                
                PyObject* res_tuple;
                res_tuple = Py_BuildValue("(si)",  word, has_intersecting);
                
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
