/* Lesson content for Insertion Sort. Contract: static/js/lessons/README.md
   Figures describe sorting_algorithms/insertion_sort.py, which does break out
   of its inner loop early, so its best case really is linear. */
window.LESSONS = window.LESSONS || {};
window.LESSONS.insertion_sort = {
    id: 'insertion_sort',
    name: 'Insertion Sort',
    family: 'sorting',

    idea: [
        'Treat the left end of the list as a sorted run that starts with one value.',
        'Take the next value out, then slide every larger value in the run one place right to open a gap.',
        'Drop the held value into the gap, which grows the sorted run by one, and repeat.'
    ],
    analogy: 'Sorting a hand of playing cards: you pick up each new card and slide it left past the cards that are bigger until it sits in the right place.',
    whenToUse: 'On small lists, or on lists that are already nearly sorted. Real libraries fall back to it for short runs inside a bigger sort, because it is fast when there is little work to do.',
    stable: true,
    presetNotes: {
        random: "A typical input. Each value slides back past about half of the sorted part, so the work is roughly n squared over 4.",
        sorted: "The best case: each value is compared once with its neighbour and stays, so the comparisons are n-1.",
        reversed: "The worst case: every value slides all the way to the front, so it makes n(n-1)/2 comparisons and the same number of shifts.",
        equal: "Also fast: an equal value is not smaller, so nothing shifts and the comparisons are n-1.",
        nearly: "Close to the best case. Each value only slides past the one or two values that are out of place."
    },

    /* Insertion sort slides values one place right to open a gap; it never
       exchanges a pair. The counter beside the comparisons counts those
       slides. See complexity.countsNote. */
    countLabel: 'shifts',

    code: {
        pseudocode: [
            { id: 'outer', text: 'for each position i from the second onwards:', indent: 0 },
            { id: 'key', text: 'hold the value at i as the key', indent: 1 },
            { id: 'inner', text: 'while there is a value to the left:', indent: 1 },
            { id: 'compare', text: 'if the key < that value:', indent: 2 },
            { id: 'shift', text: 'slide that value one place right', indent: 3 },
            { id: null, text: 'otherwise stop looking', indent: 2 },
            { id: 'place', text: 'put the key into the gap', indent: 1 }
        ],
        python: [
            { id: 'outer', text: 'for i in range(1, len(arr)):', indent: 0 },
            { id: 'key', text: 'key = arr[i]', indent: 1 },
            { id: null, text: 'j = i - 1', indent: 1 },
            { id: 'inner', text: 'while j >= 0:', indent: 1 },
            { id: 'compare', text: 'if key < arr[j]:', indent: 2 },
            { id: 'shift', text: 'arr[j + 1] = arr[j]', indent: 3 },
            { id: null, text: 'j -= 1', indent: 3 },
            { id: null, text: 'else:', indent: 2 },
            { id: null, text: 'break', indent: 3 },
            { id: 'place', text: 'arr[j + 1] = key', indent: 1 }
        ]
    },

    complexity: {
        time: {
            best: {
                value: 'O(n)',
                reason: 'On an already sorted list the key is never smaller than the value to its left, so the while loop breaks after one comparison each time. That is n-1 comparisons in total.'
            },
            average: {
                value: 'O(n squared)',
                reason: 'A value lands roughly halfway back into the sorted run on average, so each of the n keys costs about i/2 comparisons.'
            },
            worst: {
                value: 'O(n squared)',
                reason: 'On a reversed list every key has to walk past the whole sorted run, giving 1 + 2 + ... + (n-1) = n(n-1)/2 comparisons.'
            }
        },
        worked: {
            input: '[5, 3, 8, 1, 9]',
            comparisons: 6,
            note: 'n = 5. The same list sorted, [1, 3, 5, 8, 9], costs only 4 comparisons, and reversed, [9, 8, 5, 3, 1], costs the full 10. This is the one quadratic sort here whose best case really is linear, because its inner loop breaks. The shifts track the comparisons closely: 4 here, 0 on the sorted list and 10 on the reversed one.'
        },
        space: {
            value: 'O(1)',
            what: 'the single held key and two indices, whatever the list length'
        },
        auxiliaryNote: 'Auxiliary space is the memory the algorithm needs on top of the input array itself.',
        thisRun: 'Big O describes how work grows as the input grows and ignores constants. The counter shows the exact work for this one input.',
        countsNote: 'The second counter says shifts, not swaps, because insertion sort never exchanges a pair. It lifts one value out, slides everything bigger one place to the right to open a gap, and drops the value in. Each slide is one shift, so a value that has to travel four places back costs four of them. An already sorted list costs none, because no gap ever has to be opened.',
        growth: 'n2',
        growthBasis: null,
        growthNote: null,
        divergence: 'None. Compare it with bubble sort on this site: both are O(n squared) in the worst case, but insertion sort stops its inner loop as soon as it meets a smaller value, and bubble sort does not.'
    }
};
