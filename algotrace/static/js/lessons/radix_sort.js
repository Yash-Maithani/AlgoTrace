/* Lesson content for Radix Sort. Contract: static/js/lessons/README.md
   Figures describe algotrace/algorithms/sorting/radix_sort.py: least significant digit
   first, base 10, told its key range in advance (whole numbers from 0 to 99),
   so it always makes two passes and compares nothing.
   tests/unit/test_jump_counting_radix.py measures every figure stated here. */
window.LESSONS = window.LESSONS || {};
window.LESSONS.radix_sort = {
    id: 'radix_sort',
    name: 'Radix Sort',
    family: 'sorting',

    idea: [
        'Deal every value into one of ten buckets, 0 to 9, by its ones digit, keeping the order they arrive in.',
        'Empty the buckets back into the list from bucket 0 to bucket 9: the list is now sorted by its ones digit.',
        'Do the same with the tens digit; because each pass keeps the order of equal digits, the list ends up fully sorted.'
    ],
    analogy: 'Sorting a stack of letters by a two digit post code: first into ten piles by the last digit, stack the piles in order, then deal again by the first digit. Inside each pile, the second deal keeps the order the first one left.',
    whenToUse: 'When the values are whole numbers, or keys like dates and codes, with a fixed, small number of digits. It is the method behind sorting machines for punched cards and post.',
    stable: true,
    presetNotes: {
        random: "The same work as every other input: two passes, each dealing n values into buckets and writing n back.",
        sorted: "No faster than random. Each pass deals every value by its digit whatever order they are in.",
        reversed: "No slower than sorted, for the same reason: two passes of n deals and n writes.",
        equal: "Every value lands in the same bucket on both passes, and comes out in the order it went in, so the letter tags keep their order.",
        nearly: "The same two passes again. There are no comparisons for a nearly sorted list to save."
    },

    /* The values are written back from the buckets; nothing is exchanged.
       See complexity.countsNote. */
    countLabel: 'writes',

    code: {
        pseudocode: [
            { id: null, text: 'place = 1, the ones digit', indent: 0 },
            { id: null, text: 'while k still has a digit at this place:', indent: 0 },
            { id: null, text: 'make ten empty buckets, 0 to 9', indent: 1 },
            { id: null, text: 'for each value in the list:', indent: 1 },
            { id: 'drop', text: 'put it at the back of the bucket for its digit at this place', indent: 2 },
            { id: null, text: 'pos = 0', indent: 1 },
            { id: null, text: 'for each bucket from 0 to 9, and each value in it, front first:', indent: 1 },
            { id: 'write', text: 'write the value at pos, then move pos on by one', indent: 2 },
            { id: null, text: 'move place on to the next digit', indent: 1 }
        ],
        python: [
            { id: null, text: 'place = 1', indent: 0 },
            { id: null, text: 'while k // place > 0:', indent: 0 },
            { id: null, text: 'buckets = [[] for _ in range(10)]', indent: 1 },
            { id: null, text: 'for i in range(len(arr)):', indent: 1 },
            { id: null, text: 'digit = arr[i] // place % 10', indent: 2 },
            { id: 'drop', text: 'buckets[digit].append(arr[i])', indent: 2 },
            { id: null, text: 'pos = 0', indent: 1 },
            { id: null, text: 'for b in range(10):', indent: 1 },
            { id: null, text: 'for value in buckets[b]:', indent: 2 },
            { id: 'write', text: 'arr[pos] = value', indent: 3 },
            { id: null, text: 'pos += 1', indent: 3 },
            { id: null, text: 'place *= 10', indent: 1 }
        ]
    },

    complexity: {
        time: {
            best: {
                value: 'O(d times (n plus b))',
                theta: 'd times (n plus b)',
                reason: 'Every input costs the same: d passes, here 2, each dealing n values, emptying b = 10 buckets and writing n values back. That is d(2n + 10) steps.'
            },
            average: {
                value: 'O(d times (n plus b))',
                theta: 'd times (n plus b)',
                reason: 'Nothing depends on the order of the values, so a typical input costs exactly what the best one does.'
            },
            worst: {
                value: 'O(d times (n plus b))',
                theta: 'd times (n plus b)',
                reason: 'Each pass touches every value twice and every bucket once, whatever the values are, so no input costs more than d(2n + 10).'
            }
        },
        overall: { O: 'd times (n plus b)', Omega: 'd times (n plus b)', Theta: 'd times (n plus b)' },
        misconception: 'Best, average and worst are cases: three kinds of input. O, Omega and Theta are bounds: a ceiling on the growth, a floor under it, and both at once. Every case has its own bounds, so reading O as the worst case, Omega as the best and Theta as the average mixes up two different ideas.',
        worked: {
            input: '[5, 3, 8, 1, 9]',
            comparisons: 0,
            note: 'n = 5, d = 2 and b = 10. Each pass deals 5 values, empties 10 buckets and writes 5 values: 20 steps a pass, 40 in all, 10 writes and 0 comparisons. Every value here is below 10, but the tens pass still runs, because the range allows two digits.'
        },
        space: {
            value: 'O(n plus b)',
            what: 'the ten buckets, which between them hold all n values during a pass'
        },
        auxiliaryNote: 'Auxiliary space is the memory the algorithm needs on top of the input array itself.',
        thisRun: 'Big O describes how work grows as the input grows and ignores constants. The counter shows the exact work for this one input.',
        countsNote: 'The comparisons counter stays at 0, and that is the point. Any sort that decides the order by comparing two values at a time needs about n log n comparisons in its worst case; that is a proven limit. Radix sort never compares, it only reads digits, so the limit does not apply to it. The price is the rule on the input: whole numbers with a known number of digits, here 0 to 99. The second counter is writes, one for each value written back into the list, so n on every pass.',
        growth: null,
        growthBasis: null,
        growthNote: 'O(d times (n plus b)) needs three numbers, the digits per value, the length of the list and the number of buckets, so no single curve on an axis of n is that figure. On this site d is 2 and b is 10, so the work is 4n + 20 steps, which grows like the O(n) line once n is large.',
        divergence: 'Many versions count the digits of the largest value first, which costs comparisons. This one is told the range, 0 to 99, so it always makes 2 passes, even when every value is below 10. Least significant digit first only works because each pass keeps the order of values with the same digit; that is why it deals to the back of a bucket and empties from the front.'
    }
};
