/* Bubble Sort in C11, a translation of sorting_algorithms/bubble_sort.py.
 * Input and output: reference_code/README.md.
 */
// lesson:variants off on
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Plumbing: the counts the site reports and the step trace. */
static long comparisons;
static long swaps;
static int early_exit;

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

// lesson:helpers
static void swap(int *a, int *b)
{
    int t = *a;
    *a = *b;
    *b = t;
}
// lesson:end

// lesson:start
void bubble_sort(int arr[], int n) {
    for (int i = 0; i < n; i++) {                               // @pass
        int swapped = 0;                                        // @only:on
        for (int j = 0; j < n - i - 1; j++) {                   // @walk
            comparisons++;                                      // @hide
            step("compare", "compare", 2, j, arr[j], j + 1, arr[j + 1]); // @hide
            if (arr[j] > arr[j + 1]) {                          // @compare
                swap(&arr[j], &arr[j + 1]);                     // @swap
                swapped = 1;                                    // @only:on
                swaps++;                                        // @hide
                step("swap", "swap", 2, j, arr[j], j + 1, arr[j + 1]); // @hide
            }
        }
        if (early_exit) {                                       // @hide
            if (!swapped) break;                                // @only:on
        }                                                       // @hide
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
        if (strcmp(variant, "off") && strcmp(variant, "on")) {
            printf("error unknown variant %s\n", variant);
            return 2;
        }
        int *arr = malloc(sizeof(int) * (size_t)(n > 0 ? n : 1));
        for (int k = 0; k < n; k++) {
            if (scanf("%d", &arr[k]) != 1) return 1;
        }
        comparisons = 0;
        swaps = 0;
        early_exit = strcmp(variant, "on") == 0;
        bubble_sort(arr, n);
        printf("sorted");
        for (int k = 0; k < n; k++) printf(" %d", arr[k]);
        printf("\ncomparisons %ld\nswaps %ld\nend\n", comparisons, swaps);
        free(arr);
    }
    return 0;
}
