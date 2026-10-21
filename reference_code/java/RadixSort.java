// Radix Sort in Java 17, a translation of algotrace/algorithms/sorting/radix_sort.py.
// Least significant digit first, base 10, told the key range in advance,
// whole numbers from 0 to 99, so it compares nothing. Input and output:
// reference_code/README.md. The second count is writes, reported as swaps,
// exactly as the site does.
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

public class RadixSort {
    static final int KEY_MAX = 99;

    // Plumbing: the counts the site reports and the step trace.
    static long comparisons;
    static long swaps;
    static final StringBuilder out = new StringBuilder();

    // index < 0: no index:value pair. bucket < 0: no bucket. `left` is how
    // many values that bucket holds as the step is drawn.
    static void step(String action, String line, int index, int value,
                     int bucket, int left, int place) {
        out.append("step ").append(action).append(' ').append(line == null ? "-" : line);
        if (index >= 0) out.append(' ').append(index).append(':').append(value);
        if (bucket >= 0) out.append(" bucket=").append(bucket).append(" size=").append(left)
                            .append(" place=").append(place);
        out.append('\n');
    }

    // lesson:start
    static void radixSort(int[] arr, int k) {
        for (int place = 1; k / place > 0; place *= 10) {
            List<List<Integer>> buckets = new ArrayList<>();
            for (int d = 0; d < 10; d++) buckets.add(new ArrayList<>());
            for (int i = 0; i < arr.length; i++) {
                int digit = arr[i] / place % 10;
                buckets.get(digit).add(arr[i]);                     // @drop
                step("bucket", "drop", i, arr[i], digit, buckets.get(digit).size(), place); // @hide
            }
            int pos = 0;
            for (int b = 0; b < 10; b++) {
                int left = buckets.get(b).size();                   // @hide
                for (int value : buckets.get(b)) {
                    arr[pos] = value;                               // @write
                    swaps++;                                        // @hide
                    step("overwrite", "write", pos, value, b, --left, place); // @hide
                    pos++;
                }
            }
        }
        step("done", null, -1, 0, -1, 0, 0);                        // @hide
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
            radixSort(arr, KEY_MAX);
            out.append("sorted");
            for (int value : arr) out.append(' ').append(value);
            out.append("\ncomparisons ").append(comparisons)
               .append("\nswaps ").append(swaps).append("\nend\n");
        }
        System.out.print(out);
    }
}
