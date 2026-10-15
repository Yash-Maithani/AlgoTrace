def insertion_sort(arr, draw_func, delay, stats=None):
    if stats is None:
        stats = {'swaps': 0, 'comparisons': 0}
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >=0:
            stats['comparisons'] += 1
            draw_func(arr, [j, i])
            if key < arr[j]:
                arr[j + 1] = arr[j]
                stats['swaps'] += 1
                j -= 1
                draw_func(arr, [j, i])
                delay()
            else:
                break
        arr[j + 1] = key
    draw_func(arr, ['green'] * len(arr))
