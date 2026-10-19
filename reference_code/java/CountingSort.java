// Counting Sort in Java 17, a translation of sorting_algorithms/counting_sort.py.
// Told the key range in advance, whole numbers from 0 to 99, so it compares
// nothing. Input and output: reference_code/README.md. The second count is
// writes, reported as swaps, exactly as the site does.
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public class CountingSort {
    static final int KEY_MAX = 99;

    // Plumbing: the counts the site reports and the step trace.
    static long comparisons;
    static long swaps;
    static int[] shown;
    static final StringBuilder out = new StringBuilder();

    // index < 0: no index:value pair. lo < 0: no slots of the count list.
    static void step(String action, String line, int index, int value, int lo, int hi) {
        out.append("step ").append(action).append(' ').append(line == null ? "-" : line);
        if (index >= 0) out.append(' ').append(index).append(':').append(value);
        if (lo >= 0) out.append(" cells=").append(lo).append(':').append(hi)
                        .append(" count=").append(shown[lo]);
        out.append('\n');
    }

    // lesson:start
    static void countingSort(int[] arr, int k) {
        int[] count = new int[k + 1];
        shown = count;                                              // @hide
        for (int i = 0; i < arr.length; i++) {
            count[arr[i]]++;                                        // @tally
            step("count", "tally", i, arr[i], arr[i], arr[i]);      // @hide
        }
        int pos = 0;
        int emptyFrom = -1;                                         // @hide
        for (int v = 0; v <= k; v++) {                              // @scan
            if (count[v] == 0) {                                    // @hide
                if (emptyFrom < 0) emptyFrom = v;                   // @hide
                if (v < k) continue;                                // @hide
            }                                                       // @hide
            if (emptyFrom >= 0) {                                   // @hide
                step("select", "scan", -1, 0, emptyFrom, count[v] == 0 ? v : v - 1); // @hide
                emptyFrom = -1;                                     // @hide
                if (count[v] == 0) continue;                        // @hide
            }                                                       // @hide
            step("select", "scan", -1, 0, v, v);                    // @hide
            for (int c = 0; c < count[v]; c++) {
                arr[pos] = v;                                       // @write
                swaps++;                                            // @hide
                step("overwrite", "write", pos, v, v, v);           // @hide
                pos++;
            }
        }
        step("done", null, -1, 0, -1, 0);                           // @hide
    }
    // lesson:end

    public static void main(String[] args) throws IOException {
        String[] in = new String(System.in.readAllBytes(), StandardCharsets.UTF_8).trim().split("\\s+");
        int p = 0;
        int cases = Integer.parseInt(in[p++]);
        for (int c = 0; c < cases; c++) {
            String variant = in[p++];
            p += 2;                                  // the seed and target are not used here
            int n = Integer.parseInt(in[p++]);
            if (!variant.equals("-")) {
                System.out.print(out);
                System.out.println("error unknown variant " + variant);
                System.exit(2);
            }
            int[] arr = new int[n];
            for (int k = 0; k < n; k++) {
                arr[k] = Integer.parseInt(in[p++]);
                if (arr[k] < 0 || arr[k] > KEY_MAX) {
                    System.out.print(out);
                    System.out.println("error value " + arr[k] + " is outside 0 to " + KEY_MAX);
                    System.exit(3);
                }
            }
            comparisons = 0;
            swaps = 0;
            countingSort(arr, KEY_MAX);
            out.append("sorted");
            for (int value : arr) out.append(' ').append(value);
            out.append("\ncomparisons ").append(comparisons)
               .append("\nswaps ").append(swaps).append("\nend\n");
        }
        System.out.print(out);
    }
}
