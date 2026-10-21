// Linear Search in C++17, a translation of algotrace/algorithms/searching/linear_search.py.
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
int linear_search(const std::vector<int> &arr, int target) {
    for (int i = 0; i < static_cast<int>(arr.size()); i++) {    // @loop
        comparisons++;                                          // @hide
        step("compare", "compare", {i, arr[i]});                // @hide
        if (arr[i] == target) {                                 // @compare
            step("found", "found", {i, arr[i]});                // @hide
            return i;                                           // @found
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
        int index = linear_search(arr, target);
        std::cout << "index " << index << "\ncomparisons " << comparisons << "\nend\n";
    }
    return 0;
}
