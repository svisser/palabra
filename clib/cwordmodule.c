#include <Python.h>

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
    
    Py_ssize_t numCs = PyList_GET_SIZE(constraints);
    if (numCs == 0) {
        Py_ssize_t w;
        Py_ssize_t size;
        for (w = 0; w < PyList_Size(words); w++) {
            PyObject *item = PyList_GetItem(words, w);
            size = PyString_Size(item);
            if (length == size)
                Py_RETURN_TRUE;
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
                return NULL;
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
                    Py_RETURN_TRUE;
            }
        }
    }
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
            if (check == 1) {
                PyObject* new;
                new = Py_BuildValue("s", word);
                PyList_SetItem(result, total, new);
                total++;
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
