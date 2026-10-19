/* Radix Sort in C11, a translation of sorting_algorithms/radix_sort.py.
 * Least significant digit first, base 10, told the key range in advance,
 * whole numbers from 0 to 99, so it compares nothing. Input and output:
 * reference_code/README.md. The second count is writes, reported as swaps,
 * exactly as the site does.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define KEY_MAX 99

/* Plumbing: the counts the site reports and the step trace. */
static long comparisons;
static long swaps;

/* index < 0: no index:value pair. bucket < 0: no bucket. `left` is how many
   values that bucket holds as the step is drawn. */
static void step(const char *action, const char *line, int index, int value,
                 int bucket, int left, int place)
{
    printf("step %s %s", action, line ? line : "-");
    if (index >= 0) printf(" %d:%d", index, value);
    if (bucket >= 0) printf(" bucket=%d size=%d place=%d", bucket, left, place);
    printf("\n");
}

// lesson:start
void radix_sort(int arr[], int n, int k) {
    int *buckets = malloc(sizeof(int) * 10 * (size_t)(n > 0 ? n : 1));
    int size[10];
    for (int place = 1; k / place > 0; place *= 10) {
        for (int d = 0; d < 10; d++) size[d] = 0;
        for (int i = 0; i < n; i++) {
            int digit = arr[i] / place % 10;
            buckets[digit * n + size[digit]++] = arr[i];        // @drop
            step("bucket", "drop", i, arr[i], digit, size[digit], place); // @hide
        }
        int pos = 0;
        for (int b = 0; b < 10; b++) {
            for (int j = 0; j < size[b]; j++) {
                arr[pos] = buckets[b * n + j];                  // @write
                swaps++;                                        // @hide
                step("overwrite", "write", pos, arr[pos], b, size[b] - j - 1, place); // @hide
                pos++;
            }
        }
    }
    free(buckets);
    step("done", NULL, -1, 0, -1, 0, 0);                        // @hide
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
        radix_sort(arr, n, KEY_MAX);
        printf("sorted");
        for (int k = 0; k < n; k++) printf(" %d", arr[k]);
        printf("\ncomparisons %ld\nswaps %ld\nend\n", comparisons, swaps);
        free(arr);
    }
    return 0;
}
