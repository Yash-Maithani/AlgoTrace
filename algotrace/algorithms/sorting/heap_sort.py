from algotrace.core.teacher import step


def heapify(arr, n, i, draw_func, delay, stats=None, phase='build'):
    if stats is None:
        stats = {'swaps': 0, 'comparisons': 0}
    largest = i
    l = 2 * i + 1
    r = 2 * i + 2
    if l < n:
        stats['comparisons'] += 1
        draw_func(arr, [l, largest], step(
            'compare', [l, largest], [arr[l], arr[largest]], 'cmp-left',
            {'i': i, 'left': l, 'right': r, 'largest': largest,
             'heap_size': n, 'phase': phase},
            'Is the left child %d at position %d bigger than its parent %d at '
            'position %d?' % (arr[l], l, arr[largest], largest),
            'A max heap needs every parent to be at least as big as its '
            'children, so each child is checked against the parent.'))
        if arr[l] > arr[largest]:
            largest = l
    if r < n:
        stats['comparisons'] += 1
        draw_func(arr, [r, largest], step(
            'compare', [r, largest], [arr[r], arr[largest]], 'cmp-right',
            {'i': i, 'left': l, 'right': r, 'largest': largest,
             'heap_size': n, 'phase': phase},
            'Is the right child %d at position %d bigger than %s %d at position %d?'
            % (arr[r], r, 'its parent' if largest == i else 'the left child', arr[largest], largest),
            'The right child is compared against whichever of the parent and '
            'the left child is currently bigger.'))
        if arr[r] > arr[largest]:
            largest = r
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        stats['swaps'] += 1
        draw_func(arr, [i, largest], step(
            'swap', [i, largest], [arr[i], arr[largest]], 'swap-down',
            {'i': i, 'largest': largest, 'heap_size': n, 'phase': phase},
            '%d is bigger than %d, so the two swap and the parent becomes the '
            'larger of them.' % (arr[i], arr[largest]),
            'Pushing the smaller value down may break the heap below it, so '
            'the same check runs again from its new position.'))
        delay()
        heapify(arr, n, largest, draw_func, delay, stats, phase)

def heap_sort(arr, draw_func, delay, stats=None):
    if stats is None:
        stats = {'swaps': 0, 'comparisons': 0}
    n = len(arr)
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i, draw_func, delay, stats, 'build')
    for i in range(n-1, 0, -1):
        arr[i], arr[0] = arr[0], arr[i]
        stats['swaps'] += 1
        # The pair that moved, as indices. This frame used to carry a list of
        # colour names, one per bar, which every reader had to special case:
        # the third gap recorded in the lessons README.
        draw_func(arr, [0, i], step(
            'swap', [0, i], [arr[0], arr[i]], 'swap-root',
            {'i': i, 'heap_size': i, 'phase': 'extract'},
            'The largest value %d moves to position %d, which is its final '
            'place.' % (arr[i], i),
            'The root of a max heap is always the biggest value left, so '
            'taking it off the top builds the sorted list from the right.'))
        delay()
        heapify(arr, i, 0, draw_func, delay, stats, 'extract')
    draw_func(arr, ['green'] * len(arr), step(
        'done', [], [], None, {'n': n},
        'The heap is empty and every value has been placed from the right.',
        'Each extraction placed the largest value that was left, so the list '
        'is in order.'))
