/* Lesson content for Bubble Sort. Contract: static/js/lessons/README.md
   Every complexity figure here describes sorting_algorithms/bubble_sort.py,
   which has no early exit, and not the textbook version that does. */
window.LESSONS = window.LESSONS || {};
window.LESSONS.bubble_sort = {
    id: 'bubble_sort',
    name: 'Bubble Sort',
    family: 'sorting',

    idea: [
        'Walk along the list and compare each value with the one next to it.',
        'If the pair is the wrong way round, swap them, so the larger value moves right.',
        'Repeat the walk until every pass has been made, by which point the list is in order.'
    ],
    analogy: 'Tidying a shelf of books by checking each neighbouring pair and swapping any that are out of order, over and over.',
    whenToUse: 'Almost never in real code. It is here because it is the shortest sort to read, and it makes a clear picture of what a comparison and a swap are.',
    stable: true,
    presetNotes: {
        random: "A typical input. Every run makes n(n-1)/2 comparisons here; only the swap count depends on the order.",
        sorted: "No swaps are needed, yet it still makes all n(n-1)/2 comparisons, because this version has no early exit.",
        reversed: "The most swaps possible: every pair is out of order, so there is one swap for every comparison.",
        equal: "Nothing swaps, because only a strictly larger left value moves. The comparisons are still n(n-1)/2.",
        nearly: "Only a few swaps, but the comparison count does not drop, because each pass still runs to the end."
    },

    code: {
        pseudocode: [
            { id: null, text: 'n = length of list', indent: 0 },
            { id: 'pass', text: 'repeat n times:', indent: 0 },
            { id: 'walk', text: 'for each neighbouring pair, left to right:', indent: 1 },
            { id: 'compare', text: 'if left value > right value:', indent: 2 },
            { id: 'swap', text: 'swap the two values', indent: 3 }
        ],
        python: [
            { id: null, text: 'n = len(arr)', indent: 0 },
            { id: 'pass', text: 'for i in range(n):', indent: 0 },
            { id: 'walk', text: 'for j in range(0, n-i-1):', indent: 1 },
            { id: 'compare', text: 'if arr[j] > arr[j+1]:', indent: 2 },
            { id: 'swap', text: 'arr[j], arr[j+1] = arr[j+1], arr[j]', indent: 3 }
        ]
    },

    complexity: {
        time: {
            best: {
                value: 'O(n squared)',
                reason: 'The inner loop runs n-1 times, then n-2, and so on, whatever the values are. Nothing in this code stops a pass early, so a sorted list costs exactly as much as a shuffled one.'
            },
            average: {
                value: 'O(n squared)',
                reason: 'The number of comparisons does not depend on the input at all. It is always n(n-1)/2.'
            },
            worst: {
                value: 'O(n squared)',
                reason: 'Same count again. A reverse sorted list costs no more comparisons than a sorted one, only more swaps.'
            }
        },
        worked: {
            input: '[5, 3, 8, 1, 9]',
            comparisons: 10,
            note: 'n = 5, so n(n-1)/2 = 10 comparisons. Any other five values give 10 as well. Only the swap count changes: this input needs 4, a sorted list needs 0, and a reversed one needs 10.'
        },
        space: {
            value: 'O(1)',
            what: 'two loop counters and one temporary during each swap, no matter how long the list is'
        },
        auxiliaryNote: 'Auxiliary space is the memory the algorithm needs on top of the input array itself.',
        thisRun: 'Big O describes how work grows as the input grows and ignores constants. The counter shows the exact work for this one input.',
        growth: 'n2',
        growthBasis: null,
        growthNote: null,
        divergence: 'Textbooks usually give bubble sort a best case of O(n), because their version keeps a flag and stops once a pass makes no swaps. This implementation has no such flag, so its best case is O(n squared). Adding the flag would not change the worst case.'
    }
};
