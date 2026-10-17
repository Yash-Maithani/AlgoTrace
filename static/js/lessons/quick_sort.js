/* Lesson content for Quick Sort. Contract: static/js/lessons/README.md
   Figures describe sorting_algorithms/quick_sort.py, which always takes the
   last element as its pivot. That choice is what makes sorted input its
   worst case rather than its best. */
window.LESSONS = window.LESSONS || {};
window.LESSONS.quick_sort = {
    id: 'quick_sort',
    name: 'Quick Sort',
    family: 'sorting',

    idea: [
        'Pick one value as the pivot, here always the last value in the range.',
        'Walk the range and move everything smaller than the pivot to the left side, then drop the pivot just after them.',
        'The pivot is now in its final place, so repeat on the smaller group and the larger group separately.'
    ],
    analogy: 'Sorting a pile of forms by picking one at random, making a shorter pile and a taller pile around it, then sorting each of those the same way.',
    whenToUse: 'The usual default for in memory sorting, because it is fast in practice and needs no second array. Real implementations choose the pivot more carefully than this one does.',
    stable: false,

    code: {
        pseudocode: [
            { id: 'partition', text: 'to partition a range from low to high:', indent: 0 },
            { id: 'pivot', text: 'pivot = the value at high', indent: 1 },
            { id: null, text: 'i = low - 1, the end of the smaller group', indent: 1 },
            { id: 'iloop', text: 'for each position j from low up to high:', indent: 1 },
            { id: 'compare', text: 'if the value at j < pivot:', indent: 2 },
            { id: 'swap', text: 'grow the smaller group and swap the value into it', indent: 3 },
            { id: 'place-pivot', text: 'swap the pivot to just after the smaller group', indent: 1 },
            { id: 'recurse-left', text: 'sort the part before the pivot', indent: 0 },
            { id: 'recurse-right', text: 'sort the part after the pivot', indent: 0 }
        ],
        python: [
            { id: 'partition', text: 'def partition(low, high):', indent: 0 },
            { id: 'pivot', text: 'pivot = arr[high]', indent: 1 },
            { id: null, text: 'i = low - 1', indent: 1 },
            { id: 'iloop', text: 'for j in range(low, high):', indent: 1 },
            { id: 'compare', text: 'if arr[j] < pivot:', indent: 2 },
            { id: null, text: 'i += 1', indent: 3 },
            { id: 'swap', text: 'arr[i], arr[j] = arr[j], arr[i]', indent: 3 },
            { id: 'place-pivot', text: 'arr[i + 1], arr[high] = arr[high], arr[i + 1]', indent: 1 },
            { id: 'recurse-left', text: 'sort(low, pi - 1)', indent: 1 },
            { id: 'recurse-right', text: 'sort(pi + 1, high)', indent: 1 }
        ]
    },

    complexity: {
        time: {
            best: {
                value: 'O(n log n)',
                reason: 'When each pivot lands near the middle, the range halves every time, so there are about log n levels and each level scans n values once.'
            },
            average: {
                value: 'O(n log n)',
                reason: 'On shuffled input the pivot is rarely near either end, so the ranges shrink quickly enough to keep the depth logarithmic.'
            },
            worst: {
                value: 'O(n squared)',
                reason: 'The pivot is always the last value. On a list that is already sorted, or reverse sorted, every partition peels off one value and leaves n-1 behind, giving n(n-1)/2 comparisons.'
            }
        },
        worked: {
            input: '[5, 3, 8, 1, 9]',
            comparisons: 9,
            note: 'n = 5. Now feed it the sorted list [1, 3, 5, 8, 9] and the count rises to 10, the quadratic worst case, because the last element pivot is also the largest every time. Most sorts find sorted input easy. This one finds it hardest.'
        },
        space: {
            value: 'O(n)',
            what: 'the recursion stack. Nothing is copied, but the worst case nests n frames deep, and a balanced run nests about log n'
        },
        auxiliaryNote: 'Auxiliary space is the memory the algorithm needs on top of the input array itself.',
        thisRun: 'Big O describes how work grows as the input grows and ignores constants. The counter shows the exact work for this one input.',
        growth: 'n2',
        growthBasis: null,
        growthNote: null,
        divergence: 'Quick sort is often quoted at O(log n) space. That holds only when the partitions are balanced. Because this version always picks the last element, sorted input nests the recursion n deep, so the honest figure for this code is O(n). Picking a random or median of three pivot would fix both the time and the space worst case.'
    }
};
