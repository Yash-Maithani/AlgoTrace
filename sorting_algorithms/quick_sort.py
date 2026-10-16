from .teacher import step


def quick_sort(arr, draw, tick, stats=None):
    if stats is None:
        stats = {'swaps': 0, 'comparisons': 0}
    def partition(low, high):
        pivot = arr[high]
        i = low - 1
        for j in range(low, high):
            stats['comparisons'] += 1
            draw(arr, [j, high], step(
                'compare', [j, high], [arr[j], pivot], 'compare',
                {'low': low, 'high': high, 'i': i, 'j': j, 'pivot': pivot},
                'Is %d smaller than the pivot, %d?' % (arr[j], pivot),
                'Everything smaller than the pivot has to end up on its left, '
                'so each value is measured against it once.'))
            if arr[j] < pivot:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
                stats['swaps'] += 1
                draw(arr, [i, j], step(
                    'swap', [i, j], [arr[i], arr[j]], 'swap',
                    {'low': low, 'high': high, 'i': i, 'j': j, 'pivot': pivot},
                    '%d belongs on the pivot\'s left, so it swaps into '
                    'position %d.' % (arr[i], i),
                    'Position i marks the end of the smaller group, so the '
                    'group grows by one each time a smaller value is found.'))
                tick()
        arr[i + 1], arr[high] = arr[high], arr[i + 1]
        stats['swaps'] += 1
        draw(arr, [i + 1, high], step(
            'place', [i + 1, high], [arr[i + 1], arr[high]], 'place-pivot',
            {'low': low, 'high': high, 'i': i, 'pivot': pivot},
            'The pivot %d moves to position %d, with smaller values to its '
            'left and larger ones to its right.' % (pivot, i + 1),
            'That position is the pivot\'s final place, so it never has to '
            'move again.'))
        tick()
        return i + 1

    def sort(low, high):
        if low < high:
            pi = partition(low, high)
            sort(low, pi - 1)
            sort(pi + 1, high)

    sort(0, len(arr) - 1)
    draw(arr, ['green'] * len(arr), step(
        'done', [], [], None, {'n': len(arr)},
        'Every pivot has reached its final position, so the list is sorted.',
        'Each partition puts one value where it belongs and leaves two smaller '
        'problems, until those problems hold a single value each.'))
