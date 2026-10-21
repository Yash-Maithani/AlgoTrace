// Jump Search in C++17, a translation of algotrace/algorithms/searching/jump_search.py.
// The list must already be sorted; the site refuses an unsorted one before
// searching, so this program assumes it. Input and output:
// reference_code/README.md.
#include <algorithm>
#include <initializer_list>
#include <iostream>
#include <string>
#include <vector>

// Plumbing: the count the site reports and the step trace.
static long comparisons = 0;

static void step(const char *action, const char *line, std::initializer_list<int> pairs = {})
{
    std::cout << "step " << action << ' ' << (line ? line : "-");
    for (auto it = pairs.begin(); it != pairs.end(); it += 2) {
        std::cout << ' ' << *it << ':' << *(it + 1);
    }
    std::cout << '\n';
}

// lesson:helpers
// The whole part of the square root, as Python's math.isqrt gives it.
static int isqrt(int n) {
    int r = 0;
    while ((r + 1) * (r + 1) <= n) r++;
    return r;
}
// lesson:end

// lesson:start
int jump_search(const std::vector<int> &arr, int target) {
    int n = static_cast<int>(arr.size());
    if (n == 0) {                                               // @hide
        step("missing", nullptr);                               // @hide
        return -1;                                              // @hide
    }                                                           // @hide
    int block = isqrt(n);
    int low = 0, end = std::min(block, n) - 1;
    comparisons++;                                              // @hide
    step("compare", "jump-check", {end, arr[end]});             // @hide
    while (arr[end] < target) {                                 // @jump-check
        if (end == n - 1) {
            step("missing", "past-end");                        // @hide
            return -1;                                          // @past-end
        }
        low = end + 1;                                          // @jump
        end = std::min(end + block, n - 1);
        step("discard", "jump", {low - 1, arr[low - 1]});       // @hide
        comparisons++;                                          // @hide
        step("compare", "jump-check", {end, arr[end]});         // @hide
    }
    for (int i = low; i <= end; i++) {
        comparisons++;                                          // @hide
        step("compare", "scan", {i, arr[i]});                   // @hide
        if (arr[i] == target) {                                 // @scan
            step("found", "found", {i, arr[i]});                // @hide
            return i;                                           // @found
        }
        if (arr[i] > target) {
            break;
        }
    }
    step("missing", "missing");                                 // @hide
    return -1;                                                  // @missing
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
        if (variant != "-") {
            std::cout << "error unknown variant " << variant << '\n';
            return 2;
        }
        std::vector<int> arr(static_cast<size_t>(n));
        for (int &value : arr) {
            if (!(std::cin >> value)) return 1;
        }
        comparisons = 0;
        int index = jump_search(arr, target);
        std::cout << "index " << index << "\ncomparisons " << comparisons << "\nend\n";
    }
    return 0;
}
