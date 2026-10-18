from .teacher import step


def merge_sort(arr, draw_func, delay, stats=None, stable=False):
    """stable=False compares with <, the version this site has always run.
    True compares with <=, so on a tie the left half's value goes first.

    Every step carries `depth`, how many calls deep the merge is (the first
    call is 0), and `range`, the inclusive [lo, hi] slice that call owns."""
    if stats is None:
        stats = {'swaps': 0, 'comparisons': 0}

    def located(payload, depth, lo, hi):
        payload['depth'] = depth
        payload['range'] = [lo, hi]
        return payload

    def merge(left, right, start_index, depth):
        lo, hi = start_index, start_index + len(left) + len(right) - 1
        result = []
        i = j = 0
        while i < len(left) and j < len(right):
            stats['comparisons'] += 1
            told = ('Compare %d from the left half with %d from the right '
                    'half.' % (left[i], right[j]))
            if left[i] == right[j]:
                # The tie is where the two variants part ways, and where a
                # stability tag on the bars changes order or does not.
                told += (' They are equal, so %s takes the %s one first.'
                         % ('<=' if stable else '<',
                            'left' if stable else 'right'))
            # Both halves are still untouched at this point, so the right
            # hand value really is at start_index + len(left) + j. The stage
            # used to be sent start_index + j, which pointed into the left
            # half: the second gap recorded in the lessons README.
            draw_func(arr, [start_index + i, start_index + len(left) + j], located(step(
                'compare',
                [start_index + i, start_index + len(left) + j],
                [left[i], right[j]],
                'merge-compare',
                {'i': i, 'j': j, 'start': start_index,
                 'left_len': len(left), 'right_len': len(right)},
                told,
                'Both halves are already sorted, so whichever of these two is '
                'smaller is the smallest value left anywhere in the pair.'),
                depth, lo, hi))
            if (left[i] <= right[j]) if stable else (left[i] < right[j]):
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        result += left[i:]
        result += right[j:]
        for idx, val in enumerate(result):
            arr[start_index + idx] = val
            stats['swaps'] += 1
            draw_func(arr, [start_index + idx], located(step(
                'overwrite', [start_index + idx], [val], 'copy-back',
                {'idx': idx, 'start': start_index, 'merged_len': len(result)},
                'Write %d back into position %d of the array.'
                % (val, start_index + idx),
                'The merged run was built in a temporary list, so it has to be '
                'copied back over the two halves it replaces.'),
                depth, lo, hi))
            delay()

    def sort(start, end, depth):
        if end - start > 1:
            mid = (start + end) // 2
            sort(start, mid, depth + 1)
            sort(mid, end, depth + 1)
            merge(arr[start:mid], arr[mid:end], start, depth)

    sort(0, len(arr), 0)
    draw_func(arr, ['green'] * len(arr), located(step(
        'done', [], [], None, {'n': len(arr)},
        'Every pair of halves has been merged back together in order.',
        'Splitting stops at single values, which are sorted by definition, so '
        'every merge above them produces a sorted run.'),
        0, 0, len(arr) - 1))
