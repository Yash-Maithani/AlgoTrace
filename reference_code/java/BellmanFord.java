// Bellman-Ford in Java 17, a translation of algotrace/algorithms/graph/bellman_ford.py.
// Input and output: reference_code/README.md, "Graph programs".
// The graph is directed as given. Edges are swept in input order, at most
// V-1 times, stopping after a pass that changes nothing; one more sweep
// then reports whether anything could still improve, a negative cycle.
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

public class BellmanFord {
    static final long INF = Long.MAX_VALUE;

    // lesson:helpers
    // Node names: keys in input order, then names met only as neighbours.
    static final List<String> names = new ArrayList<>();
    static final Map<String, Integer> indexOf = new HashMap<>();

    static int nodeIndex(String name) {
        Integer found = indexOf.get(name);
        if (found != null) return found;
        indexOf.put(name, names.size());
        names.add(name);
        return names.size() - 1;
    }

    // The edge list, in the order the endpoint builds it: each key's
    // neighbours in turn.
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

    static long[] dist;
    static int iterations;
    static boolean negativeCycle;

    // lesson:start
    static void bellmanFord(List<Edge> edges, int start) {
        int n = names.size();
        dist = new long[n];
        Arrays.fill(dist, INF);
        dist[start] = 0;
        iterations = 0;
        for (int pass = 1; pass < Math.max(n, 1); pass++) {
            iterations = pass;                                      // @hide
            boolean changed = false;
            for (Edge edge : edges) {                               // @edge-loop
                beginStep("consider", "edge-loop"); putNode(edge.u()); putNode(edge.v()); putBar(); putValue(edge.w()); endStep(); // @hide
                if (dist[edge.u()] != INF && dist[edge.u()] + edge.w() < dist[edge.v()]) { // @relax
                    dist[edge.v()] = dist[edge.u()] + edge.w();
                    changed = true;
                    beginStep("relax", "relax"); putNode(edge.u()); putNode(edge.v()); putBar(); putValue(dist[edge.v()]); endStep(); // @hide
                } else {                                            // @no-improve
                    beginStep("reject", "no-improve"); putNode(edge.u()); putNode(edge.v()); putBar(); putValue(edge.w()); endStep(); // @hide
                }
            }
            beginStep("milestone", "pass-done"); putBar(); putValue(pass); endStep(); // @hide
            if (!changed) break;                                    // @pass-done
        }
        negativeCycle = false;
        for (Edge edge : edges) {
            if (dist[edge.u()] != INF && dist[edge.u()] + edge.w() < dist[edge.v()]) negativeCycle = true;
        }
    }
    // lesson:end

    public static void main(String[] args) throws IOException {
        String[] in = new String(System.in.readAllBytes(), StandardCharsets.UTF_8).trim().split("\\s+");
        int p = 0;
        int cases = Integer.parseInt(in[p++]);
        for (int c = 0; c < cases; c++) {
            String startName = in[p++];
            int k = Integer.parseInt(in[p++]);
            List<String> keys = new ArrayList<>();
            List<List<String>> lines = new ArrayList<>();
            List<List<Long>> lineWeights = new ArrayList<>();
            for (int i = 0; i < k; i++) {
                keys.add(in[p++]);
                int d = Integer.parseInt(in[p++]);
                List<String> line = new ArrayList<>();
                List<Long> ws = new ArrayList<>();
                for (int j = 0; j < d; j++) {
                    line.add(in[p++]);
                    ws.add(Long.parseLong(in[p++]));
                }
                lines.add(line);
                lineWeights.add(ws);
            }
            int m = Integer.parseInt(in[p++]);
            p += 3 * m;
            names.clear();
            indexOf.clear();
            for (String key : keys) nodeIndex(key);
            List<Edge> edges = new ArrayList<>();
            for (int i = 0; i < k; i++) {
                int u = nodeIndex(keys.get(i));
                for (int j = 0; j < lines.get(i).size(); j++) {
                    int v = nodeIndex(lines.get(i).get(j));
                    edges.add(new Edge(u, v, lineWeights.get(i).get(j)));
                }
            }
            bellmanFord(edges, nodeIndex(startName));

            List<Integer> order = new ArrayList<>();
            for (int i = 0; i < names.size(); i++) order.add(i);
            order.sort((a, b) -> compareNames(names.get(a), names.get(b)));
            for (int i : order) {
                out.append("distance ").append(names.get(i));
                putValue(dist[i]);
                out.append('\n');
            }
            out.append("negative_cycle ").append(negativeCycle ? "true" : "false")
               .append("\niterations ").append(iterations).append("\nend\n");
        }
        PrintStream utf8 = new PrintStream(new FileOutputStream(FileDescriptor.out), true, StandardCharsets.UTF_8);
        utf8.print(out);
        utf8.flush();
    }
}
