/* Kruskal in C11, a translation of algotrace/algorithms/graph/kruskal.py.
 * Input and output: reference_code/README.md, "Graph programs".
 * Python's sorted() is stable: edges of equal weight keep their input
 * order. C's qsort promises no such thing, so the edges are sorted here
 * with a stable insertion sort. Union-Find uses path halving and union by
 * rank, as the endpoint does. Like the endpoint, the walk does not stop
 * when the tree is complete: it notes it and looks at the rest.
 */
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_NODES 256
#define MAX_EDGES 4096

// lesson:helpers
/* Node names in input order; an edge refers to its ends by index. */
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

typedef struct { int u, v; long long w; } Edge;

/* A stable sort by weight: equal weights keep their input order, as
   Python's sorted(edges, key=weight) does. */
static void sort_by_weight(Edge edges[], int count)
{
    for (int i = 1; i < count; i++) {
        Edge item = edges[i];
        int j = i - 1;
        while (j >= 0 && edges[j].w > item.w) {
            edges[j + 1] = edges[j];
            j--;
        }
        edges[j + 1] = item;
    }
}

/* Union-Find with path halving and union by rank. */
static int parent[MAX_NODES];
static int rank_of[MAX_NODES];

static int find(int x)
{
    while (parent[x] != x) {
        parent[x] = parent[parent[x]];
        x = parent[x];
    }
    return x;
}

static int unite(int a, int b)
{
    int ra = find(a), rb = find(b);
    if (ra == rb) return 0;
    if (rank_of[ra] < rank_of[rb]) {
        int t = ra;
        ra = rb;
        rb = t;
    }
    parent[rb] = ra;
    if (rank_of[ra] == rank_of[rb]) rank_of[ra]++;
    return 1;
}
// lesson:end

/* Plumbing: the step trace. */
static void begin_step(const char *action, const char *line) { printf("step %s %s", action, line ? line : "-"); }
static void put_node(int i) { printf(" %s", names[i]); }
static void put_bar(void) { printf(" |"); }
static void put_value(long long v) { printf(" %lld", v); }
static void end_step(void) { printf("\n"); }

static Edge tree[MAX_NODES];
static int tree_size;

// lesson:start
void kruskal(Edge edges[], int edge_count, int spanning_total) {
    sort_by_weight(edges, edge_count);                          // @sort
    begin_step("milestone", "sort"); put_bar();                 // @hide
    for (int e = 0; e < edge_count; e++) put_value(edges[e].w); // @hide
    end_step();                                                 // @hide
    for (int e = 0; e < edge_count; e++) {
        Edge edge = edges[e];
        begin_step("consider", "take-next"); put_node(edge.u); put_node(edge.v); put_bar(); put_value(edge.w); end_step(); // @hide
        if (unite(edge.u, edge.v)) {                            // @take-next
            tree[tree_size++] = edge;                           // @union
            begin_step("include", "union"); put_node(edge.u); put_node(edge.v); put_bar(); put_value(edge.w); end_step(); // @hide
            if (tree_size == spanning_total) {                  // @mst-complete
                begin_step("milestone", "mst-complete"); put_bar(); end_step(); // @hide
            }
        } else {                                                // @cycle
            begin_step("reject", "cycle"); put_node(edge.u); put_node(edge.v); put_bar(); put_value(edge.w); end_step(); // @hide
        }
    }
}
// lesson:end

int main(void)
{
    int cases;
    if (scanf("%d", &cases) != 1) return 1;
    while (cases-- > 0) {
        char start_name[64], name[64], other[64];
        static int listed[MAX_NODES];
        static Edge edges[MAX_EDGES];
        int k, m, d;
        if (scanf("%63s %d", start_name, &k) != 2) return 1;
        node_count = 0;
        for (int i = 0; i < k; i++) {
            if (scanf("%63s %d", name, &d) != 2) return 1;
            listed[i] = node_index(name);
            for (int j = 0; j < d; j++) {
                long long ignored;
                if (scanf("%63s %lld", other, &ignored) != 2) return 1;
            }
        }
        if (scanf("%d", &m) != 1) return 1;
        for (int e = 0; e < m; e++) {
            if (scanf("%63s %63s %lld", name, other, &edges[e].w) != 3) return 1;
            edges[e].u = node_index(name);
            edges[e].v = node_index(other);
        }
        for (int i = 0; i < node_count; i++) {
            parent[i] = i;
            rank_of[i] = 0;
        }
        tree_size = 0;
        kruskal(edges, m, k > 1 ? k - 1 : 0);

        long long total = 0;
        for (int t = 0; t < tree_size; t++) total += tree[t].w;
        begin_step("done", NULL);
        for (int i = 0; i < k; i++) put_node(listed[i]);
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
