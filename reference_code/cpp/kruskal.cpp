// Kruskal in C++17, a translation of /run_kruskal in app.py.
// Input and output: reference_code/README.md, "Graph programs".
// Python's sorted() is stable, so equal weights keep their input order;
// std::stable_sort does the same, where std::sort would not promise it.
// Union-Find uses path halving and union by rank, as the endpoint does.
// Like the endpoint, the walk notes when the tree is complete and goes on.
#include <algorithm>
#include <iostream>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

// lesson:helpers
// Node names in input order; an edge refers to its ends by index.
static std::vector<std::string> names;
static std::unordered_map<std::string, int> index_of;

static int node_index(const std::string &name) {
    auto found = index_of.find(name);
    if (found != index_of.end()) return found->second;
    index_of[name] = static_cast<int>(names.size());
    names.push_back(name);
    return static_cast<int>(names.size()) - 1;
}

struct Edge { int u, v; long long w; };

// Union-Find with path halving and union by rank.
struct UnionFind {
    std::vector<int> parent, rank;
    explicit UnionFind(int n) : parent(static_cast<size_t>(n)), rank(static_cast<size_t>(n), 0) {
        for (int i = 0; i < n; i++) parent[i] = i;
    }
    int find(int x) {
        while (parent[x] != x) {
            parent[x] = parent[parent[x]];
            x = parent[x];
        }
        return x;
    }
    bool unite(int a, int b) {
        int ra = find(a), rb = find(b);
        if (ra == rb) return false;
        if (rank[ra] < rank[rb]) std::swap(ra, rb);
        parent[rb] = ra;
        if (rank[ra] == rank[rb]) rank[ra]++;
        return true;
    }
};
// lesson:end

// Plumbing: the step trace.
static void begin_step(const char *action, const char *line) { std::cout << "step " << action << ' ' << (line ? line : "-"); }
static void put_node(int i) { std::cout << ' ' << names[i]; }
static void put_bar() { std::cout << " |"; }
static void put_value(long long v) { std::cout << ' ' << v; }
static void end_step() { std::cout << '\n'; }

// lesson:start
std::vector<Edge> kruskal(std::vector<Edge> edges, int spanning_total) {
    std::stable_sort(edges.begin(), edges.end(), [](const Edge &a, const Edge &b) { return a.w < b.w; }); // @sort
    begin_step("milestone", "sort"); put_bar();                 // @hide
    for (const auto &edge : edges) put_value(edge.w);           // @hide
    end_step();                                                 // @hide
    UnionFind groups(static_cast<int>(names.size()));
    std::vector<Edge> tree;
    for (const auto &edge : edges) {
        begin_step("consider", "take-next"); put_node(edge.u); put_node(edge.v); put_bar(); put_value(edge.w); end_step(); // @hide
        if (groups.unite(edge.u, edge.v)) {                     // @take-next
            tree.push_back(edge);                               // @union
            begin_step("include", "union"); put_node(edge.u); put_node(edge.v); put_bar(); put_value(edge.w); end_step(); // @hide
            if (static_cast<int>(tree.size()) == spanning_total) { // @mst-complete
                begin_step("milestone", "mst-complete"); put_bar(); end_step(); // @hide
            }
        } else {                                                // @cycle
            begin_step("reject", "cycle"); put_node(edge.u); put_node(edge.v); put_bar(); put_value(edge.w); end_step(); // @hide
        }
    }
    return tree;
}
// lesson:end

int main() {
    std::ios::sync_with_stdio(false);
    int cases = 0;
    if (!(std::cin >> cases)) return 1;
    while (cases-- > 0) {
        std::string start, name, other;
        int k = 0, m = 0;
        if (!(std::cin >> start >> k)) return 1;
        names.clear();
        index_of.clear();
        std::vector<int> listed;
        for (int i = 0; i < k; i++) {
            int d = 0;
            if (!(std::cin >> name >> d)) return 1;
            listed.push_back(node_index(name));
            for (int j = 0; j < d; j++) {
                long long ignored = 0;
                if (!(std::cin >> other >> ignored)) return 1;
            }
        }
        if (!(std::cin >> m)) return 1;
        std::vector<Edge> edges;
        for (int e = 0; e < m; e++) {
            long long w = 0;
            if (!(std::cin >> name >> other >> w)) return 1;
            int u = node_index(name);
            int v = node_index(other);
            edges.push_back({u, v, w});
        }
        std::vector<Edge> tree = kruskal(edges, k > 1 ? k - 1 : 0);

        long long total = 0;
        for (const auto &edge : tree) total += edge.w;
        begin_step("done", nullptr);
        for (int i : listed) put_node(i);
        put_bar();
        put_value(total);
        end_step();
        for (const auto &edge : tree) {
            std::cout << "edge " << names[edge.u] << ' ' << names[edge.v] << ' ' << edge.w << '\n';
        }
        std::cout << "total " << total << "\nend\n";
    }
    return 0;
}
