/* Counting Sort in C11, a translation of sorting_algorithms/counting_sort.py.
 * Told the key range in advance, whole numbers from 0 to 99, so it compares
 * nothing. Input and output: reference_code/README.md. The second count is
 * writes, reported as swaps, exactly as the site does.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define KEY_MAX 99

/* Plumbing: the counts the site reports and the step trace. */
static long comparisons;
static long swaps;
static const int *shown;

/* index < 0: no index:value pair. lo < 0: no slots of the count list. */
static void step(const char *action, const char *line, int index, int value, int lo, int hi)
{
    printf("step %s %s", action, line ? line : "-");
    if (index >= 0) printf(" %d:%d", index, value);
    if (lo >= 0) printf(" cells=%d:%d count=%d", lo, hi, shown[lo]);
    printf("\n");
}

// lesson:start
void counting_sort(int arr[], int n, int k) {
    int *count = calloc((size_t)k + 1, sizeof(int));
    shown = count;                                              // @hide
    for (int i = 0; i < n; i++) {
        count[arr[i]]++;                                        // @tally
        step("count", "tally", i, arr[i], arr[i], arr[i]);      // @hide
    }
    int pos = 0;
    int empty_from = -1;                                        // @hide
    for (int v = 0; v <= k; v++) {                              // @scan
        if (count[v] == 0) {                                    // @hide
            if (empty_from < 0) empty_from = v;                 // @hide
            if (v < k) continue;                                // @hide
        }                                                       // @hide
        if (empty_from >= 0) {                                  // @hide
            step("select", "scan", -1, 0, empty_from, count[v] == 0 ? v : v - 1); // @hide
            empty_from = -1;                                    // @hide
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
    free(count);
    step("done", NULL, -1, 0, -1, 0);                           // @hide
}
// lesson:end

int main(void)
{
    int cases;
    if (scanf("%d", &cases) != 1) return 1;
    while (cases-- > 0) {
        char variant[32];
        unsigned long seed;
        int target, n;
        if (scanf("%31s %lu %d %d", variant, &seed, &target, &n) != 4) return 1;
        if (strcmp(variant, "-")) {
            printf("error unknown variant %s\n", variant);
            return 2;
        }
        int *arr = malloc(sizeof(int) * (size_t)(n > 0 ? n : 1));
        for (int k = 0; k < n; k++) {
            if (scanf("%d", &arr[k]) != 1) return 1;
            if (arr[k] < 0 || arr[k] > KEY_MAX) {
                printf("error value %d is outside 0 to %d\n", arr[k], KEY_MAX);
                return 3;
            }
        }
        comparisons = 0;
        swaps = 0;
        counting_sort(arr, n, KEY_MAX);
        printf("sorted");
        for (int k = 0; k < n; k++) printf(" %d", arr[k]);
        printf("\ncomparisons %ld\nswaps %ld\nend\n", comparisons, swaps);
        free(arr);
    }
    return 0;
}
