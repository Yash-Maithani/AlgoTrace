/* Lesson content for Linear Search. Contract: static/js/lessons/README.md

   The listing matches algotrace/algorithms/searching/linear_search.py, and the counts
   assume one comparison each time the loop looks at a value, which is what
   that module counts. tests/unit/test_searching.py holds the two together. */
window.LESSONS = window.LESSONS || {};
window.LESSONS.linear_search = {
    id: 'linear_search',
    name: 'Linear Search',
    family: 'searching',

    idea: [
        'Start at the first value and look at each one in turn.',
        'Stop as soon as a value matches the target and report where it was.',
        'If the end is reached without a match, the target is not in the list.'
    ],
    analogy: 'Looking for a friend in an unsorted queue by walking along it and checking every face until you find them.',
    whenToUse: 'When the list is short, or when it is not sorted and you only need to search it once. Sorting a list first only pays off if you are going to search it many times.',
    stable: null,
    presetNotes: {
        random: "Unsorted data is what linear search is for: it works on any order, and the cost depends on where the target is.",
        sorted: "Order does not help it. It still checks from the start, so a target near the end costs nearly n comparisons.",
        reversed: "Order does not help it. A target at the far end still costs nearly n comparisons.",
        equal: "If the target is that value it stops at the first cell, one comparison. Any other target makes it check all n values.",
        nearly: "Order does not help it. The cost depends only on where the target sits."
    },

    code: {
        pseudocode: [
            { id: 'loop', text: 'for each position i from the start:', indent: 0 },
            { id: 'compare', text: 'if the value at i is the target:', indent: 1 },
            { id: 'found', text: 'report i and stop', indent: 2 },
            { id: 'missing', text: 'report that the target is not in the list', indent: 0 }
        ],
        python: [
            { id: 'loop', text: 'for i in range(len(arr)):', indent: 0 },
            { id: 'compare', text: 'if arr[i] == target:', indent: 1 },
            { id: 'found', text: 'return i', indent: 2 },
            { id: 'missing', text: 'return -1', indent: 0 }
        ]
    },

    complexity: {
        time: {
            best: {
                value: 'O(1)',
                theta: '1',
                reason: 'If the target is the very first value, the loop compares once and returns.'
            },
            average: {
                value: 'O(n)',
                theta: 'n',
                reason: 'A target that is present is equally likely to be anywhere, so on average the loop looks at about half the list, which still grows in step with n.'
            },
            worst: {
                value: 'O(n)',
                theta: 'n',
                reason: 'If the target is last, or missing altogether, every one of the n values is compared before the loop can answer.'
            }
        },
        overall: { O: 'n', Omega: '1', Theta: null },
        misconception: 'Best, average and worst are cases: three kinds of input. O, Omega and Theta are bounds: a ceiling on the growth, a floor under it, and both at once. Every case has its own bounds, so reading O as the worst case, Omega as the best and Theta as the average mixes up two different ideas.',
        worked: {
            input: '[4, 8, 15, 16, 23], target 16',
            comparisons: 4,
            note: 'n = 5. The loop checks 4, 8, 15 and then 16, so it answers after 4 comparisons. Searching for 42 costs the full 5, because a linear search can only rule out a missing value by looking at everything.'
        },
        space: {
            value: 'O(1)',
            what: 'one index, whatever the list length'
        },
        auxiliaryNote: 'Auxiliary space is the memory the algorithm needs on top of the input array itself.',
        thisRun: 'Big O describes how work grows as the input grows and ignores constants. The counter shows the exact work for this one input.',
        growth: 'n',
        growthBasis: null,
        growthNote: null,
        divergence: null
    }
};
