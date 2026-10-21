/* Binary Search in C11, a translation of algotrace/algorithms/searching/binary_search.py.
 * Iterative, as the Python is. The list must already be sorted; the site
 * refuses an unsorted one before searching, so this program assumes it.
 * Input and output: reference_code/README.md.
 */
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Plumbing: the count the site reports and the step trace. */
static long comparisons;

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
int binary_search(const int arr[], int n, int target) {
    int low = 0, high = n - 1;
    while (low <= high) {                                       // @loop
        int mid = (low + high) / 2;                             // @mid
        comparisons++;                                          // @hide
        step("compare", "compare", 1, mid, arr[mid]);           // @hide
        if (arr[mid] == target) {                               // @compare
            step("found", "found", 1, mid, arr[mid]);           // @hide
            return mid;                                         // @found
        }
        if (arr[mid] < target) {                                // @go-right
            low = mid + 1;
            step("discard", "go-right", 1, mid, arr[mid]);      // @hide
        } else {                                                // @go-left
            high = mid - 1;
            step("discard", "go-left", 1, mid, arr[mid]);       // @hide
        }
    }
    step("missing", "missing", 0);                              // @hide
    return -1;                                                  // @missing
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
        int index = binary_search(arr, n, target);
        printf("index %d\ncomparisons %ld\nend\n", index, comparisons);
        free(arr);
    }
    return 0;
}
