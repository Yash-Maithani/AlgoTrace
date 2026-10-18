/* Prim in C11, a translation of /run_prim in app.py.
 * Input and output: reference_code/README.md, "Graph programs".
 * The endpoint pushes (weight, u, v) tuples onto Python's heapq, so this
 * uses a binary heap ordered the same way: by weight, then u's name, then
 * v's name. Every edge leaving a newly joined node is pushed, stale ones
 * included, which is the lesson's O(E log E).
 */
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_NODES 256
#define MAX_DEGREE 256
#define MAX_HEAP (MAX_NODES * MAX_DEGREE)

// lesson:helpers
/* The graph, as the endpoint receives it: nodes keep their input order,
   and every node's neighbours keep theirs. */
static char names[MAX_NODES][64];
static int node_count;
static int degree[MAX_NODES];
static int neighbour[MAX_NODES][MAX_DEGREE];
static long long weight[MAX_NODES][MAX_DEGREE];

static int node_index(const char *name)
{
    for (int i = 0; i < node_count; i++) {
        if (strcmp(names[i], name) == 0) return i;
    }
    strcpy(names[node_count], name);
    degree[node_count] = 0;
    return node_count++;
}

/* A binary min-heap of edges, compared as Python compares the tuple
   (weight, u, v): weight first, then the names of u and v. */
typedef struct { long long w; int u, v; } Edge;

static Edge heap[MAX_HEAP];
static int heap_size;

static int edge_less(Edge a, Edge b)
{
    if (a.w != b.w) return a.w < b.w;
    int by_u = strcmp(names[a.u], names[b.u]);
    if (by_u != 0) return by_u < 0;
    return strcmp(names[a.v], names[b.v]) < 0;
}

static void heap_push(long long w, int u, int v)
{
    int i = heap_size++;
    heap[i] = (Edge){w, u, v};
    while (i > 0 && edge_less(heap[i], heap[(i - 1) / 2])) {
        Edge t = heap[i];
        heap[i] = heap[(i - 1) / 2];
        heap[(i - 1) / 2] = t;
        i = (i - 1) / 2;
    }
}

static Edge heap_pop(void)
{
    Edge top = heap[0];
    heap[0] = heap[--heap_size];
    int i = 0;
    for (;;) {
        int l = 2 * i + 1, r = l + 1, least = i;
        if (l < heap_size && edge_less(heap[l], heap[least])) least = l;
        if (r < heap_size && edge_less(heap[r], heap[least])) least = r;
        if (least == i) break;
        Edge t = heap[i];
        heap[i] = heap[least];
        heap[least] = t;
        i = least;
    }
    return top;
}

/* Node indices in order of their names, as Python's sorted() puts them. */
static void sort_by_name(int items[], int count)
{
    for (int i = 1; i < count; i++) {
        int item = items[i];
        int j = i - 1;
        while (j >= 0 && strcmp(names[items[j]], names[item]) > 0) {
            items[j + 1] = items[j];
            j--;
        }
        items[j + 1] = item;
    }
}
// lesson:end

/* Plumbing: the step trace. */
static void begin_step(const char *action, const char *line) { printf("step %s %s", action, line ? line : "-"); }
static void put_node(int i) { printf(" %s", names[i]); }
static void put_bar(void) { printf(" |"); }
static void put_value(long long v) { printf(" %lld", v); }
static void end_step(void) { printf("\n"); }

static int visited[MAX_NODES];
static Edge tree[MAX_NODES];
static int tree_size;

// lesson:start
void prim(int start) {
    int frontier[MAX_DEGREE], reached = 0;                      // @hide
    visited[start] = 1;                                         // @start
    begin_step("visit", "start"); put_node(start); put_bar(); end_step(); // @hide
    for (int k = 0; k < degree[start]; k++) {
        heap_push(weight[start][k], start, neighbour[start][k]); // @push-edges
        if (!visited[neighbour[start][k]]) frontier[reached++] = neighbour[start][k]; // @hide
    }
    if (reached) {                                              // @hide
        begin_step("enqueue", "push-edges");                    // @hide
        for (int f = 0; f < reached; f++) put_node(frontier[f]); // @hide
        put_bar(); end_step();                                  // @hide
    }                                                           // @hide
    while (heap_size > 0) {
        Edge e = heap_pop();                                    // @pop-min
        if (visited[e.v]) {                                     // @skip-visited
            begin_step("reject", "skip-visited"); put_node(e.u); put_node(e.v); put_bar(); put_value(e.w); end_step(); // @hide
            continue;
        }
        begin_step("consider", "pop-min"); put_node(e.u); put_node(e.v); put_bar(); put_value(e.w); end_step(); // @hide
        tree[tree_size++] = e;                                  // @add-edge
        visited[e.v] = 1;
        begin_step("include", "add-edge"); put_node(e.u); put_node(e.v); put_bar(); put_value(e.w); end_step(); // @hide
        reached = 0;                                            // @hide
        for (int k = 0; k < degree[e.v]; k++) {
            if (!visited[neighbour[e.v][k]]) {
                heap_push(weight[e.v][k], e.v, neighbour[e.v][k]); // @push-edges
                frontier[reached++] = neighbour[e.v][k];        // @hide
            }
        }
        if (reached) {                                          // @hide
            begin_step("enqueue", "push-edges");                // @hide
            for (int f = 0; f < reached; f++) put_node(frontier[f]); // @hide
            put_bar(); end_step();                              // @hide
        }                                                       // @hide
    }
}
// lesson:end

int main(void)
{
    int cases;
    if (scanf("%d", &cases) != 1) return 1;
    while (cases-- > 0) {
        char start_name[64], name[64];
        static char lines[MAX_NODES][MAX_DEGREE][64];
        static long long weights[MAX_NODES][MAX_DEGREE];
        static char keys[MAX_NODES][64];
        static int degrees[MAX_NODES];
        long long ignored;
        int k, m;
        if (scanf("%63s %d", start_name, &k) != 2) return 1;
        for (int i = 0; i < k; i++) {
            if (scanf("%63s %d", keys[i], &degrees[i]) != 2) return 1;
            for (int j = 0; j < degrees[i]; j++) {
                if (scanf("%63s %lld", lines[i][j], &weights[i][j]) != 2) return 1;
            }
        }
        if (scanf("%d", &m) != 1) return 1;
        for (int e = 0; e < m; e++) {
            if (scanf("%63s %63s %lld", name, name, &ignored) != 3) return 1;
        }
        node_count = 0;
        for (int i = 0; i < k; i++) node_index(keys[i]);
        int key_count = node_count;
        for (int i = 0; i < k; i++) {
            int u = node_index(keys[i]);
            for (int j = 0; j < degrees[i]; j++) {
                neighbour[u][degree[u]] = node_index(lines[i][j]);
                weight[u][degree[u]++] = weights[i][j];
            }
        }
        memset(visited, 0, sizeof visited);
        heap_size = 0;
        tree_size = 0;
        prim(node_index(start_name));

        long long total = 0;
        for (int t = 0; t < tree_size; t++) total += tree[t].w;
        int order[MAX_NODES], seen = 0;
        for (int i = 0; i < key_count; i++) if (visited[i]) order[seen++] = i;
        sort_by_name(order, seen);
        begin_step("done", NULL);
        for (int i = 0; i < seen; i++) put_node(order[i]);
        put_bar();
        put_value(total);
        end_step();
        for (int t = 0; t < tree_size; t++) {
            printf("edge %s %s %lld\n", names[tree[t].u], names[tree[t].v], tree[t].w);
        }
        printf("total %lld\nend\n", total);
    }
    return 0;
}
