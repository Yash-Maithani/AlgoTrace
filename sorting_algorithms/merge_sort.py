def merge_sort(arr, draw_func, delay, stats=None):
    if stats is None:
        stats = {'swaps': 0, 'comparisons': 0}
    def merge(left, right, start_index):
        result = []
        i = j = 0
        while i < len(left) and j < len(right):
            stats['comparisons'] += 1
            draw_func(arr, [start_index + i, start_index + j])
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
            draw_func(arr, [start_index + idx])
            delay()

    def sort(start, end):
        if end - start > 1:
            mid = (start + end) // 2
            sort(start, mid)
            sort(mid, end)
            merge(arr[start:mid], arr[mid:end], start)

    sort(0, len(arr))
    draw_func(arr, ['green'] * len(arr))
