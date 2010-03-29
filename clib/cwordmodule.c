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
        PyErr_SetString(PyExc_TypeError, "has_matches expects a list as first argument.");
        return NULL;
    }
    if (!PyList_Check(constraints)) {
        PyErr_SetString(PyExc_TypeError, "has_matches expects a list as third argument");
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

static PyMethodDef methods[] = {
    {"has_matches",  cWord_has_matches, METH_VARARGS, "TODO"},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
initcWord(void)
{
    (void) Py_InitModule("cWord", methods);
}
