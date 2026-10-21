// Dijkstra in Java 17, a translation of algotrace/algorithms/graph/dijkstra.py.
// Input and output: reference_code/README.md, "Graph programs".
// The nearest node is found by a linear scan over the nodes in input order,
// taking the first smallest, exactly as the endpoint's min() does, so ties
// break the same way and the lesson's O(V squared) holds.
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

public class Dijkstra {
    static final long INF = Long.MAX_VALUE;

    // lesson:helpers
    // The graph, as the endpoint receives it: nodes keep their input order,
    // and every node's neighbours keep theirs, each with its weight. The first
    // keyCount nodes are the ones with a line of their own.
    static final List<String> names = new ArrayList<>();
    static final Map<String, Integer> indexOf = new HashMap<>();
    static final List<List<int[]>> neighbours = new ArrayList<>();
    static final List<List<Long>> weights = new ArrayList<>();
    static int keyCount;

    static int nodeIndex(String name) {
        Integer found = indexOf.get(name);
        if (found != null) return found;
        indexOf.put(name, names.size());
        names.add(name);
        neighbours.add(new ArrayList<>());
        weights.add(new ArrayList<>());
        return names.size() - 1;
    }

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
    static int[] previous;

    // lesson:start
    static void dijkstra(int start) {
        dist = new long[keyCount];
        previous = new int[keyCount];
        boolean[] unvisited = new boolean[keyCount];
        Arrays.fill(dist, INF);
        Arrays.fill(previous, -1);
        Arrays.fill(unvisited, true);
        dist[start] = 0;
        int remaining = keyCount;
        while (remaining > 0) {
            int current = -1;
            for (int i = 0; i < keyCount; i++) {
                if (unvisited[i] && (current == -1 || dist[i] < dist[current])) current = i; // @pick-min
            }
            if (dist[current] == INF) break;
            unvisited[current] = false;
            remaining--;
            beginStep("visit", "pick-min"); putNode(current); putBar(); putValue(dist[current]); endStep(); // @hide
            List<int[]> around = neighbours.get(current);
            for (int k = 0; k < around.size(); k++) {
                int next = around.get(k)[0];
                if (next < keyCount && unvisited[next]) {
                    long through = dist[current] + weights.get(current).get(k);
                    if (through < dist[next]) {                     // @relax
                        dist[next] = through;
                        previous[next] = current;
                        beginStep("relax", "relax"); putNode(next); putBar(); putValue(through); endStep(); // @hide
                    }
                }
            }
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
            neighbours.clear();
            weights.clear();
            for (String key : keys) nodeIndex(key);
            keyCount = names.size();
            for (int i = 0; i < k; i++) {
                int u = nodeIndex(keys.get(i));
                for (int j = 0; j < lines.get(i).size(); j++) {
                    int v = nodeIndex(lines.get(i).get(j));
                    neighbours.get(u).add(new int[] {v});
                    weights.get(u).add(lineWeights.get(i).get(j));
                }
            }
            int start = nodeIndex(startName);
            dijkstra(start);

            List<Integer> order = new ArrayList<>();
            for (int i = 0; i < keyCount; i++) order.add(i);
            order.sort((a, b) -> compareNames(names.get(a), names.get(b)));
            beginStep("done", null);
            for (int i : order) putNode(i);
            putBar();
            endStep();
            // The result as the endpoint sends it: its JSON sorts object keys,
            // so both maps arrive in order of node name.
            for (int i : order) {
                out.append("distance ").append(names.get(i));
                putValue(dist[i]);
                out.append('\n');
            }
            for (int i : order) {
                if (i == start || dist[i] == INF) continue;
                List<Integer> route = new ArrayList<>();
                for (int at = i; at != -1; at = previous[at]) route.add(at);
                if (route.get(route.size() - 1) != start) continue;
                out.append("path ").append(names.get(i));
                for (int r = route.size() - 1; r >= 0; r--) out.append(' ').append(names.get(route.get(r)));
                out.append('\n');
            }
            out.append("end\n");
        }
        PrintStream utf8 = new PrintStream(new FileOutputStream(FileDescriptor.out), true, StandardCharsets.UTF_8);
        utf8.print(out);
        utf8.flush();
    }
}
