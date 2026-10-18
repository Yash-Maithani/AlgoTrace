/* Bellman-Ford in C11, a translation of /run_bellman_ford in app.py.
 * Input and output: reference_code/README.md, "Graph programs".
 * The graph is directed as given. Edges are swept in input order, at most
 * V-1 times, stopping after a pass that changes nothing; one more sweep
 * then reports whether anything could still improve, a negative cycle.
 */
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_NODES 256
#define MAX_EDGES 65536
#define INF LLONG_MAX

// lesson:helpers
/* Node names: keys in input order, then names met only as neighbours. */
static char names[MAX_NODES][64];
static int node_count;

static int node_index(const char *name)
{
    for (int i = 0; i < node_count; i++) {
        if (strcmp(names[i], name) == 0) return i;
    }
    strcpy(names[node_count], name);
    return node_count++;
}

/* The edge list, in the order the endpoint builds it: each key's
   neighbours in turn. */
typedef struct { int u, v; long long w; } Edge;
static Edge edges[MAX_EDGES];
static int edge_count;

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
static void put_value(long long v) { if (v == INF) printf(" \xE2\x88\x9E"); else printf(" %lld", v); }
static void end_step(void) { printf("\n"); }

static long long dist[MAX_NODES];
static int iterations;
static int negative_cycle;

// lesson:start
void bellman_ford(int start) {
    for (int i = 0; i < node_count; i++) dist[i] = INF;
    dist[start] = 0;
    iterations = 0;
    int passes = node_count > 1 ? node_count : 1;               // @hide
    for (int pass = 1; pass < passes; pass++) {
        iterations = pass;                                      // @hide
        int changed = 0;
        for (int e = 0; e < edge_count; e++) {                  // @edge-loop
            Edge edge = edges[e];
            begin_step("consider", "edge-loop"); put_node(edge.u); put_node(edge.v); put_bar(); put_value(edge.w); end_step(); // @hide
            if (dist[edge.u] != INF && dist[edge.u] + edge.w < dist[edge.v]) { // @relax
                dist[edge.v] = dist[edge.u] + edge.w;
                changed = 1;
                begin_step("relax", "relax"); put_node(edge.u); put_node(edge.v); put_bar(); put_value(dist[edge.v]); end_step(); // @hide
            } else {                                            // @no-improve
                begin_step("reject", "no-improve"); put_node(edge.u); put_node(edge.v); put_bar(); put_value(edge.w); end_step(); // @hide
            }
        }
        begin_step("milestone", "pass-done"); put_bar(); put_value(pass); end_step(); // @hide
        if (!changed) break;                                    // @pass-done
    }
    negative_cycle = 0;
    for (int e = 0; e < edge_count; e++) {
        Edge edge = edges[e];
        if (dist[edge.u] != INF && dist[edge.u] + edge.w < dist[edge.v]) negative_cycle = 1;
    }
}
// lesson:end

int main(void)
{
    int cases;
    if (scanf("%d", &cases) != 1) return 1;
    while (cases-- > 0) {
        char start_name[64], name[64], other[64];
        static char keys[MAX_NODES][64];
        static char lines[MAX_NODES][MAX_NODES][64];
        static long long weights[MAX_NODES][MAX_NODES];
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
            if (scanf("%63s %63s %lld", name, other, &ignored) != 3) return 1;
        }
        node_count = 0;
        edge_count = 0;
        for (int i = 0; i < k; i++) node_index(keys[i]);
        for (int i = 0; i < k; i++) {
            for (int j = 0; j < degrees[i]; j++) {
                edges[edge_count].u = node_index(keys[i]);
                edges[edge_count].v = node_index(lines[i][j]);
                edges[edge_count++].w = weights[i][j];
            }
        }
        bellman_ford(node_index(start_name));

        int order[MAX_NODES];
        for (int i = 0; i < node_count; i++) order[i] = i;
        sort_by_name(order, node_count);
        for (int o = 0; o < node_count; o++) {
            printf("distance %s", names[order[o]]);
            put_value(dist[order[o]]);
            printf("\n");
        }
        printf("negative_cycle %s\niterations %d\nend\n",
               negative_cycle ? "true" : "false", iterations);
    }
    return 0;
}
