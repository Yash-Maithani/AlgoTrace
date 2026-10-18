/* Linear Search in C11, a translation of searching_algorithms/linear_search.py.
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
int linear_search(const int arr[], int n, int target) {
    for (int i = 0; i < n; i++) {                               // @loop
        comparisons++;                                          // @hide
        step("compare", "compare", 1, i, arr[i]);               // @hide
        if (arr[i] == target) {                                 // @compare
            step("found", "found", 1, i, arr[i]);               // @hide
            return i;                                           // @found
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
        int index = linear_search(arr, n, target);
        printf("index %d\ncomparisons %ld\nend\n", index, comparisons);
        free(arr);
    }
    return 0;
}
