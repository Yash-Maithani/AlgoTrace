// Merge Sort in Java 17, a translation of sorting_algorithms/merge_sort.py.
// Input and output: reference_code/README.md. The second count is writes,
// reported as swaps, exactly as the site does. Variant lt compares with <
// (not stable), le with <= (stable).
// lesson:variants lt le
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

public class MergeSort {
    // Plumbing: the counts the site reports and the step trace.
    static long comparisons;
    static long swaps;
    static boolean stable;
    static final StringBuilder out = new StringBuilder();

    static void stepAt(int depth, int lo, int hi, String action, String line, int... pairs) {
        out.append("step ").append(action).append(' ').append(line == null ? "-" : line);
        for (int k = 0; k < pairs.length; k += 2) {
            out.append(' ').append(pairs[k]).append(':').append(pairs[k + 1]);
        }
        out.append(" depth=").append(depth).append(" range=").append(lo).append(':').append(hi).append('\n');
    }

    // lesson:start
    static void merge(int[] arr, int[] left, int[] right, int start, int depth) {
        int hi = start + left.length + right.length - 1;           // @hide
        int[] result = new int[left.length + right.length];
        int i = 0, j = 0, k = 0;
        while (i < left.length && j < right.length) {               // @merge-compare
            comparisons++;                                          // @hide
            stepAt(depth, start, hi, "compare", "merge-compare",    // @hide
                   start + i, left[i], start + left.length + j, right[j]); // @hide
            if (!stable) {                                          // @hide
                if (left[i] < right[j]) {                           // @only:lt
                    result[k++] = left[i++];                        // @only:lt
                } else {                                            // @only:lt
                    result[k++] = right[j++];                       // @only:lt
                }                                                   // @only:lt
            } else {                                                // @hide
                if (left[i] <= right[j]) {                          // @only:le
                    result[k++] = left[i++];                        // @only:le
                } else {                                            // @only:le
                    result[k++] = right[j++];                       // @only:le
                }                                                   // @only:le
            }                                                       // @hide
        }
        while (i < left.length) result[k++] = left[i++];
        while (j < right.length) result[k++] = right[j++];
        for (int idx = 0; idx < result.length; idx++) {
            arr[start + idx] = result[idx];                         // @copy-back
            swaps++;                                                // @hide
            stepAt(depth, start, hi, "overwrite", "copy-back",      // @hide
                   start + idx, result[idx]);                       // @hide
        }
    }

    static void sort(int[] arr, int start, int end, int depth) {
        if (end - start > 1) {                                      // @split
            int mid = (start + end) / 2;
            sort(arr, start, mid, depth + 1);                       // @sortleft
            sort(arr, mid, end, depth + 1);                         // @sortright
            int[] left = Arrays.copyOfRange(arr, start, mid);
            int[] right = Arrays.copyOfRange(arr, mid, end);
            merge(arr, left, right, start, depth);
        }
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
            if (!variant.equals("lt") && !variant.equals("le")) {
                System.out.print(out);
                System.out.println("error unknown variant " + variant);
                System.exit(2);
            }
            int[] arr = new int[n];
            for (int k = 0; k < n; k++) arr[k] = Integer.parseInt(in[p++]);
            comparisons = 0;
            swaps = 0;
            stable = variant.equals("le");
            sort(arr, 0, n, 0);
            stepAt(0, 0, n - 1, "done", null);
            out.append("sorted");
            for (int value : arr) out.append(' ').append(value);
            out.append("\ncomparisons ").append(comparisons)
               .append("\nswaps ").append(swaps).append("\nend\n");
        }
        System.out.print(out);
    }
}
