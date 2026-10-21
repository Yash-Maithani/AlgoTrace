// Dijkstra in C++17, a translation of algotrace/algorithms/graph/dijkstra.py.
// Input and output: reference_code/README.md, "Graph programs".
// The nearest node is found by a linear scan over the nodes in input order,
// taking the first smallest, exactly as the endpoint's min() does, so ties
// break the same way and the lesson's O(V squared) holds.
#include <algorithm>
#include <climits>
#include <iostream>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

static const long long INF = LLONG_MAX;

// lesson:helpers
// The graph, as the endpoint receives it: nodes keep their input order,
// and every node's neighbours keep theirs, each with its weight. The first
// key_count nodes are the ones with a line of their own.
static std::vector<std::string> names;
static std::unordered_map<std::string, int> index_of;
static std::vector<std::vector<std::pair<int, long long>>> neighbours;
static int key_count = 0;

static int node_index(const std::string &name) {
    auto found = index_of.find(name);
    if (found != index_of.end()) return found->second;
    index_of[name] = static_cast<int>(names.size());
    names.push_back(name);
    neighbours.emplace_back();
    return static_cast<int>(names.size()) - 1;
}

// Node indices in order of their names, as Python's sorted() puts them.
static std::vector<int> by_name(std::vector<int> items) {
    std::sort(items.begin(), items.end(), [](int a, int b) { return names[a] < names[b]; });
    return items;
}
// lesson:end

// Plumbing: the step trace.
static void begin_step(const char *action, const char *line) { std::cout << "step " << action << ' ' << (line ? line : "-"); }
static void put_node(int i) { std::cout << ' ' << names[i]; }
static void put_bar() { std::cout << " |"; }
static void put_value(long long v) { if (v == INF) std::cout << " \xE2\x88\x9E"; else std::cout << ' ' << v; }
static void end_step() { std::cout << '\n'; }

static std::vector<long long> dist;
static std::vector<int> previous;

// lesson:start
void dijkstra(int start) {
    dist.assign(key_count, INF);
    previous.assign(key_count, -1);
    std::vector<bool> unvisited(key_count, true);
    dist[start] = 0;
    int remaining = key_count;
    while (remaining > 0) {
        int current = -1;
        for (int i = 0; i < key_count; i++) {
            if (unvisited[i] && (current == -1 || dist[i] < dist[current])) current = i; // @pick-min
        }
        if (dist[current] == INF) break;
        unvisited[current] = false;
        remaining--;
        begin_step("visit", "pick-min"); put_node(current); put_bar(); put_value(dist[current]); end_step(); // @hide
        for (const auto &[next, weight] : neighbours[current]) {
            if (next < key_count && unvisited[next]) {
                long long through = dist[current] + weight;
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
        neighbours.clear();
        for (const auto &key : keys) node_index(key);
        key_count = static_cast<int>(names.size());
        for (int i = 0; i < k; i++) {
            int u = node_index(keys[i]);
            for (const auto &[n, w] : lines[i]) {
                int v = node_index(n);
                neighbours[u].emplace_back(v, w);
            }
        }
        int start = node_index(start_name);
        dijkstra(start);

        std::vector<int> all;
        for (int i = 0; i < key_count; i++) all.push_back(i);
        std::vector<int> order = by_name(all);
        begin_step("done", nullptr);
        for (int i : order) put_node(i);
        put_bar();
        end_step();
        // The result as the endpoint sends it: its JSON sorts object keys,
        // so both maps arrive in order of node name.
        for (int i : order) {
            std::cout << "distance " << names[i];
            put_value(dist[i]);
            std::cout << '\n';
        }
        for (int i : order) {
            if (i == start || dist[i] == INF) continue;
            std::vector<int> route;
            for (int at = i; at != -1; at = previous[at]) route.push_back(at);
            if (route.back() != start) continue;
            std::cout << "path " << names[i];
            for (auto it = route.rbegin(); it != route.rend(); ++it) std::cout << ' ' << names[*it];
            std::cout << '\n';
        }
        std::cout << "end\n";
    }
    return 0;
}
