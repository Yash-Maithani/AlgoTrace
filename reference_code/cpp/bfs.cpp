// Breadth-First Search in C++17, a translation of algotrace/algorithms/graph/bfs.py.
// Input and output: reference_code/README.md, "Graph programs".
// Like the endpoint, `not in queue` scans the queue, so the membership test
// is linear: the lesson's O(V times E).
#include <algorithm>
#include <deque>
#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>

// lesson:helpers
// The graph, as the endpoint receives it: nodes keep their input order,
// and every node's neighbours keep theirs.
static std::vector<std::string> names;
static std::unordered_map<std::string, int> index_of;
static std::vector<std::vector<int>> neighbours;

static int node_index(const std::string &name) {
    auto found = index_of.find(name);
    if (found != index_of.end()) return found->second;
    index_of[name] = static_cast<int>(names.size());
    names.push_back(name);
    neighbours.emplace_back();
    return static_cast<int>(names.size()) - 1;
}
// lesson:end

// Plumbing: the step trace.
static void begin_step(const char *action, const char *line) { std::cout << "step " << action << ' ' << (line ? line : "-"); }
static void put_node(int i) { std::cout << ' ' << names[i]; }
static void end_step() { std::cout << " |\n"; }

// lesson:start
std::vector<int> bfs(int start) {
    std::vector<bool> visited(names.size(), false);
    std::vector<int> path;
    std::deque<int> queue = {start};                            // @start
    begin_step("enqueue", "start"); put_node(start); end_step(); // @hide
    while (!queue.empty()) {
        int node = queue.front();                               // @pop
        queue.pop_front();
        if (!visited[node]) {
            visited[node] = true;
            path.push_back(node);
            begin_step("visit", "pop"); put_node(node); end_step(); // @hide
            for (int next : neighbours[node]) {
                if (!visited[next] && std::find(queue.begin(), queue.end(), next) == queue.end()) { // @enqueue
                    queue.push_back(next);
                    begin_step("enqueue", "enqueue"); put_node(next); end_step(); // @hide
                }
            }
        }
    }
    begin_step("done", nullptr);                                // @hide
    for (int node : path) put_node(node);                       // @hide
    end_step();                                                 // @hide
    return path;
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
        std::vector<std::string> keys(static_cast<size_t>(k));
        std::vector<std::vector<std::string>> lines(static_cast<size_t>(k));
        for (int i = 0; i < k; i++) {
            int d = 0;
            if (!(std::cin >> keys[i] >> d)) return 1;
            for (int j = 0; j < d; j++) {
                long long ignored = 0;
                if (!(std::cin >> name >> ignored)) return 1;
                lines[i].push_back(name);
            }
        }
        if (!(std::cin >> m)) return 1;
        for (int e = 0; e < m; e++) {
            long long ignored = 0;
            if (!(std::cin >> name >> other >> ignored)) return 1;
        }
        // Keys first, in order, then names met only as neighbours.
        names.clear();
        index_of.clear();
        neighbours.clear();
        for (const auto &key : keys) node_index(key);
        for (int i = 0; i < k; i++) {
            int u = node_index(keys[i]);
            for (const auto &n : lines[i]) {
                int v = node_index(n);
                neighbours[u].push_back(v);
            }
        }
        std::vector<int> path = bfs(node_index(start));
        std::cout << "path";
        for (int node : path) std::cout << ' ' << names[node];
        std::cout << "\nend\n";
    }
    return 0;
}
