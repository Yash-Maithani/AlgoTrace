// Selection Sort in C++17, a translation of algotrace/algorithms/sorting/selection_sort.py.
// Input and output: reference_code/README.md.
#include <initializer_list>
#include <iostream>
#include <string>
#include <utility>
#include <vector>

// Plumbing: the counts the site reports and the step trace.
static long comparisons = 0;
static long swaps = 0;

static void step(const char *action, const char *line, std::initializer_list<int> pairs = {})
{
    std::cout << "step " << action << ' ' << (line ? line : "-");
    for (auto it = pairs.begin(); it != pairs.end(); it += 2) {
        std::cout << ' ' << *it << ':' << *(it + 1);
    }
    std::cout << '\n';
}

// lesson:start
void selection_sort(std::vector<int> &arr) {
    int n = static_cast<int>(arr.size());
    for (int i = 0; i < n; i++) {                               // @outer
        int min_idx = i;                                        // @min-init
        step("select", "min-init", {i, arr[i]});                // @hide
        for (int j = i + 1; j < n; j++) {                       // @inner
            comparisons++;                                      // @hide
            step("compare", "compare", {min_idx, arr[min_idx], j, arr[j]}); // @hide
            if (arr[min_idx] > arr[j]) {                        // @compare
                min_idx = j;                                    // @update-min
                step("select", "update-min", {min_idx, arr[min_idx]}); // @hide
            }
        }
        if (i != min_idx) {
            std::swap(arr[i], arr[min_idx]);                    // @swap
            swaps++;                                            // @hide
            step("swap", "swap", {i, arr[i], min_idx, arr[min_idx]}); // @hide
        }
    }
    step("done", nullptr);                                      // @hide
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
        swaps = 0;
        selection_sort(arr);
        std::cout << "sorted";
        for (int value : arr) std::cout << ' ' << value;
        std::cout << "\ncomparisons " << comparisons << "\nswaps " << swaps << "\nend\n";
    }
    return 0;
}
