def bubble_sort(arr, draw_func, delay, stats=None):
    if stats is None:
        stats = {'swaps': 0, 'comparisons': 0}
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            stats['comparisons'] += 1
            draw_func(arr, [j, j+1])
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
                stats['swaps'] += 1
                draw_func(arr, [j, j+1])
                delay()
    draw_func(arr, ['green'] * len(arr))
