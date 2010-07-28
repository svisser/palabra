#ifndef CPALABRA
#define CPALABRA

#define CONSTRAINT_EMPTY ' '

#define DEBUG 1
#define DEBUG_WORDS 0

#define MAX_WORD_LENGTH 64
#define MAX_ALPHABET_SIZE 50 // TODO

extern char* find_candidate(PyObject *words, int length, char *cs);
extern int process_constraints(PyObject* constraints, char *cs);
extern int check_constraints(char *word, char *cs);

#endif
