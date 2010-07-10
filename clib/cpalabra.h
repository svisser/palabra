#ifndef CPALABRA
#define CPALABRA

#define CONSTRAINT_EMPTY ' '

#define MAX_WORD_LENGTH 64

//int debug_checked = 0;

extern int process_constraints(PyObject* constraints, char *cs);
extern int check_constraints(char *word, char *cs);

#endif
