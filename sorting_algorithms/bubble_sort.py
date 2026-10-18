from .teacher import step


def bubble_sort(arr, draw_func, delay, stats=None, early_exit=False):
    """early_exit=False is the version this site has always run. True adds
    the textbook flag: a pass that makes no swaps ends the sort."""
    if stats is None:
        stats = {'swaps': 0, 'comparisons': 0}
    n = len(arr)
    passes = 0
    for i in range(n):
        swapped = False
        passes = i + 1
        for j in range(0, n-i-1):
            stats['comparisons'] += 1
            draw_func(arr, [j, j+1], step(
                'compare', [j, j+1], [arr[j], arr[j+1]], 'compare',
                {'i': i, 'j': j, 'n': n},
                'Compare %d and %d, the pair sitting next to each other at '
                'positions %d and %d.' % (arr[j], arr[j+1], j, j+1),
                'Bubble sort only ever looks at neighbours, so this is the '
                'only comparison it can make from here.'))
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
                swapped = True
                stats['swaps'] += 1
                draw_func(arr, [j, j+1], step(
                    'swap', [j, j+1], [arr[j], arr[j+1]], 'swap',
                    {'i': i, 'j': j, 'n': n},
                    '%d was bigger than %d, so the two change places.'
                    % (arr[j+1], arr[j]),
                    'Each swap pushes the larger value one step to the right, '
                    'which is how the biggest value reaches the end of this pass.'))
                delay()
        if early_exit and not swapped:
            break
    if early_exit:
        if passes < n:
            told = ('Pass %d made no swaps, so nothing is out of order and the '
                    'sort stops after %d of the %d passes.' % (passes, passes, n))
        else:
            told = ('Only the last pass made no swaps, so all %d passes ran '
                    'and the flag saved nothing on this input.' % n)
        draw_func(arr, ['green'] * len(arr), step(
            'done', [], [], None, {'n': n, 'passes': passes}, told,
            'With the early exit flag, one clean pass proves the list is '
            'sorted, so the passes left over are skipped.'))
        return
    draw_func(arr, ['green'] * len(arr), step(
        'done', [], [], None, {'n': n},
        'Nothing is left out of order, so the sort is finished.',
        'Bubble sort runs every pass to the end, so it stops only when all '
        'of them are done.'))
