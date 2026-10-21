from algotrace.core.teacher import step

# Counting sort is told the range of its keys in advance: every value is a
# whole number from 0 to KEY_MAX. It needs that range to size its count list,
# and knowing it is what lets the sort finish without ever comparing two
# values. /run_sort refuses anything outside it.
KEY_MAX = 99


def counting_sort(arr, draw_func, delay, stats=None, key_max=KEY_MAX):
    """Count how often each value appears, then rewrite the list from the
    counts, smallest value first.

    No two values are ever compared, so stats['comparisons'] stays 0. The
    second counter, reported as swaps, is the writes into the list.
    stats['operations'] counts every unit of work: one per tally, one per
    slot of the count list read, one per write. That is 2n + k + 1, the
    n + k of the lesson, and tests/unit/test_jump_counting_radix.py measures it.

    Every step carries `counts`, the count list as it stands, and `cells`,
    the inclusive [lo, hi] slots of it the step is about, for the strip
    under the bars. The values written back are new copies made from the
    tallies, not the values that were read, so they have no starting
    position to keep."""
    if stats is None:
        stats = {'swaps': 0, 'comparisons': 0}
    stats.setdefault('operations', 0)
    n = len(arr)
    k = key_max

    def drawn(payload, cells):
        payload['counts'] = list(count)
        payload['cells'] = list(cells)
        return payload

    count = [0] * (k + 1)
    for i in range(n):
        count[arr[i]] += 1
        stats['operations'] += 1
        value = arr[i]
        draw_func(arr, [i], drawn(step(
            'count', [i], [value], 'tally',
            {'i': i, 'value': value, 'k': k},
            'Position %d holds %d, so count[%d] goes up to %d.'
            % (i, value, value, count[value]),
            'Counting sort never compares two values. It only counts how '
            'many times each value appears.'), [value, value]))
        delay()

    pos = 0
    empty_from = None
    for v in range(k + 1):
        stats['operations'] += 1
        # A run of empty slots is drawn as one frame, so a short list does
        # not spend most of its animation on zeros. Every slot is still read,
        # and counted, one at a time.
        if count[v] == 0:
            if empty_from is None:
                empty_from = v
            if v < k:
                continue
        if empty_from is not None:
            last = v if count[v] == 0 else v - 1
            if empty_from == last:
                told = 'count[%d] is 0, so no %d is written.' % (last, last)
            else:
                told = ('count[%d] to count[%d] are all 0, so none of the values '
                        '%d to %d is written.' % (empty_from, last, empty_from, last))
            draw_func(arr, [], drawn(step(
                'select', [], [], 'scan',
                {'v': last, 'pos': pos, 'k': k}, told,
                'The scan reads every slot of the count list, empty or not. '
                'That is where the k in n + k comes from.'), [empty_from, last]))
            empty_from = None
            if count[v] == 0:
                continue
        draw_func(arr, [], drawn(step(
            'select', [], [], 'scan',
            {'v': v, 'pos': pos, 'k': k},
            'count[%d] is %d, so %d is written %d time%s, starting at position %d.'
            % (v, count[v], v, count[v], '' if count[v] == 1 else 's', pos),
            'The slots are read from 0 upwards, so the values come out '
            'smallest first.'), [v, v]))
        for _ in range(count[v]):
            arr[pos] = v
            stats['swaps'] += 1
            stats['operations'] += 1
            draw_func(arr, [pos], drawn(step(
                'overwrite', [pos], [v], 'write',
                {'v': v, 'pos': pos, 'k': k},
                'Write %d into position %d.' % (v, pos),
                'Every value smaller than %d has already been written, so %d '
                'belongs here.' % (v, v)), [v, v]))
            pos += 1
            delay()

    draw_func(arr, ['green'] * n, drawn(step(
        'done', [], [], None, {'n': n, 'k': k},
        'Every slot of the count list has been read, and the list is rebuilt '
        'in order.',
        'Counting and rewriting took n + k steps and not a single comparison '
        'between two values.'), []))
