/* Lesson content for Counting Sort. Contract: static/js/lessons/README.md
   Figures describe algotrace/algorithms/sorting/counting_sort.py, which is told its key
   range in advance (whole numbers from 0 to 99) and so compares nothing.
   tests/unit/test_jump_counting_radix.py measures every figure stated here. */
window.LESSONS = window.LESSONS || {};
window.LESSONS.counting_sort = {
    id: 'counting_sort',
    name: 'Counting Sort',
    family: 'sorting',

    idea: [
        'Make a count list with one slot for every value the input may hold, here 0 to 99, all starting at zero.',
        'Read the list once and add one to the slot of each value you meet.',
        'Read the count list from slot 0 upwards and write each value back as many times as it was counted.'
    ],
    analogy: 'Sorting a pile of exam papers by mark with a row of 100 trays: drop each paper in the tray for its mark, then collect the trays from 0 upwards. You never compare two papers.',
    whenToUse: 'When the values are whole numbers in a small, known range, such as marks out of 100 or ages. The count list costs one slot per possible value, so a wide range makes it slow and wasteful.',
    stable: null,
    presetNotes: {
        random: "The same work as every other input: n tallies, all 100 slots read, n writes. The order of the input changes nothing.",
        sorted: "No faster than random. Counting sort does not look at the order, only at how many of each value there are.",
        reversed: "No slower than sorted, for the same reason: n tallies, 100 slots, n writes.",
        equal: "Every tally lands in one slot, and the other 99 slots are still read and found empty.",
        nearly: "The same work again. There are no comparisons for a nearly sorted list to save."
    },

    /* The values are rewritten from the counts; nothing is exchanged. See
       complexity.countsNote. */
    countLabel: 'writes',

    code: {
        pseudocode: [
            { id: null, text: 'make a count list with a 0 for each value from 0 to k', indent: 0 },
            { id: null, text: 'for each value in the list:', indent: 0 },
            { id: 'tally', text: 'add 1 to count[value]', indent: 1 },
            { id: null, text: 'pos = 0', indent: 0 },
            { id: 'scan', text: 'for each v from 0 to k:', indent: 0 },
            { id: null, text: 'repeat count[v] times:', indent: 1 },
            { id: 'write', text: 'write v at pos, then move pos on by one', indent: 2 }
        ],
        python: [
            { id: null, text: 'count = [0] * (k + 1)', indent: 0 },
            { id: null, text: 'for i in range(len(arr)):', indent: 0 },
            { id: 'tally', text: 'count[arr[i]] += 1', indent: 1 },
            { id: null, text: 'pos = 0', indent: 0 },
            { id: 'scan', text: 'for v in range(k + 1):', indent: 0 },
            { id: null, text: 'for _ in range(count[v]):', indent: 1 },
            { id: 'write', text: 'arr[pos] = v', indent: 2 },
            { id: null, text: 'pos += 1', indent: 2 }
        ]
    },

    complexity: {
        time: {
            best: {
                value: 'O(n plus k)',
                theta: 'n plus k',
                reason: 'Every input costs the same: one tally per value, one read per slot of the count list, one write per value. That is 2n + k + 1 steps, here k = 99.'
            },
            average: {
                value: 'O(n plus k)',
                theta: 'n plus k',
                reason: 'Nothing depends on the order of the values, so a typical input costs exactly what the best one does.'
            },
            worst: {
                value: 'O(n plus k)',
                theta: 'n plus k',
                reason: 'The scan reads every one of the k + 1 slots even when most are empty, and the tallies and writes are one per value, so no input costs more than 2n + k + 1.'
            }
        },
        overall: { O: 'n plus k', Omega: 'n plus k', Theta: 'n plus k' },
        misconception: 'Best, average and worst are cases: three kinds of input. O, Omega and Theta are bounds: a ceiling on the growth, a floor under it, and both at once. Every case has its own bounds, so reading O as the worst case, Omega as the best and Theta as the average mixes up two different ideas.',
        worked: {
            input: '[5, 3, 8, 1, 9]',
            comparisons: 0,
            note: 'n = 5 and k = 99. It makes 5 tallies, reads all 100 slots of the count list and writes 5 values back: 110 steps and 0 comparisons. Any other 5 values from 0 to 99 cost exactly the same.'
        },
        space: {
            value: 'O(k)',
            what: 'the count list, one slot for each value from 0 to k, however short the input is'
        },
        auxiliaryNote: 'Auxiliary space is the memory the algorithm needs on top of the input array itself.',
        thisRun: 'Big O describes how work grows as the input grows and ignores constants. The counter shows the exact work for this one input.',
        countsNote: 'The comparisons counter stays at 0, and that is the point. Any sort that decides the order by comparing two values at a time needs about n log n comparisons in its worst case; that is a proven limit. Counting sort never compares, so the limit does not apply to it. The price is the rule on the input: whole numbers in a known range, here 0 to 99. The second counter is writes, one for each value written back into the list.',
        growth: null,
        growthBasis: null,
        growthNote: 'O(n plus k) needs two numbers, the length of the list and the size of the key range, so no single curve on an axis of n is that figure. On this site k is always 99, so the work is 2n + 100 steps, which grows like the O(n) line once n is large.',
        divergence: 'Many versions find k from the largest value, which costs n - 1 comparisons. This one is told the range, 0 to 99, so it compares nothing. The version that keeps equal records in order adds the counts up into starting positions and copies each record into a second list; this one rebuilds the numbers from their counts, which is all plain numbers need, so the values written back are new copies and stability does not apply.'
    }
};
