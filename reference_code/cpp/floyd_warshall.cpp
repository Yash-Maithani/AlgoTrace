// Floyd-Warshall in C++17, a translation of /run_floyd_warshall in app.py.
// Input and output: reference_code/README.md, "Graph programs".
// Edges are undirected and a parallel edge only replaces a dearer one.
// Three nested loops with nothing to cut them short: the lesson's V cubed.
#include <algorithm>
#include <climits>
#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>

static const long long INF = LLONG_MAX;

// lesson:helpers
// Node names in input order.
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
// lesson:end

// Plumbing: the step trace.
static void begin_step(const char *action, const char *line) { std::cout << "step " << action << ' ' << (line ? line : "-"); }
static void put_node(int i) { std::cout << ' ' << names[i]; }
static void put_bar() { std::cout << " |"; }
static void put_value(long long v) { if (v == INF) std::cout << " \xE2\x88\x9E"; else std::cout << ' ' << v; }
static void end_step() { std::cout << '\n'; }

static std::vector<std::vector<long long>> dist;
static std::vector<std::vector<int>> next_hop;

// lesson:start
void floyd_warshall(int n, const std::vector<Edge> &edges) {
    dist.assign(n, std::vector<long long>(n, INF));
    next_hop.assign(n, std::vector<int>(n, -1));
    for (int i = 0; i < n; i++) dist[i][i] = 0;
    for (const auto &edge : edges) {
        if (edge.w < dist[edge.u][edge.v]) {                    // keep the cheaper of parallel edges
            dist[edge.u][edge.v] = dist[edge.v][edge.u] = edge.w; // @init
            next_hop[edge.u][edge.v] = edge.v;
            next_hop[edge.v][edge.u] = edge.u;
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
        for (int i = 0; i < k; i++) {
            int d = 0;
            if (!(std::cin >> name >> d)) return 1;
            node_index(name);
            for (int j = 0; j < d; j++) {
                long long ignored = 0;
                if (!(std::cin >> other >> ignored)) return 1;
            }
        }
        int n = static_cast<int>(names.size());
        if (!(std::cin >> m)) return 1;
        std::vector<Edge> edges;
        for (int e = 0; e < m; e++) {
            long long w = 0;
            if (!(std::cin >> name >> other >> w)) return 1;
            int u = node_index(name);
            int v = node_index(other);
            edges.push_back({u, v, w});
        }
        floyd_warshall(n, edges);

        begin_step("done", nullptr);
        for (int i = 0; i < n; i++) put_node(i);
        put_bar();
        end_step();
        for (int i = 0; i < n; i++) {
            std::cout << "row " << names[i];
            for (int j = 0; j < n; j++) put_value(dist[i][j]);
            std::cout << '\n';
        }
        // One route per reachable ordered pair, by from then to name, the
        // order the endpoint's JSON sorts its "from -> to" keys into.
        std::vector<int> order;
        for (int i = 0; i < n; i++) order.push_back(i);
        std::sort(order.begin(), order.end(), [](int a, int b) { return names[a] < names[b]; });
        for (int i : order) {
            for (int j : order) {
                if (i == j || dist[i][j] == INF || next_hop[i][j] == -1) continue;
                std::vector<int> route = {i};
                while (route.back() != j && static_cast<int>(route.size()) <= n) {
                    int step_to = next_hop[route.back()][j];
                    if (step_to == -1) break;
                    route.push_back(step_to);
                }
                if (route.back() != j) continue;
                std::cout << "path " << names[i] << ' ' << names[j];
                put_value(dist[i][j]);
                for (int r : route) std::cout << ' ' << names[r];
                std::cout << '\n';
            }
        }
        std::cout << "end\n";
    }
    return 0;
}
