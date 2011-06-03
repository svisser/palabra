
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
        PyObject *item = Py_BuildValue("(si)", p->word, p->score);
        PyList_Append(list, item);
        Py_DECREF(item);
        // continue recursion as we may have more words
        if (p->eqkid != NULL) {
            find_matches(list, p->eqkid, s);
        }
    }
    if (*s == '.' || *s > p->splitchar)
        find_matches(list, p->hikid, s);
    return list;
}

void update_score(Tptr p, char *s, int score)
{
    if (!p) return;
    if (*s < p->splitchar)
        update_score(p->lokid, s, score);
    if (*s == p->splitchar)
        if (p->splitchar && *s)
            update_score(p->eqkid, s + 1, score);
    if (*s == 0 && p->splitchar == 0) {
        p->score = score;
    }
    if (*s > p->splitchar)
        update_score(p->hikid, s, score);
}

void read_counts_str(char *counts_c, int *counts_i, char *s) {
    const int length = strlen(s);
    int i;
    for (i = 0; i < length; i++) {
        char c = *(s + i);
        int j = 0;
        for (j = 0; j < length; j++) {
            if (counts_c[j] == ' ') {
                counts_c[j] = c;
                counts_i[j] = 1;
                break;
            } else if (counts_c[j] == c) {
                counts_i[j]++;
                break;
            }
        }
    }
}

PyObject *find_matches_i(int index, char *s) {
    const int length = strlen(s);
    char counts_c[length];
    int counts_i[length];
    int k;
    for (k = 0; k < length; k++) {
        counts_c[k] = ' ';
        counts_i[k] = 0;
    }
    read_counts_str(counts_c, counts_i, s);
    char cons_str[length + 1];
    int i;
    for (i = 0; i < length; i++) {
        cons_str[i] = '.';
    }
    cons_str[length] = '\0';
    PyObject *result = PyList_New(0);
    PyObject *mwords = PyList_New(0);
    mwords = find_matches(mwords, trees[index][length], cons_str);
    Py_ssize_t m;
    for (m = 0; m < PyList_Size(mwords); m++) {
        char *word = PyString_AS_STRING(PyList_GET_ITEM(mwords, m));
        int ok = 0;
        for (i = 0; i < length; i++) {
            int count = 0;
            int j;
            for (j = 0; j < length; j++) {
                if (word[j] == counts_c[i]) count++;
            }
            if (count == counts_i[i]) {
                ok++;
            }
        }
        if (ok == length) {
            PyObject *py_word = PyString_FromString(word);
            PyList_Append(result, py_word);
            Py_DECREF(py_word);
        }
    }
    return result;
}

// fills in is_char_ok with 1 = ok, 0 = not ok
void check_intersect(char *word, char **cs, int length, Sptr *results, int is_char_ok[MAX_WORD_LENGTH]) {
    int c;
    for (c = 0; c < length; c++)
        if (results[c] == NULL)
            return;
    for (c = 0; c < length; c++) {
        if (strchr(cs[c], '.') == NULL) {
            continue;
        }
        int m;
        for (m = 0; m < MAX_ALPHABET_SIZE; m++) {
            char m_c = results[c]->chars[m];
            if (m_c == ' ') break;
            if (m_c == *(word + c)) {
                is_char_ok[c] = 1;
                break;
            }
        }
    }
}

