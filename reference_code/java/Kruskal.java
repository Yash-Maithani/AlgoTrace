// Kruskal in Java 17, a translation of algotrace/algorithms/graph/kruskal.py.
// Input and output: reference_code/README.md, "Graph programs".
// Python's sorted() is stable, so equal weights keep their input order.
// List.sort is a stable merge sort too, so the order matches. Union-Find
// uses path halving and union by rank, as the endpoint does. Like the
// endpoint, the walk notes when the tree is complete and goes on.
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

public class Kruskal {
    // lesson:helpers
    // Node names in input order; an edge refers to its ends by index.
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

    // Union-Find with path halving and union by rank.
    static int[] parent;
    static int[] rank;

    static int find(int x) {
        while (parent[x] != x) {
            parent[x] = parent[parent[x]];
            x = parent[x];
        }
        return x;
    }

    static boolean unite(int a, int b) {
        int ra = find(a), rb = find(b);
        if (ra == rb) return false;
        if (rank[ra] < rank[rb]) {
            int t = ra;
            ra = rb;
            rb = t;
        }
        parent[rb] = ra;
        if (rank[ra] == rank[rb]) rank[ra]++;
        return true;
    }
    // lesson:end

    // Plumbing: the step trace.
    static final StringBuilder out = new StringBuilder();

    static void beginStep(String action, String line) {
        out.append("step ").append(action).append(' ').append(line == null ? "-" : line);
    }

    static void putNode(int i) { out.append(' ').append(names.get(i)); }

    static void putBar() { out.append(" |"); }

    static void putValue(long v) { out.append(' ').append(v); }

    static void endStep() { out.append('\n'); }

    // lesson:start
    static List<Edge> kruskal(List<Edge> edges, int spanningTotal) {
        edges.sort(Comparator.comparingLong(Edge::w));              // @sort
        beginStep("milestone", "sort"); putBar();                   // @hide
        for (Edge edge : edges) putValue(edge.w());                 // @hide
        endStep();                                                  // @hide
        List<Edge> tree = new ArrayList<>();
        for (Edge edge : edges) {
            beginStep("consider", "take-next"); putNode(edge.u()); putNode(edge.v()); putBar(); putValue(edge.w()); endStep(); // @hide
            if (unite(edge.u(), edge.v())) {                        // @take-next
                tree.add(edge);                                     // @union
                beginStep("include", "union"); putNode(edge.u()); putNode(edge.v()); putBar(); putValue(edge.w()); endStep(); // @hide
                if (tree.size() == spanningTotal) {                 // @mst-complete
                    beginStep("milestone", "mst-complete"); putBar(); endStep(); // @hide
                }
            } else {                                                // @cycle
                beginStep("reject", "cycle"); putNode(edge.u()); putNode(edge.v()); putBar(); putValue(edge.w()); endStep(); // @hide
            }
        }
        return tree;
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
            List<Integer> listed = new ArrayList<>();
            for (int i = 0; i < k; i++) {
                listed.add(nodeIndex(in[p++]));
                int d = Integer.parseInt(in[p++]);
                p += 2 * d;
            }
            int m = Integer.parseInt(in[p++]);
            List<Edge> edges = new ArrayList<>();
            for (int e = 0; e < m; e++) {
                int u = nodeIndex(in[p++]);
                int v = nodeIndex(in[p++]);
                edges.add(new Edge(u, v, Long.parseLong(in[p++])));
            }
            parent = new int[names.size()];
            rank = new int[names.size()];
            for (int i = 0; i < parent.length; i++) parent[i] = i;
            List<Edge> tree = kruskal(edges, k > 1 ? k - 1 : 0);

            long total = 0;
            for (Edge edge : tree) total += edge.w();
            beginStep("done", null);
            for (int i : listed) putNode(i);
            putBar();
            putValue(total);
            endStep();
            for (Edge edge : tree) {
                out.append("edge ").append(names.get(edge.u())).append(' ').append(names.get(edge.v()))
                   .append(' ').append(edge.w()).append('\n');
            }
            out.append("total ").append(total).append("\nend\n");
        }
        PrintStream utf8 = new PrintStream(new FileOutputStream(FileDescriptor.out), true, StandardCharsets.UTF_8);
        utf8.print(out);
        utf8.flush();
    }
}
