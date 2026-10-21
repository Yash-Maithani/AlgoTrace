// Topological Sort (Kahn's algorithm) in C++17, a translation of
// algotrace/algorithms/graph/topological_sort.py. Input and output: reference_code/README.md,
// "Graph programs". The queue is a std::deque, as the endpoint's is, so
// taking from the front is O(1): the lesson's O(V plus E).
#include <deque>
#include <iostream>
#include <string>
#include <vector>

// lesson:helpers
// The graph, as the endpoint receives it: nodes keep their input order, and
// every node's arrows keep theirs.
static std::vector<std::string> names;
static std::vector<std::vector<int>> arrows;

static int node_index(const std::string &name)
{
    for (size_t i = 0; i < names.size(); i++) {
        if (names[i] == name) return static_cast<int>(i);
    }
    names.push_back(name);
    arrows.emplace_back();
    return static_cast<int>(names.size()) - 1;
}

// One cycle among the nodes left over, as the endpoint finds it: walk back
// along the first arrow (in input order) that comes into each node from
// another node left over, until a node repeats; then turn the loop round to
// the direction the arrows point and start it at its earliest node.
static std::vector<int> find_cycle(const std::vector<bool> &left)
{
    int n = static_cast<int>(names.size());
    std::vector<int> first_in(n, -1);
    for (int u = 0; u < n; u++) {
        if (!left[u]) continue;
        for (int v : arrows[u]) {
            if (left[v] && first_in[v] < 0) first_in[v] = u;
        }
    }
    int node = 0;
    while (!left[node]) node++;
    std::vector<bool> seen(n, false);
    std::vector<int> walk;
    while (!seen[node]) {
        seen[node] = true;
        walk.push_back(node);
        node = first_in[node];
    }
    size_t from = 0;
    while (walk[from] != node) from++;
    std::vector<int> loop(walk.rbegin(), walk.rend() - static_cast<long>(from));
    size_t first = 0;
    for (size_t k = 1; k < loop.size(); k++) {
        if (loop[k] < loop[first]) first = k;
    }
    std::vector<int> turned;
    for (size_t k = 0; k < loop.size(); k++) turned.push_back(loop[(first + k) % loop.size()]);
    return turned;
}
// lesson:end

// Plumbing: the step trace.
static void trace(const char *action, const char *line, const std::vector<int> &nodes,
                  const std::vector<int> &values)
{
    std::cout << "step " << action << ' ' << (line ? line : "-");
    for (int u : nodes) std::cout << ' ' << names[u];
    std::cout << " |";
    for (int v : values) std::cout << ' ' << v;
    std::cout << '\n';
}

static std::vector<int> order;
static std::vector<bool> left_over;
static std::vector<int> cycle;

// lesson:start
void topological_sort() {
    int n = static_cast<int>(names.size());
    std::vector<int> in_degree(n, 0);
    for (int u = 0; u < n; u++) {
        for (int v : arrows[u]) {
            in_degree[v]++;                                     // @count
            trace("consider", "count", {u, v}, {in_degree[v]}); // @hide
        }
    }
    std::deque<int> queue;
    for (int u = 0; u < n; u++) {
        if (in_degree[u] == 0) {
            queue.push_back(u);                                 // @seed
            trace("enqueue", "seed", {u}, {0});                 // @hide
        }
    }
    while (!queue.empty()) {
        int u = queue.front();                                  // @remove
        queue.pop_front();
        order.push_back(u);
        trace("visit", "remove", {u}, {static_cast<int>(order.size())}); // @hide
        for (int v : arrows[u]) {
            in_degree[v]--;                                     // @decrement
            trace("consider", "decrement", {u, v}, {in_degree[v]}); // @hide
            if (in_degree[v] == 0) {
                queue.push_back(v);                             // @enqueue
                trace("enqueue", "enqueue", {v}, {0});          // @hide
            }
        }
    }
    if (static_cast<int>(order.size()) < n) {
        for (int u = 0; u < n; u++) left_over[u] = in_degree[u] > 0; // @cycle
        cycle = find_cycle(left_over);
    }
    std::vector<int> shown;                                     // @hide
    for (int u = 0; u < n; u++) {                               // @hide
        if (!cycle.empty() && left_over[u]) shown.push_back(u); // @hide
    }                                                           // @hide
    if (cycle.empty()) shown = order;                           // @hide
    trace("done", cycle.empty() ? nullptr : "cycle", shown, {}); // @hide
}
// lesson:end

int main()
{
    std::ios::sync_with_stdio(false);
    int cases = 0;
    if (!(std::cin >> cases)) return 1;
    while (cases-- > 0) {
        std::string start, name;
        int k = 0, m = 0;
        if (!(std::cin >> start >> k)) return 1;
        std::vector<std::string> keys(static_cast<size_t>(k));
        std::vector<std::vector<std::string>> lists(static_cast<size_t>(k));
        for (int i = 0; i < k; i++) {
            int d = 0;
            if (!(std::cin >> keys[i] >> d)) return 1;
            for (int j = 0; j < d; j++) {
                long long ignored = 0;
                if (!(std::cin >> name >> ignored)) return 1;
                lists[i].push_back(name);
            }
        }
        if (!(std::cin >> m)) return 1;
        for (int e = 0; e < m; e++) {
            long long ignored = 0;
            if (!(std::cin >> name >> name >> ignored)) return 1;
        }
        names.clear();
        arrows.clear();
        for (const std::string &key : keys) node_index(key);
        for (int i = 0; i < k; i++) {
            int u = node_index(keys[i]);
            for (const std::string &target : lists[i]) {
                int v = node_index(target);
                arrows[u].push_back(v);
            }
        }
        order.clear();
        cycle.clear();
        left_over.assign(names.size(), false);
        topological_sort();
        std::cout << "order";
        for (int u : order) std::cout << ' ' << names[u];
        std::cout << "\nremaining";
        for (size_t u = 0; u < names.size(); u++) if (left_over[u]) std::cout << ' ' << names[u];
        std::cout << "\ncycle";
        for (int u : cycle) std::cout << ' ' << names[u];
        std::cout << "\nend\n";
    }
    return 0;
}
