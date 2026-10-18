/* Selection Sort in C11, a translation of sorting_algorithms/selection_sort.py.
 * Input and output: reference_code/README.md.
 */
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Plumbing: the counts the site reports and the step trace. */
static long comparisons;
static long swaps;

static void step(const char *action, const char *line, int pairs, ...)
{
    va_list args;
    va_start(args, pairs);
    printf("step %s %s", action, line ? line : "-");
    for (int k = 0; k < pairs; k++) {
        int index = va_arg(args, int);
        int value = va_arg(args, int);
        printf(" %d:%d", index, value);
    }
    va_end(args);
    printf("\n");
}

static void swap(int *a, int *b)
{
    int t = *a;
    *a = *b;
    *b = t;
}

// lesson:start
void selection_sort(int arr[], int n) {
    for (int i = 0; i < n; i++) {                               // @outer
        int min_idx = i;                                        // @min-init
        step("select", "min-init", 1, i, arr[i]);               // @hide
        for (int j = i + 1; j < n; j++) {                       // @inner
            comparisons++;                                      // @hide
            step("compare", "compare", 2, min_idx, arr[min_idx], j, arr[j]); // @hide
            if (arr[min_idx] > arr[j]) {                        // @compare
                min_idx = j;                                    // @update-min
                step("select", "update-min", 1, min_idx, arr[min_idx]); // @hide
            }
        }
        if (i != min_idx) {
            swap(&arr[i], &arr[min_idx]);                       // @swap
            swaps++;                                            // @hide
            step("swap", "swap", 2, i, arr[i], min_idx, arr[min_idx]); // @hide
        }
    }
    step("done", NULL, 0);                                      // @hide
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
        }
        comparisons = 0;
        swaps = 0;
        selection_sort(arr, n);
        printf("sorted");
        for (int k = 0; k < n; k++) printf(" %d", arr[k]);
        printf("\ncomparisons %ld\nswaps %ld\nend\n", comparisons, swaps);
        free(arr);
    }
    return 0;
}
