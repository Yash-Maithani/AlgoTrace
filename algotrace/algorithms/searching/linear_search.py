"""Linear search, instrumented for the visualization.

Counting convention, as stated in static/js/lessons/linear_search.js: one
comparison each time the loop looks at a value. The line ids below match the
code listing in that lesson.
"""
from algotrace.core.teacher import step


def linear_search(arr, target, draw_func, delay=None, stats=None):
    """Walk the list from the start and stop at the first match.

    draw_func(indices, meta) records one frame. The array never changes, so
    unlike a sort there is nothing to redraw: the frame is the position being
    looked at plus its teacher payload.
    """
    if stats is None:
        stats = {'comparisons': 0}
    if delay is None:
        def delay():
            return None

    n = len(arr)

    for i in range(n):
        stats['comparisons'] += 1
        draw_func([i], step(
            'compare', [i], [arr[i]], 'compare',
            {'i': i, 'target': target, 'comparisons': stats['comparisons'],
             'n': n},
            'Is the value at position %d, which is %d, equal to %d?'
            % (i, arr[i], target),
            'Linear search has no idea where the target might be, so it has '
            'to look at every value in turn until it finds one.'))
        delay()

        if arr[i] == target:
            draw_func([i], step(
                'found', [i], [arr[i]], 'found',
                {'i': i, 'target': target,
                 'comparisons': stats['comparisons'], 'n': n},
                'Found %d at position %d after %d comparison%s.'
                % (target, i, stats['comparisons'],
                   '' if stats['comparisons'] == 1 else 's'),
                'The search stops at the first match, so a target near the '
                'front is found quickly and one near the back is not.'))
            return i

    draw_func([], step(
        'missing', [], [], 'missing',
        {'target': target, 'comparisons': stats['comparisons'], 'n': n},
        '%d is not in the list. All %d value%s were checked.'
        % (target, stats['comparisons'],
           '' if stats['comparisons'] == 1 else 's'),
        'Ruling a value out means looking at every single position, which is '
        'why a failed search is always the worst case.'))
    return -1