char* find_candidate(char **cs_i, Sptr *results, Slot *slot, char *cs, int option_nice, int offset) {
    //printf("Finding for %i %i %i from %i with %s\n", slot->x, slot->y, slot->dir, slot->offset, cs);
    Py_ssize_t count = PyList_Size(slot->words);
    Py_ssize_t w;
    Py_ssize_t m_count = 0;
    for (w = 0; w < count; w++) {
        char *word = PyString_AsString(PyList_GetItem(slot->words, w));
        if (check_constraints(word, cs)) {
            //printf("Considering %i %s %s\n", option_nice, word, cs);
            if (!option_nice) {
                // TODO refactor with cPalabra_search
                int is_char_ok[MAX_WORD_LENGTH];
                int j = 0;
                for (j = 0; j < slot->length; j++) {
                    is_char_ok[j] = 0;
                }
                check_intersect(word, cs_i, slot->length, results, is_char_ok);
                int n_chars = 0;
                // mark fully filled in intersecting words also as ok
                for (j = 0; j < slot->length; j++) {
                    if (strchr(cs_i[j], '.') == NULL) {
                        n_chars++;
                    }
                }
                for (j = 0; j < slot->length; j++) {
                    if (is_char_ok[j]) n_chars++;
                }
                //printf("%i %i\n", n_chars, slot->length);
                if (n_chars < slot->length)
                    continue;
            }
            //printf("checking %i %i\n", m_count, offset);
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

// 1 = equal, 0 = not equal, 2 = error
int is_intersecting_equal(IntersectingSlot s0, IntersectingSlot s1) {
    if (s0.index != s1.index) return 0;
    if (s0.length != s1.length) return 0;
    const Py_ssize_t len_m = PyList_Size(s0.cs);
    const Py_ssize_t len_mm = PyList_Size(s1.cs);
    if (len_m != len_mm) return 0;
    Py_ssize_t l;
    for (l = 0; l < len_m; l++) {
        const int j_m;
        const char *c_m;
        PyObject *tuple_m = PyList_GetItem(s0.cs, l);
        if (!PyArg_ParseTuple(tuple_m, "is", &j_m, &c_m))
            return 2;
        const int j_mm;
        const char *c_mm;
        PyObject *tuple_mm = PyList_GetItem(s1.cs, l);
        if (!PyArg_ParseTuple(tuple_mm, "is", &j_mm, &c_mm))
            return 2;
        if (j_m != j_mm || *c_m != *c_mm)
            return 0;
    }
    return 1;
}

void print(Tptr p, int indent)
{
    if (p == NULL) return;
    if (p->splitchar != 0) {
        int i;
        for (i = 0; i < indent; i++)
        {
            printf(" ");
        }
        printf("%c\n", p->splitchar);
    }
    if (p->lokid != NULL) print(p->lokid, indent + 2);
    if (p->eqkid != NULL) print(p->eqkid, indent + 2);
    if (p->hikid != NULL) print(p->hikid, indent + 2);
}

Tptr insert1(Tptr p, char *s, char *word, int score)
{
    if (p == NULL) {
        p = (Tptr) PyMem_Malloc(sizeof(Tnode));
        p->splitchar = *s;
        p->word = word;
        p->score = score;
        p->lokid = NULL;
        p->eqkid = NULL;
        p->hikid = NULL;
    } else if (*s == 0 && p != NULL) {
        // if we are inserting the same word more than once, continue recursion
        p->eqkid = insert1(p->eqkid, s, word, score);
    }
    if (*s < p->splitchar)
        p->lokid = insert1(p->lokid, s, word, score);
    else if (*s == p->splitchar) {
        if (*s != 0)
            p->eqkid = insert1(p->eqkid, ++s, word, score);
    } else
        p->hikid = insert1(p->hikid, s, word, score);
    return p;
}

int analyze(int offset, Sptr result, Tptr p, char *s, char *cs, int min_score)
{
    if (!p) return 0;
    int n = 0;
    if (*s == '.' || *s < p->splitchar)
        n += analyze(offset, result, p->lokid, s, cs, min_score);
    if (*s == '.' || *s == p->splitchar)
        if (p->splitchar && *s)
            n += analyze(offset, result, p->eqkid, s + 1, cs, min_score);
    if (*s == 0 && p->splitchar == 0 && p->score >= min_score) {
        n += 1;
        char intersect_char = *(cs + offset);
        if (intersect_char == '.') {
            char c = *(p->word + offset);
            int m;
            for (m = 0; m < MAX_ALPHABET_SIZE; m++) {
                if (result->chars[m] == c)
                    break;
                if (result->chars[m] == ' ') {
                    result->chars[m] = c;
                    break;
                }
            }
        } else {
            result->chars[0] = intersect_char;
        }
    }
    if (*s == '.' || *s > p->splitchar)
        n += analyze(offset, result, p->hikid, s, cs, min_score);
    result->n_matches = n;
    return n;
}

Sptr analyze_intersect_slot(int offset, char *cs, int index, int min_score) {
    if (!trees[index][strlen(cs)]) {
        return NULL;
    }
    Sptr result;
    result = (Sptr) PyMem_Malloc(sizeof(SearchResult));
    if (!result) {
        return NULL; //PyErr_NoMemory(); TODO fix
    }
    result->chars = PyMem_Malloc(MAX_ALPHABET_SIZE * sizeof(char));
    if (!result->chars) {
        PyMem_Free(result);
        return NULL; //PyErr_NoMemory(); TODO fix
    }
    int c;
    for (c = 0; c < MAX_ALPHABET_SIZE; c++) {
        result->chars[c] = ' ';
    }
    analyze(offset, result, trees[index][strlen(cs)], cs, cs, min_score);
    return result;
}

void analyze_intersect_slot2(Sptr *results, int *skipped, int *offsets, char **cs, int length, int index, int min_score) {
    int t;
    for (t = 0; t < length; t++) {
        int skip = -1;
        int s;
        for (s = 0; s < t; s++) {
            if (cs[s] == NULL || cs[t] == NULL)
                continue;
            if (strcmp(cs[s], cs[t]) == 0) {
                skip = s;
                break;
            }
        }
        if (skip < 0) {
            results[t] = analyze_intersect_slot(offsets[t], cs[t], index, min_score);
        } else {
            skipped[t] = 1;
            results[t] = results[skip];
        }
    }
}

void free_tree(Tptr p) {
    if (!p) return;
    if (p->lokid != NULL) {
        free_tree(p->lokid);
        PyMem_Free(p->lokid);
        p->lokid = NULL;
    }
    if (p->eqkid != NULL) {
        free_tree(p->eqkid);
        PyMem_Free(p->eqkid);
        p->eqkid = NULL;
    }
    if (p->hikid != NULL) {
        free_tree(p->hikid);
        PyMem_Free(p->hikid);
        p->hikid = NULL;
    }
}

// 0 = false, 1 = true
int calc_is_available(PyObject *grid, int x, int y) {
    int width = (int) PyInt_AsLong(PyObject_GetAttrString(grid, "width"));
    int height = (int) PyInt_AsLong(PyObject_GetAttrString(grid, "height"));
    
    if (!(0 <= x && x < width && 0 <= y && y < height))
        return 0;
    
    PyObject* data = PyObject_GetAttrString(grid, "data");
    PyObject* col = PyObject_GetItem(data, PyInt_FromLong(y));
    PyObject* cell = PyObject_GetItem(col, PyInt_FromLong(x));
    
    int is_block = PyObject_IsTrue(PyObject_GetItem(cell, PyString_FromString("block")));
    if (is_block != 0)
        return 0;
    int is_void = PyObject_IsTrue(PyObject_GetItem(cell, PyString_FromString("void")));
    if (is_void != 0)
        return 0;
    return 1;
}

// 0 = false, 1 = true
int calc_is_start_word(PyObject *grid, int x, int y) {
    int available = calc_is_available(grid, x, y);
    if (available == 0)
        return 0;
    
    PyObject *bar_str = PyString_FromString("bar");
    PyObject *side_left = PyString_FromString("left");
    PyObject *side_top = PyString_FromString("top");
    
    // 0 = across, 1 = down
    int e;
    for (e = 0; e < 2; e++) {
        int bdx = e == 0 ? -1 : 0;
        int bdy = e == 0 ? 0 : -1;
        int adx = e == 0 ? 1 : 0;
        int ady = e == 0 ? 0 : 1;
        PyObject *side = e == 0 ? side_left : side_top;
        
        // both conditions of after
        if (calc_is_available(grid, x + adx, y + ady) == 0)
            continue;
        PyObject* data = PyObject_GetAttrString(grid, "data");
        PyObject* col = PyObject_GetItem(data, PyInt_FromLong(y + ady));
        PyObject* cell = PyObject_GetItem(col, PyInt_FromLong(x + adx));
        PyObject* bars = PyObject_GetItem(cell, bar_str);
        if (PyObject_IsTrue(PyObject_GetItem(bars, side)) == 1)
            continue;
        
        // both conditions of before
        if (calc_is_available(grid, x + bdx, y + bdy) == 0)
            return 1;
        col = PyObject_GetItem(data, PyInt_FromLong(y));
        cell = PyObject_GetItem(col, PyInt_FromLong(x));
        bars = PyObject_GetItem(cell, bar_str);
        if (PyObject_IsTrue(PyObject_GetItem(bars, side)) == 1)
            return 1;
    }
    return 0;
}

int count_words(PyObject *words, int length, char *cs) {
    int count = 0;
    Py_ssize_t w;
    PyObject* key = Py_BuildValue("i", length);
    PyObject* words_m = PyDict_GetItem(words, key);
    for (w = 0; w < PyList_Size(words_m); w++) {
        PyObject* word_obj = PyList_GET_ITEM(words_m, w);
        PyObject* word_str;
        const int word_score;
        if (!PyArg_ParseTuple(word_obj, "Oi", &word_str, &word_score))
            return -1;
        char *word = PyString_AsString(word_str);
        if (!check_constraints(word, cs)) {
            continue;
        }
        count++;
    }
    return count;
}

int get_slot_index(Slot *slots, int n_slots, int x, int y, int dir) {
    int s;
    for (s = 0; s < n_slots; s++) {
        Slot slot = slots[s];
        if (dir == slot.dir) {
            int match_across = (dir == DIR_ACROSS && x>= slot.x
                && x < slot.x + slot.length && slot.y == y);
            int match_down = (dir == DIR_DOWN && y >= slot.y
                && y < slot.y + slot.length && slot.x == x);
            if (match_across || match_down) {
                return s;
            }
        }
    }
    return -1;
}

// 1 = yes, 0 = no
int can_clear_char(Cell *cgrid, int width, int height, Slot slot) {
    int j;
    for (j = 0; j < slot.length; j++) {
        int cx = slot.x + (slot.dir == DIR_ACROSS ? j : 0);
        int cy = slot.y + (slot.dir == DIR_DOWN ? j : 0);
        if (cgrid[cx + cy * width].c == CONSTRAINT_EMPTY)
            return 1;
    }
    return 0;
}

void clear_slot(Cell *cgrid, int width, int height, Slot *slots, int n_slots, int index) {
    Slot slot = slots[index];
    int l;
    for (l = 0; l < slot.length; l++) {
        if (cgrid[slot.x + slot.y * width].fixed == 1)
            continue;
        int cx = slot.x + (slot.dir == DIR_ACROSS ? l : 0);
        int cy = slot.y + (slot.dir == DIR_DOWN ? l : 0);
        int m = get_slot_index(slots, n_slots, cx, cy, slot.dir == DIR_ACROSS ? 1 : 0);
        int is_inter_ok = 1;
        if (m >= 0) {
            // a char can be cleared if the intersecting slot is not done or
            // when it has one or more missing characters (these are not mutually
            // exclusive as a slot can be fully filled in but not yet marked as done:
            // the content of the slot may not be a valid word)
            is_inter_ok = !slots[m].done || can_clear_char(cgrid, width, height, slots[m]);
        }
        Cell *cell = &cgrid[cx + cy * width];
        if (is_inter_ok && cell->c != CONSTRAINT_EMPTY) {
            cell->c = CONSTRAINT_EMPTY;
        }
    }
}

// 0 = false, 1 = true
int is_intersecting(Slot *slot1, Slot *slot2) {
    if (slot1->dir == slot2->dir) return 0;
    if (slot1->dir == DIR_ACROSS) {
        return (slot2->x >= slot1->x && slot2->x < slot1->x + slot1->length
            && slot1->y >= slot2->y && slot1->y < slot2->y + slot2->length);
    } else if (slot1->dir == DIR_DOWN) {
        return (slot1->x >= slot2->x && slot1->x < slot2->x + slot2->length
            && slot2->y >= slot1->y && slot2->y < slot1->y + slot1->length);
    }
    return 0;
}

int is_valid(int x, int y, int width, int height) {
    return x >= 0 && y >= 0 && x < width && y < height;
}

int is_available(Cell *cgrid, int width, int height, int x, int y) {
    if (!is_valid(x, y, width, height)) return 0;
    int a0 = cgrid[x + y * width].block == 0;
    int a1 = cgrid[x + y * width].empty == 0;
    return a0 && a1;
}

char* get_constraints(Cell *cgrid, int width, int height, Slot *slot) {
    // TODO reduce these malloc calls
    //printf("Constraint search\n");
    char* cs = PyMem_Malloc(slot->length * sizeof(char) + 1);
    if (!cs) {
        return NULL;
    }
    get_constraints_i(cgrid, width, height, slot, cs);
    return cs;
}

void get_constraints_i(Cell *cgrid, int width, int height, Slot *slot, char *cs) {
    const int dx = slot->dir == DIR_ACROSS ? 1 : 0;
    const int dy = slot->dir == DIR_DOWN ? 1 : 0;
    int j;
    for (j = 0; j < slot->length; j++) {
        cs[j] = cgrid[(slot->x + j * dx) + (slot->y + j * dy) * width].c;
    }
    cs[slot->length] = '\0';
}

int determine_count(PyObject *words, Cell *cgrid, int width, int height, Slot *slot) {
    int prev = slot->count;
    // TODO reduce these malloc calls
    //printf("Constraint search\n");
    char* cs = PyMem_Malloc(slot->length * sizeof(char) + 1);
    if (!cs) {
        return -1;
    }
    get_constraints_i(cgrid, width, height, slot, cs);
    int count = count_words(words, slot->length, cs);
    if (DEBUG && count == 0) {
        printf("WARNING: slot (%i, %i, %i): from %i to %i\n", slot->x, slot->y, slot->dir, prev, count);
    }
    PyMem_Free(cs);
    return count;
}

// return = number of slots cleared
int backtrack(PyObject *words, Cell *cgrid, int width, int height, Slot *slots, int n_slots, int* order, int n_done_slots, int index) {
    //printf("Backtracking\n");
    int cleared = 0;
    int s;
    int iindex = -1;
    /*for (s = n_done_slots; s >= 0; s--) {
        //printf("Checking: %i %i %i with %i %i %i\n", slots[order[s]].x, slots[order[s]].y, slots[order[s]].dir, slots[order[index]].x, slots[order[index]].y, slots[order[index]].dir);
        if (is_intersecting(&slots[order[s]], &slots[index])) {
            iindex = s;
            break;
        }
    }*/
    iindex = n_done_slots - 1;
    if (iindex < 0) {
        printf("No index found for %i %i %i !\n", slots[index].x, slots[index].y, slots[index].dir);
        iindex = 0;
    }
    //printf("Backtracking %i %i\n", iindex, index);
    if (iindex >= 0) {
        if (0) {
            printf("Blanking between (%i, %i, %s) and (%i, %i, %s)\n"
                , (&slots[iindex])->x, (&slots[iindex])->y, (&slots[iindex])->dir == DIR_ACROSS ? "across" : "down"
                , (&slots[index])->x, (&slots[index])->y, (&slots[index])->dir == DIR_ACROSS ? "across" : "down" );
            printf("Indices: %i %i\n", iindex, index);
        }
        for (s = n_done_slots; s >= iindex; s--) {
            int blank = order[s];
            if (blank < 0) {
                // no word was actually filled in so skip
                continue;
            }
            Slot *bslot = &slots[blank];
            //printf("About to clear: (%i, %i, %s)\n", bslot->x, bslot->y, bslot->dir == DIR_ACROSS ? "across" : "down");
            cleared++;
            clear_slot(cgrid, width, height, slots, n_slots, blank);
            bslot->count = determine_count(words, cgrid, width, height, bslot);
            bslot->done = 0;
            if (s > iindex) bslot->offset = 0;
            if (s == iindex) {
                bslot->offset++;
                if (bslot->offset == bslot->count && iindex > 0) {
                    // if we exhaused all words, backtrack one more
                    bslot->offset = 0;
                    iindex -= 1;
                }
            }
        }
    }
    return cleared;
}

PyObject* gather_fill(Cell *cgrid, int width, int height) {
    int x;
    int y;
    PyObject *fill = PyList_New(0);
    for (y = 0; y < height; y++) {
        for (x = 0; x < width; x++) {
            Cell *cell = &cgrid[x + y * width];
            if (cell->fixed == 1 || cell->c == CONSTRAINT_EMPTY) continue;
            char cell_c[2];
            cell_c[0] = toupper(cell->c);
            cell_c[1] = '\0';
            PyList_Append(fill, Py_BuildValue("(iis)", x, y, cell_c));
        }
    }
    return fill;
}

inline int find_initial_slot(Slot *slots, int n_slots, int option_start) {
    int index = -1;
    if (option_start == FILL_START_AT_ZERO) {
        index = 0;
    } else if (option_start == FILL_START_AT_SELECTION) {
        // TODO
    } else if (option_start == FILL_START_AT_AUTO) {
        // find most-constrained slot that is not done and has at least one possible word
        int m;
        for (m = 0; m < n_slots; m++) {
            if (!slots[m].done && slots[m].count > 0) {
                index = m;
                break;
            }
        }
        for (m = 0; m < n_slots; m++) {
            if (slots[m].count == 0) continue;
            if (slots[m].count < slots[index].count && !slots[m].done) {
                index = m;
            }
        }
    }
    return index;
}

inline int find_slot(Slot *slots, int n_slots, int* order) {
    // find most-constrained slot that is connected to a previously filled in slot
    int index = -1;
    int o;
    for (o = 0; o < n_slots; o++) {
        if (order[o] < 0) break;
        int l;
        for (l = 0; l < slots[order[o]].length; l++) {
            int m;
            for (m = 0; m < n_slots; m++) {
                if (order[o] == m) continue;
                if (slots[m].done) continue;
                if (is_intersecting(&slots[order[o]], &slots[m])) {
                    if (slots[order[o]].dir == DIR_ACROSS && (slots[m].x - slots[order[o]].x == l)) {
                        index = m;
                        break;
                    } else if (slots[order[o]].dir == DIR_DOWN && (slots[m].y - slots[order[o]].y == l)) {
                        index = m;
                        break;
                    }
                }
            }
            if (index >= 0) break;
        }
        if (index >= 0) break;
    }
    return index;
}

inline int find_nice_slot(PyObject *words, Slot *slots, int n_slots, int width, int height, int* order) {
    // compute lengths of provided words and lengths of actually filled in words
    int lengths[MAX_WORD_LENGTH];
    int a_lengths[MAX_WORD_LENGTH];
    int t;
    for (t = 0; t < MAX_WORD_LENGTH; t++) {
        lengths[t] = 0;
        a_lengths[t] = 0;
    }
    for (t = 0; t < MAX_WORD_LENGTH; t++) {
        PyObject *key = Py_BuildValue("i", t);
        PyObject *l_words = PyDict_GetItem(words, key);
        lengths[t] += PyList_Size(l_words);
    }
    for (t = 0; t < n_slots; t++) {
        int i = order[t];
        if (i < 0) break;
        a_lengths[slots[i].length]++;
    }
    // find index of a possible symmetrical slot
    for (t = 0; t < n_slots; t++) {
        int i = order[t];
        if (i < 0) break;
        int x = slots[i].x;
        int y = slots[i].y;
        int dir = slots[i].dir;
        int length = slots[i].length;
        int s;
        for (s = 0; s < n_slots; s++) {
            if (s == t) continue;
            int symm_x = width - x - (dir == DIR_ACROSS ? length : 0) - (dir == DIR_DOWN ? 1 : 0);
            int symm_y = height - y - (dir == DIR_DOWN ? length : 0) - (dir == DIR_ACROSS ? 1 : 0);
            if ((slots[s].x == symm_x)
                && (slots[s].y == symm_y)
                && slots[s].dir == dir
                && slots[s].length == length
                && !slots[s].done
                //&& slots[s].count > 0
                && a_lengths[length] < lengths[length]) {
                return s;
            }
        }
    }
    // find "nicest" slot (= close to center and preferably across)
    int c_x = width / 2;
    int c_y = height / 2;
    int index = -1;
    int score = 1000 * (width + height);
    for (t = 0; t < n_slots; t++) {
        int l = slots[t].length;
        //printf("%i %i %i | %i %i\n", slots[t].x, slots[t].y, slots[t].dir, slots[t].done, slots[t].count);
        if (!slots[t].done && /*slots[t].count > 0 &&*/ a_lengths[l] < lengths[l]) {
            int s_x = slots[t].x - c_x;
            int s_y = slots[t].y - c_y;
            int s_score = (s_x >= 0 ? s_x : -1 * s_x) + (s_y >= 0 ? s_y : -1 * s_y) + (slots[t].dir == DIR_DOWN ? 5 : 0);
            if (s_score < score) {
                //printf("Score: %i %i\n", s_score, score);
                index = t;
                score = s_score;
            }
        }
    }
    return index;
}
