'''def quick_sort(arr, draw_func, delay):
    def partition(low, high):
        pivot = arr[high]
        i = low - 1
        for j in range(low, high):
            if arr[j] <= pivot:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
            draw_func(arr, ['red' if x == j or x == i else 'blue' for x in range(len(arr))])
            delay()
        arr[i + 1], arr[high] = arr[high], arr[i + 1]
        return i + 1

    def sort(low, high):
        if low < high:
            pi = partition(low, high)
            sort(low, pi - 1)
            sort(pi + 1, high)

    sort(0, len(arr))
    draw_func(arr, ['green'] * len(arr))'''

def quick_sort(arr, draw, tick, stats=None):
    if stats is None:
        stats = {'swaps': 0, 'comparisons': 0}
    def partition(low, high):
        pivot = arr[high]
        i = low - 1
        for j in range(low, high):
            stats['comparisons'] += 1
            draw(arr, [j, high])
            if arr[j] < pivot:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
                stats['swaps'] += 1
                draw(arr, [i, j])
                tick()
        arr[i + 1], arr[high] = arr[high], arr[i + 1]
        stats['swaps'] += 1
        draw(arr, [i + 1, high])
        tick()
        return i + 1

    def sort(low, high):
        if low < high:
            pi = partition(low, high)
            sort(low, pi - 1)
            sort(pi + 1, high)

    sort(0, len(arr) - 1)
    draw(arr, ['green'] * len(arr))

