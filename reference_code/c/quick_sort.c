/* Quick Sort in C11, a translation of sorting_algorithms/quick_sort.py.
 * Input and output: reference_code/README.md. Variant last takes the last
 * value as pivot; middle and random swap their choice to the end first and
 * run the same partition. random draws from mulberry32, the same generator
 * as sorting_algorithms/seeded.py, so a seed gives the same run as Python.
 */
// lesson:variants last middle random
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Plumbing: the counts the site reports and the step trace. */
static long comparisons;
static long swaps;

enum { PIVOT_LAST, PIVOT_MIDDLE, PIVOT_RANDOM };
static int pivot_rule;

static void step_at(int depth, int lo, int hi, const char *action,
                    const char *line, int pairs, ...)
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
    printf(" depth=%d range=%d:%d\n", depth, lo, hi);
}

/* mulberry32, as in sorting_algorithms/seeded.py: a float in [0, 1). */
static uint32_t rng_state;

static double rand_unit(void)
{
    rng_state += 0x6D2B79F5u;
    uint32_t t = rng_state;
    t = (t ^ (t >> 15)) * (t | 1u);
    t ^= t + (t ^ (t >> 7)) * (t | 61u);
    return (double)(t ^ (t >> 14)) / 4294967296.0;
}

static void swap(int *a, int *b)
{
    int t = *a;
    *a = *b;
    *b = t;
}

// lesson:start
int partition(int arr[], int low, int high, int depth) {       // @partition
    if (pivot_rule == PIVOT_MIDDLE) {                           // @hide
        int mid = (low + high) / 2;                             // @only:middle
        swap(&arr[mid], &arr[high]);                            // @choose-pivot @only:middle
        swaps++;                                                // @hide
        step_at(depth, low, high, "swap", "choose-pivot", 2,    // @hide
                mid, arr[mid], high, arr[high]);                // @hide
    } else if (pivot_rule == PIVOT_RANDOM) {                    // @hide
        int r = low + (int)(rand_unit() * (high - low + 1));    // @only:random
        if (r != high) {                                        // @only:random
            swap(&arr[r], &arr[high]);                          // @choose-pivot @only:random
            swaps++;                                            // @hide
            step_at(depth, low, high, "swap", "choose-pivot", 2, // @hide
                    r, arr[r], high, arr[high]);                // @hide
        }                                                       // @only:random
    }                                                           // @hide
    int pivot = arr[high];                                      // @pivot
    int i = low - 1;
    for (int j = low; j < high; j++) {                          // @iloop
        comparisons++;                                          // @hide
        step_at(depth, low, high, "compare", "compare", 2,      // @hide
                j, arr[j], high, pivot);                        // @hide
        if (arr[j] < pivot) {                                   // @compare
            i++;
            swap(&arr[i], &arr[j]);                             // @swap
            swaps++;                                            // @hide
            step_at(depth, low, high, "swap", "swap", 2,        // @hide
                    i, arr[i], j, arr[j]);                      // @hide
        }
    }
    swap(&arr[i + 1], &arr[high]);                              // @place-pivot
    swaps++;                                                    // @hide
    step_at(depth, low, high, "place", "place-pivot", 2,        // @hide
            i + 1, arr[i + 1], high, arr[high]);                // @hide
    return i + 1;
}

void sort(int arr[], int low, int high, int depth) {
    if (low < high) {
        int pi = partition(arr, low, high, depth);
        sort(arr, low, pi - 1, depth + 1);                      // @recurse-left
        sort(arr, pi + 1, high, depth + 1);                     // @recurse-right
    }
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
        if (!strcmp(variant, "last")) pivot_rule = PIVOT_LAST;
        else if (!strcmp(variant, "middle")) pivot_rule = PIVOT_MIDDLE;
        else if (!strcmp(variant, "random")) pivot_rule = PIVOT_RANDOM;
        else {
            printf("error unknown variant %s\n", variant);
            return 2;
        }
        int *arr = malloc(sizeof(int) * (size_t)(n > 0 ? n : 1));
        for (int k = 0; k < n; k++) {
            if (scanf("%d", &arr[k]) != 1) return 1;
        }
        comparisons = 0;
        swaps = 0;
        rng_state = (uint32_t)seed;
        sort(arr, 0, n - 1, 0);
        step_at(0, 0, n - 1, "done", NULL, 0);
        printf("sorted");
        for (int k = 0; k < n; k++) printf(" %d", arr[k]);
        printf("\ncomparisons %ld\nswaps %ld\nend\n", comparisons, swaps);
        free(arr);
    }
    return 0;
}
