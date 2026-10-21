// Merge Sort in C++17, a translation of algotrace/algorithms/sorting/merge_sort.py.
// Input and output: reference_code/README.md. The second count is writes,
// reported as swaps, exactly as the site does. Variant lt compares with <
// (not stable), le with <= (stable).
// lesson:variants lt le
#include <initializer_list>
#include <iostream>
#include <string>
#include <vector>

// Plumbing: the counts the site reports and the step trace.
static long comparisons = 0;
static long swaps = 0;
static bool stable = false;

static void step_at(int depth, int lo, int hi, const char *action, const char *line,
                    std::initializer_list<int> pairs = {})
{
    std::cout << "step " << action << ' ' << (line ? line : "-");
    for (auto it = pairs.begin(); it != pairs.end(); it += 2) {
        std::cout << ' ' << *it << ':' << *(it + 1);
    }
    std::cout << " depth=" << depth << " range=" << lo << ':' << hi << '\n';
}

// lesson:start
void merge(std::vector<int> &arr, const std::vector<int> &left, const std::vector<int> &right, int start, int depth) {
    int left_len = static_cast<int>(left.size());
    int right_len = static_cast<int>(right.size());
    int hi = start + left_len + right_len - 1;                 // @hide
    std::vector<int> result;
    int i = 0, j = 0;
    while (i < left_len && j < right_len) {                     // @merge-compare
        comparisons++;                                          // @hide
        step_at(depth, start, hi, "compare", "merge-compare",   // @hide
                {start + i, left[i], start + left_len + j, right[j]}); // @hide
        if (!stable) {                                          // @hide
            if (left[i] < right[j]) {                           // @only:lt
                result.push_back(left[i++]);                    // @only:lt
            } else {                                            // @only:lt
                result.push_back(right[j++]);                   // @only:lt
            }                                                   // @only:lt
        } else {                                                // @hide
            if (left[i] <= right[j]) {                          // @only:le
                result.push_back(left[i++]);                    // @only:le
            } else {                                            // @only:le
                result.push_back(right[j++]);                   // @only:le
            }                                                   // @only:le
        }                                                       // @hide
    }
    result.insert(result.end(), left.begin() + i, left.end());
    result.insert(result.end(), right.begin() + j, right.end());
    for (int idx = 0; idx < static_cast<int>(result.size()); idx++) {
        arr[start + idx] = result[idx];                         // @copy-back
        swaps++;                                                // @hide
        step_at(depth, start, hi, "overwrite", "copy-back",     // @hide
                {start + idx, result[idx]});                    // @hide
    }
}

void sort(std::vector<int> &arr, int start, int end, int depth) {
    if (end - start > 1) {                                      // @split
        int mid = (start + end) / 2;
        sort(arr, start, mid, depth + 1);                       // @sortleft
        sort(arr, mid, end, depth + 1);                         // @sortright
        std::vector<int> left(arr.begin() + start, arr.begin() + mid);
        std::vector<int> right(arr.begin() + mid, arr.begin() + end);
        merge(arr, left, right, start, depth);
    }
}
// lesson:end

int main()
{
    std::ios::sync_with_stdio(false);
    int cases = 0;
    if (!(std::cin >> cases)) return 1;
    while (cases-- > 0) {
        std::string variant;
        unsigned long seed = 0;
        int target = 0, n = 0;
        if (!(std::cin >> variant >> seed >> target >> n)) return 1;
        if (variant != "lt" && variant != "le") {
            std::cout << "error unknown variant " << variant << '\n';
            return 2;
        }
        std::vector<int> arr(static_cast<size_t>(n));
        for (int &value : arr) {
            if (!(std::cin >> value)) return 1;
        }
        comparisons = 0;
        swaps = 0;
        stable = variant == "le";
        sort(arr, 0, n, 0);
        step_at(0, 0, n - 1, "done", nullptr);
        std::cout << "sorted";
        for (int value : arr) std::cout << ' ' << value;
        std::cout << "\ncomparisons " << comparisons << "\nswaps " << swaps << "\nend\n";
    }
    return 0;
}
