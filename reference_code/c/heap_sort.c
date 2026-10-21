/* Heap Sort in C11, a translation of algotrace/algorithms/sorting/heap_sort.py.
 * Input and output: reference_code/README.md. heapify calls itself, as the
 * Python does, which is why the lesson gives O(log n) auxiliary space.
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

// lesson:helpers
static void swap(int *a, int *b)
{
    int t = *a;
    *a = *b;
    *b = t;
}
// lesson:end

// lesson:start
void heapify(int arr[], int n, int i) {
    int largest = i;
    int l = 2 * i + 1;
    int r = 2 * i + 2;
    if (l < n) {                                                // @cmp-left
        comparisons++;                                          // @hide
        step("compare", "cmp-left", 2, l, arr[l], largest, arr[largest]); // @hide
        if (arr[l] > arr[largest]) largest = l;
    }
    if (r < n) {                                                // @cmp-right
        comparisons++;                                          // @hide
        step("compare", "cmp-right", 2, r, arr[r], largest, arr[largest]); // @hide
        if (arr[r] > arr[largest]) largest = r;
    }
    if (largest != i) {                                         // @swap-down
        swap(&arr[i], &arr[largest]);
        swaps++;                                                // @hide
        step("swap", "swap-down", 2, i, arr[i], largest, arr[largest]); // @hide
        heapify(arr, n, largest);
    }
}

void heap_sort(int arr[], int n) {
    for (int i = n / 2 - 1; i >= 0; i--) heapify(arr, n, i);   // @build
    for (int i = n - 1; i > 0; i--) {                           // @extract
        swap(&arr[i], &arr[0]);                                 // @swap-root
        swaps++;                                                // @hide
        step("swap", "swap-root", 2, 0, arr[0], i, arr[i]);     // @hide
        heapify(arr, i, 0);
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
        heap_sort(arr, n);
        printf("sorted");
        for (int k = 0; k < n; k++) printf(" %d", arr[k]);
        printf("\ncomparisons %ld\nswaps %ld\nend\n", comparisons, swaps);
        free(arr);
    }
    return 0;
}
