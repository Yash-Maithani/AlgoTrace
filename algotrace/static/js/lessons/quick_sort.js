/* Lesson content for Quick Sort. Contract: static/js/lessons/README.md
   Figures describe algotrace/algorithms/sorting/quick_sort.py, which always takes the
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
    presetNotes: {
        random: "The case quick sort is good at: the last element is usually near the middle, so the splits are balanced.",
        sorted: "Already sorted is the worst case for Quick Sort with the last element as pivot: one side is always empty, so n(n-1)/2 comparisons.",
        reversed: "Also a worst case with the last element as pivot: it is always the smallest, so the split is as lopsided as it can be.",
        equal: "Also a worst case here: no value is smaller than the pivot, so every split is lopsided and it makes n(n-1)/2 comparisons.",
        nearly: "Nearly sorted stays close to the worst case, because the last element is rarely near the middle."
    },

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
                theta: 'n log n',
                reason: 'When each pivot lands near the middle, the range halves every time, so there are about log n levels and each level scans n values once.'
            },
            average: {
                value: 'O(n log n)',
                theta: 'n log n',
                reason: 'On shuffled input the pivot is rarely near either end, so the ranges shrink quickly enough to keep the depth logarithmic.'
            },
            worst: {
                value: 'O(n squared)',
                theta: 'n squared',
                reason: 'The pivot is always the last value. On a list that is already sorted, or reverse sorted, every partition peels off one value and leaves n-1 behind, giving n(n-1)/2 comparisons.'
            }
        },
        overall: { O: 'n squared', Omega: 'n log n', Theta: null },
        misconception: 'Best, average and worst are cases: three kinds of input. O, Omega and Theta are bounds: a ceiling on the growth, a floor under it, and both at once. Every case has its own bounds, so reading O as the worst case, Omega as the best and Theta as the average mixes up two different ideas.',
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
        divergence: 'Quick sort is often quoted at O(log n) space. That holds only when the partitions are balanced. Because this version always picks the last element, sorted input nests the recursion n deep, so the honest figure for this code is O(n). The middle and random pivots on the switch make sorted input an ordinary case, but with this partition a list of equal values stays quadratic whichever pivot is chosen.',
        claims: [
            { input: 'sorted', comparisons: 'n*(n-1)/2', bound: 'exact', where: 'time.worst' },
            { input: 'reversed', comparisons: 'n*(n-1)/2', bound: 'exact', where: 'presetNotes.reversed' },
            { input: 'equal', comparisons: 'n*(n-1)/2', bound: 'exact', where: 'presetNotes.equal' }
        ]
    },

    /* The switch in the Setup column. "last" is the code above. The other
       two choose a position, swap that value to the end and then run the
       same partition. Contract: static/js/lessons/README.md. */
    variants: {
        key: 'pivot',
        label: 'Pivot',
        default: 'last',
        options: {
            last: {
                label: 'Last',
                note: 'The pivot is always the last value in the range, so sorted input is the worst case.'
            },
            middle: {
                label: 'Middle',
                note: 'The value in the middle of the range is swapped to the end and used as the pivot.',
                idea: [
                    'Pick the value in the middle of the range as the pivot and swap it to the end.',
                    'Walk the range and move everything smaller than the pivot to the left side, then drop the pivot just after them.',
                    'The pivot is now in its final place, so repeat on the smaller group and the larger group separately.'
                ],
                presetNotes: {
                    random: "On shuffled input the middle position holds a typical value, so the splits are usually balanced.",
                    sorted: "The middle of a sorted range is its median, so the first split is perfect and it makes fewer than n log2 n comparisons.",
                    reversed: "The middle value is the median here too, so reversed input is no longer a bad case.",
                    equal: "Still the worst case: no value is smaller than the pivot, so it makes n(n-1)/2 comparisons whichever position the pivot came from.",
                    nearly: "Close to sorted, so the middle value is close to the median and the splits stay balanced."
                },
                code: {
                    pseudocode: [
                        { id: 'partition', text: 'to partition a range from low to high:', indent: 0 },
                        { id: null, text: 'mid = the middle position of the range', indent: 1 },
                        { id: 'choose-pivot', text: 'swap the value at mid to the end of the range', indent: 1 },
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
                        { id: null, text: 'mid = (low + high) // 2', indent: 1 },
                        { id: 'choose-pivot', text: 'arr[mid], arr[high] = arr[high], arr[mid]', indent: 1 },
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
                            theta: 'n log n',
                            reason: 'When the middle value is the median of its range, each partition halves the range. A sorted or reversed list starts that way, so both now cost fewer than n log2 n comparisons.'
                        },
                        average: {
                            value: 'O(n log n)',
                            theta: 'n log n',
                            reason: 'On shuffled input the middle position holds a value no better or worse than any other, so it behaves like a random pivot and the depth stays logarithmic.'
                        },
                        worst: {
                            value: 'O(n squared)',
                            theta: 'n squared',
                            reason: 'An all equal list still costs n(n-1)/2: no value is smaller than the pivot, so every split peels off one value. Some arrangements built against the middle choice do the same.'
                        }
                    },
                    overall: { O: 'n squared', Omega: 'n log n', Theta: null },
                    worked: {
                        input: '[5, 3, 8, 1, 9]',
                        comparisons: 6,
                        note: 'n = 5. The sorted list [1, 3, 5, 8, 9] also costs 6, where the last element pivot paid 10. But [7, 7, 7, 7, 7] still costs 10, because a tie never moves to the left of the pivot.'
                    },
                    space: {
                        value: 'O(n)',
                        what: 'the recursion stack. A sorted list now nests about log n frames deep, but an all equal list still nests n deep'
                    },
                    divergence: 'Textbooks often pair a middle pivot with Hoare\'s partition, which splits runs of equal values evenly. This version keeps the same partition as the last element pivot, which sends ties to the right, so equal values are still its worst case.',
                    claims: [
                        { input: 'sorted', comparisons: 'n*log2(n)', bound: 'atMost', where: 'time.best' },
                        { input: 'reversed', comparisons: 'n*log2(n)', bound: 'atMost', where: 'presetNotes.reversed' },
                        { input: 'equal', comparisons: 'n*(n-1)/2', bound: 'exact', where: 'time.worst' }
                    ]
                }
            },
            random: {
                label: 'Random (seeded)',
                note: 'A seeded random position in the range is swapped to the end and used as the pivot. The same seed replays the same run.',
                idea: [
                    'Pick a random value in the range as the pivot and swap it to the end. The randomness comes from a seed, so a run can be replayed.',
                    'Walk the range and move everything smaller than the pivot to the left side, then drop the pivot just after them.',
                    'The pivot is now in its final place, so repeat on the smaller group and the larger group separately.'
                ],
                presetNotes: {
                    random: "The pivot is a random value whatever the order, so expect about 1.39 n log2 n comparisons.",
                    sorted: "Sorted input is no longer special: a random pivot costs about the same here as on shuffled data.",
                    reversed: "Reversed input is no longer special either: about 1.39 n log2 n comparisons, depending on the seed.",
                    equal: "Still the worst case: a tie never moves left of the pivot, so it makes n(n-1)/2 comparisons for every seed.",
                    nearly: "Like sorted input, nearly sorted makes no difference to a random pivot."
                },
                code: {
                    pseudocode: [
                        { id: 'partition', text: 'to partition a range from low to high:', indent: 0 },
                        { id: null, text: 'r = a random position from low to high, from the seeded generator', indent: 1 },
                        { id: 'choose-pivot', text: 'swap the value at r to the end of the range', indent: 1 },
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
                        { id: null, text: 'r = low + int(rand() * (high - low + 1))', indent: 1 },
                        { id: 'choose-pivot', text: 'arr[r], arr[high] = arr[high], arr[r]', indent: 1 },
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
                            theta: 'n log n',
                            reason: 'When the seed happens to pick values near the middle, each partition halves the range, so there are about log n levels of n comparisons each.'
                        },
                        average: {
                            value: 'O(n log n)',
                            theta: 'n log n',
                            reason: 'Whatever the order of distinct values, a random pivot is a typical value, so averaged over seeds the count is 2(n+1)H(n) - 4n, about 1.39 n log2 n, where H(n) = 1 + 1/2 + ... + 1/n.'
                        },
                        worst: {
                            value: 'O(n squared)',
                            theta: 'n squared',
                            reason: 'An unlucky seed can still pick the smallest or largest value every time, and an all equal list costs n(n-1)/2 for every seed.'
                        }
                    },
                    overall: { O: 'n squared', Omega: 'n log n', Theta: null },
                    worked: {
                        input: '[5, 3, 8, 1, 9]',
                        seed: 42,
                        comparisons: 8,
                        note: 'n = 5 with seed 42. A different seed picks different pivots, so seed 1 costs 10 on the same input. The sorted list [1, 3, 5, 8, 9] costs 6 with seed 42.'
                    },
                    space: {
                        value: 'O(n)',
                        what: 'the recursion stack, about log n frames deep on average for any order of distinct values, but n deep for an all equal list or an unlucky seed'
                    },
                    divergence: 'Library quick sorts seed their random generator afresh on every call, so no two runs match. Here the seed is shown and reused, so the same seed and the same input always replay the same run.',
                    claims: [
                        { input: 'sorted', comparisons: '2*(n+1)*H(n)-4*n', bound: 'mean', where: 'time.average' },
                        { input: 'reversed', comparisons: '2*(n+1)*H(n)-4*n', bound: 'mean', where: 'presetNotes.reversed' },
                        { input: 'random', comparisons: '2*(n+1)*H(n)-4*n', bound: 'mean', where: 'presetNotes.random' },
                        { input: 'equal', comparisons: 'n*(n-1)/2', bound: 'exact', where: 'time.worst' }
                    ]
                }
            }
        }
    }
};
