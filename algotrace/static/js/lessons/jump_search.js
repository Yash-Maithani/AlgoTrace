/* Lesson content for Jump Search. Contract: static/js/lessons/README.md

   The listing matches algotrace/algorithms/searching/jump_search.py, and the counts
   assume one comparison each time the search looks at a value, the rule
   linear and binary search follow too. tests/unit/test_jump_counting_radix.py measures every
   figure stated here. */
window.LESSONS = window.LESSONS || {};
window.LESSONS.jump_search = {
    id: 'jump_search',
    name: 'Jump Search',
    family: 'searching',

    idea: [
        'Split the sorted list into blocks of about the square root of n values each.',
        'Jump from block to block, looking only at the last value of each, until one is not smaller than the target.',
        'The target can only be in that block, so scan it from its start, one value at a time.'
    ],
    analogy: 'Finding a page in a thick book by flipping ten pages at a time until you pass the page number you want, then turning back and going one page at a time.',
    whenToUse: 'On a sorted list where jumping forward is cheap but going backwards is not, such as a long file read from start to end. On a list in memory binary search does fewer comparisons.',
    stable: null,
    presets: ['sorted', 'equal'],
    presetNotes: {
        sorted: "The input jump search needs. With blocks of about the square root of n, a search costs at most about 2 times the square root of n comparisons.",
        equal: "Still sorted. A target equal to the value is found after 2 comparisons, the first block end and then position 0; a bigger target jumps through every block."
    },

    code: {
        pseudocode: [
            { id: null, text: 'block = the whole part of the square root of n', indent: 0 },
            { id: null, text: 'low = 0, end = the last position of the first block', indent: 0 },
            { id: 'jump-check', text: 'while the value at end is smaller than the target:', indent: 0 },
            { id: null, text: 'if end is the last position:', indent: 1 },
            { id: 'past-end', text: 'report that the target is not in the list', indent: 2 },
            { id: 'jump', text: 'low = end + 1, and end moves to the end of the next block', indent: 1 },
            { id: null, text: 'for each position i from low to end:', indent: 0 },
            { id: 'scan', text: 'if the value at i is the target:', indent: 1 },
            { id: 'found', text: 'report i and stop', indent: 2 },
            { id: null, text: 'if it is bigger than the target, stop scanning', indent: 1 },
            { id: 'missing', text: 'report that the target is not in the list', indent: 0 }
        ],
        python: [
            { id: null, text: 'block = math.isqrt(len(arr))', indent: 0 },
            { id: null, text: 'low, end = 0, min(block, len(arr)) - 1', indent: 0 },
            { id: 'jump-check', text: 'while arr[end] < target:', indent: 0 },
            { id: null, text: 'if end == len(arr) - 1:', indent: 1 },
            { id: 'past-end', text: 'return -1', indent: 2 },
            { id: 'jump', text: 'low = end + 1', indent: 1 },
            { id: null, text: 'end = min(end + block, len(arr) - 1)', indent: 1 },
            { id: null, text: 'for i in range(low, end + 1):', indent: 0 },
            { id: 'scan', text: 'if arr[i] == target:', indent: 1 },
            { id: 'found', text: 'return i', indent: 2 },
            { id: null, text: 'if arr[i] > target:', indent: 1 },
            { id: null, text: 'break', indent: 2 },
            { id: 'missing', text: 'return -1', indent: 0 }
        ]
    },

    complexity: {
        time: {
            best: {
                value: 'O(1)',
                theta: '1',
                reason: 'If the target is the first value, the search looks at the end of the first block, sees it is not smaller, and finds the target at position 0: 2 comparisons, whatever n is.'
            },
            average: {
                value: 'O(square root of n)',
                theta: 'square root of n',
                reason: 'A target in the middle of the list costs about half the jumps and half a block of scanning, which is about the square root of n comparisons.'
            },
            worst: {
                value: 'O(square root of n)',
                theta: 'square root of n',
                reason: 'There are about the square root of n blocks to jump over and the square root of n values in the last one to scan, so at most about 2 times the square root of n comparisons.'
            }
        },
        overall: { O: 'square root of n', Omega: '1', Theta: null },
        misconception: 'Best, average and worst are cases: three kinds of input. O, Omega and Theta are bounds: a ceiling on the growth, a floor under it, and both at once. Every case has its own bounds, so reading O as the worst case, Omega as the best and Theta as the average mixes up two different ideas.',
        worked: {
            input: '[4, 8, 15, 16, 23], target 23',
            comparisons: 4,
            note: 'n = 5, so the blocks are 2 long. It checks 8 at position 1 and jumps, checks 16 at position 3 and jumps, checks 23 at position 4, which is not smaller, and the scan finds 23 there: 4 comparisons. Target 4 takes 2. At n = 1024 the worst case is 64 comparisons, against 1024 for linear search and 11 for binary search.'
        },
        space: {
            value: 'O(1)',
            what: 'the block size and the low, end and i positions, whatever the list length'
        },
        auxiliaryNote: 'Auxiliary space is the memory the algorithm needs on top of the input array itself.',
        thisRun: 'Big O describes how work grows as the input grows and ignores constants. The counter shows the exact work for this one input.',
        growth: 'sqrtn',
        growthBasis: null,
        growthNote: null,
        divergence: 'None. A block of the square root of n is the size that makes the jumps and the scan cost the same, which is what keeps the total near 2 times the square root of n.'
    }
};
