// Selection Sort in Java 17, a translation of sorting_algorithms/selection_sort.py.
// Input and output: reference_code/README.md.
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public class SelectionSort {
    // Plumbing: the counts the site reports and the step trace.
    static long comparisons;
    static long swaps;
    static final StringBuilder out = new StringBuilder();

    static void step(String action, String line, int... pairs) {
        out.append("step ").append(action).append(' ').append(line == null ? "-" : line);
        for (int k = 0; k < pairs.length; k += 2) {
            out.append(' ').append(pairs[k]).append(':').append(pairs[k + 1]);
        }
        out.append('\n');
    }

    // lesson:start
    static void selectionSort(int[] arr) {
        int n = arr.length;
        for (int i = 0; i < n; i++) {                               // @outer
            int minIdx = i;                                         // @min-init
            step("select", "min-init", i, arr[i]);                  // @hide
            for (int j = i + 1; j < n; j++) {                       // @inner
                comparisons++;                                      // @hide
                step("compare", "compare", minIdx, arr[minIdx], j, arr[j]); // @hide
                if (arr[minIdx] > arr[j]) {                         // @compare
                    minIdx = j;                                     // @update-min
                    step("select", "update-min", minIdx, arr[minIdx]); // @hide
                }
            }
            if (i != minIdx) {
                int t = arr[i];                                     // @swap
                arr[i] = arr[minIdx];
                arr[minIdx] = t;
                swaps++;                                            // @hide
                step("swap", "swap", i, arr[i], minIdx, arr[minIdx]); // @hide
            }
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
            if (!variant.equals("-")) {
                System.out.print(out);
                System.out.println("error unknown variant " + variant);
                System.exit(2);
            }
            int[] arr = new int[n];
            for (int k = 0; k < n; k++) arr[k] = Integer.parseInt(in[p++]);
            comparisons = 0;
            swaps = 0;
            selectionSort(arr);
            out.append("sorted");
            for (int value : arr) out.append(' ').append(value);
            out.append("\ncomparisons ").append(comparisons)
               .append("\nswaps ").append(swaps).append("\nend\n");
        }
        System.out.print(out);
    }
}
