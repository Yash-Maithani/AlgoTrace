// Prim in C++17, a translation of /run_prim in app.py.
// Input and output: reference_code/README.md, "Graph programs".
// The endpoint pushes (weight, u, v) tuples onto Python's heapq. Here the
// same tuples go into std::priority_queue, a binary heap, compared as whole
// tuples: weight, then u's name, then v's name. Every edge leaving a newly
// joined node is pushed, stale ones included: the lesson's O(E log E).
#include <algorithm>
#include <functional>
#include <iostream>
#include <queue>
#include <string>
#include <tuple>
#include <unordered_map>
#include <utility>
#include <vector>

// lesson:helpers
// The graph, as the endpoint receives it: nodes keep their input order,
// and every node's neighbours keep theirs, each with its weight.
static std::vector<std::string> names;
static std::unordered_map<std::string, int> index_of;
static std::vector<std::vector<std::pair<int, long long>>> neighbours;

static int node_index(const std::string &name) {
    auto found = index_of.find(name);
    if (found != index_of.end()) return found->second;
    index_of[name] = static_cast<int>(names.size());
    names.push_back(name);
    neighbours.emplace_back();
    return static_cast<int>(names.size()) - 1;
}

// A min-heap of (weight, u, v), compared as Python compares the tuple.
using Edge = std::tuple<long long, std::string, std::string>;
using MinHeap = std::priority_queue<Edge, std::vector<Edge>, std::greater<Edge>>;
// lesson:end

// Plumbing: the step trace.
static void begin_step(const char *action, const char *line) { std::cout << "step " << action << ' ' << (line ? line : "-"); }
static void put_name(const std::string &name) { std::cout << ' ' << name; }
static void put_bar() { std::cout << " |"; }
static void put_value(long long v) { std::cout << ' ' << v; }
static void end_step() { std::cout << '\n'; }

static std::vector<bool> visited;
static std::vector<Edge> tree;

// lesson:start
void prim(int start) {
    MinHeap heap;
    std::vector<std::string> frontier;                          // @hide
    visited[start] = true;                                      // @start
    begin_step("visit", "start"); put_name(names[start]); put_bar(); end_step(); // @hide
    for (const auto &[next, weight] : neighbours[start]) {
        heap.emplace(weight, names[start], names[next]);        // @push-edges
        if (!visited[next]) frontier.push_back(names[next]);    // @hide
    }
    if (!frontier.empty()) {                                    // @hide
        begin_step("enqueue", "push-edges");                    // @hide
        for (const auto &name : frontier) put_name(name);       // @hide
        put_bar(); end_step();                                  // @hide
    }                                                           // @hide
    while (!heap.empty()) {
        auto [weight, u, v] = heap.top();                       // @pop-min
        heap.pop();
        if (visited[index_of[v]]) {                             // @skip-visited
            begin_step("reject", "skip-visited"); put_name(u); put_name(v); put_bar(); put_value(weight); end_step(); // @hide
            continue;
        }
        begin_step("consider", "pop-min"); put_name(u); put_name(v); put_bar(); put_value(weight); end_step(); // @hide
        tree.emplace_back(weight, u, v);                        // @add-edge
        visited[index_of[v]] = true;
        begin_step("include", "add-edge"); put_name(u); put_name(v); put_bar(); put_value(weight); end_step(); // @hide
        frontier.clear();                                       // @hide
        for (const auto &[next, w] : neighbours[index_of[v]]) {
            if (!visited[next]) {
                heap.emplace(w, v, names[next]);                // @push-edges
                frontier.push_back(names[next]);                // @hide
            }
        }
        if (!frontier.empty()) {                                // @hide
            begin_step("enqueue", "push-edges");                // @hide
            for (const auto &name : frontier) put_name(name);   // @hide
            put_bar(); end_step();                              // @hide
        }                                                       // @hide
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
        int key_count = static_cast<int>(names.size());
        for (int i = 0; i < k; i++) {
            int u = node_index(keys[i]);
            for (const auto &[n, w] : lines[i]) {
                int v = node_index(n);
                neighbours[u].emplace_back(v, w);
            }
        }
        visited.assign(names.size(), false);
        tree.clear();
        prim(node_index(start_name));

        long long total = 0;
        for (const auto &edge : tree) total += std::get<0>(edge);
        std::vector<std::string> seen;
        for (int i = 0; i < key_count; i++) if (visited[i]) seen.push_back(names[i]);
        std::sort(seen.begin(), seen.end());
        begin_step("done", nullptr);
        for (const auto &s : seen) put_name(s);
        put_bar();
        put_value(total);
        end_step();
        for (const auto &[w, u, v] : tree) std::cout << "edge " << u << ' ' << v << ' ' << w << '\n';
        std::cout << "total " << total << "\nend\n";
    }
    return 0;
}
