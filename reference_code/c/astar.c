/* A* on a grid in C11, a translation of grid_algorithms/astar.py.
 * Input and output: reference_code/README.md, "Grid programs". Moves go up,
 * right, down, left at cost 1; h is the Manhattan distance, or 0 for
 * Dijkstra. The heap is the same binary heap as the Python, ordered by
 * lowest f, then lowest h, then push order, so it pops the same entries in
 * the same order and makes the same number of comparisons.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_CELLS 1024
#define MAX_ENTRIES (4 * MAX_CELLS + 1)

// lesson:helpers
/* The grid and the four moves, in the order the Python tries them. */
static int rows, cols;
static char wall[MAX_CELLS];
static const int MOVE_R[4] = {-1, 0, 1, 0};
static const int MOVE_C[4] = {0, 1, 0, -1};

static int manhattan;
static int goal_r, goal_c;

static int h_of(int cell)
{
    if (!manhattan) return 0;
    return abs(cell / cols - goal_r) + abs(cell % cols - goal_c);
}

/* One open set entry. `order` counts the pushes, so no two entries tie. */
typedef struct { int f, h, order, cell, g; } Entry;

static Entry heap[MAX_ENTRIES];
static int heap_size;
static long comparisons;

static int less(const Entry *a, const Entry *b)
{
    comparisons++;
    if (a->f != b->f) return a->f < b->f;
    if (a->h != b->h) return a->h < b->h;
    return a->order < b->order;
}

static void swap_entries(int i, int j) { Entry t = heap[i]; heap[i] = heap[j]; heap[j] = t; }

static void heap_push(Entry e)
{
    int i = heap_size++;
    heap[i] = e;
    while (i > 0) {
        int parent = (i - 1) / 2;
        if (less(&heap[i], &heap[parent])) {
            swap_entries(i, parent);
            i = parent;
        } else {
            break;
        }
    }
}

static Entry heap_pop(void)
{
    Entry top = heap[0];
    Entry last = heap[--heap_size];
    if (heap_size > 0) {
        heap[0] = last;
        int i = 0;
        for (;;) {
            int left = 2 * i + 1, right = 2 * i + 2, best = i;
            if (left < heap_size && less(&heap[left], &heap[best])) best = left;
            if (right < heap_size && less(&heap[right], &heap[best])) best = right;
            if (best == i) break;
            swap_entries(i, best);
            i = best;
        }
    }
    return top;
}
// lesson:end

/* Plumbing: the step trace, with cells named r,c as the site names them. */
static void begin_step(const char *action, const char *line) { printf("step %s %s", action, line); }
static void put_cell(int cell) { printf(" %d,%d", cell / cols, cell % cols); }
static void put_values(int a, int b) { printf(" | %d %d\n", a, b); }

static int g[MAX_CELLS], came_from[MAX_CELLS], closed[MAX_CELLS];
static int path[MAX_CELLS], path_len;
static int expanded;

// lesson:start
int astar(int start, int goal) {
    for (int i = 0; i < rows * cols; i++) { g[i] = -1; closed[i] = 0; }
    g[start] = 0;
    int order = 0;
    heap_push((Entry){h_of(start), h_of(start), 0, start, 0});            // @push-start
    begin_step("enqueue", "push-start"); put_cell(start); put_values(0, h_of(start)); // @hide
    while (heap_size > 0) {
        Entry e = heap_pop();
        if (closed[e.cell] || g[e.cell] != e.g) {
            begin_step("reject", "stale"); put_cell(e.cell); put_values(e.g, e.h); // @hide
            continue;                                                     // @stale
        }
        closed[e.cell] = 1;                                               // @expand
        expanded++;                                                       // @hide
        begin_step("visit", "expand"); put_cell(e.cell); put_values(e.g, e.h); // @hide
        if (e.cell == goal) {
            path_len = 0;                                                 // @path
            for (int at = goal; at != start; at = came_from[at]) path[path_len++] = at;
            path[path_len++] = start;
            begin_step("done", "path");                                   // @hide
            for (int k = path_len - 1; k >= 0; k--) put_cell(path[k]);    // @hide
            printf(" | %d\n", path_len - 1);                              // @hide
            return 1;
        }
        int r = e.cell / cols, c = e.cell % cols;
        for (int m = 0; m < 4; m++) {
            int nr = r + MOVE_R[m], nc = c + MOVE_C[m];
            if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue;
            int nb = nr * cols + nc;
            if (wall[nb] || closed[nb]) continue;
            if (g[nb] < 0 || e.g + 1 < g[nb]) {                           // @improve
                int improved = g[nb] >= 0;                                // @hide
                g[nb] = e.g + 1;
                came_from[nb] = e.cell;
                order++;
                heap_push((Entry){g[nb] + h_of(nb), h_of(nb), order, nb, g[nb]}); // @push
                begin_step(improved ? "relax" : "enqueue", improved ? "improve" : "push"); // @hide
                put_cell(nb); put_cell(e.cell); put_values(g[nb], h_of(nb));         // @hide
            }
        }
    }
    begin_step("done", "no-path"); printf(" | %d\n", expanded);           // @hide
    return 0;                                                             // @no-path
}
// lesson:end

int main(void)
{
    int cases;
    if (scanf("%d", &cases) != 1) return 1;
    while (cases-- > 0) {
        char heuristic[32], line[64];
        int sr, sc, gr, gc;
        if (scanf("%31s %d %d", heuristic, &rows, &cols) != 3) return 1;
        if (strcmp(heuristic, "manhattan") && strcmp(heuristic, "zero")) {
            printf("error unknown heuristic %s\n", heuristic);
            return 2;
        }
        manhattan = strcmp(heuristic, "manhattan") == 0;
        if (scanf("%d %d %d %d", &sr, &sc, &gr, &gc) != 4) return 1;
        for (int r = 0; r < rows; r++) {
            if (scanf("%63s", line) != 1) return 1;
            for (int c = 0; c < cols; c++) wall[r * cols + c] = line[c] == '#';
        }
        goal_r = gr;
        goal_c = gc;
        heap_size = 0;
        comparisons = 0;
        expanded = 0;
        path_len = 0;
        int found = astar(sr * cols + sc, gr * cols + gc);
        printf("path");
        if (found) for (int k = path_len - 1; k >= 0; k--) printf(" %d,%d", path[k] / cols, path[k] % cols);
        printf("\nexpanded %d\ncomparisons %ld\nend\n", expanded, comparisons);
    }
    return 0;
}
