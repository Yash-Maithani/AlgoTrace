/* Lesson content for Binary Search. Contract: static/js/lessons/README.md

   codePending: the implementation lands in Phase 5. The listing below is the
   iterative form the plan specifies, and the counts here assume one
   comparison each time the loop looks at a middle value. Phase 5 must build
   searching_algorithms/binary_search.py to match this listing and its line
   ids, or update this file in the same commit. */
window.LESSONS = window.LESSONS || {};
window.LESSONS.binary_search = {
    id: 'binary_search',
    name: 'Binary Search',
    family: 'searching',
    codePending: true,

    idea: [
        'Keep a low and a high marker around the part of the list that could still hold the target.',
        'Look at the value in the middle: if it is the target you are done, and if not you know which half to throw away.',
        'Move the marker past the discarded half and look at the middle of what is left, until the range is empty.'
    ],
    analogy: 'Finding a word in a dictionary. You open it near the middle, see whether your word comes before or after, and never look at the other half again.',
    whenToUse: 'When the list is sorted and you will search it more than once. It needs a sorted list, so searching an unsorted one means paying for the sort first.',
    stable: null,

    code: {
        pseudocode: [
            { id: null, text: 'low = first position, high = last position', indent: 0 },
            { id: 'loop', text: 'while low <= high:', indent: 0 },
            { id: 'mid', text: 'mid = the position halfway between them', indent: 1 },
            { id: 'compare', text: 'if the value at mid is the target:', indent: 1 },
            { id: 'found', text: 'report mid and stop', indent: 2 },
            { id: 'go-right', text: 'if the target is larger, move low past mid', indent: 1 },
            { id: 'go-left', text: 'otherwise move high below mid', indent: 1 },
            { id: 'missing', text: 'report that the target is not in the list', indent: 0 }
        ],
        python: [
            { id: null, text: 'low, high = 0, len(arr) - 1', indent: 0 },
            { id: 'loop', text: 'while low <= high:', indent: 0 },
            { id: 'mid', text: 'mid = (low + high) // 2', indent: 1 },
            { id: 'compare', text: 'if arr[mid] == target:', indent: 1 },
            { id: 'found', text: 'return mid', indent: 2 },
            { id: 'go-right', text: 'elif arr[mid] < target:', indent: 1 },
            { id: null, text: 'low = mid + 1', indent: 2 },
            { id: 'go-left', text: 'else:', indent: 1 },
            { id: null, text: 'high = mid - 1', indent: 2 },
            { id: 'missing', text: 'return -1', indent: 0 }
        ]
    },

    complexity: {
        time: {
            best: {
                value: 'O(1)',
                reason: 'If the target happens to sit at the first middle position the loop answers after one comparison.'
            },
            average: {
                value: 'O(log n)',
                reason: 'Every comparison that misses throws away half of what is left, so the range shrinks 5, 2, 1 rather than 5, 4, 3.'
            },
            worst: {
                value: 'O(log n)',
                reason: 'The range can only be halved so many times before it is empty, which is log base 2 of n steps. A missing target costs exactly that.'
            }
        },
        worked: {
            input: '[4, 8, 15, 16, 23], target 4',
            comparisons: 2,
            note: 'n = 5. It checks the middle, 15, discards everything from 15 rightwards, then checks 4 and finds it. The worst case here is 3 comparisons, for example target 23 or any value the list does not contain. Linear search needs 5 to rule out a missing value, and the gap widens fast: at n = 1000 it is about 10 against 1000.'
        },
        space: {
            value: 'O(1)',
            what: 'the low, high and mid markers, whatever the list length'
        },
        auxiliaryNote: 'Auxiliary space is the memory the algorithm needs on top of the input array itself.',
        thisRun: 'Big O describes how work grows as the input grows and ignores constants. The counter shows the exact work for this one input.',
        growth: 'logn',
        divergence: 'A recursive binary search costs O(log n) stack frames instead. This listing is the iterative form the plan calls for, so its space stays constant.'
    }
};
