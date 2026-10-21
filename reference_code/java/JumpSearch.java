// Jump Search in Java 17, a translation of algotrace/algorithms/searching/jump_search.py.
// The list must already be sorted; the site refuses an unsorted one before
// searching, so this program assumes it. Input and output:
// reference_code/README.md.
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public class JumpSearch {
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

    // lesson:helpers
    // The whole part of the square root, as Python's math.isqrt gives it.
    static int isqrt(int n) {
        int r = 0;
        while ((r + 1) * (r + 1) <= n) r++;
        return r;
    }
    // lesson:end

    // lesson:start
    static int jumpSearch(int[] arr, int target) {
        int n = arr.length;
        if (n == 0) {                                               // @hide
            step("missing", null);                                  // @hide
            return -1;                                              // @hide
        }                                                           // @hide
        int block = isqrt(n);
        int low = 0, end = Math.min(block, n) - 1;
        comparisons++;                                              // @hide
        step("compare", "jump-check", end, arr[end]);               // @hide
        while (arr[end] < target) {                                 // @jump-check
            if (end == n - 1) {
                step("missing", "past-end");                        // @hide
                return -1;                                          // @past-end
            }
            low = end + 1;                                          // @jump
            end = Math.min(end + block, n - 1);
            step("discard", "jump", low - 1, arr[low - 1]);         // @hide
            comparisons++;                                          // @hide
            step("compare", "jump-check", end, arr[end]);           // @hide
        }
        for (int i = low; i <= end; i++) {
            comparisons++;                                          // @hide
            step("compare", "scan", i, arr[i]);                     // @hide
            if (arr[i] == target) {                                 // @scan
                step("found", "found", i, arr[i]);                  // @hide
                return i;                                           // @found
            }
            if (arr[i] > target) {
                break;
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
            int index = jumpSearch(arr, target);
            out.append("index ").append(index)
               .append("\ncomparisons ").append(comparisons).append("\nend\n");
        }
        System.out.print(out);
    }
}
