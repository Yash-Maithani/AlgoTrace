/* Floyd-Warshall in C11, a translation of /run_floyd_warshall in app.py.
 * Input and output: reference_code/README.md, "Graph programs".
 * Edges are undirected and a parallel edge only replaces a dearer one.
 * Three nested loops with nothing to cut them short: the lesson's V cubed.
 */
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_NODES 128
#define INF LLONG_MAX

// lesson:helpers
/* Node names in input order. */
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
// lesson:end

/* Plumbing: the step trace. */
static void begin_step(const char *action, const char *line) { printf("step %s %s", action, line ? line : "-"); }
static void put_node(int i) { printf(" %s", names[i]); }
static void put_bar(void) { printf(" |"); }
static void put_value(long long v) { if (v == INF) printf(" \xE2\x88\x9E"); else printf(" %lld", v); }
static void end_step(void) { printf("\n"); }

static long long dist[MAX_NODES][MAX_NODES];
static int next_hop[MAX_NODES][MAX_NODES];

typedef struct { int u, v; long long w; } Edge;

// lesson:start
void floyd_warshall(int n, const Edge edges[], int edge_count) {
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            dist[i][j] = i == j ? 0 : INF;
            next_hop[i][j] = -1;
        }
    }
    for (int e = 0; e < edge_count; e++) {
        int i = edges[e].u, j = edges[e].v;
        if (edges[e].w < dist[i][j]) {                          /* keep the cheaper of parallel edges */
            dist[i][j] = dist[j][i] = edges[e].w;               // @init
            next_hop[i][j] = j;
            next_hop[j][i] = i;
        }
    }
    begin_step("milestone", "init");                            // @hide
    for (int i = 0; i < n; i++) put_node(i);                    // @hide
    put_bar(); end_step();                                      // @hide
    for (int k = 0; k < n; k++) {                               // @k-loop
        begin_step("milestone", "k-loop"); put_node(k); put_bar(); end_step(); // @hide
        long long updates = 0;
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                if (i == j) continue;
                long long current = dist[i][j];
                if (dist[i][k] == INF || dist[k][j] == INF) {   // @check-inf
                    begin_step("reject", "check-inf"); put_node(i); put_node(j); put_node(k); put_bar(); end_step(); // @hide
                    continue;
                }
                long long via_k = dist[i][k] + dist[k][j];      // @compare
                begin_step("consider", "compare"); put_node(i); put_node(j); put_node(k); put_bar(); // @hide
                put_value(current); put_value(dist[i][k]); put_value(dist[k][j]); put_value(via_k); end_step(); // @hide
                if (via_k < current) {                          // @update
                    dist[i][j] = via_k;
                    next_hop[i][j] = next_hop[i][k];
                    updates++;
                    begin_step("relax", "update"); put_node(i); put_node(j); put_node(k); put_bar(); put_value(via_k); end_step(); // @hide
                } else {                                        // @keep
                    begin_step("reject", "keep"); put_node(i); put_node(j); put_node(k); put_bar(); put_value(current); end_step(); // @hide
                }
            }
        }                                                       // @k-done
        begin_step("milestone", "k-done"); put_node(k); put_bar(); put_value(updates); end_step(); // @hide
    }
}
// lesson:end

int main(void)
{
    int cases;
    if (scanf("%d", &cases) != 1) return 1;
    while (cases-- > 0) {
        char start_name[64], name[64], other[64];
        int k, m, d;
        if (scanf("%63s %d", start_name, &k) != 2) return 1;
        node_count = 0;
        for (int i = 0; i < k; i++) {
            if (scanf("%63s %d", name, &d) != 2) return 1;
            node_index(name);
            for (int j = 0; j < d; j++) {
                long long ignored;
                if (scanf("%63s %lld", other, &ignored) != 2) return 1;
            }
        }
        int n = node_count;
        static Edge edges[MAX_NODES * MAX_NODES];
        if (scanf("%d", &m) != 1) return 1;
        for (int e = 0; e < m; e++) {
            if (scanf("%63s %63s %lld", name, other, &edges[e].w) != 3) return 1;
            edges[e].u = node_index(name);
            edges[e].v = node_index(other);
        }
        floyd_warshall(n, edges, m);

        begin_step("done", NULL);
        for (int i = 0; i < n; i++) put_node(i);
        put_bar();
        end_step();
        for (int i = 0; i < n; i++) {
            printf("row %s", names[i]);
            for (int j = 0; j < n; j++) put_value(dist[i][j]);
            printf("\n");
        }
        /* One route per reachable ordered pair, by from then to name, the
           order the endpoint's JSON sorts its "from → to" keys into. */
        int order[MAX_NODES];
        for (int i = 0; i < n; i++) order[i] = i;
        for (int a = 1; a < n; a++) {
            int item = order[a], b = a - 1;
            while (b >= 0 && strcmp(names[order[b]], names[item]) > 0) {
                order[b + 1] = order[b];
                b--;
            }
            order[b + 1] = item;
        }
        for (int oi = 0; oi < n; oi++) {
            for (int oj = 0; oj < n; oj++) {
                int i = order[oi], j = order[oj];
                if (i == j || dist[i][j] == INF || next_hop[i][j] == -1) continue;
                int route[MAX_NODES + 2], len = 0;
                route[len++] = i;
                while (route[len - 1] != j && len <= n) {
                    int step_to = next_hop[route[len - 1]][j];
                    if (step_to == -1) break;
                    route[len++] = step_to;
                }
                if (route[len - 1] != j) continue;
                printf("path %s %s", names[i], names[j]);
                put_value(dist[i][j]);
                for (int r = 0; r < len; r++) printf(" %s", names[route[r]]);
                printf("\n");
            }
        }
        printf("end\n");
    }
    return 0;
}
