// Insertion Sort in Java 17, a translation of algotrace/algorithms/sorting/insertion_sort.py.
// Input and output: reference_code/README.md. The second count is shifts,
// reported as swaps, exactly as the site does.
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public class InsertionSort {
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
    static void insertionSort(int[] arr) {
        for (int i = 1; i < arr.length; i++) {                      // @outer
            int key = arr[i];                                       // @key
            int j = i - 1;
            while (j >= 0) {                                        // @inner
                comparisons++;                                      // @hide
                step("compare", "compare", j, arr[j]);              // @hide
                if (key < arr[j]) {                                 // @compare
                    int destination = j + 1;                        // @hide
                    arr[j + 1] = arr[j];                            // @shift
                    swaps++;                                        // @hide
                    j--;
                    step("overwrite", "shift", destination, arr[destination]); // @hide
                } else {
                    break;
                }
            }
            arr[j + 1] = key;                                       // @place
            step("overwrite", "place", j + 1, arr[j + 1]);          // @hide
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
            insertionSort(arr);
            out.append("sorted");
            for (int value : arr) out.append(' ').append(value);
            out.append("\ncomparisons ").append(comparisons)
               .append("\nswaps ").append(swaps).append("\nend\n");
        }
        System.out.print(out);
    }
}
