
#include <Python.h>
#include "cpalabra.h"

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

char* find_candidate(PyObject *words, int length, char *cs, Py_ssize_t offset) {
    Py_ssize_t count = PyList_Size(words);
    Py_ssize_t w;
    Py_ssize_t m_count = 0;
    for (w = 0; w < count; w++) {
        char *word = PyString_AsString(PyList_GetItem(words, w));
        if (check_constraints(word, cs)) {
            if (m_count == offset) {
                return word;
            }
            m_count++;
        }
    }
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
