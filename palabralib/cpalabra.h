#ifndef CPALABRA
#define CPALABRA

#define CONSTRAINT_EMPTY '.'

#define DEBUG 0
#define DEBUG_WORDS 0

#define MAX_WORD_LENGTH 64
#define MAX_ALPHABET_SIZE 50 // TODO

typedef struct tnode *Tptr;
typedef struct tnode {
    char splitchar;
    char *word;
    Tptr lokid, eqkid, hikid;
} Tnode;

typedef struct sresult *Sptr;
typedef struct sresult {
    int n_matches;
    char *chars;
} SearchResult;

Tptr trees[MAX_WORD_LENGTH];

extern int check_intersect(char *word, char **cs, int length, Sptr *results);
extern PyObject* find_matches(PyObject *list, Tptr p, char *s);
extern char* find_candidate(char **cs_i, Sptr *results, PyObject *words, int length, char *cs, Py_ssize_t offset);
extern int process_constraints(PyObject* constraints, char *cs);
extern int check_constraints(char *word, char *cs);

#endif
