/* Breadth-First Search in C11, a translation of algotrace/algorithms/graph/bfs.py.
 * Input and output: reference_code/README.md, "Graph programs".
 * Like the endpoint, the queue is a list scanned by `not in queue`, so the
 * membership test is linear: the lesson's O(V times E).
 */
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_NODES 256
#define MAX_DEGREE 256

// lesson:helpers
/* The graph, as the endpoint receives it: nodes keep their input order,
   and every node's neighbours keep theirs. */
static char names[MAX_NODES][64];
static int node_count;
static int degree[MAX_NODES];
static int neighbour[MAX_NODES][MAX_DEGREE];

static int node_index(const char *name)
{
    for (int i = 0; i < node_count; i++) {
        if (strcmp(names[i], name) == 0) return i;
    }
    strcpy(names[node_count], name);
    degree[node_count] = 0;
    return node_count++;
}

/* A queue kept as a list, as Python's list is: popping takes the front,
   and checking membership walks what is still waiting. */
typedef struct {
    int items[MAX_NODES];
    int head, tail;
} Queue;

static void queue_push(Queue *q, int node) { q->items[q->tail++] = node; }
static int queue_pop_front(Queue *q) { return q->items[q->head++]; }
static int queue_empty(const Queue *q) { return q->head == q->tail; }

static int queue_contains(const Queue *q, int node)
{
    for (int i = q->head; i < q->tail; i++) {
        if (q->items[i] == node) return 1;
    }
    return 0;
}
// lesson:end

/* Plumbing: the step trace. */
static void begin_step(const char *action, const char *line) { printf("step %s %s", action, line ? line : "-"); }
static void put_node(int i) { printf(" %s", names[i]); }
static void end_step(void) { printf(" |\n"); }

static int visited[MAX_NODES];
static int path[MAX_NODES];
static int path_len;

// lesson:start
void bfs(int start) {
    Queue queue = {{0}, 0, 0};
    queue_push(&queue, start);                                  // @start
    begin_step("enqueue", "start"); put_node(start); end_step(); // @hide
    while (!queue_empty(&queue)) {
        int node = queue_pop_front(&queue);                     // @pop
        if (!visited[node]) {
            visited[node] = 1;
            path[path_len++] = node;
            begin_step("visit", "pop"); put_node(node); end_step(); // @hide
            for (int k = 0; k < degree[node]; k++) {
                int next = neighbour[node][k];
                if (!visited[next] && !queue_contains(&queue, next)) { // @enqueue
                    queue_push(&queue, next);
                    begin_step("enqueue", "enqueue"); put_node(next); end_step(); // @hide
                }
            }
        }
    }
    begin_step("done", NULL);                                   // @hide
    for (int i = 0; i < path_len; i++) put_node(path[i]);       // @hide
    end_step();                                                 // @hide
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
        /* Keys first, in order, then names met only as neighbours. */
        node_count = 0;
        for (int i = 0; i < k; i++) node_index(keys[i]);
        for (int i = 0; i < k; i++) {
            int u = node_index(keys[i]);
            for (int j = 0; j < degrees[i]; j++) neighbour[u][degree[u]++] = node_index(lines[i][j]);
        }
        memset(visited, 0, sizeof visited);
        path_len = 0;
        bfs(node_index(start_name));
        printf("path");
        for (int i = 0; i < path_len; i++) printf(" %s", names[path[i]]);
        printf("\nend\n");
    }
    return 0;
}
