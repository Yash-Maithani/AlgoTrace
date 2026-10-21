"""Jump search, instrumented for the visualization.

Counting convention, as stated in static/js/lessons/jump_search.js: one
comparison each time the search looks at a value, the same rule linear and
binary search follow. The line ids below match the code listing in that
lesson.

Like binary search it is only correct on a sorted list, and the caller
refuses an unsorted one (binary_search.is_sorted).

Every step's vars carry `low` and `high`, the first and last position that
could still hold the target: while jumping, high is the end of the list;
while scanning, it is the end of the block.
"""
import math

from algotrace.core.teacher import step


def jump_search(arr, target, draw_func, delay=None, stats=None):
    """Jump ahead a block of floor(sqrt(n)) values at a time, looking only at
    the last value of each block, then scan the one block that can hold the
    target."""
    if stats is None:
        stats = {'comparisons': 0}
    if delay is None:
        def delay():
            return None

    n = len(arr)
    if n == 0:
        draw_func([], step(
            'missing', [], [], None,
            {'target': target, 'comparisons': 0, 'n': 0},
            '%d is not in the list. The list is empty.' % target,
            'There is nothing to look at, so the answer is settled at once.'))
        return -1

    block = math.isqrt(n)
    low = 0
    end = min(block, n) - 1

    def plural(count):
        return '' if count == 1 else 's'

    while True:
        stats['comparisons'] += 1
        draw_func([end], step(
            'compare', [end], [arr[end]], 'jump-check',
            {'low': low, 'end': end, 'high': n - 1, 'block': block,
             'target': target, 'comparisons': stats['comparisons'], 'n': n},
            'Position %d, the last of the block from %d to %d, holds %d. Is it '
            'smaller than %d?' % (end, low, end, arr[end], target),
            'Looking only at the end of a block tells the search whether the '
            'target can be anywhere inside it.'))
        delay()
        if arr[end] >= target:
            break
        if end == n - 1:
            draw_func([], step(
                'missing', [], [], 'past-end',
                {'low': n, 'end': end, 'high': n - 1, 'block': block,
                 'target': target, 'comparisons': stats['comparisons'], 'n': n},
                'Even the last value, %d, is smaller than %d, so %d is not in '
                'the list. Checked %d value%s.'
                % (arr[end], target, target, stats['comparisons'],
                   plural(stats['comparisons'])),
                'The list is sorted, so once the last value is smaller than the '
                'target, nothing in the list can be the target.'))
            return -1
        passed = arr[end]
        low = end + 1
        end = min(end + block, n - 1)
        draw_func([low - 1], step(
            'discard', [low - 1], [passed], 'jump',
            {'low': low, 'end': end, 'high': n - 1, 'block': block,
             'target': target, 'comparisons': stats['comparisons'], 'n': n},
            '%d is smaller than %d, so the whole block up to position %d is '
            'ruled out. Jump ahead to position %d.'
            % (passed, target, low - 1, end),
            'The list is sorted, so every value in a block whose last value is '
            'smaller than the target is smaller too.'))
        delay()

    for i in range(low, end + 1):
        stats['comparisons'] += 1
        draw_func([i], step(
            'compare', [i], [arr[i]], 'scan',
            {'low': low, 'end': end, 'high': end, 'block': block, 'i': i,
             'target': target, 'comparisons': stats['comparisons'], 'n': n},
            'Scan the block: position %d holds %d. Is that %d?'
            % (i, arr[i], target),
            'The block from %d to %d is the only place the target can be, '
            'so the search checks it one value at a time.' % (low, end)))
        delay()
        if arr[i] == target:
            draw_func([i], step(
                'found', [i], [arr[i]], 'found',
                {'low': low, 'end': end, 'high': end, 'block': block, 'i': i,
                 'target': target, 'comparisons': stats['comparisons'], 'n': n},
                'Found %d at position %d after %d comparison%s.'
                % (target, i, stats['comparisons'], plural(stats['comparisons'])),
                'The jumps skipped whole blocks, so only a few values were '
                'looked at before the scan found it.'))
            return i
        if arr[i] > target:
            break

    draw_func([], step(
        'missing', [], [], 'missing',
        {'low': low, 'end': end, 'high': end, 'block': block,
         'target': target, 'comparisons': stats['comparisons'], 'n': n},
        'The scan reached %d, which is bigger than %d, so %d is not in the '
        'list. Checked %d value%s.'
        % (arr[i], target, target, stats['comparisons'],
           plural(stats['comparisons'])),
        'The list is sorted, so once the scan passes a value bigger than the '
        'target, the target cannot come later.'))
    return -1
