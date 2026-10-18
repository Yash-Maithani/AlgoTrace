// Prim in Java 17, a translation of /run_prim in app.py.
// Input and output: reference_code/README.md, "Graph programs".
// The endpoint pushes (weight, u, v) tuples onto Python's heapq. Here the
// same tuples go into a PriorityQueue, a binary heap, compared as whole
// tuples: weight, then u's name, then v's name, names by code point as
// Python compares them. Every edge leaving a newly joined node is pushed,
// stale ones included: the lesson's O(E log E).
import java.io.FileDescriptor;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;

public class Prim {
    // lesson:helpers
    // The graph, as the endpoint receives it: nodes keep their input order,
    // and every node's neighbours keep theirs, each with its weight.
    static final List<String> names = new ArrayList<>();
    static final Map<String, Integer> indexOf = new HashMap<>();
    static final List<List<Integer>> neighbours = new ArrayList<>();
    static final List<List<Long>> weights = new ArrayList<>();

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

    // An edge as the tuple (weight, u, v), ordered as Python orders it.
    record Edge(long w, String u, String v) {}

    static final Comparator<Edge> TUPLE_ORDER = Comparator.comparingLong(Edge::w)
            .thenComparing(Edge::u, Prim::compareNames)
            .thenComparing(Edge::v, Prim::compareNames);
    // lesson:end

    // Plumbing: the step trace.
    static final StringBuilder out = new StringBuilder();

    static void beginStep(String action, String line) {
        out.append("step ").append(action).append(' ').append(line == null ? "-" : line);
    }

    static void putName(String name) { out.append(' ').append(name); }

    static void putBar() { out.append(" |"); }

    static void putValue(long v) { out.append(' ').append(v); }

    static void endStep() { out.append('\n'); }

    static boolean[] visited;
    static final List<Edge> tree = new ArrayList<>();

    // lesson:start
    static void prim(int start) {
        PriorityQueue<Edge> heap = new PriorityQueue<>(TUPLE_ORDER);
        List<String> frontier = new ArrayList<>();                  // @hide
        visited[start] = true;                                      // @start
        beginStep("visit", "start"); putName(names.get(start)); putBar(); endStep(); // @hide
        for (int k = 0; k < neighbours.get(start).size(); k++) {
            int next = neighbours.get(start).get(k);
            heap.add(new Edge(weights.get(start).get(k), names.get(start), names.get(next))); // @push-edges
            if (!visited[next]) frontier.add(names.get(next));      // @hide
        }
        if (!frontier.isEmpty()) {                                  // @hide
            beginStep("enqueue", "push-edges");                     // @hide
            for (String name : frontier) putName(name);             // @hide
            putBar(); endStep();                                    // @hide
        }                                                           // @hide
        while (!heap.isEmpty()) {
            Edge e = heap.poll();                                   // @pop-min
            int v = indexOf.get(e.v());
            if (visited[v]) {                                       // @skip-visited
                beginStep("reject", "skip-visited"); putName(e.u()); putName(e.v()); putBar(); putValue(e.w()); endStep(); // @hide
                continue;
            }
            beginStep("consider", "pop-min"); putName(e.u()); putName(e.v()); putBar(); putValue(e.w()); endStep(); // @hide
            tree.add(e);                                            // @add-edge
            visited[v] = true;
            beginStep("include", "add-edge"); putName(e.u()); putName(e.v()); putBar(); putValue(e.w()); endStep(); // @hide
            frontier.clear();                                       // @hide
            for (int k = 0; k < neighbours.get(v).size(); k++) {
                int next = neighbours.get(v).get(k);
                if (!visited[next]) {
                    heap.add(new Edge(weights.get(v).get(k), e.v(), names.get(next))); // @push-edges
                    frontier.add(names.get(next));                  // @hide
                }
            }
            if (!frontier.isEmpty()) {                              // @hide
                beginStep("enqueue", "push-edges");                 // @hide
                for (String name : frontier) putName(name);         // @hide
                putBar(); endStep();                                // @hide
            }                                                       // @hide
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
            int keyCount = names.size();
            for (int i = 0; i < k; i++) {
                int u = nodeIndex(keys.get(i));
                for (int j = 0; j < lines.get(i).size(); j++) {
                    int v = nodeIndex(lines.get(i).get(j));
                    neighbours.get(u).add(v);
                    weights.get(u).add(lineWeights.get(i).get(j));
                }
            }
            visited = new boolean[names.size()];
            tree.clear();
            prim(nodeIndex(startName));

            long total = 0;
            for (Edge e : tree) total += e.w();
            List<String> seen = new ArrayList<>();
            for (int i = 0; i < keyCount; i++) if (visited[i]) seen.add(names.get(i));
            seen.sort(Prim::compareNames);
            beginStep("done", null);
            for (String s : seen) putName(s);
            putBar();
            putValue(total);
            endStep();
            for (Edge e : tree) out.append("edge ").append(e.u()).append(' ').append(e.v()).append(' ').append(e.w()).append('\n');
            out.append("total ").append(total).append("\nend\n");
        }
        PrintStream utf8 = new PrintStream(new FileOutputStream(FileDescriptor.out), true, StandardCharsets.UTF_8);
        utf8.print(out);
        utf8.flush();
    }
}
