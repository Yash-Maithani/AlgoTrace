/* Topological Sort (Kahn's algorithm) in C11, a translation of
 * /run_topological_sort in app.py. Input and output: reference_code/README.md,
 * "Graph programs". The queue is a ring of node numbers, so taking from the
 * front is O(1), as the endpoint's deque is: the lesson's O(V plus E).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_NODES 256
#define MAX_DEGREE 256

// lesson:helpers
/* The graph, as the endpoint receives it: nodes keep their input order,
   and every node's arrows keep theirs. */
static char names[MAX_NODES][64];
static int node_count;
static int degree[MAX_NODES];
static int arrow[MAX_NODES][MAX_DEGREE];

static int node_index(const char *name)
{
    for (int i = 0; i < node_count; i++) {
        if (strcmp(names[i], name) == 0) return i;
    }
    strcpy(names[node_count], name);
    degree[node_count] = 0;
    return node_count++;
}

/* A first in, first out queue: every node joins it at most once. */
typedef struct {
    int items[MAX_NODES];
    int head, tail;
} Queue;

static void queue_push(Queue *q, int node) { q->items[q->tail++] = node; }
static int queue_pop_front(Queue *q) { return q->items[q->head++]; }
static int queue_empty(const Queue *q) { return q->head == q->tail; }

/* One cycle among the nodes left over, as the endpoint finds it: walk back
   along the first arrow (in input order) that comes into each node from
   another node left over, until a node repeats; then turn the loop round to
   the direction the arrows point and start it at its earliest node. */
static int find_cycle(const int left[], int cycle[])
{
    int first_in[MAX_NODES], seen[MAX_NODES], walk[MAX_NODES] = {0};
    int walked = 0;
    for (int i = 0; i < node_count; i++) { first_in[i] = -1; seen[i] = 0; }
    for (int u = 0; u < node_count; u++) {
        if (!left[u]) continue;
        for (int k = 0; k < degree[u]; k++) {
            int v = arrow[u][k];
            if (left[v] && first_in[v] < 0) first_in[v] = u;
        }
    }
    int node = 0;
    while (!left[node]) node++;
    while (!seen[node]) {
        seen[node] = 1;
        walk[walked++] = node;
        node = first_in[node];
    }
    int from = 0;
    while (walk[from] != node) from++;
    int length = 0;
    for (int k = walked - 1; k >= from; k--) cycle[length++] = walk[k];
    int first = 0;
    for (int k = 1; k < length; k++) {
        if (cycle[k] < cycle[first]) first = k;
    }
    int turned[MAX_NODES];
    for (int k = 0; k < length; k++) turned[k] = cycle[(first + k) % length];
    for (int k = 0; k < length; k++) cycle[k] = turned[k];
    return length;
}
// lesson:end

/* Plumbing: the step trace. */
static void begin_step(const char *action, const char *line) { printf("step %s %s", action, line ? line : "-"); }
static void put_node(int i) { printf(" %s", names[i]); }
static void put_value(int v) { printf(" %d", v); }
static void bar(void) { printf(" |"); }
static void end_step(void) { printf("\n"); }

static int order[MAX_NODES];
static int order_len;
static int left_over[MAX_NODES];
static int cycle[MAX_NODES];
static int cycle_len;

// lesson:start
void topological_sort(void) {
    int in_degree[MAX_NODES] = {0};
    for (int u = 0; u < node_count; u++) {
        for (int k = 0; k < degree[u]; k++) {
            int v = arrow[u][k];
            in_degree[v]++;                                     // @count
            begin_step("consider", "count"); put_node(u); put_node(v); bar(); put_value(in_degree[v]); end_step(); // @hide
        }
    }
    Queue queue = {{0}, 0, 0};
    for (int u = 0; u < node_count; u++) {
        if (in_degree[u] == 0) {
            queue_push(&queue, u);                              // @seed
            begin_step("enqueue", "seed"); put_node(u); bar(); put_value(0); end_step(); // @hide
        }
    }
    while (!queue_empty(&queue)) {
        int u = queue_pop_front(&queue);                        // @remove
        order[order_len++] = u;
        begin_step("visit", "remove"); put_node(u); bar(); put_value(order_len); end_step(); // @hide
        for (int k = 0; k < degree[u]; k++) {
            int v = arrow[u][k];
            in_degree[v]--;                                     // @decrement
            begin_step("consider", "decrement"); put_node(u); put_node(v); bar(); put_value(in_degree[v]); end_step(); // @hide
            if (in_degree[v] == 0) {
                queue_push(&queue, v);                          // @enqueue
                begin_step("enqueue", "enqueue"); put_node(v); bar(); put_value(0); end_step(); // @hide
            }
        }
    }
    if (order_len < node_count) {
        for (int u = 0; u < node_count; u++) left_over[u] = in_degree[u] > 0; // @cycle
        cycle_len = find_cycle(left_over, cycle);
    }
    begin_step("done", cycle_len ? "cycle" : NULL);            // @hide
    for (int u = 0; u < node_count; u++) {                      // @hide
        if (cycle_len ? left_over[u] : 0) put_node(u);          // @hide
    }                                                           // @hide
    for (int i = 0; i < order_len && !cycle_len; i++) put_node(order[i]); // @hide
    bar(); end_step();                                          // @hide
}
// lesson:end

int main(void)
{
    int cases;
    if (scanf("%d", &cases) != 1) return 1;
    while (cases-- > 0) {
        char start_name[64], name[64];
        static char lines[MAX_NODES][MAX_DEGREE][64];
        static char keys[MAX_NODES][64];
        static int degrees[MAX_NODES];
        long long ignored;
        int k, m;
        if (scanf("%63s %d", start_name, &k) != 2) return 1;
        for (int i = 0; i < k; i++) {
            if (scanf("%63s %d", keys[i], &degrees[i]) != 2) return 1;
            for (int j = 0; j < degrees[i]; j++) {
                if (scanf("%63s %lld", lines[i][j], &ignored) != 2) return 1;
            }
        }
        if (scanf("%d", &m) != 1) return 1;
        for (int e = 0; e < m; e++) {
            if (scanf("%63s %63s %lld", name, name, &ignored) != 3) return 1;
        }
        node_count = 0;
        for (int i = 0; i < k; i++) node_index(keys[i]);
        for (int i = 0; i < k; i++) {
            int u = node_index(keys[i]);
            for (int j = 0; j < degrees[i]; j++) arrow[u][degree[u]++] = node_index(lines[i][j]);
        }
        order_len = 0;
        cycle_len = 0;
        memset(left_over, 0, sizeof left_over);
        topological_sort();
        printf("order");
        for (int i = 0; i < order_len; i++) printf(" %s", names[order[i]]);
        printf("\nremaining");
        for (int u = 0; u < node_count; u++) if (left_over[u]) printf(" %s", names[u]);
        printf("\ncycle");
        for (int i = 0; i < cycle_len; i++) printf(" %s", names[cycle[i]]);
        printf("\nend\n");
    }
    return 0;
}
