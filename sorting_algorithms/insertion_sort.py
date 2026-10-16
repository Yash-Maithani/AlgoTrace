from .teacher import step


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
    draw_func(arr, ['green'] * len(arr), step(
        'done', [], [], None, {'n': len(arr)},
        'Every value has been walked back into a sorted run.',
        'Once the last value has been inserted there is nothing left outside '
        'the sorted part, so the list is in order.'))
