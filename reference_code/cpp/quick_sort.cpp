// Quick Sort in C++17, a translation of sorting_algorithms/quick_sort.py.
// Input and output: reference_code/README.md. Variant last takes the last
// value as pivot; middle and random swap their choice to the end first and
// run the same partition. random draws from mulberry32, the same generator
// as sorting_algorithms/seeded.py, so a seed gives the same run as Python.
// lesson:variants last middle random
#include <cstdint>
#include <initializer_list>
#include <iostream>
#include <string>
#include <utility>
#include <vector>

// Plumbing: the counts the site reports and the step trace.
static long comparisons = 0;
static long swaps = 0;

enum class Pivot { Last, Middle, Random };
static Pivot pivot_rule = Pivot::Last;

static void step_at(int depth, int lo, int hi, const char *action, const char *line,
                    std::initializer_list<int> pairs = {})
{
    std::cout << "step " << action << ' ' << (line ? line : "-");
    for (auto it = pairs.begin(); it != pairs.end(); it += 2) {
        std::cout << ' ' << *it << ':' << *(it + 1);
    }
    std::cout << " depth=" << depth << " range=" << lo << ':' << hi << '\n';
}

// mulberry32, as in sorting_algorithms/seeded.py: a double in [0, 1).
static std::uint32_t rng_state = 0;

static double rand_unit()
{
    rng_state += 0x6D2B79F5u;
    std::uint32_t t = rng_state;
    t = (t ^ (t >> 15)) * (t | 1u);
    t ^= t + (t ^ (t >> 7)) * (t | 61u);
    return static_cast<double>(t ^ (t >> 14)) / 4294967296.0;
}

// lesson:start
int partition(std::vector<int> &arr, int low, int high, int depth) { // @partition
    if (pivot_rule == Pivot::Middle) {                          // @hide
        int mid = (low + high) / 2;                             // @only:middle
        std::swap(arr[mid], arr[high]);                         // @choose-pivot @only:middle
        swaps++;                                                // @hide
        step_at(depth, low, high, "swap", "choose-pivot",       // @hide
                {mid, arr[mid], high, arr[high]});              // @hide
    } else if (pivot_rule == Pivot::Random) {                   // @hide
        int r = low + static_cast<int>(rand_unit() * (high - low + 1)); // @only:random
        if (r != high) {                                        // @only:random
            std::swap(arr[r], arr[high]);                       // @choose-pivot @only:random
            swaps++;                                            // @hide
            step_at(depth, low, high, "swap", "choose-pivot",   // @hide
                    {r, arr[r], high, arr[high]});              // @hide
        }                                                       // @only:random
    }                                                           // @hide
    int pivot = arr[high];                                      // @pivot
    int i = low - 1;
    for (int j = low; j < high; j++) {                          // @iloop
        comparisons++;                                          // @hide
        step_at(depth, low, high, "compare", "compare", {j, arr[j], high, pivot}); // @hide
        if (arr[j] < pivot) {                                   // @compare
            i++;
            std::swap(arr[i], arr[j]);                          // @swap
            swaps++;                                            // @hide
            step_at(depth, low, high, "swap", "swap", {i, arr[i], j, arr[j]}); // @hide
        }
    }
    std::swap(arr[i + 1], arr[high]);                           // @place-pivot
    swaps++;                                                    // @hide
    step_at(depth, low, high, "place", "place-pivot",           // @hide
            {i + 1, arr[i + 1], high, arr[high]});              // @hide
    return i + 1;
}

void sort(std::vector<int> &arr, int low, int high, int depth) {
    if (low < high) {
        int pi = partition(arr, low, high, depth);
        sort(arr, low, pi - 1, depth + 1);                      // @recurse-left
        sort(arr, pi + 1, high, depth + 1);                     // @recurse-right
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
        if (variant == "last") pivot_rule = Pivot::Last;
        else if (variant == "middle") pivot_rule = Pivot::Middle;
        else if (variant == "random") pivot_rule = Pivot::Random;
        else {
            std::cout << "error unknown variant " << variant << '\n';
            return 2;
        }
        std::vector<int> arr(static_cast<size_t>(n));
        for (int &value : arr) {
            if (!(std::cin >> value)) return 1;
        }
        comparisons = 0;
        swaps = 0;
        rng_state = static_cast<std::uint32_t>(seed);
        sort(arr, 0, n - 1, 0);
        step_at(0, 0, n - 1, "done", nullptr);
        std::cout << "sorted";
        for (int value : arr) std::cout << ' ' << value;
        std::cout << "\ncomparisons " << comparisons << "\nswaps " << swaps << "\nend\n";
    }
    return 0;
}
