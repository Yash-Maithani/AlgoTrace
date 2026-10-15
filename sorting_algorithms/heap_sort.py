def heapify(arr, n, i, draw_func, delay, stats=None):
    if stats is None:
        stats = {'swaps': 0, 'comparisons': 0}
    largest = i
    l = 2 * i + 1
    r = 2 * i + 2
    if l < n:
        stats['comparisons'] += 1
        draw_func(arr, [l, largest])
        if arr[l] > arr[largest]:
            largest = l
    if r < n:
        stats['comparisons'] += 1
        draw_func(arr, [r, largest])
        if arr[r] > arr[largest]:
            largest = r
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        stats['swaps'] += 1
        draw_func(arr, [i, largest])
        delay()
        heapify(arr, n, largest, draw_func, delay, stats)

def heap_sort(arr, draw_func, delay, stats=None):
    if stats is None:
        stats = {'swaps': 0, 'comparisons': 0}
    n = len(arr)
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i, draw_func, delay, stats)
    for i in range(n-1, 0, -1):
        arr[i], arr[0] = arr[0], arr[i]
        stats['swaps'] += 1
        draw_func(arr, ['red' if x == i or x == 0 else 'blue' for x in range(len(arr))])
        delay()
        heapify(arr, i, 0, draw_func, delay, stats)
    draw_func(arr, ['green'] * len(arr))
