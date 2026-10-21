/* Insertion Sort in C11, a translation of algotrace/algorithms/sorting/insertion_sort.py.
 * Input and output: reference_code/README.md. The second count is shifts,
 * reported as swaps, exactly as the site does.
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

// lesson:start
void insertion_sort(int arr[], int n) {
    for (int i = 1; i < n; i++) {                               // @outer
        int key = arr[i];                                       // @key
        int j = i - 1;
        while (j >= 0) {                                        // @inner
            comparisons++;                                      // @hide
            step("compare", "compare", 1, j, arr[j]);           // @hide
            if (key < arr[j]) {                                 // @compare
                int destination = j + 1;                        // @hide
                arr[j + 1] = arr[j];                            // @shift
                swaps++;                                        // @hide
                j--;
                step("overwrite", "shift", 1, destination, arr[destination]); // @hide
            } else {
                break;
            }
        }
        arr[j + 1] = key;                                       // @place
        step("overwrite", "place", 1, j + 1, arr[j + 1]);       // @hide
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
        insertion_sort(arr, n);
        printf("sorted");
        for (int k = 0; k < n; k++) printf(" %d", arr[k]);
        printf("\ncomparisons %ld\nswaps %ld\nend\n", comparisons, swaps);
        free(arr);
    }
    return 0;
}
