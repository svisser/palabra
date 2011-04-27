#ifndef CPALABRA
#define CPALABRA

#define CONSTRAINT_EMPTY '.'

#define DEBUG 0
#define DEBUG_WORDS 0

#define MAX_WORD_LENGTH 64
#define MAX_ALPHABET_SIZE 50 // TODO

#define FILL_START_AT_ZERO 0
#define FILL_START_AT_SELECTION 1
#define FILL_START_AT_AUTO 2

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

typedef struct sparams *SPPtr;
typedef struct sparams {
    int offset;
} SearchParams;

typedef struct {
    int index;
    int length;
    PyObject* cs;
    int skip; // 0 = ok, 1 = skip in search process
    int equal; // -1 = unique, 0 and up = index in array that this slot is equal to
} IntersectingSlot;

typedef struct Cell {
    int top_bar; // {0,1}
    int left_bar; // {0,1}
    int block; // {0,1}
    char c;
    int number;
    int empty; // {0,1}
    int fixed; // {0,1} 0 = read/write, 1 = read
} Cell;

typedef struct Slot {
    int x;
    int y;
    int dir; // 0 = across, 1 = down
    int length;
    int count;
    int done; // {0, 1}
    Py_ssize_t offset;
    PyObject *words;
} Slot;

Tptr trees[MAX_WORD_LENGTH];

extern int check_intersect(char *word, char **cs, int length, Sptr *results);
extern PyObject* find_matches(PyObject *list, Tptr p, char *s);
extern char* find_candidate(char **cs_i, Sptr *results, PyObject *words, int length, char *cs, Py_ssize_t offset);
extern int process_constraints(PyObject* constraints, char *cs);
extern int check_constraints(char *word, char *cs);
extern int is_intersecting_equal(IntersectingSlot s0, IntersectingSlot s1);
extern void print(Tptr p, int indent);
extern Tptr insert1(Tptr p, char *s, char *word);
extern int analyze(int offset, Sptr result, Tptr p, char *s, char *cs);
extern Sptr analyze_intersect_slot(int offset, char *cs);
extern void analyze_intersect_slot2(Sptr *results, int *skipped, int *offsets, char **cs, int length);
extern void free_tree(Tptr p);
extern int calc_is_available(PyObject *grid, int x, int y);
extern int calc_is_start_word(PyObject *grid, int x, int y);
extern int count_words(PyObject *words, int length, char *cs);
extern int get_slot_index(Slot *slots, int n_slots, int x, int y, int dir);
extern int can_clear_char(Cell *cgrid, int width, int height, Slot slot);
extern void clear_slot(Cell *cgrid, int width, int height, Slot *slots, int n_slots, int index);
extern int is_intersecting(Slot *slot1, Slot *slot2);
extern int is_valid(int x, int y, int width, int height);
extern int is_available(Cell *cgrid, int width, int height, int x, int y);
extern char* get_constraints(Cell *cgrid, int width, int height, Slot *slot);
extern int determine_count(PyObject *words, Cell *cgrid, int width, int height, Slot *slot);
extern int backtrack(PyObject *words, Cell *cgrid, int width, int height, Slot *slots, int n_slots, int* order, int n_done_slots, int index);
extern PyObject* gather_fill(Cell *cgrid, int width, int height);
extern int find_initial_slot(Slot *slots, int n_slots, int option_start);
extern int find_slot(Slot *slots, int n_slots, int* order);

#endif
