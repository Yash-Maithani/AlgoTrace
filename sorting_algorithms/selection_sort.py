from .teacher import step


def selection_sort(arr, draw_func, delay, stats=None):
    if stats is None:
        stats = {'swaps': 0, 'comparisons': 0}
    n = len(arr)

    for i in range(n):
        min_idx = i
        # Show current position being filled (green)
        draw_func(arr, [i], step(
            'select', [i], [arr[i]], 'min-init',
            {'i': i, 'min_idx': min_idx, 'n': n},
            'Position %d is the next slot to fill, and %d is the smallest '
            'value found so far.' % (i, arr[i]),
            'Selection sort fills the list from the left, one final position '
            'at a time.'))
        delay()

        for j in range(i+1, n):
            stats['comparisons'] += 1
            # Show comparison: current minimum (red) and element being compared (blue)
            draw_func(arr, [min_idx, j], step(
                'compare', [min_idx, j], [arr[min_idx], arr[j]], 'compare',
                {'i': i, 'j': j, 'min_idx': min_idx, 'n': n},
                'Is %d smaller than the smallest so far, %d?'
                % (arr[j], arr[min_idx]),
                'The scan has to see every remaining value before it can be '
                'sure which one is smallest.'))
            delay()

            if arr[min_idx] > arr[j]:
                min_idx = j
                # Show new minimum found
                draw_func(arr, [min_idx], step(
                    'select', [min_idx], [arr[min_idx]], 'update-min',
                    {'i': i, 'j': j, 'min_idx': min_idx, 'n': n},
                    '%d is the new smallest value, at position %d.'
                    % (arr[min_idx], min_idx),
                    'Remembering the position is enough. Nothing moves until '
                    'the scan has finished.'))
                delay()

        # Swap if needed
        if i != min_idx:
            arr[i], arr[min_idx] = arr[min_idx], arr[i]
            stats['swaps'] += 1
            # Show the swap
            draw_func(arr, [i, min_idx], step(
                'swap', [i, min_idx], [arr[i], arr[min_idx]], 'swap',
                {'i': i, 'min_idx': min_idx, 'n': n},
                '%d was the smallest, so it moves into position %d and %d '
                'takes its old place.' % (arr[i], i, arr[min_idx]),
                'One swap per pass is all selection sort ever needs, which is '
                'what makes it cheap on writes.'))
            delay()

    # Show final sorted array
    draw_func(arr, ['green'] * len(arr), step(
        'done', [], [], None, {'n': n},
        'Every position has been filled with the smallest value that was left.',
        'After n passes there is nothing left to choose from, so the list is '
        'sorted.'))
