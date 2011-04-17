
#include <Python.h>
#include "cpalabra.h"

char* find_candidate(PyObject *words, int length, char *cs, int offset) {
    PyObject* key = Py_BuildValue("i", length);
    PyObject* words_m = PyDict_GetItem(words, key);
    
    Py_ssize_t count = PyList_Size(words_m);
    char **words_array = (char**) calloc(sizeof(char**), count);
    if (!words_array)
        return NULL;
    
    Py_ssize_t w;
    for (w = 0; w < count; w++) {
        char *word = PyString_AsString(PyList_GetItem(words_m, w));
        words_array[w] = word;
    }
    int matches = 0;
    for (w = 0; w < count; w++) {
        char *word = words_array[w];
        if (check_constraints(word, cs) == 1) {
            if (matches == offset) {
                free(words_array);
                return word;
            }
            matches++;
        }
    }
    free(words_array);
    return NULL;
}

// return 1 in case of error, 0 otherwise
int process_constraints(PyObject* constraints, char *cs) {
    int k;
    for (k = 0; k < MAX_WORD_LENGTH; k++) {
        cs[k] = CONSTRAINT_EMPTY;
    }
    Py_ssize_t i;
    Py_ssize_t size = PyList_Size(constraints);
    for (i = 0; i < size; i++) {
        const int j;
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
    //debug_checked++;
    int i = 0;                
    while (*word != '\0') {
        if (cs[i] != CONSTRAINT_EMPTY && *word != cs[i]) {
            return 0;
        }
        word++;
        i++;
    }
    return 1;
}

