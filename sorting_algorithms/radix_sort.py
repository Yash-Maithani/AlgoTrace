from .counting_sort import KEY_MAX
from .teacher import step

PLACE_NAMES = {1: 'ones', 10: 'tens', 100: 'hundreds', 1000: 'thousands'}


def radix_sort(arr, draw_func, delay, stats=None, key_max=KEY_MAX):
    """Least significant digit first, base 10. One pass per digit of
    key_max: deal every value into ten buckets by that digit, then empty the
    buckets 0 to 9 back into the list, each from the front.

    Like counting sort it is told the range in advance, every value a whole
    number from 0 to key_max, so it knows how many digits to pass over
    without comparing anything. stats['comparisons'] stays 0. The second
    counter, reported as swaps, is the writes into the list. stats
    ['operations'] counts one per value dealt, one per bucket emptied and
    one per write: d(2n + 10), the d(n + b) of the lesson.

    Every step carries `buckets`, the ten buckets as they stand, `bucket`,
    the one the step is about (or None), and `place`, 1 for the ones digit,
    10 for the tens. The values themselves move, so each keeps the position
    it started from, and equal values keep their order."""
    if stats is None:
        stats = {'swaps': 0, 'comparisons': 0}
    stats.setdefault('operations', 0)
    n = len(arr)

    def drawn(payload, buckets, taken, bucket, place):
        # A bucket being emptied is drawn without the values already taken
        # from its front.
        payload['buckets'] = [list(b[taken[d]:]) for d, b in enumerate(buckets)]
        payload['bucket'] = bucket
        payload['place'] = place
        return payload

    place = 1
    passes = 0
    while key_max // place > 0:
        passes += 1
        name = PLACE_NAMES.get(place, '%d' % place)
        buckets = [[] for _ in range(10)]
        taken = [0] * 10
        for i in range(n):
            digit = arr[i] // place % 10
            buckets[digit].append(arr[i])
            stats['operations'] += 1
            value = arr[i]
            draw_func(arr, [i], drawn(step(
                'bucket', [i], [value], 'drop',
                {'pass': passes, 'place': place, 'i': i, 'digit': digit},
                '%d has %d in the %s place, so it goes into bucket %d.'
                % (value, digit, name, digit),
                'This pass looks only at the %s digit. Values go to the back of '
                'their bucket, so the order the last pass left them in is kept.'
                % name), buckets, taken, digit, place))
            delay()

        pos = 0
        for b in range(10):
            stats['operations'] += 1
            for value in buckets[b]:
                arr[pos] = value
                taken[b] += 1
                stats['swaps'] += 1
                stats['operations'] += 1
                draw_func(arr, [pos], drawn(step(
                    'overwrite', [pos], [value], 'write',
                    {'pass': passes, 'place': place, 'b': b, 'pos': pos},
                    'Take %d from the front of bucket %d and write it into '
                    'position %d.' % (value, b, pos),
                    'Emptying the buckets 0 to 9 in order sorts the list by the '
                    '%s digit, and values with the same digit keep the order '
                    'they had.' % name), buckets, taken, b, place))
                pos += 1
                delay()
        place *= 10

    draw_func(arr, ['green'] * n, drawn(step(
        'done', [], [], None, {'n': n, 'passes': passes},
        'After %d digit pass%s the list is sorted.'
        % (passes, '' if passes == 1 else 'es'),
        'Each pass sorted by one more digit without disturbing the order the '
        'earlier passes set, and no two values were ever compared.'),
        [[] for _ in range(10)], [0] * 10, None, None))
