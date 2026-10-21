"""Binary search, iterative, instrumented for the visualization.

Counting convention, as stated in static/js/lessons/binary_search.js: one
comparison each time the loop looks at a middle value. The line ids below
match the code listing in that lesson.

The caller is responsible for refusing an unsorted list. is_sorted is here so
the endpoint and the tests ask the same question.
"""
from algotrace.core.teacher import step


def is_sorted(arr):
    """True when every value is at least as large as the one before it."""
    return all(arr[i] <= arr[i + 1] for i in range(len(arr) - 1))


def binary_search(arr, target, draw_func, delay=None, stats=None):
    """Halve the live range until the target is found or the range is empty."""
    if stats is None:
        stats = {'comparisons': 0}
    if delay is None:
        def delay():
            return None

    n = len(arr)
    low, high = 0, n - 1

    while low <= high:
        mid = (low + high) // 2
        stats['comparisons'] += 1
        draw_func([mid], step(
            'compare', [mid], [arr[mid]], 'compare',
            {'low': low, 'mid': mid, 'high': high, 'target': target,
             'comparisons': stats['comparisons'], 'n': n,
             'range_size': high - low + 1},
            'The middle of positions %d to %d is %d, which holds %d. Is that '
            '%d?' % (low, high, mid, arr[mid], target),
            'Looking at the middle is what lets one comparison rule out half '
            'of what is left.'))
        delay()

        if arr[mid] == target:
            draw_func([mid], step(
                'found', [mid], [arr[mid]], 'found',
                {'low': low, 'mid': mid, 'high': high, 'target': target,
                 'comparisons': stats['comparisons'], 'n': n},
                'Found %d at position %d after %d comparison%s.'
                % (target, mid, stats['comparisons'],
                   '' if stats['comparisons'] == 1 else 's'),
                'Each comparison halved the range, so even a long list is '
                'settled in very few steps.'))
            return mid

        if arr[mid] < target:
            low = mid + 1
            draw_func([mid], step(
                'discard', [mid], [arr[mid]], 'go-right',
                {'low': low, 'mid': mid, 'high': high, 'target': target,
                 'comparisons': stats['comparisons'], 'n': n,
                 'range_size': max(high - low + 1, 0)},
                '%d is bigger than %d, so everything from position %d '
                'leftwards is out.' % (target, arr[mid], mid),
                'The list is sorted, so nothing to the left of a value '
                'smaller than the target can be the target.'))
        else:
            high = mid - 1
            draw_func([mid], step(
                'discard', [mid], [arr[mid]], 'go-left',
                {'low': low, 'mid': mid, 'high': high, 'target': target,
                 'comparisons': stats['comparisons'], 'n': n,
                 'range_size': max(high - low + 1, 0)},
                '%d is smaller than %d, so everything from position %d '
                'rightwards is out.' % (target, arr[mid], mid),
                'The list is sorted, so nothing to the right of a value '
                'bigger than the target can be the target.'))
        delay()

    draw_func([], step(
        'missing', [], [], 'missing',
        {'low': low, 'high': high, 'target': target,
         'comparisons': stats['comparisons'], 'n': n, 'range_size': 0},
        '%d is not in the list. The range closed after %d comparison%s.'
        % (target, stats['comparisons'],
           '' if stats['comparisons'] == 1 else 's'),
        'When low passes high there is nothing left that could hold the '
        'target, so the answer is settled without looking at the rest.'))
    return -1
