// A* on a grid in C++17, a translation of algotrace/algorithms/grid/astar.py.
// Input and output: reference_code/README.md, "Grid programs". Moves go up,
// right, down, left at cost 1; h is the Manhattan distance, or 0 for
// Dijkstra. The heap is the same binary heap as the Python, ordered by
// lowest f, then lowest h, then push order, so it pops the same entries in
// the same order and makes the same number of comparisons.
#include <cstdlib>
#include <iostream>
#include <string>
#include <utility>
#include <vector>

// lesson:helpers
// The grid and the four moves, in the order the Python tries them.
static int rows = 0, cols = 0;
static std::vector<bool> wall;
static const int MOVE_R[4] = {-1, 0, 1, 0};
static const int MOVE_C[4] = {0, 1, 0, -1};
static bool manhattan = true;
static int goal_r = 0, goal_c = 0;

static int h_of(int cell)
{
    if (!manhattan) return 0;
    return std::abs(cell / cols - goal_r) + std::abs(cell % cols - goal_c);
}

// One open set entry. `order` counts the pushes, so no two entries tie.
struct Entry { int f, h, order, cell, g; };

static std::vector<Entry> heap;
static long comparisons = 0;

static bool less(const Entry &a, const Entry &b)
{
    comparisons++;
    if (a.f != b.f) return a.f < b.f;
    if (a.h != b.h) return a.h < b.h;
    return a.order < b.order;
}

static void heap_push(const Entry &e)
{
    heap.push_back(e);
    size_t i = heap.size() - 1;
    while (i > 0) {
        size_t parent = (i - 1) / 2;
        if (less(heap[i], heap[parent])) {
            std::swap(heap[i], heap[parent]);
            i = parent;
        } else {
            break;
        }
    }
}

static Entry heap_pop()
{
    Entry top = heap[0];
    Entry last = heap.back();
    heap.pop_back();
    if (!heap.empty()) {
        heap[0] = last;
        size_t i = 0, n = heap.size();
        for (;;) {
            size_t left = 2 * i + 1, right = 2 * i + 2, best = i;
            if (left < n && less(heap[left], heap[best])) best = left;
            if (right < n && less(heap[right], heap[best])) best = right;
            if (best == i) break;
            std::swap(heap[i], heap[best]);
            i = best;
        }
    }
    return top;
}
// lesson:end

// Plumbing: the step trace, with cells named r,c as the site names them.
static std::string name(int cell) { return std::to_string(cell / cols) + "," + std::to_string(cell % cols); }
static void trace(const char *action, const char *line, const std::vector<int> &cells, const std::vector<int> &values)
{
    std::cout << "step " << action << ' ' << line;
    for (int c : cells) std::cout << ' ' << name(c);
    std::cout << " |";
    for (int v : values) std::cout << ' ' << v;
    std::cout << '\n';
}

static std::vector<int> path;
static int expanded = 0;

// lesson:start
bool astar(int start, int goal) {
    std::vector<int> g(rows * cols, -1), came_from(rows * cols, -1);
    std::vector<bool> closed(rows * cols, false);
    g[start] = 0;
    int order = 0;
    heap_push({h_of(start), h_of(start), 0, start, 0});                 // @push-start
    trace("enqueue", "push-start", {start}, {0, h_of(start)});          // @hide
    while (!heap.empty()) {
        Entry e = heap_pop();
        if (closed[e.cell] || g[e.cell] != e.g) {
            trace("reject", "stale", {e.cell}, {e.g, e.h});             // @hide
            continue;                                                   // @stale
        }
        closed[e.cell] = true;                                          // @expand
        expanded++;                                                     // @hide
        trace("visit", "expand", {e.cell}, {e.g, e.h});                 // @hide
        if (e.cell == goal) {
            path.clear();                                               // @path
            for (int at = goal; at != start; at = came_from[at]) path.insert(path.begin(), at);
            path.insert(path.begin(), start);
            trace("done", "path", path, {static_cast<int>(path.size()) - 1}); // @hide
            return true;
        }
        int r = e.cell / cols, c = e.cell % cols;
        for (int m = 0; m < 4; m++) {
            int nr = r + MOVE_R[m], nc = c + MOVE_C[m];
            if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue;
            int nb = nr * cols + nc;
            if (wall[nb] || closed[nb]) continue;
            if (g[nb] < 0 || e.g + 1 < g[nb]) {                         // @improve
                bool improved = g[nb] >= 0;                             // @hide
                g[nb] = e.g + 1;
                came_from[nb] = e.cell;
                order++;
                heap_push({g[nb] + h_of(nb), h_of(nb), order, nb, g[nb]}); // @push
                trace(improved ? "relax" : "enqueue", improved ? "improve" : "push", {nb, e.cell}, {g[nb], h_of(nb)}); // @hide
            }
        }
    }
    trace("done", "no-path", {}, {expanded});                           // @hide
    return false;                                                       // @no-path
}
// lesson:end

int main()
{
    std::ios::sync_with_stdio(false);
    int cases = 0;
    if (!(std::cin >> cases)) return 1;
    while (cases-- > 0) {
        std::string heuristic;
        int sr, sc, gr, gc;
        if (!(std::cin >> heuristic >> rows >> cols)) return 1;
        if (heuristic != "manhattan" && heuristic != "zero") {
            std::cout << "error unknown heuristic " << heuristic << '\n';
            return 2;
        }
        manhattan = heuristic == "manhattan";
        if (!(std::cin >> sr >> sc >> gr >> gc)) return 1;
        wall.assign(rows * cols, false);
        for (int r = 0; r < rows; r++) {
            std::string line;
            if (!(std::cin >> line)) return 1;
            for (int c = 0; c < cols; c++) wall[r * cols + c] = line[c] == '#';
        }
        goal_r = gr;
        goal_c = gc;
        heap.clear();
        comparisons = 0;
        expanded = 0;
        path.clear();
        bool found = astar(sr * cols + sc, gr * cols + gc);
        std::cout << "path";
        if (found) for (int cell : path) std::cout << ' ' << name(cell);
        std::cout << "\nexpanded " << expanded << "\ncomparisons " << comparisons << "\nend\n";
    }
    return 0;
}
