// Heap Sort in C++17, a translation of algotrace/algorithms/sorting/heap_sort.py.
// Input and output: reference_code/README.md. heapify calls itself, as the
// Python does, which is why the lesson gives O(log n) auxiliary space.
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
void heapify(std::vector<int> &arr, int n, int i) {
    int largest = i;
    int l = 2 * i + 1;
    int r = 2 * i + 2;
    if (l < n) {                                                // @cmp-left
        comparisons++;                                          // @hide
        step("compare", "cmp-left", {l, arr[l], largest, arr[largest]}); // @hide
        if (arr[l] > arr[largest]) largest = l;
    }
    if (r < n) {                                                // @cmp-right
        comparisons++;                                          // @hide
        step("compare", "cmp-right", {r, arr[r], largest, arr[largest]}); // @hide
        if (arr[r] > arr[largest]) largest = r;
    }
    if (largest != i) {                                         // @swap-down
        std::swap(arr[i], arr[largest]);
        swaps++;                                                // @hide
        step("swap", "swap-down", {i, arr[i], largest, arr[largest]}); // @hide
        heapify(arr, n, largest);
    }
}

void heap_sort(std::vector<int> &arr) {
    int n = static_cast<int>(arr.size());
    for (int i = n / 2 - 1; i >= 0; i--) heapify(arr, n, i);   // @build
    for (int i = n - 1; i > 0; i--) {                           // @extract
        std::swap(arr[i], arr[0]);                              // @swap-root
        swaps++;                                                // @hide
        step("swap", "swap-root", {0, arr[0], i, arr[i]});      // @hide
        heapify(arr, i, 0);
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
        heap_sort(arr);
        std::cout << "sorted";
        for (int value : arr) std::cout << ' ' << value;
        std::cout << "\ncomparisons " << comparisons << "\nswaps " << swaps << "\nend\n";
    }
    return 0;
}
