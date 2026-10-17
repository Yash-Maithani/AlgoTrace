/* Lesson content for Heap Sort. Contract: static/js/lessons/README.md
   Figures describe sorting_algorithms/heap_sort.py, whose heapify is
   recursive, so the honest space figure is the stack, not O(1). */
window.LESSONS = window.LESSONS || {};
window.LESSONS.heap_sort = {
    id: 'heap_sort',
    name: 'Heap Sort',
    family: 'sorting',

    idea: [
        'Read the array as a binary tree, where the value at position i has children at 2i+1 and 2i+2.',
        'Rearrange it into a max heap, so every parent is at least as large as its children and the biggest value sits at the top.',
        'Swap the top value to the end, shrink the heap by one, repair the heap, and repeat until nothing is left.'
    ],
    analogy: 'A knockout tournament. The winner rises to the top, is taken out and recorded, and the remaining players play off again for the next place.',
    whenToUse: 'When you need a guaranteed O(n log n) and cannot spare the extra array merge sort needs. It is the usual safety net when quick sort goes bad.',
    stable: false,

    code: {
        pseudocode: [
            { id: 'build', text: 'build a max heap from the whole array', indent: 0 },
            { id: 'extract', text: 'for each position i from the end back to 1:', indent: 0 },
            { id: 'swap-root', text: 'swap the top value with the value at i', indent: 1 },
            { id: null, text: 'shrink the heap so i is now outside it', indent: 1 },
            { id: null, text: 'repair the heap from the top:', indent: 1 },
            { id: 'cmp-left', text: 'if the left child is bigger than the largest so far:', indent: 2 },
            { id: null, text: 'the left child is the largest', indent: 3 },
            { id: 'cmp-right', text: 'if the right child is bigger than the largest so far:', indent: 2 },
            { id: null, text: 'the right child is the largest', indent: 3 },
            { id: 'swap-down', text: 'if the largest is not the parent, swap and repeat below', indent: 2 }
        ],
        python: [
            { id: 'build', text: 'for i in range(n // 2 - 1, -1, -1): heapify(arr, n, i)', indent: 0 },
            { id: 'extract', text: 'for i in range(n-1, 0, -1):', indent: 0 },
            { id: 'swap-root', text: 'arr[i], arr[0] = arr[0], arr[i]', indent: 1 },
            { id: null, text: 'heapify(arr, i, 0)', indent: 1 },
            { id: null, text: 'def heapify(arr, n, i):', indent: 0 },
            { id: null, text: 'largest, l, r = i, 2 * i + 1, 2 * i + 2', indent: 1 },
            { id: 'cmp-left', text: 'if l < n and arr[l] > arr[largest]:', indent: 1 },
            { id: null, text: 'largest = l', indent: 2 },
            { id: 'cmp-right', text: 'if r < n and arr[r] > arr[largest]:', indent: 1 },
            { id: null, text: 'largest = r', indent: 2 },
            { id: 'swap-down', text: 'if largest != i: swap, then heapify(arr, n, largest)', indent: 1 }
        ]
    },

    complexity: {
        time: {
            best: {
                value: 'O(n log n)',
                reason: 'Building the heap costs O(n), then each of the n-1 extractions repairs a heap of height log n. Nothing about the input lets the repair stop early.'
            },
            average: {
                value: 'O(n log n)',
                reason: 'Each repair walks at most one path from the root to a leaf, comparing up to two children per level.'
            },
            worst: {
                value: 'O(n log n)',
                reason: 'The height of the heap bounds every repair, so there is no arrangement that makes a repair longer than log n levels.'
            }
        },
        worked: {
            input: '[5, 3, 8, 1, 9]',
            comparisons: 11,
            note: 'n = 5. More comparisons than the quadratic sorts need at this size, which is the point: the n log n shape only pays off once n is large. The sorted list [1, 3, 5, 8, 9] costs 12 here, because a sorted array is a poor max heap to start from.'
        },
        space: {
            value: 'O(log n)',
            what: 'the recursion stack inside heapify, which nests once per level of the heap. The sorting itself happens inside the original array'
        },
        auxiliaryNote: 'Auxiliary space is the memory the algorithm needs on top of the input array itself.',
        thisRun: 'Big O describes how work grows as the input grows and ignores constants. The counter shows the exact work for this one input.',
        growth: 'nlogn',
        growthBasis: null,
        growthNote: null,
        divergence: 'Heap sort is normally quoted at O(1) space because it sorts in place. That holds for the version that repairs the heap with a loop. The heapify here calls itself, so each level of the heap adds a stack frame and the honest figure for this code is O(log n).'
    }
};
