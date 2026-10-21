from algotrace.core.teacher import step


def insertion_sort(arr, draw_func, delay, stats=None):
    if stats is None:
        stats = {'swaps': 0, 'comparisons': 0}
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >=0:
            stats['comparisons'] += 1
            # The key is held in a variable, not in the array, so only arr[j]
            # is a real cell here. `compared` still highlights the slot the key
            # came from so the stage can show where it is heading back to.
            draw_func(arr, [j, i], step(
                'compare', [j], [arr[j]], 'compare',
                {'i': i, 'j': j, 'key': key},
                'Is the held value %d smaller than %d?' % (key, arr[j]),
                'The part of the list to the left is already sorted, so the '
                'key only has to walk back until it meets something smaller.'))
            if key < arr[j]:
                destination = j + 1
                arr[j + 1] = arr[j]
                stats['swaps'] += 1
                j -= 1
                draw_func(arr, [j, i], step(
                    'overwrite', [destination], [arr[destination]], 'shift',
                    {'i': i, 'j': j, 'key': key},
                    '%d is bigger than %d, so it slides one place right into '
                    'position %d.' % (arr[destination], key, destination),
                    'Sliding rather than swapping keeps the gap open for the '
                    'key, which costs one write instead of three.'))
                delay()
            else:
                break
        arr[j + 1] = key
        # The gap closes here. Without this frame the array appeared to shift
        # and the held key never visibly landed, which is the first gap
        # recorded in static/js/lessons/README.md. It draws only; the write
        # above is the same one that was always made, and it is not a swap.
        draw_func(arr, [j + 1], step(
            'overwrite', [j + 1], [arr[j + 1]], 'place',
            {'i': i, 'j': j, 'key': key},
            '%d drops into the gap at position %d, and the sorted run on the '
            'left is now one longer.' % (key, j + 1),
            'Every value to the left of the gap was already smaller, so the '
            'key is in the right place the moment the sliding stops.'))
    draw_func(arr, ['green'] * len(arr), step(
        'done', [], [], None, {'n': len(arr)},
        'Every value has been walked back into a sorted run.',
        'Once the last value has been inserted there is nothing left outside '
        'the sorted part, so the list is in order.'))
