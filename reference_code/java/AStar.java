// A* on a grid in Java 17, a translation of algotrace/algorithms/grid/astar.py.
// Input and output: reference_code/README.md, "Grid programs". Moves go up,
// right, down, left at cost 1; h is the Manhattan distance, or 0 for
// Dijkstra. The heap is the same binary heap as the Python, ordered by
// lowest f, then lowest h, then push order, so it pops the same entries in
// the same order and makes the same number of comparisons.
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

public class AStar {
    // lesson:helpers
    // The grid and the four moves, in the order the Python tries them.
    static int rows, cols;
    static boolean[] wall;
    static final int[] MOVE_R = {-1, 0, 1, 0};
    static final int[] MOVE_C = {0, 1, 0, -1};
    static boolean manhattan;
    static int goalR, goalC;

    static int hOf(int cell) {
        if (!manhattan) return 0;
        return Math.abs(cell / cols - goalR) + Math.abs(cell % cols - goalC);
    }

    // One open set entry. `order` counts the pushes, so no two entries tie.
    record Entry(int f, int h, int order, int cell, int g) {}

    static List<Entry> heap = new ArrayList<>();
    static long comparisons;

    static boolean less(Entry a, Entry b) {
        comparisons++;
        if (a.f() != b.f()) return a.f() < b.f();
        if (a.h() != b.h()) return a.h() < b.h();
        return a.order() < b.order();
    }

    static void swap(int i, int j) {
        Entry t = heap.get(i);
        heap.set(i, heap.get(j));
        heap.set(j, t);
    }

    static void heapPush(Entry e) {
        heap.add(e);
        int i = heap.size() - 1;
        while (i > 0) {
            int parent = (i - 1) / 2;
            if (less(heap.get(i), heap.get(parent))) {
                swap(i, parent);
                i = parent;
            } else {
                break;
            }
        }
    }

    static Entry heapPop() {
        Entry top = heap.get(0);
        Entry last = heap.remove(heap.size() - 1);
        if (!heap.isEmpty()) {
            heap.set(0, last);
            int i = 0, n = heap.size();
            while (true) {
                int left = 2 * i + 1, right = 2 * i + 2, best = i;
                if (left < n && less(heap.get(left), heap.get(best))) best = left;
                if (right < n && less(heap.get(right), heap.get(best))) best = right;
                if (best == i) break;
                swap(i, best);
                i = best;
            }
        }
        return top;
    }
    // lesson:end

    // Plumbing: the step trace, with cells named r,c as the site names them.
    static final StringBuilder out = new StringBuilder();

    static String name(int cell) { return (cell / cols) + "," + (cell % cols); }

    static void trace(String action, String line, List<Integer> cells, int... values) {
        out.append("step ").append(action).append(' ').append(line);
        for (int c : cells) out.append(' ').append(name(c));
        out.append(" |");
        for (int v : values) out.append(' ').append(v);
        out.append('\n');
    }

    static List<Integer> path = new ArrayList<>();
    static int expanded;

    // lesson:start
    static boolean astar(int start, int goal) {
        int[] g = new int[rows * cols];
        int[] cameFrom = new int[rows * cols];
        boolean[] closed = new boolean[rows * cols];
        java.util.Arrays.fill(g, -1);
        g[start] = 0;
        int order = 0;
        heapPush(new Entry(hOf(start), hOf(start), 0, start, 0));          // @push-start
        trace("enqueue", "push-start", List.of(start), 0, hOf(start));     // @hide
        while (!heap.isEmpty()) {
            Entry e = heapPop();
            if (closed[e.cell()] || g[e.cell()] != e.g()) {
                trace("reject", "stale", List.of(e.cell()), e.g(), e.h()); // @hide
                continue;                                                  // @stale
            }
            closed[e.cell()] = true;                                       // @expand
            expanded++;                                                    // @hide
            trace("visit", "expand", List.of(e.cell()), e.g(), e.h());     // @hide
            if (e.cell() == goal) {
                path.clear();                                              // @path
                for (int at = goal; at != start; at = cameFrom[at]) path.add(0, at);
                path.add(0, start);
                trace("done", "path", path, path.size() - 1);              // @hide
                return true;
            }
            int r = e.cell() / cols, c = e.cell() % cols;
            for (int m = 0; m < 4; m++) {
                int nr = r + MOVE_R[m], nc = c + MOVE_C[m];
                if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue;
                int nb = nr * cols + nc;
                if (wall[nb] || closed[nb]) continue;
                if (g[nb] < 0 || e.g() + 1 < g[nb]) {                      // @improve
                    boolean improved = g[nb] >= 0;                         // @hide
                    g[nb] = e.g() + 1;
                    cameFrom[nb] = e.cell();
                    order++;
                    heapPush(new Entry(g[nb] + hOf(nb), hOf(nb), order, nb, g[nb])); // @push
                    trace(improved ? "relax" : "enqueue", improved ? "improve" : "push", List.of(nb, e.cell()), g[nb], hOf(nb)); // @hide
                }
            }
        }
        trace("done", "no-path", List.of(), expanded);                     // @hide
        return false;                                                      // @no-path
    }
    // lesson:end

    public static void main(String[] args) throws IOException {
        String[] in = new String(System.in.readAllBytes(), StandardCharsets.UTF_8).trim().split("\\s+");
        int p = 0;
        int cases = Integer.parseInt(in[p++]);
        for (int k = 0; k < cases; k++) {
            String heuristic = in[p++];
            rows = Integer.parseInt(in[p++]);
            cols = Integer.parseInt(in[p++]);
            if (!heuristic.equals("manhattan") && !heuristic.equals("zero")) {
                System.out.print(out);
                System.out.println("error unknown heuristic " + heuristic);
                System.exit(2);
            }
            manhattan = heuristic.equals("manhattan");
            int sr = Integer.parseInt(in[p++]), sc = Integer.parseInt(in[p++]);
            int gr = Integer.parseInt(in[p++]), gc = Integer.parseInt(in[p++]);
            wall = new boolean[rows * cols];
            for (int r = 0; r < rows; r++) {
                String line = in[p++];
                for (int c = 0; c < cols; c++) wall[r * cols + c] = line.charAt(c) == '#';
            }
            goalR = gr;
            goalC = gc;
            heap = new ArrayList<>();
            comparisons = 0;
            expanded = 0;
            path = new ArrayList<>();
            boolean found = astar(sr * cols + sc, gr * cols + gc);
            out.append("path");
            if (found) for (int cell : path) out.append(' ').append(name(cell));
            out.append("\nexpanded ").append(expanded)
               .append("\ncomparisons ").append(comparisons).append("\nend\n");
        }
        System.out.print(out);
    }
}
