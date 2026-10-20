// Topological Sort (Kahn's algorithm) in Java 17, a translation of
// /run_topological_sort in app.py. Input and output: reference_code/README.md,
// "Graph programs". The queue is an ArrayDeque, as the endpoint's is a deque,
// so taking from the front is O(1): the lesson's O(V plus E).
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;

public class TopologicalSort {
    // lesson:helpers
    // The graph, as the endpoint receives it: nodes keep their input order,
    // and every node's arrows keep theirs.
    static List<String> names = new ArrayList<>();
    static List<List<Integer>> arrows = new ArrayList<>();

    static int nodeIndex(String name) {
        int at = names.indexOf(name);
        if (at >= 0) return at;
        names.add(name);
        arrows.add(new ArrayList<>());
        return names.size() - 1;
    }

    // One cycle among the nodes left over, as the endpoint finds it: walk
    // back along the first arrow (in input order) that comes into each node
    // from another node left over, until a node repeats; then turn the loop
    // round to the direction the arrows point and start it at its earliest node.
    static List<Integer> findCycle(boolean[] left) {
        int n = names.size();
        int[] firstIn = new int[n];
        java.util.Arrays.fill(firstIn, -1);
        for (int u = 0; u < n; u++) {
            if (!left[u]) continue;
            for (int v : arrows.get(u)) {
                if (left[v] && firstIn[v] < 0) firstIn[v] = u;
            }
        }
        int node = 0;
        while (!left[node]) node++;
        boolean[] seen = new boolean[n];
        List<Integer> walk = new ArrayList<>();
        while (!seen[node]) {
            seen[node] = true;
            walk.add(node);
            node = firstIn[node];
        }
        int from = walk.indexOf(node);
        List<Integer> loop = new ArrayList<>();
        for (int k = walk.size() - 1; k >= from; k--) loop.add(walk.get(k));
        int first = 0;
        for (int k = 1; k < loop.size(); k++) {
            if (loop.get(k) < loop.get(first)) first = k;
        }
        List<Integer> turned = new ArrayList<>();
        for (int k = 0; k < loop.size(); k++) turned.add(loop.get((first + k) % loop.size()));
        return turned;
    }
    // lesson:end

    // Plumbing: the step trace.
    static final StringBuilder out = new StringBuilder();

    static void trace(String action, String line, List<Integer> nodes, int... values) {
        out.append("step ").append(action).append(' ').append(line == null ? "-" : line);
        for (int u : nodes) out.append(' ').append(names.get(u));
        out.append(" |");
        for (int v : values) out.append(' ').append(v);
        out.append('\n');
    }

    static List<Integer> order = new ArrayList<>();
    static boolean[] leftOver = new boolean[0];
    static List<Integer> cycle = new ArrayList<>();

    // lesson:start
    static void topologicalSort() {
        int n = names.size();
        int[] inDegree = new int[n];
        for (int u = 0; u < n; u++) {
            for (int v : arrows.get(u)) {
                inDegree[v]++;                                      // @count
                trace("consider", "count", List.of(u, v), inDegree[v]); // @hide
            }
        }
        ArrayDeque<Integer> queue = new ArrayDeque<>();
        for (int u = 0; u < n; u++) {
            if (inDegree[u] == 0) {
                queue.addLast(u);                                   // @seed
                trace("enqueue", "seed", List.of(u), 0);            // @hide
            }
        }
        while (!queue.isEmpty()) {
            int u = queue.pollFirst();                              // @remove
            order.add(u);
            trace("visit", "remove", List.of(u), order.size());     // @hide
            for (int v : arrows.get(u)) {
                inDegree[v]--;                                      // @decrement
                trace("consider", "decrement", List.of(u, v), inDegree[v]); // @hide
                if (inDegree[v] == 0) {
                    queue.addLast(v);                               // @enqueue
                    trace("enqueue", "enqueue", List.of(v), 0);     // @hide
                }
            }
        }
        if (order.size() < n) {
            for (int u = 0; u < n; u++) leftOver[u] = inDegree[u] > 0; // @cycle
            cycle = findCycle(leftOver);
        }
        List<Integer> shown = new ArrayList<>();                    // @hide
        for (int u = 0; u < n; u++) {                               // @hide
            if (!cycle.isEmpty() && leftOver[u]) shown.add(u);      // @hide
        }                                                           // @hide
        if (cycle.isEmpty()) shown = order;                         // @hide
        trace("done", cycle.isEmpty() ? null : "cycle", shown);     // @hide
    }
    // lesson:end

    public static void main(String[] args) throws IOException {
        String[] in = new String(System.in.readAllBytes(), StandardCharsets.UTF_8).trim().split("\\s+");
        int p = 0;
        int cases = Integer.parseInt(in[p++]);
        for (int c = 0; c < cases; c++) {
            p++;                                     // the start node is not used here
            int k = Integer.parseInt(in[p++]);
            String[] keys = new String[k];
            List<List<String>> lists = new ArrayList<>();
            for (int i = 0; i < k; i++) {
                keys[i] = in[p++];
                int d = Integer.parseInt(in[p++]);
                List<String> list = new ArrayList<>();
                for (int j = 0; j < d; j++) {
                    list.add(in[p++]);
                    p++;                             // the weight placeholder
                }
                lists.add(list);
            }
            int m = Integer.parseInt(in[p++]);
            p += 3 * m;
            names = new ArrayList<>();
            arrows = new ArrayList<>();
            for (String key : keys) nodeIndex(key);
            for (int i = 0; i < k; i++) {
                int u = nodeIndex(keys[i]);
                for (String target : lists.get(i)) {
                    int v = nodeIndex(target);
                    arrows.get(u).add(v);
                }
            }
            order = new ArrayList<>();
            cycle = new ArrayList<>();
            leftOver = new boolean[names.size()];
            topologicalSort();
            out.append("order");
            for (int u : order) out.append(' ').append(names.get(u));
            out.append("\nremaining");
            for (int u = 0; u < names.size(); u++) if (leftOver[u]) out.append(' ').append(names.get(u));
            out.append("\ncycle");
            for (int u : cycle) out.append(' ').append(names.get(u));
            out.append("\nend\n");
        }
        System.out.print(out);
    }
}
