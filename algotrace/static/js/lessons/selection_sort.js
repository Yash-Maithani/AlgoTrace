/* Lesson content for Selection Sort. Contract: static/js/lessons/README.md
   Figures describe algotrace/algorithms/sorting/selection_sort.py. */
window.LESSONS = window.LESSONS || {};
window.LESSONS.selection_sort = {
    id: 'selection_sort',
    name: 'Selection Sort',
    family: 'sorting',

    idea: [
        'Look through the part of the list that is not sorted yet and find the smallest value in it.',
        'Swap that value into the leftmost unsorted position, which fixes it for good.',
        'Move the boundary one place right and do the same again with what is left.'
    ],
    analogy: 'Picking a team by scanning everyone still waiting, choosing the best one, and lining them up, then scanning the rest again.',
    whenToUse: 'When writing to the array is expensive and reading is cheap. It never makes more than n-1 swaps, which is far fewer than bubble or insertion sort.',
    stable: false,
    presetNotes: {
        random: "A typical input. Selection sort always makes n(n-1)/2 comparisons and at most n-1 swaps.",
        sorted: "Each minimum is already in place, so it swaps nothing, but it still scans the whole unsorted part every time.",
        reversed: "Still n(n-1)/2 comparisons. It swaps only about half the positions, because each swap fixes two values at once.",
        equal: "No swaps, and the same n(n-1)/2 comparisons as any other input.",
        nearly: "A couple of swaps, and the same n(n-1)/2 comparisons: selection sort cannot tell that the list was almost done."
    },

    code: {
        pseudocode: [
            { id: null, text: 'n = length of list', indent: 0 },
            { id: 'outer', text: 'for each position i from left to right:', indent: 0 },
            { id: 'min-init', text: 'assume the value at i is the smallest', indent: 1 },
            { id: 'inner', text: 'for each position j after i:', indent: 1 },
            { id: 'compare', text: 'if value at j < smallest so far:', indent: 2 },
            { id: 'update-min', text: 'remember j as the position of the smallest', indent: 3 },
            { id: 'swap', text: 'swap the smallest into position i', indent: 1 }
        ],
        python: [
            { id: null, text: 'n = len(arr)', indent: 0 },
            { id: 'outer', text: 'for i in range(n):', indent: 0 },
            { id: 'min-init', text: 'min_idx = i', indent: 1 },
            { id: 'inner', text: 'for j in range(i+1, n):', indent: 1 },
            { id: 'compare', text: 'if arr[min_idx] > arr[j]:', indent: 2 },
            { id: 'update-min', text: 'min_idx = j', indent: 3 },
            { id: 'swap', text: 'arr[i], arr[min_idx] = arr[min_idx], arr[i]', indent: 1 }
        ]
    },

    complexity: {
        time: {
            best: {
                value: 'O(n squared)',
                theta: 'n squared',
                reason: 'The inner scan always runs from i+1 to the end. It has no way to stop early, because the smallest value could be the very last one it looks at.'
            },
            average: {
                value: 'O(n squared)',
                theta: 'n squared',
                reason: 'The scan runs n-1 times, then n-2, and so on, giving n(n-1)/2 comparisons for every input.'
            },
            worst: {
                value: 'O(n squared)',
                theta: 'n squared',
                reason: 'The same n(n-1)/2 comparisons. The input only changes how often a new smallest value is found, which costs nothing extra.'
            }
        },
        overall: { O: 'n squared', Omega: 'n squared', Theta: 'n squared' },
        misconception: 'Best, average and worst are cases: three kinds of input. O, Omega and Theta are bounds: a ceiling on the growth, a floor under it, and both at once. Every case has its own bounds, so reading O as the worst case, Omega as the best and Theta as the average mixes up two different ideas.',
        worked: {
            input: '[5, 3, 8, 1, 9]',
            comparisons: 10,
            note: 'n = 5, so n(n-1)/2 = 10 comparisons, the same as bubble sort. The difference is the swaps: 2 here against bubble sort 4, because selection sort swaps at most once per pass.'
        },
        space: {
            value: 'O(1)',
            what: 'two loop counters and the remembered position of the smallest value'
        },
        auxiliaryNote: 'Auxiliary space is the memory the algorithm needs on top of the input array itself.',
        thisRun: 'Big O describes how work grows as the input grows and ignores constants. The counter shows the exact work for this one input.',
        growth: 'n2',
        growthBasis: null,
        growthNote: null,
        divergence: 'None on time. Note that this version is not stable: swapping a distant smallest value into place can jump one equal value over another, so [2, 2, 1] finishes with the two 2s in the opposite order.'
    }
};
