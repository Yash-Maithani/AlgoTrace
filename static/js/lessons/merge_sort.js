/* Lesson content for Merge Sort. Contract: static/js/lessons/README.md
   Figures describe sorting_algorithms/merge_sort.py, which allocates
   temporary lists and, because it compares with <, is not stable. */
window.LESSONS = window.LESSONS || {};
window.LESSONS.merge_sort = {
    id: 'merge_sort',
    name: 'Merge Sort',
    family: 'sorting',

    idea: [
        'Split the list down the middle, again and again, until every piece holds a single value.',
        'A single value is already sorted, so start joining pairs of pieces back together.',
        'Merging two sorted pieces is cheap: repeatedly take whichever front value is smaller.'
    ],
    analogy: 'Two people each hold a sorted pile of cards. To make one sorted pile, you keep taking whichever top card is lower.',
    whenToUse: 'When you need a guaranteed O(n log n) regardless of the input, or when the data is too big for memory and has to be merged in runs from disk.',
    stable: false,
    presetNotes: {
        random: "A typical input. The work is about n log n whatever the order, because the list is always split in half.",
        sorted: "The same splits as any input, but each merge finishes early, so it makes fewer comparisons than on random data.",
        reversed: "The same splits again. Merges end early here too, but every value is still written back at every level.",
        equal: "Every comparison is a tie and < takes the right value first, so equal values change order (watch the tags) and it costs as many comparisons as a reversed list.",
        nearly: "Almost sorted halves merge quickly, so the comparisons are low, but the writes stay at n log n."
    },

    /* Merge sort never exchanges a pair of values, so the counter beside the
       comparisons counts writes, not swaps. See complexity.countsNote. */
    countLabel: 'writes',

    code: {
        pseudocode: [
            { id: 'split', text: 'if the piece holds more than one value:', indent: 0 },
            { id: 'sortleft', text: 'sort the left half', indent: 1 },
            { id: 'sortright', text: 'sort the right half', indent: 1 },
            { id: null, text: 'merge the two halves:', indent: 1 },
            { id: 'merge-compare', text: 'while both halves still have values:', indent: 2 },
            { id: null, text: 'take the smaller of the two front values', indent: 3 },
            { id: null, text: 'append whatever is left over', indent: 2 },
            { id: 'copy-back', text: 'copy the merged run back over the piece', indent: 2 }
        ],
        python: [
            { id: 'split', text: 'if end - start > 1:', indent: 0 },
            { id: null, text: 'mid = (start + end) // 2', indent: 1 },
            { id: 'sortleft', text: 'sort(start, mid)', indent: 1 },
            { id: 'sortright', text: 'sort(mid, end)', indent: 1 },
            { id: null, text: 'merge(arr[start:mid], arr[mid:end], start)', indent: 1 },
            { id: 'merge-compare', text: 'while i < len(left) and j < len(right):', indent: 1 },
            { id: null, text: 'if left[i] < right[j]: take left[i]', indent: 2 },
            { id: null, text: 'else: take right[j]', indent: 2 },
            { id: 'copy-back', text: 'arr[start_index + idx] = val', indent: 1 }
        ]
    },

    complexity: {
        time: {
            best: {
                value: 'O(n log n)',
                theta: 'n log n',
                reason: 'The list is always cut exactly in half, so there are always about log n levels, and every level merges all n values. The input cannot make the splitting any cheaper.'
            },
            average: {
                value: 'O(n log n)',
                theta: 'n log n',
                reason: 'Same shape of work. Each merge of two runs costs at most one comparison per value taken.'
            },
            worst: {
                value: 'O(n log n)',
                theta: 'n log n',
                reason: 'Even in the worst arrangement a merge costs one comparison per value, so a level is O(n) and the total is O(n log n). No input makes it worse. It is not alone in that: heap sort has the same n log n worst case, and counting and radix sort cost the same on every input.'
            }
        },
        overall: { O: 'n log n', Omega: 'n log n', Theta: 'n log n' },
        misconception: 'Best, average and worst are cases: three kinds of input. O, Omega and Theta are bounds: a ceiling on the growth, a floor under it, and both at once. Every case has its own bounds, so reading O as the worst case, Omega as the best and Theta as the average mixes up two different ideas.',
        worked: {
            input: '[5, 3, 8, 1, 9]',
            comparisons: 7,
            note: 'n = 5. Fewer comparisons than the quadratic sorts need even at this tiny size, where they all cost 10. Note that the merge loop stops as soon as one side empties, so a run that is already in order uses fewer comparisons: [1, 3, 5, 8, 9] costs 5. The write count does not fall the same way, because the copy back writes every value either way: both of those inputs cost 12 writes.'
        },
        space: {
            value: 'O(n)',
            what: 'the temporary list each merge builds, plus the two half slices it copies out, plus about log n stack frames for the recursion'
        },
        auxiliaryNote: 'Auxiliary space is the memory the algorithm needs on top of the input array itself.',
        thisRun: 'Big O describes how work grows as the input grows and ignores constants. The counter shows the exact work for this one input.',
        countsNote: 'The second counter says writes, not swaps, because merge sort never exchanges a pair of values. It builds the merged run in a temporary list and then copies the whole run back over the array, so every value in the run is written whether or not it moved. That is why an already sorted list still reports writes: the copy back happens either way.',
        growth: 'nlogn',
        growthBasis: null,
        growthNote: null,
        divergence: 'Merge sort is usually described as stable, but this implementation is not. It compares with left[i] < right[j], so when two values are equal it takes the one from the right half first, which puts the later value ahead of the earlier one. Changing the test to <= makes it stable, and that is the other setting of the switch. The counts only differ when there are equal values: with < an all equal list costs as many comparisons as a reversed one, with <= as few as a sorted one.',
        claims: [
            { input: 'sorted', comparisons: 'n*log2(n)', bound: 'atMost', where: 'time.best' },
            { input: 'random', comparisons: 'n*log2(n)', bound: 'atMost', where: 'time.average' },
            { input: 'reversed', comparisons: 'n*log2(n)', bound: 'atMost', where: 'time.worst' },
            { input: 'equal', sameAs: 'reversed', where: 'divergence' }
        ]
    },

    /* The switch in the Setup column. "lt" is the code above; "le" is the
       textbook, stable merge. Contract: static/js/lessons/README.md. */
    variants: {
        key: 'compare',
        label: 'Merge comparison',
        default: 'lt',
        options: {
            lt: {
                label: 'left < right',
                note: 'On a tie the value from the right half goes first, so equal values can swap order. Not stable.'
            },
            le: {
                label: 'left <= right',
                note: 'On a tie the value from the left half goes first, so equal values keep their order. Stable.',
                stable: true,
                presetNotes: {
                    equal: "Every comparison is a tie and <= takes the left value, so the tags stay in order and each merge stops as early as on a sorted list."
                },
                code: {
                    pseudocode: [
                        { id: 'split', text: 'if the piece holds more than one value:', indent: 0 },
                        { id: 'sortleft', text: 'sort the left half', indent: 1 },
                        { id: 'sortright', text: 'sort the right half', indent: 1 },
                        { id: null, text: 'merge the two halves:', indent: 1 },
                        { id: 'merge-compare', text: 'while both halves still have values:', indent: 2 },
                        { id: null, text: 'take the smaller front value; on a tie, take the left one', indent: 3 },
                        { id: null, text: 'append whatever is left over', indent: 2 },
                        { id: 'copy-back', text: 'copy the merged run back over the piece', indent: 2 }
                    ],
                    python: [
                        { id: 'split', text: 'if end - start > 1:', indent: 0 },
                        { id: null, text: 'mid = (start + end) // 2', indent: 1 },
                        { id: 'sortleft', text: 'sort(start, mid)', indent: 1 },
                        { id: 'sortright', text: 'sort(mid, end)', indent: 1 },
                        { id: null, text: 'merge(arr[start:mid], arr[mid:end], start)', indent: 1 },
                        { id: 'merge-compare', text: 'while i < len(left) and j < len(right):', indent: 1 },
                        { id: null, text: 'if left[i] <= right[j]: take left[i]', indent: 2 },
                        { id: null, text: 'else: take right[j]', indent: 2 },
                        { id: 'copy-back', text: 'arr[start_index + idx] = val', indent: 1 }
                    ]
                },
                complexity: {
                    worked: {
                        input: '[5, 3, 8, 1, 9]',
                        comparisons: 7,
                        note: 'n = 5, the same 7 as with <, because these five values are all different and a tie is the only place the two tests disagree. Give it [2, 2, 2, 2, 2] and they split: <= makes 5 comparisons, the same as the sorted [1, 3, 5, 8, 9], while < makes 7. Both write 12 times.'
                    },
                    divergence: null,
                    claims: [
                        { input: 'sorted', comparisons: 'n*log2(n)', bound: 'atMost', where: 'time.best' },
                        { input: 'random', comparisons: 'n*log2(n)', bound: 'atMost', where: 'time.average' },
                        { input: 'reversed', comparisons: 'n*log2(n)', bound: 'atMost', where: 'time.worst' },
                        { input: 'equal', sameAs: 'sorted', where: 'presetNotes.equal' }
                    ]
                }
            }
        }
    }
};
