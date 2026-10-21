// Depth-First Search in Java 17, a translation of algotrace/algorithms/graph/dfs.py.
// Input and output: reference_code/README.md, "Graph programs".
// Like the endpoint, `not in stack` scans the stack, so the membership test
// is linear: the lesson's O(V times E).
import java.io.FileDescriptor;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class DepthFirstSearch {
    // lesson:helpers
    // The graph, as the endpoint receives it: nodes keep their input order,
    // and every node's neighbours keep theirs.
    static final List<String> names = new ArrayList<>();
    static final Map<String, Integer> indexOf = new HashMap<>();
    static final List<List<Integer>> neighbours = new ArrayList<>();

    static int nodeIndex(String name) {
        Integer found = indexOf.get(name);
        if (found != null) return found;
        indexOf.put(name, names.size());
        names.add(name);
        neighbours.add(new ArrayList<>());
        return names.size() - 1;
    }
    // lesson:end

    // Plumbing: the step trace.
    static final StringBuilder out = new StringBuilder();

    static void beginStep(String action, String line) {
        out.append("step ").append(action).append(' ').append(line == null ? "-" : line);
    }

    static void putNode(int i) { out.append(' ').append(names.get(i)); }

    static void endStep() { out.append(" |\n"); }

    // lesson:start
    static List<Integer> dfs(int start) {
        boolean[] visited = new boolean[names.size()];
        List<Integer> path = new ArrayList<>();
        List<Integer> stack = new ArrayList<>();
        stack.add(start);                                           // @start
        beginStep("enqueue", "start"); putNode(start); endStep();   // @hide
        while (!stack.isEmpty()) {
            int node = stack.remove(stack.size() - 1);              // @pop
            if (!visited[node]) {
                visited[node] = true;
                path.add(node);
                beginStep("visit", "pop"); putNode(node); endStep(); // @hide
                List<Integer> around = neighbours.get(node);
                for (int k = around.size() - 1; k >= 0; k--) {      // reversed, as in Python
                    int next = around.get(k);
                    if (!visited[next] && !stack.contains(next)) {  // @push
                        stack.add(next);
                        beginStep("enqueue", "push"); putNode(next); endStep(); // @hide
                    }
                }
            }
        }
        beginStep("done", null);                                    // @hide
        for (int node : path) putNode(node);                        // @hide
        endStep();                                                  // @hide
        return path;
    }
    // lesson:end

    public static void main(String[] args) throws IOException {
        String[] in = new String(System.in.readAllBytes(), StandardCharsets.UTF_8).trim().split("\\s+");
        int p = 0;
        int cases = Integer.parseInt(in[p++]);
        for (int c = 0; c < cases; c++) {
            String start = in[p++];
            int k = Integer.parseInt(in[p++]);
            List<String> keys = new ArrayList<>();
            List<List<String>> lines = new ArrayList<>();
            for (int i = 0; i < k; i++) {
                keys.add(in[p++]);
                int d = Integer.parseInt(in[p++]);
                List<String> line = new ArrayList<>();
                for (int j = 0; j < d; j++) {
                    line.add(in[p++]);
                    p++;                                 // weights are placeholders here
                }
                lines.add(line);
            }
            int m = Integer.parseInt(in[p++]);
            p += 3 * m;
            // Keys first, in order, then names met only as neighbours.
            names.clear();
            indexOf.clear();
            neighbours.clear();
            for (String key : keys) nodeIndex(key);
            for (int i = 0; i < k; i++) {
                int u = nodeIndex(keys.get(i));
                for (String n : lines.get(i)) {
                    int v = nodeIndex(n);
                    neighbours.get(u).add(v);
                }
            }
            List<Integer> path = dfs(nodeIndex(start));
            out.append("path");
            for (int node : path) out.append(' ').append(names.get(node));
            out.append("\nend\n");
        }
        PrintStream utf8 = new PrintStream(new FileOutputStream(FileDescriptor.out), true, StandardCharsets.UTF_8);
        utf8.print(out);
        utf8.flush();
    }
}
