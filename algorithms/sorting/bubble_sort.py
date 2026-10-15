"""
Bubble Sort Algorithm Implementation
"""
from typing import List, Dict, Any, Callable, Optional
from ..base import SortingAlgorithm


class BubbleSort(SortingAlgorithm):
    """Bubble Sort implementation with visualization support"""
    
    def get_name(self) -> str:
        return "Bubble Sort"
    
    def get_description(self) -> str:
        return ("Bubble Sort repeatedly steps through the list, compares adjacent elements "
                "and swaps them if they are in the wrong order. The process is repeated until the list is sorted.")
    
    def get_time_complexity(self) -> Dict[str, str]:
        return {"Best": "O(n)", "Average": "O(n²)", "Worst": "O(n²)"}
    
    def get_space_complexity(self) -> str:
        return "O(1)"
    
    def is_stable(self) -> bool:
        return True
    
    def sort(self, data: List[int], draw_callback: Callable = None) -> List[Dict[str, Any]]:
        """
        Perform bubble sort with visualization steps
        
        Args:
            data: List to sort (modified in-place)
            draw_callback: Optional callback for real-time visualization
            
        Returns:
            List of visualization steps
        """
        steps = []
        self.stats = {'comparisons': 0, 'swaps': 0, 'steps': 0}
        n = len(data)
        
        for i in range(n):
            swapped = False
            for j in range(0, n - i - 1):
                self.stats['comparisons'] += 1
                
                # Record comparison step
                step = {
                    'array': data[:],
                    'compared': [j, j + 1],
                    'action': 'compare',
                    'message': f"Comparing {data[j]} and {data[j + 1]}"
                }
                steps.append(step)
                
                if draw_callback:
                    draw_callback(data, [j, j + 1])
                
                if data[j] > data[j + 1]:
                    # Swap elements
                    data[j], data[j + 1] = data[j + 1], data[j]
                    self.stats['swaps'] += 1
                    swapped = True
                    
                    # Record swap step
                    step = {
                        'array': data[:],
                        'compared': [j, j + 1],
                        'action': 'swap',
                        'message': f"Swapped {data[j + 1]} and {data[j]}"
                    }
                    steps.append(step)
                    
                    if draw_callback:
                        draw_callback(data, [j, j + 1])
            
            # If no swapping occurred, array is sorted
            if not swapped:
                break
        
        # Final step - all elements sorted
        steps.append({
            'array': data[:],
            'compared': [],
            'action': 'complete',
            'message': 'Sorting complete!'
        })
        
        self.stats['steps'] = len(steps)
        return steps
    
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
def bubble_sort(arr, draw_func, delay, stats=None):
    """Legacy wrapper function"""
    if stats is None:
        stats = {'swaps': 0, 'comparisons': 0}
    
    sorter = BubbleSort()
    steps = sorter.sort(arr, draw_func)
    
    # Update stats for legacy compatibility
    stats.update(sorter.stats)
    
    return steps
