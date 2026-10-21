from algotrace.core.teacher import step
from .seeded import mulberry32

PIVOTS = ('last', 'middle', 'random')


def quick_sort(arr, draw, tick, stats=None, pivot_rule='last', seed=None):
    """pivot_rule='last' is the version this site has always run. 'middle'
    and 'random' pick another position and swap it to the end first, so the
    partition below is the same code in all three. 'random' draws from a
    mulberry32 generator seeded with `seed`, so a seed replays a run exactly.

    Every step carries `depth`, how many calls deep the partition is (the
    first call is 0), and `range`, the inclusive [lo, hi] it works on."""
    if stats is None:
        stats = {'swaps': 0, 'comparisons': 0}
    if pivot_rule not in PIVOTS:
        raise ValueError('unknown pivot rule %r' % (pivot_rule,))
    if pivot_rule == 'random' and seed is None:
        raise ValueError('a random pivot needs a seed, so the run can be replayed')
    rand = mulberry32(seed) if pivot_rule == 'random' else None

    def located(payload, depth, low, high):
        payload['depth'] = depth
        payload['range'] = [low, high]
        return payload

    def choose_pivot(low, high, depth):
        if pivot_rule == 'last':
            return
        if pivot_rule == 'middle':
            chosen = (low + high) // 2
            how = 'the middle of the range'
        else:
            chosen = low + int(rand() * (high - low + 1))
            how = 'a seeded random pick'
        if chosen == high:
            return
        arr[chosen], arr[high] = arr[high], arr[chosen]
        stats['swaps'] += 1
        draw(arr, [chosen, high], located(step(
            'swap', [chosen, high], [arr[chosen], arr[high]], 'choose-pivot',
            {'low': low, 'high': high, 'chosen': chosen, 'pivot': arr[high]},
            '%d at position %d is the pivot, %s, so it swaps to the end of '
            'the range first.' % (arr[high], chosen, how),
            'Moving the chosen pivot to the end lets the same partition code '
            'run whichever position the pivot came from.'),
            depth, low, high))
        tick()

    def partition(low, high, depth):
        choose_pivot(low, high, depth)
        pivot = arr[high]
        i = low - 1
        for j in range(low, high):
            stats['comparisons'] += 1
            draw(arr, [j, high], located(step(
                'compare', [j, high], [arr[j], pivot], 'compare',
                {'low': low, 'high': high, 'i': i, 'j': j, 'pivot': pivot},
                'Is %d smaller than the pivot, %d?' % (arr[j], pivot),
                'Everything smaller than the pivot has to end up on its left, '
                'so each value is measured against it once.'),
                depth, low, high))
            if arr[j] < pivot:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
                stats['swaps'] += 1
                draw(arr, [i, j], located(step(
                    'swap', [i, j], [arr[i], arr[j]], 'swap',
                    {'low': low, 'high': high, 'i': i, 'j': j, 'pivot': pivot},
                    '%d belongs on the pivot\'s left, so it swaps into '
                    'position %d.' % (arr[i], i),
                    'Position i marks the end of the smaller group, so the '
                    'group grows by one each time a smaller value is found.'),
                    depth, low, high))
                tick()
        arr[i + 1], arr[high] = arr[high], arr[i + 1]
        stats['swaps'] += 1
        draw(arr, [i + 1, high], located(step(
            'place', [i + 1, high], [arr[i + 1], arr[high]], 'place-pivot',
            {'low': low, 'high': high, 'i': i, 'pivot': pivot},
            'The pivot %d moves to position %d, with smaller values to its '
            'left and larger ones to its right.' % (pivot, i + 1),
            'That position is the pivot\'s final place, so it never has to '
            'move again.'),
            depth, low, high))
        tick()
        return i + 1

    def sort(low, high, depth):
        if low < high:
            pi = partition(low, high, depth)
            sort(low, pi - 1, depth + 1)
            sort(pi + 1, high, depth + 1)

    sort(0, len(arr) - 1, 0)
    draw(arr, ['green'] * len(arr), located(step(
        'done', [], [], None, {'n': len(arr)},
        'Every pivot has reached its final position, so the list is sorted.',
        'Each partition puts one value where it belongs and leaves two smaller '
        'problems, until those problems hold a single value each.'),
        0, 0, len(arr) - 1))
