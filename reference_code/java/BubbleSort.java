// Bubble Sort in Java 17, a translation of sorting_algorithms/bubble_sort.py.
// Input and output: reference_code/README.md.
// lesson:variants off on
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public class BubbleSort {
    // Plumbing: the counts the site reports and the step trace.
    static long comparisons;
    static long swaps;
    static boolean earlyExit;
    static final StringBuilder out = new StringBuilder();

    static void step(String action, String line, int... pairs) {
        out.append("step ").append(action).append(' ').append(line == null ? "-" : line);
        for (int k = 0; k < pairs.length; k += 2) {
            out.append(' ').append(pairs[k]).append(':').append(pairs[k + 1]);
        }
        out.append('\n');
    }

    // lesson:start
    static void bubbleSort(int[] arr) {
        int n = arr.length;
        for (int i = 0; i < n; i++) {                               // @pass
            boolean swapped = false;                                // @only:on
            for (int j = 0; j < n - i - 1; j++) {                   // @walk
                comparisons++;                                      // @hide
                step("compare", "compare", j, arr[j], j + 1, arr[j + 1]); // @hide
                if (arr[j] > arr[j + 1]) {                          // @compare
                    int t = arr[j];                                 // @swap
                    arr[j] = arr[j + 1];
                    arr[j + 1] = t;
                    swapped = true;                                 // @only:on
                    swaps++;                                        // @hide
                    step("swap", "swap", j, arr[j], j + 1, arr[j + 1]); // @hide
                }
            }
            if (earlyExit) {                                        // @hide
                if (!swapped) break;                                // @only:on
            }                                                       // @hide
        }
        step("done", null);                                         // @hide
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
            if (!variant.equals("off") && !variant.equals("on")) {
                System.out.print(out);
                System.out.println("error unknown variant " + variant);
                System.exit(2);
            }
            int[] arr = new int[n];
            for (int k = 0; k < n; k++) arr[k] = Integer.parseInt(in[p++]);
            comparisons = 0;
            swaps = 0;
            earlyExit = variant.equals("on");
            bubbleSort(arr);
            out.append("sorted");
            for (int value : arr) out.append(' ').append(value);
            out.append("\ncomparisons ").append(comparisons)
               .append("\nswaps ").append(swaps).append("\nend\n");
        }
        System.out.print(out);
    }
}
