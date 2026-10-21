// Bubble Sort in C++17, a translation of algotrace/algorithms/sorting/bubble_sort.py.
// Input and output: reference_code/README.md.
// lesson:variants off on
#include <initializer_list>
#include <iostream>
#include <string>
#include <utility>
#include <vector>

// Plumbing: the counts the site reports and the step trace.
static long comparisons = 0;
static long swaps = 0;
static bool early_exit = false;

static void step(const char *action, const char *line, std::initializer_list<int> pairs = {})
{
    std::cout << "step " << action << ' ' << (line ? line : "-");
    for (auto it = pairs.begin(); it != pairs.end(); it += 2) {
        std::cout << ' ' << *it << ':' << *(it + 1);
    }
    std::cout << '\n';
}

// lesson:start
void bubble_sort(std::vector<int> &arr) {
    int n = static_cast<int>(arr.size());
    for (int i = 0; i < n; i++) {                               // @pass
        bool swapped = false;                                   // @only:on
        for (int j = 0; j < n - i - 1; j++) {                   // @walk
            comparisons++;                                      // @hide
            step("compare", "compare", {j, arr[j], j + 1, arr[j + 1]}); // @hide
            if (arr[j] > arr[j + 1]) {                          // @compare
                std::swap(arr[j], arr[j + 1]);                  // @swap
                swapped = true;                                 // @only:on
                swaps++;                                        // @hide
                step("swap", "swap", {j, arr[j], j + 1, arr[j + 1]}); // @hide
            }
        }
        if (early_exit) {                                       // @hide
            if (!swapped) break;                                // @only:on
        }                                                       // @hide
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
        if (variant != "off" && variant != "on") {
            std::cout << "error unknown variant " << variant << '\n';
            return 2;
        }
        std::vector<int> arr(static_cast<size_t>(n));
        for (int &value : arr) {
            if (!(std::cin >> value)) return 1;
        }
        comparisons = 0;
        swaps = 0;
        early_exit = variant == "on";
        bubble_sort(arr);
        std::cout << "sorted";
        for (int value : arr) std::cout << ' ' << value;
        std::cout << "\ncomparisons " << comparisons << "\nswaps " << swaps << "\nend\n";
    }
    return 0;
}
