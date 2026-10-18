// Binary Search in C++17, a translation of searching_algorithms/binary_search.py.
// Iterative, as the Python is. The list must already be sorted; the site
// refuses an unsorted one before searching, so this program assumes it.
// Input and output: reference_code/README.md.
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

// lesson:start
int binary_search(const std::vector<int> &arr, int target) {
    int low = 0, high = static_cast<int>(arr.size()) - 1;
    while (low <= high) {                                       // @loop
        int mid = (low + high) / 2;                             // @mid
        comparisons++;                                          // @hide
        step("compare", "compare", {mid, arr[mid]});            // @hide
        if (arr[mid] == target) {                               // @compare
            step("found", "found", {mid, arr[mid]});            // @hide
            return mid;                                         // @found
        }
        if (arr[mid] < target) {                                // @go-right
            low = mid + 1;
            step("discard", "go-right", {mid, arr[mid]});       // @hide
        } else {                                                // @go-left
            high = mid - 1;
            step("discard", "go-left", {mid, arr[mid]});        // @hide
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
        int index = binary_search(arr, target);
        std::cout << "index " << index << "\ncomparisons " << comparisons << "\nend\n";
    }
    return 0;
}
