/* Jump Search in C11, a translation of searching_algorithms/jump_search.py.
 * The list must already be sorted; the site refuses an unsorted one before
 * searching, so this program assumes it. Input and output:
 * reference_code/README.md.
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

// lesson:helpers
/* The whole part of the square root, as Python's math.isqrt gives it. */
static int isqrt(int n) {
    int r = 0;
    while ((r + 1) * (r + 1) <= n) r++;
    return r;
}
// lesson:end

// lesson:start
int jump_search(const int arr[], int n, int target) {
    if (n == 0) {                                               // @hide
        step("missing", NULL, 0);                               // @hide
        return -1;                                              // @hide
    }                                                           // @hide
    int block = isqrt(n);
    int low = 0, end = (block < n ? block : n) - 1;
    comparisons++;                                              // @hide
    step("compare", "jump-check", 1, end, arr[end]);            // @hide
    while (arr[end] < target) {                                 // @jump-check
        if (end == n - 1) {
            step("missing", "past-end", 0);                     // @hide
            return -1;                                          // @past-end
        }
        low = end + 1;                                          // @jump
        end = end + block < n - 1 ? end + block : n - 1;
        step("discard", "jump", 1, low - 1, arr[low - 1]);      // @hide
        comparisons++;                                          // @hide
        step("compare", "jump-check", 1, end, arr[end]);        // @hide
    }
    for (int i = low; i <= end; i++) {
        comparisons++;                                          // @hide
        step("compare", "scan", 1, i, arr[i]);                  // @hide
        if (arr[i] == target) {                                 // @scan
            step("found", "found", 1, i, arr[i]);               // @hide
            return i;                                           // @found
        }
        if (arr[i] > target) {
            break;
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
        int index = jump_search(arr, n, target);
        printf("index %d\ncomparisons %ld\nend\n", index, comparisons);
        free(arr);
    }
    return 0;
}
