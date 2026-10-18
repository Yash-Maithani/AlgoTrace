// Heap Sort in Java 17, a translation of sorting_algorithms/heap_sort.py.
// Input and output: reference_code/README.md. heapify calls itself, as the
// Python does, which is why the lesson gives O(log n) auxiliary space.
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public class HeapSort {
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

    // lesson:helpers
    static void swap(int[] arr, int a, int b) {
        int t = arr[a];
        arr[a] = arr[b];
        arr[b] = t;
    }
    // lesson:end

    // lesson:start
    static void heapify(int[] arr, int n, int i) {
        int largest = i;
        int l = 2 * i + 1;
        int r = 2 * i + 2;
        if (l < n) {                                                // @cmp-left
            comparisons++;                                          // @hide
            step("compare", "cmp-left", l, arr[l], largest, arr[largest]); // @hide
            if (arr[l] > arr[largest]) largest = l;
        }
        if (r < n) {                                                // @cmp-right
            comparisons++;                                          // @hide
            step("compare", "cmp-right", r, arr[r], largest, arr[largest]); // @hide
            if (arr[r] > arr[largest]) largest = r;
        }
        if (largest != i) {                                         // @swap-down
            swap(arr, i, largest);
            swaps++;                                                // @hide
            step("swap", "swap-down", i, arr[i], largest, arr[largest]); // @hide
            heapify(arr, n, largest);
        }
    }

    static void heapSort(int[] arr) {
        int n = arr.length;
        for (int i = n / 2 - 1; i >= 0; i--) heapify(arr, n, i);   // @build
        for (int i = n - 1; i > 0; i--) {                           // @extract
            swap(arr, i, 0);                                        // @swap-root
            swaps++;                                                // @hide
            step("swap", "swap-root", 0, arr[0], i, arr[i]);        // @hide
            heapify(arr, i, 0);
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
            heapSort(arr);
            out.append("sorted");
            for (int value : arr) out.append(' ').append(value);
            out.append("\ncomparisons ").append(comparisons)
               .append("\nswaps ").append(swaps).append("\nend\n");
        }
        System.out.print(out);
    }
}
