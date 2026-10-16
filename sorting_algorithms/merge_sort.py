from .teacher import step


def merge_sort(arr, draw_func, delay, stats=None):
    if stats is None:
        stats = {'swaps': 0, 'comparisons': 0}
    def merge(left, right, start_index):
        result = []
        i = j = 0
        while i < len(left) and j < len(right):
            stats['comparisons'] += 1
            # Both halves are still untouched at this point, so the right
            # hand value really is at start_index + len(left) + j. The stage
            # used to be sent start_index + j, which pointed into the left
            # half: the second gap recorded in the lessons README.
            draw_func(arr, [start_index + i, start_index + len(left) + j], step(
                'compare',
                [start_index + i, start_index + len(left) + j],
                [left[i], right[j]],
                'merge-compare',
                {'i': i, 'j': j, 'start': start_index,
                 'left_len': len(left), 'right_len': len(right)},
                'Compare %d from the left half with %d from the right half.'
                % (left[i], right[j]),
                'Both halves are already sorted, so whichever of these two is '
                'smaller is the smallest value left anywhere in the pair.'))
            if left[i] < right[j]:
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
            draw_func(arr, [start_index + idx], step(
                'overwrite', [start_index + idx], [val], 'copy-back',
                {'idx': idx, 'start': start_index, 'merged_len': len(result)},
                'Write %d back into position %d of the array.'
                % (val, start_index + idx),
                'The merged run was built in a temporary list, so it has to be '
                'copied back over the two halves it replaces.'))
            delay()

    def sort(start, end):
        if end - start > 1:
            mid = (start + end) // 2
            sort(start, mid)
            sort(mid, end)
            merge(arr[start:mid], arr[mid:end], start)

    sort(0, len(arr))
    draw_func(arr, ['green'] * len(arr), step(
        'done', [], [], None, {'n': len(arr)},
        'Every pair of halves has been merged back together in order.',
        'Splitting stops at single values, which are sorted by definition, so '
        'every merge above them produces a sorted run.'))
