"""
Selection Sort Algorithm Implementation
"""
from typing import List, Dict, Any, Callable, Optional
from ..base import SortingAlgorithm


class SelectionSort(SortingAlgorithm):
    """Selection Sort implementation with visualization support"""
    
    def get_name(self) -> str:
        return "Selection Sort"
    
    def get_description(self) -> str:
        return ("Selection Sort repeatedly finds the minimum element from the unsorted part "
                "and puts it at the beginning of the sorted part.")
    
    def get_time_complexity(self) -> Dict[str, str]:
        return {"Best": "O(n²)", "Average": "O(n²)", "Worst": "O(n²)"}
    
    def get_space_complexity(self) -> str:
        return "O(1)"
    
    def is_stable(self) -> bool:
        return False
    
    def sort(self, data: List[int], draw_callback: Callable = None) -> List[Dict[str, Any]]:
        """
        Perform selection sort with visualization steps
        
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
            min_idx = i
            
            # Record start of new iteration
            step = {
                'array': data[:],
                'compared': [i],
                'action': 'select_position',
                'message': f"Finding minimum for position {i}",
                'sorted_boundary': i
            }
            steps.append(step)
            
            if draw_callback:
                draw_callback(data, [i])
            
            # Find minimum element in remaining unsorted array
            for j in range(i + 1, n):
                self.stats['comparisons'] += 1
                
                # Record comparison step
                step = {
                    'array': data[:],
                    'compared': [min_idx, j],
                    'action': 'compare',
                    'message': f"Comparing {data[min_idx]} (current min) with {data[j]}",
                    'sorted_boundary': i,
                    'current_min': min_idx
                }
                steps.append(step)
                
                if draw_callback:
                    draw_callback(data, [min_idx, j])
                
                if data[j] < data[min_idx]:
                    min_idx = j
                    
                    # Record new minimum found
                    step = {
                        'array': data[:],
                        'compared': [min_idx],
                        'action': 'new_minimum',
                        'message': f"New minimum found: {data[min_idx]} at position {min_idx}",
                        'sorted_boundary': i,
                        'current_min': min_idx
                    }
                    steps.append(step)
                    
                    if draw_callback:
                        draw_callback(data, [min_idx])
            
            # Swap minimum element with first element of unsorted part
            if min_idx != i:
                data[i], data[min_idx] = data[min_idx], data[i]
                self.stats['swaps'] += 1
                
                # Record swap step
                step = {
                    'array': data[:],
                    'compared': [i, min_idx],
                    'action': 'swap',
                    'message': f"Swapped {data[min_idx]} and {data[i]}",
                    'sorted_boundary': i + 1
                }
                steps.append(step)
                
                if draw_callback:
                    draw_callback(data, [i, min_idx])
            else:
                # No swap needed
                step = {
                    'array': data[:],
                    'compared': [i],
                    'action': 'no_swap',
                    'message': f"Element {data[i]} already in correct position",
                    'sorted_boundary': i + 1
                }
                steps.append(step)
        
        # Final step - all elements sorted
        steps.append({
            'array': data[:],
            'compared': [],
            'action': 'complete',
            'message': 'Selection sort complete!',
            'sorted_boundary': n
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
def selection_sort(arr, draw_func, delay, stats=None):
    """Legacy wrapper function"""
    if stats is None:
        stats = {'swaps': 0, 'comparisons': 0}
    
    sorter = SelectionSort()
    steps = sorter.sort(arr, draw_func)
    
    # Update stats for legacy compatibility
    stats.update(sorter.stats)
    
    return steps
