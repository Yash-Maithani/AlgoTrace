"""
Quick Sort Algorithm Implementation
"""
from typing import List, Dict, Any, Callable, Optional
from ..base import SortingAlgorithm


class QuickSort(SortingAlgorithm):
    """Quick Sort implementation with visualization support"""
    
    def get_name(self) -> str:
        return "Quick Sort"
    
    def get_description(self) -> str:
        return ("Quick Sort picks a pivot element, partitions the array around the pivot, "
                "and recursively sorts the partitions.")
    
    def get_time_complexity(self) -> Dict[str, str]:
        return {"Best": "O(n log n)", "Average": "O(n log n)", "Worst": "O(n²)"}
    
    def get_space_complexity(self) -> str:
        return "O(log n)"
    
    def is_stable(self) -> bool:
        return False
    
    def sort(self, data: List[int], draw_callback: Callable = None) -> List[Dict[str, Any]]:
        """
        Perform quick sort with visualization steps
        
        Args:
            data: List to sort (modified in-place)
            draw_callback: Optional callback for real-time visualization
            
        Returns:
            List of visualization steps
        """
        self.steps = []
        self.stats = {'comparisons': 0, 'swaps': 0, 'steps': 0}
        self.draw_callback = draw_callback
        
        self._quick_sort_recursive(data, 0, len(data) - 1)
        
        # Final step - all elements sorted
        self.steps.append({
            'array': data[:],
            'compared': [],
            'action': 'complete',
            'message': 'Sorting complete!'
        })
        
        self.stats['steps'] = len(self.steps)
        return self.steps
    
    def _quick_sort_recursive(self, data: List[int], low: int, high: int):
        """Recursive quick sort implementation"""
        if low < high:
            # Partition and get pivot index
            pivot_index = self._partition(data, low, high)
            
            # Recursively sort elements before and after partition
            self._quick_sort_recursive(data, low, pivot_index - 1)
            self._quick_sort_recursive(data, pivot_index + 1, high)
    
    def _partition(self, data: List[int], low: int, high: int) -> int:
        """Partition function for quick sort"""
        pivot = data[high]  # Choose rightmost element as pivot
        i = low - 1  # Index of smaller element
        
        # Record pivot selection
        self.steps.append({
            'array': data[:],
            'compared': [high],
            'action': 'pivot',
            'message': f"Selected pivot: {pivot}",
            'pivot': high,
            'range': [low, high]
        })
        
        for j in range(low, high):
            self.stats['comparisons'] += 1
            
            # Record comparison with pivot
            self.steps.append({
                'array': data[:],
                'compared': [j, high],
                'action': 'compare',
                'message': f"Comparing {data[j]} with pivot {pivot}",
                'pivot': high,
                'range': [low, high]
            })
            
            if self.draw_callback:
                self.draw_callback(data, [j, high])
            
            # If current element is smaller than or equal to pivot
            if data[j] <= pivot:
                i += 1
                if i != j:  # Only swap if different positions
                    data[i], data[j] = data[j], data[i]
                    self.stats['swaps'] += 1
                    
                    # Record swap
                    self.steps.append({
                        'array': data[:],
                        'compared': [i, j],
                        'action': 'swap',
                        'message': f"Swapped {data[j]} and {data[i]}",
                        'pivot': high,
                        'range': [low, high]
                    })
                    
                    if self.draw_callback:
                        self.draw_callback(data, [i, j])
        
        # Place pivot in correct position
        data[i + 1], data[high] = data[high], data[i + 1]
        self.stats['swaps'] += 1
        
        # Record pivot placement
        self.steps.append({
            'array': data[:],
            'compared': [i + 1, high],
            'action': 'pivot_place',
            'message': f"Placed pivot {pivot} at position {i + 1}",
            'pivot': i + 1,
            'range': [low, high]
        })
        
        if self.draw_callback:
            self.draw_callback(data, [i + 1, high])
        
        return i + 1
    
    def visualize(self, data: List[int]) -> Dict[str, Any]:
        """
        Main entry point for visualization
        
        Args:
            data: List to sort
            
        Returns:
            Complete visualization data
        """
        data_copy = data[:]
        steps = self.sort(data_copy)
        
        return {
            'algorithm': self.get_name(),
            'description': self.get_description(),
            'time_complexity': self.get_time_complexity(),
            'space_complexity': self.get_space_complexity(),
            'stable': self.is_stable(),
            'steps': steps,
            'stats': self.stats,
            'sorted_array': data_copy
        }


# Legacy wrapper function for backwards compatibility
def quick_sort(arr, draw, tick, stats=None):
    """Legacy wrapper function"""
    if stats is None:
        stats = {'swaps': 0, 'comparisons': 0}
    
    sorter = QuickSort()
    steps = sorter.sort(arr, draw)
    
    # Update stats for legacy compatibility
    stats.update(sorter.stats)
    
    return steps
