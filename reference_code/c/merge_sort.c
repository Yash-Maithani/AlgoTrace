/* Merge Sort in C11, a translation of sorting_algorithms/merge_sort.py.
 * Input and output: reference_code/README.md. The second count is writes,
 * reported as swaps, exactly as the site does. Variant lt compares with <
 * (not stable), le with <= (stable).
 */
// lesson:variants lt le
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Plumbing: the counts the site reports and the step trace. */
static long comparisons;
static long swaps;
static int stable;

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

// lesson:start
void merge(int arr[], int left[], int left_len, int right[], int right_len, int start, int depth) {
    int hi = start + left_len + right_len - 1;                 // @hide
    int *result = malloc(sizeof(int) * (size_t)(left_len + right_len));
    int i = 0, j = 0, k = 0;
    while (i < left_len && j < right_len) {                     // @merge-compare
        comparisons++;                                          // @hide
        step_at(depth, start, hi, "compare", "merge-compare", 2, // @hide
                start + i, left[i], start + left_len + j, right[j]); // @hide
        if (!stable) {                                          // @hide
            if (left[i] < right[j]) {                           // @only:lt
                result[k++] = left[i++];                        // @only:lt
            } else {                                            // @only:lt
                result[k++] = right[j++];                       // @only:lt
            }                                                   // @only:lt
        } else {                                                // @hide
            if (left[i] <= right[j]) {                          // @only:le
                result[k++] = left[i++];                        // @only:le
            } else {                                            // @only:le
                result[k++] = right[j++];                       // @only:le
            }                                                   // @only:le
        }                                                       // @hide
    }
    while (i < left_len) result[k++] = left[i++];
    while (j < right_len) result[k++] = right[j++];
    for (int idx = 0; idx < k; idx++) {
        arr[start + idx] = result[idx];                         // @copy-back
        swaps++;                                                // @hide
        step_at(depth, start, hi, "overwrite", "copy-back", 1,  // @hide
                start + idx, result[idx]);                      // @hide
    }
    free(result);
}

void sort(int arr[], int start, int end, int depth) {
    if (end - start > 1) {                                      // @split
        int mid = (start + end) / 2;
        sort(arr, start, mid, depth + 1);                       // @sortleft
        sort(arr, mid, end, depth + 1);                         // @sortright
        int left_len = mid - start, right_len = end - mid;
        int *left = malloc(sizeof(int) * (size_t)left_len);
        int *right = malloc(sizeof(int) * (size_t)right_len);
        memcpy(left, arr + start, sizeof(int) * (size_t)left_len);
        memcpy(right, arr + mid, sizeof(int) * (size_t)right_len);
        merge(arr, left, left_len, right, right_len, start, depth);
        free(left);
        free(right);
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
        if (strcmp(variant, "lt") && strcmp(variant, "le")) {
            printf("error unknown variant %s\n", variant);
            return 2;
        }
        int *arr = malloc(sizeof(int) * (size_t)(n > 0 ? n : 1));
        for (int k = 0; k < n; k++) {
            if (scanf("%d", &arr[k]) != 1) return 1;
        }
        comparisons = 0;
        swaps = 0;
        stable = strcmp(variant, "le") == 0;
        sort(arr, 0, n, 0);
        step_at(0, 0, n - 1, "done", NULL, 0);
        printf("sorted");
        for (int k = 0; k < n; k++) printf(" %d", arr[k]);
        printf("\ncomparisons %ld\nswaps %ld\nend\n", comparisons, swaps);
        free(arr);
    }
    return 0;
}
