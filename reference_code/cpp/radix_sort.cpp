// Radix Sort in C++17, a translation of algotrace/algorithms/sorting/radix_sort.py.
// Least significant digit first, base 10, told the key range in advance,
// whole numbers from 0 to 99, so it compares nothing. Input and output:
// reference_code/README.md. The second count is writes, reported as swaps,
// exactly as the site does.
#include <iostream>
#include <string>
#include <vector>

static const int KEY_MAX = 99;

// Plumbing: the counts the site reports and the step trace.
static long comparisons = 0;
static long swaps = 0;

// index < 0: no index:value pair. bucket < 0: no bucket. `left` is how many
// values that bucket holds as the step is drawn.
static void step(const char *action, const char *line, int index, int value,
                 int bucket, int left, int place)
{
    std::cout << "step " << action << ' ' << (line ? line : "-");
    if (index >= 0) std::cout << ' ' << index << ':' << value;
    if (bucket >= 0) std::cout << " bucket=" << bucket << " size=" << left << " place=" << place;
    std::cout << '\n';
}

// lesson:start
void radix_sort(std::vector<int> &arr, int k) {
    int n = static_cast<int>(arr.size());
    for (int place = 1; k / place > 0; place *= 10) {
        std::vector<std::vector<int>> buckets(10);
        for (int i = 0; i < n; i++) {
            int digit = arr[i] / place % 10;
            buckets[digit].push_back(arr[i]);                   // @drop
            step("bucket", "drop", i, arr[i], digit, static_cast<int>(buckets[digit].size()), place); // @hide
        }
        int pos = 0;
        for (int b = 0; b < 10; b++) {
            int left = static_cast<int>(buckets[b].size());     // @hide
            for (int value : buckets[b]) {
                arr[pos] = value;                               // @write
                swaps++;                                        // @hide
                step("overwrite", "write", pos, value, b, --left, place); // @hide
                pos++;
            }
        }
    }
    step("done", nullptr, -1, 0, -1, 0, 0);                     // @hide
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
        radix_sort(arr, KEY_MAX);
        std::cout << "sorted";
        for (int value : arr) std::cout << ' ' << value;
        std::cout << "\ncomparisons " << comparisons << "\nswaps " << swaps << "\nend\n";
    }
    return 0;
}
