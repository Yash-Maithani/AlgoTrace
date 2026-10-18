// Insertion Sort in C++17, a translation of sorting_algorithms/insertion_sort.py.
// Input and output: reference_code/README.md. The second count is shifts,
// reported as swaps, exactly as the site does.
#include <initializer_list>
#include <iostream>
#include <string>
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
void insertion_sort(std::vector<int> &arr) {
    int n = static_cast<int>(arr.size());
    for (int i = 1; i < n; i++) {                               // @outer
        int key = arr[i];                                       // @key
        int j = i - 1;
        while (j >= 0) {                                        // @inner
            comparisons++;                                      // @hide
            step("compare", "compare", {j, arr[j]});            // @hide
            if (key < arr[j]) {                                 // @compare
                int destination = j + 1;                        // @hide
                arr[j + 1] = arr[j];                            // @shift
                swaps++;                                        // @hide
                j--;
                step("overwrite", "shift", {destination, arr[destination]}); // @hide
            } else {
                break;
            }
        }
        arr[j + 1] = key;                                       // @place
        step("overwrite", "place", {j + 1, arr[j + 1]});        // @hide
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
        insertion_sort(arr);
        std::cout << "sorted";
        for (int value : arr) std::cout << ' ' << value;
        std::cout << "\ncomparisons " << comparisons << "\nswaps " << swaps << "\nend\n";
    }
    return 0;
}
