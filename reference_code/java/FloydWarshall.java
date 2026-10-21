// Floyd-Warshall in Java 17, a translation of algotrace/algorithms/graph/floyd_warshall.py.
// Input and output: reference_code/README.md, "Graph programs".
// Edges are undirected and a parallel edge only replaces a dearer one.
// Three nested loops with nothing to cut them short: the lesson's V cubed.
import java.io.FileDescriptor;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class FloydWarshall {
    static final long INF = Long.MAX_VALUE;

    // lesson:helpers
    // Node names in input order.
    static final List<String> names = new ArrayList<>();
    static final Map<String, Integer> indexOf = new HashMap<>();

    static int nodeIndex(String name) {
        Integer found = indexOf.get(name);
        if (found != null) return found;
        indexOf.put(name, names.size());
        names.add(name);
        return names.size() - 1;
    }

    record Edge(int u, int v, long w) {}

    // Names compared by Unicode code point, as Python compares strings.
    static int compareNames(String a, String b) {
        int i = 0, j = 0;
        while (i < a.length() && j < b.length()) {
            int ca = a.codePointAt(i), cb = b.codePointAt(j);
            if (ca != cb) return Integer.compare(ca, cb);
            i += Character.charCount(ca);
            j += Character.charCount(cb);
        }
        return Integer.compare(a.length() - i, b.length() - j);
    }
    // lesson:end

    // Plumbing: the step trace.
    static final StringBuilder out = new StringBuilder();

    static void beginStep(String action, String line) {
        out.append("step ").append(action).append(' ').append(line == null ? "-" : line);
    }

    static void putNode(int i) { out.append(' ').append(names.get(i)); }

    static void putBar() { out.append(" |"); }

    static void putValue(long v) { out.append(' ').append(v == INF ? "∞" : Long.toString(v)); }

    static void endStep() { out.append('\n'); }

    static long[][] dist;
    static int[][] nextHop;

    // lesson:start
    static void floydWarshall(int n, List<Edge> edges) {
        dist = new long[n][n];
        nextHop = new int[n][n];
        for (int i = 0; i < n; i++) {
            Arrays.fill(dist[i], INF);
            Arrays.fill(nextHop[i], -1);
            dist[i][i] = 0;
        }
        for (Edge edge : edges) {
            if (edge.w() < dist[edge.u()][edge.v()]) {              // keep the cheaper of parallel edges
                dist[edge.u()][edge.v()] = dist[edge.v()][edge.u()] = edge.w(); // @init
                nextHop[edge.u()][edge.v()] = edge.v();
                nextHop[edge.v()][edge.u()] = edge.u();
            }
        }
        beginStep("milestone", "init");                             // @hide
        for (int i = 0; i < n; i++) putNode(i);                     // @hide
        putBar(); endStep();                                        // @hide
        for (int k = 0; k < n; k++) {                               // @k-loop
            beginStep("milestone", "k-loop"); putNode(k); putBar(); endStep(); // @hide
            long updates = 0;
            for (int i = 0; i < n; i++) {
                for (int j = 0; j < n; j++) {
                    if (i == j) continue;
                    long current = dist[i][j];
                    if (dist[i][k] == INF || dist[k][j] == INF) {   // @check-inf
                        beginStep("reject", "check-inf"); putNode(i); putNode(j); putNode(k); putBar(); endStep(); // @hide
                        continue;
                    }
                    long viaK = dist[i][k] + dist[k][j];            // @compare
                    beginStep("consider", "compare"); putNode(i); putNode(j); putNode(k); putBar(); // @hide
                    putValue(current); putValue(dist[i][k]); putValue(dist[k][j]); putValue(viaK); endStep(); // @hide
                    if (viaK < current) {                           // @update
                        dist[i][j] = viaK;
                        nextHop[i][j] = nextHop[i][k];
                        updates++;
                        beginStep("relax", "update"); putNode(i); putNode(j); putNode(k); putBar(); putValue(viaK); endStep(); // @hide
                    } else {                                        // @keep
                        beginStep("reject", "keep"); putNode(i); putNode(j); putNode(k); putBar(); putValue(current); endStep(); // @hide
                    }
                }
            }                                                       // @k-done
            beginStep("milestone", "k-done"); putNode(k); putBar(); putValue(updates); endStep(); // @hide
        }
    }
    // lesson:end

    public static void main(String[] args) throws IOException {
        String[] in = new String(System.in.readAllBytes(), StandardCharsets.UTF_8).trim().split("\\s+");
        int p = 0;
        int cases = Integer.parseInt(in[p++]);
        for (int c = 0; c < cases; c++) {
            p++;                                         // no start node
            int k = Integer.parseInt(in[p++]);
            names.clear();
            indexOf.clear();
            for (int i = 0; i < k; i++) {
                nodeIndex(in[p++]);
                int d = Integer.parseInt(in[p++]);
                p += 2 * d;
            }
            int n = names.size();
            int m = Integer.parseInt(in[p++]);
            List<Edge> edges = new ArrayList<>();
            for (int e = 0; e < m; e++) {
                int u = nodeIndex(in[p++]);
                int v = nodeIndex(in[p++]);
                edges.add(new Edge(u, v, Long.parseLong(in[p++])));
            }
            floydWarshall(n, edges);

            beginStep("done", null);
            for (int i = 0; i < n; i++) putNode(i);
            putBar();
            endStep();
            for (int i = 0; i < n; i++) {
                out.append("row ").append(names.get(i));
                for (int j = 0; j < n; j++) putValue(dist[i][j]);
                out.append('\n');
            }
            // One route per reachable ordered pair, by from then to name, the
            // order the endpoint's JSON sorts its "from -> to" keys into.
            List<Integer> order = new ArrayList<>();
            for (int i = 0; i < n; i++) order.add(i);
            order.sort((a, b) -> compareNames(names.get(a), names.get(b)));
            for (int i : order) {
                for (int j : order) {
                    if (i == j || dist[i][j] == INF || nextHop[i][j] == -1) continue;
                    List<Integer> route = new ArrayList<>();
                    route.add(i);
                    while (route.get(route.size() - 1) != j && route.size() <= n) {
                        int stepTo = nextHop[route.get(route.size() - 1)][j];
                        if (stepTo == -1) break;
                        route.add(stepTo);
                    }
                    if (route.get(route.size() - 1) != j) continue;
                    out.append("path ").append(names.get(i)).append(' ').append(names.get(j));
                    putValue(dist[i][j]);
                    for (int r : route) out.append(' ').append(names.get(r));
                    out.append('\n');
                }
            }
            out.append("end\n");
        }
        PrintStream utf8 = new PrintStream(new FileOutputStream(FileDescriptor.out), true, StandardCharsets.UTF_8);
        utf8.print(out);
        utf8.flush();
    }
}
