// Bellman-Ford in C++17, a translation of algotrace/algorithms/graph/bellman_ford.py.
// Input and output: reference_code/README.md, "Graph programs".
// The graph is directed as given. Edges are swept in input order, at most
// V-1 times, stopping after a pass that changes nothing; one more sweep
// then reports whether anything could still improve, a negative cycle.
#include <algorithm>
#include <climits>
#include <iostream>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

static const long long INF = LLONG_MAX;

// lesson:helpers
// Node names: keys in input order, then names met only as neighbours.
static std::vector<std::string> names;
static std::unordered_map<std::string, int> index_of;

static int node_index(const std::string &name) {
    auto found = index_of.find(name);
    if (found != index_of.end()) return found->second;
    index_of[name] = static_cast<int>(names.size());
    names.push_back(name);
    return static_cast<int>(names.size()) - 1;
}

// The edge list, in the order the endpoint builds it: each key's
// neighbours in turn.
struct Edge { int u, v; long long w; };
// lesson:end

// Plumbing: the step trace.
static void begin_step(const char *action, const char *line) { std::cout << "step " << action << ' ' << (line ? line : "-"); }
static void put_node(int i) { std::cout << ' ' << names[i]; }
static void put_bar() { std::cout << " |"; }
static void put_value(long long v) { if (v == INF) std::cout << " \xE2\x88\x9E"; else std::cout << ' ' << v; }
static void end_step() { std::cout << '\n'; }

static std::vector<long long> dist;
static int iterations = 0;
static bool negative_cycle = false;

// lesson:start
void bellman_ford(const std::vector<Edge> &edges, int start) {
    int n = static_cast<int>(names.size());
    dist.assign(static_cast<size_t>(n), INF);
    dist[start] = 0;
    iterations = 0;
    for (int pass = 1; pass < std::max(n, 1); pass++) {
        iterations = pass;                                      // @hide
        bool changed = false;
        for (const auto &edge : edges) {                        // @edge-loop
            begin_step("consider", "edge-loop"); put_node(edge.u); put_node(edge.v); put_bar(); put_value(edge.w); end_step(); // @hide
            if (dist[edge.u] != INF && dist[edge.u] + edge.w < dist[edge.v]) { // @relax
                dist[edge.v] = dist[edge.u] + edge.w;
                changed = true;
                begin_step("relax", "relax"); put_node(edge.u); put_node(edge.v); put_bar(); put_value(dist[edge.v]); end_step(); // @hide
            } else {                                            // @no-improve
                begin_step("reject", "no-improve"); put_node(edge.u); put_node(edge.v); put_bar(); put_value(edge.w); end_step(); // @hide
            }
        }
        begin_step("milestone", "pass-done"); put_bar(); put_value(pass); end_step(); // @hide
        if (!changed) break;                                    // @pass-done
    }
    negative_cycle = std::any_of(edges.begin(), edges.end(), [](const Edge &edge) {
        return dist[edge.u] != INF && dist[edge.u] + edge.w < dist[edge.v];
    });
}
// lesson:end

int main() {
    std::ios::sync_with_stdio(false);
    int cases = 0;
    if (!(std::cin >> cases)) return 1;
    while (cases-- > 0) {
        std::string start_name, name, other;
        int k = 0, m = 0;
        if (!(std::cin >> start_name >> k)) return 1;
        std::vector<std::string> keys(static_cast<size_t>(k));
        std::vector<std::vector<std::pair<std::string, long long>>> lines(static_cast<size_t>(k));
        for (int i = 0; i < k; i++) {
            int d = 0;
            if (!(std::cin >> keys[i] >> d)) return 1;
            for (int j = 0; j < d; j++) {
                long long w = 0;
                if (!(std::cin >> name >> w)) return 1;
                lines[i].emplace_back(name, w);
            }
        }
        if (!(std::cin >> m)) return 1;
        for (int e = 0; e < m; e++) {
            long long ignored = 0;
            if (!(std::cin >> name >> other >> ignored)) return 1;
        }
        names.clear();
        index_of.clear();
        for (const auto &key : keys) node_index(key);
        std::vector<Edge> edges;
        for (int i = 0; i < k; i++) {
            int u = node_index(keys[i]);
            for (const auto &[n, w] : lines[i]) {
                int v = node_index(n);
                edges.push_back({u, v, w});
            }
        }
        bellman_ford(edges, node_index(start_name));

        std::vector<int> order;
        for (int i = 0; i < static_cast<int>(names.size()); i++) order.push_back(i);
        std::sort(order.begin(), order.end(), [](int a, int b) { return names[a] < names[b]; });
        for (int i : order) {
            std::cout << "distance " << names[i];
            put_value(dist[i]);
            std::cout << '\n';
        }
        std::cout << "negative_cycle " << (negative_cycle ? "true" : "false")
                  << "\niterations " << iterations << "\nend\n";
    }
    return 0;
}
