// Linear Search in Java 17, a translation of algotrace/algorithms/searching/linear_search.py.
// Input and output: reference_code/README.md.
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public class LinearSearch {
    // Plumbing: the count the site reports and the step trace.
    static long comparisons;
    static final StringBuilder out = new StringBuilder();

    static void step(String action, String line, int... pairs) {
        out.append("step ").append(action).append(' ').append(line == null ? "-" : line);
        for (int k = 0; k < pairs.length; k += 2) {
            out.append(' ').append(pairs[k]).append(':').append(pairs[k + 1]);
        }
        out.append('\n');
    }

    // lesson:start
    static int linearSearch(int[] arr, int target) {
        for (int i = 0; i < arr.length; i++) {                      // @loop
            comparisons++;                                          // @hide
            step("compare", "compare", i, arr[i]);                  // @hide
            if (arr[i] == target) {                                 // @compare
                step("found", "found", i, arr[i]);                  // @hide
                return i;                                           // @found
            }
        }
        step("missing", "missing");                                 // @hide
        return -1;                                                  // @missing
    }
    // lesson:end

    public static void main(String[] args) throws IOException {
        String[] in = new String(System.in.readAllBytes(), StandardCharsets.UTF_8).trim().split("\\s+");
        int p = 0;
        int cases = Integer.parseInt(in[p++]);
        for (int c = 0; c < cases; c++) {
            String variant = in[p++];
            p++;                                     // the seed is not used here
            int target = Integer.parseInt(in[p++]);
            int n = Integer.parseInt(in[p++]);
            if (!variant.equals("-")) {
                System.out.print(out);
                System.out.println("error unknown variant " + variant);
                System.exit(2);
            }
            int[] arr = new int[n];
            for (int k = 0; k < n; k++) arr[k] = Integer.parseInt(in[p++]);
            comparisons = 0;
            int index = linearSearch(arr, target);
            out.append("index ").append(index).append("\ncomparisons ").append(comparisons)
               .append("\nend\n");
        }
        System.out.print(out);
    }
}
