def selection_sort(arr, draw_func, delay, stats=None):
    if stats is None:
        stats = {'swaps': 0, 'comparisons': 0}
    n = len(arr)
    
    for i in range(n):
        min_idx = i
        # Show current position being filled (green)
        draw_func(arr, [i])
        delay()
        
        for j in range(i+1, n):
            stats['comparisons'] += 1
            # Show comparison: current minimum (red) and element being compared (blue)
            draw_func(arr, [min_idx, j])
            delay()
            
            if arr[min_idx] > arr[j]:
                min_idx = j
                # Show new minimum found
                draw_func(arr, [min_idx])
                delay()
        
        # Swap if needed
        if i != min_idx:
            arr[i], arr[min_idx] = arr[min_idx], arr[i]
            stats['swaps'] += 1
            # Show the swap
            draw_func(arr, [i, min_idx])
            delay()
    
    # Show final sorted array
    draw_func(arr, ['green'] * len(arr))
