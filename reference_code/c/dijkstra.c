/* Dijkstra in C11, a translation of algotrace/algorithms/graph/dijkstra.py.
 * Input and output: reference_code/README.md, "Graph programs".
 * The nearest node is found by a linear scan over the nodes in input order,
 * taking the first smallest, exactly as the endpoint's min() does, so ties
 * break the same way and the lesson's O(V squared) holds.
 */
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_NODES 256
#define MAX_DEGREE 256
#define INF LLONG_MAX

// lesson:helpers
/* The graph, as the endpoint receives it: nodes keep their input order,
   and every node's neighbours keep theirs. The first key_count nodes are
   the ones with a line of their own. */
static char names[MAX_NODES][64];
static int node_count;
static int key_count;
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
static int previous[MAX_NODES];

// lesson:start
void dijkstra(int start) {
    int unvisited[MAX_NODES];
    for (int i = 0; i < key_count; i++) {
        dist[i] = INF;
        previous[i] = -1;
        unvisited[i] = 1;
    }
    dist[start] = 0;
    int remaining = key_count;
    while (remaining > 0) {
        int current = -1;
        for (int i = 0; i < key_count; i++) {
            if (unvisited[i] && (current == -1 || dist[i] < dist[current])) current = i; // @pick-min
        }
        if (dist[current] == INF) break;
        unvisited[current] = 0;
        remaining--;
        begin_step("visit", "pick-min"); put_node(current); put_bar(); put_value(dist[current]); end_step(); // @hide
        for (int k = 0; k < degree[current]; k++) {
            int next = neighbour[current][k];
            if (next < key_count && unvisited[next]) {
                long long through = dist[current] + weight[current][k];
                if (through < dist[next]) {                     // @relax
                    dist[next] = through;
                    previous[next] = current;
                    begin_step("relax", "relax"); put_node(next); put_bar(); put_value(through); end_step(); // @hide
                }
            }
        }
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
        key_count = node_count;
        for (int i = 0; i < k; i++) {
            int u = node_index(keys[i]);
            for (int j = 0; j < degrees[i]; j++) {
                neighbour[u][degree[u]] = node_index(lines[i][j]);
                weight[u][degree[u]++] = weights[i][j];
            }
        }
        int start = node_index(start_name);
        dijkstra(start);

        /* The final frame: every node, by name. */
        int order[MAX_NODES];
        for (int i = 0; i < key_count; i++) order[i] = i;
        sort_by_name(order, key_count);
        begin_step("done", NULL);
        for (int i = 0; i < key_count; i++) put_node(order[i]);
        put_bar();
        end_step();

        /* The result as the endpoint sends it: its JSON sorts object keys,
           so both maps arrive in order of node name. */
        for (int o = 0; o < key_count; o++) {
            int i = order[o];
            printf("distance %s", names[i]);
            put_value(dist[i]);
            printf("\n");
        }
        for (int o = 0; o < key_count; o++) {
            int i = order[o];
            if (i == start || dist[i] == INF) continue;
            int route[MAX_NODES], len = 0;
            for (int at = i; at != -1; at = previous[at]) route[len++] = at;
            if (route[len - 1] != start) continue;
            printf("path %s", names[i]);
            for (int r = len - 1; r >= 0; r--) printf(" %s", names[route[r]]);
            printf("\n");
        }
        printf("end\n");
    }
    return 0;
}
