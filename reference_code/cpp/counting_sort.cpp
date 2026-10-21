// Counting Sort in C++17, a translation of algotrace/algorithms/sorting/counting_sort.py.
// Told the key range in advance, whole numbers from 0 to 99, so it compares
// nothing. Input and output: reference_code/README.md. The second count is
// writes, reported as swaps, exactly as the site does.
#include <iostream>
#include <string>
#include <vector>

static const int KEY_MAX = 99;

// Plumbing: the counts the site reports and the step trace.
static long comparisons = 0;
static long swaps = 0;
static const std::vector<int> *shown = nullptr;

// index < 0: no index:value pair. lo < 0: no slots of the count list.
static void step(const char *action, const char *line, int index, int value, int lo, int hi)
{
    std::cout << "step " << action << ' ' << (line ? line : "-");
    if (index >= 0) std::cout << ' ' << index << ':' << value;
    if (lo >= 0) std::cout << " cells=" << lo << ':' << hi << " count=" << (*shown)[lo];
    std::cout << '\n';
}

// lesson:start
void counting_sort(std::vector<int> &arr, int k) {
    int n = static_cast<int>(arr.size());
    std::vector<int> count(k + 1, 0);
    shown = &count;                                             // @hide
    for (int i = 0; i < n; i++) {
        count[arr[i]]++;                                        // @tally
        step("count", "tally", i, arr[i], arr[i], arr[i]);      // @hide
    }
    int pos = 0;
    int empty_from = -1;                                        // @hide
    for (int v = 0; v <= k; v++) {                              // @scan
        if (count[v] == 0) {                                    // @hide
            if (empty_from < 0) empty_from = v;                 // @hide
            if (v < k) continue;                                // @hide
        }                                                       // @hide
        if (empty_from >= 0) {                                  // @hide
            step("select", "scan", -1, 0, empty_from, count[v] == 0 ? v : v - 1); // @hide
            empty_from = -1;                                    // @hide
            if (count[v] == 0) continue;                        // @hide
        }                                                       // @hide
        step("select", "scan", -1, 0, v, v);                    // @hide
        for (int c = 0; c < count[v]; c++) {
            arr[pos] = v;                                       // @write
            swaps++;                                            // @hide
            step("overwrite", "write", pos, v, v, v);           // @hide
            pos++;
        }
    }
    step("done", nullptr, -1, 0, -1, 0);                        // @hide
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
            if (value < 0 || value > KEY_MAX) {
                std::cout << "error value " << value << " is outside 0 to " << KEY_MAX << '\n';
                return 3;
            }
        }
        comparisons = 0;
        swaps = 0;
        counting_sort(arr, KEY_MAX);
        std::cout << "sorted";
        for (int value : arr) std::cout << ' ' << value;
        std::cout << "\ncomparisons " << comparisons << "\nswaps " << swaps << "\nend\n";
    }
    return 0;
}
