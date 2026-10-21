// Quick Sort in Java 17, a translation of algotrace/algorithms/sorting/quick_sort.py.
// Input and output: reference_code/README.md. Variant last takes the last
// value as pivot; middle and random swap their choice to the end first and
// run the same partition. random draws from mulberry32, the same generator
// as algotrace/algorithms/sorting/seeded.py, so a seed gives the same run as Python.
// lesson:variants last middle random
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public class QuickSort {
    // Plumbing: the counts the site reports and the step trace.
    static long comparisons;
    static long swaps;
    static String pivotRule = "last";
    static final StringBuilder out = new StringBuilder();

    static void stepAt(int depth, int lo, int hi, String action, String line, int... pairs) {
        out.append("step ").append(action).append(' ').append(line == null ? "-" : line);
        for (int k = 0; k < pairs.length; k += 2) {
            out.append(' ').append(pairs[k]).append(':').append(pairs[k + 1]);
        }
        out.append(" depth=").append(depth).append(" range=").append(lo).append(':').append(hi).append('\n');
    }

    // mulberry32, as in algotrace/algorithms/sorting/seeded.py: a double in [0, 1).
    // Java's int arithmetic wraps at 32 bits, and >>> is the unsigned shift.
    static int rngState;

    static double randUnit() {
        rngState += 0x6D2B79F5;
        int t = rngState;
        t = (t ^ (t >>> 15)) * (t | 1);
        t ^= t + (t ^ (t >>> 7)) * (t | 61);
        return ((t ^ (t >>> 14)) & 0xFFFFFFFFL) / 4294967296.0;
    }

    // lesson:helpers
    static void swap(int[] arr, int a, int b) {
        int t = arr[a];
        arr[a] = arr[b];
        arr[b] = t;
    }
    // lesson:end

    // lesson:start
    static int partition(int[] arr, int low, int high, int depth) { // @partition
        if (pivotRule.equals("middle")) {                           // @hide
            int mid = (low + high) / 2;                             // @only:middle
            swap(arr, mid, high);                                   // @choose-pivot @only:middle
            swaps++;                                                // @hide
            stepAt(depth, low, high, "swap", "choose-pivot",        // @hide
                   mid, arr[mid], high, arr[high]);                 // @hide
        } else if (pivotRule.equals("random")) {                    // @hide
            int r = low + (int) (randUnit() * (high - low + 1));    // @only:random
            if (r != high) {                                        // @only:random
                swap(arr, r, high);                                 // @choose-pivot @only:random
                swaps++;                                            // @hide
                stepAt(depth, low, high, "swap", "choose-pivot",    // @hide
                       r, arr[r], high, arr[high]);                 // @hide
            }                                                       // @only:random
        }                                                           // @hide
        int pivot = arr[high];                                      // @pivot
        int i = low - 1;
        for (int j = low; j < high; j++) {                          // @iloop
            comparisons++;                                          // @hide
            stepAt(depth, low, high, "compare", "compare", j, arr[j], high, pivot); // @hide
            if (arr[j] < pivot) {                                   // @compare
                i++;
                swap(arr, i, j);                                    // @swap
                swaps++;                                            // @hide
                stepAt(depth, low, high, "swap", "swap", i, arr[i], j, arr[j]); // @hide
            }
        }
        swap(arr, i + 1, high);                                     // @place-pivot
        swaps++;                                                    // @hide
        stepAt(depth, low, high, "place", "place-pivot",            // @hide
               i + 1, arr[i + 1], high, arr[high]);                 // @hide
        return i + 1;
    }

    static void sort(int[] arr, int low, int high, int depth) {
        if (low < high) {
            int pi = partition(arr, low, high, depth);
            sort(arr, low, pi - 1, depth + 1);                      // @recurse-left
            sort(arr, pi + 1, high, depth + 1);                     // @recurse-right
        }
    }
    // lesson:end

    public static void main(String[] args) throws IOException {
        String[] in = new String(System.in.readAllBytes(), StandardCharsets.UTF_8).trim().split("\\s+");
        int p = 0;
        int cases = Integer.parseInt(in[p++]);
        for (int c = 0; c < cases; c++) {
            String variant = in[p++];
            long seed = Long.parseLong(in[p++]);
            p++;                                     // the target is not used here
            int n = Integer.parseInt(in[p++]);
            if (!variant.equals("last") && !variant.equals("middle") && !variant.equals("random")) {
                System.out.print(out);
                System.out.println("error unknown variant " + variant);
                System.exit(2);
            }
            int[] arr = new int[n];
            for (int k = 0; k < n; k++) arr[k] = Integer.parseInt(in[p++]);
            comparisons = 0;
            swaps = 0;
            pivotRule = variant;
            rngState = (int) seed;
            sort(arr, 0, n - 1, 0);
            stepAt(0, 0, n - 1, "done", null);
            out.append("sorted");
            for (int value : arr) out.append(' ').append(value);
            out.append("\ncomparisons ").append(comparisons)
               .append("\nswaps ").append(swaps).append("\nend\n");
        }
        System.out.print(out);
    }
}
