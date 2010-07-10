
#include <Python.h>
#include "cpalabra.h"

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
