"""
Algorithm Services - Business logic layer
"""
from typing import List, Dict, Any, Optional
import random
from algorithms.sorting.bubble_sort import BubbleSort
from algorithms.sorting.quick_sort import QuickSort
from algorithms.sorting.selection_sort import SelectionSort


class SortingService:
    """Service class for handling sorting algorithm operations"""
    
    def __init__(self):
        self.algorithms = {
            "Bubble Sort": BubbleSort(),
            "Quick Sort": QuickSort(),
            "Selection Sort": SelectionSort(),
            # TODO: Add other sorting algorithms
        }
    
    def get_available_algorithms(self) -> List[str]:
        """Get list of available sorting algorithms"""
        return list(self.algorithms.keys())
    
    def get_algorithm_info(self, algorithm_name: str) -> Dict[str, Any]:
        """Get information about a specific algorithm"""
        if algorithm_name not in self.algorithms:
            raise ValueError(f"Algorithm '{algorithm_name}' not found")
        
        algo = self.algorithms[algorithm_name]
        return {
            'name': algo.get_name(),
            'description': algo.get_description(),
            'time_complexity': algo.get_time_complexity(),
            'space_complexity': algo.get_space_complexity(),
            'stable': algo.is_stable()
        }
    
    def generate_random_data(self, size: int, min_val: int = 1, max_val: int = 100) -> List[int]:
        """Generate random data for sorting"""
        if size < 1 or size > 1000:
            raise ValueError("Size must be between 1 and 1000")
        return [random.randint(min_val, max_val) for _ in range(size)]
    
    def parse_manual_input(self, input_string: str) -> List[int]:
        """Parse manual input string into list of integers"""
        try:
            data = [int(x.strip()) for x in input_string.split(',') if x.strip()]
            if not data:
                raise ValueError("No valid numbers found")
            if len(data) > 1000:
                raise ValueError("Too many elements (max 1000)")
            return data
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError("Invalid input. Please enter comma-separated integers only.")
            raise e
    
    def visualize_algorithm(self, algorithm_name: str, data: List[int]) -> Dict[str, Any]:
        """
        Execute algorithm and return visualization data
        
        Args:
            algorithm_name: Name of the algorithm to use
            data: Data to sort
            
        Returns:
            Dictionary containing algorithm execution results and visualization data
        """
        if algorithm_name not in self.algorithms:
            raise ValueError(f"Algorithm '{algorithm_name}' not found")
        
        if not data:
            raise ValueError("Data cannot be empty")
        
        if len(data) > 1000:
            raise ValueError("Data size too large (max 1000 elements)")
        
        algorithm = self.algorithms[algorithm_name]
        result = algorithm.visualize(data)
        
        return result


class GraphService:
    """Service class for handling graph algorithm operations"""
    
    def __init__(self):
        # TODO: Implement graph algorithms
        pass
    
    def get_available_algorithms(self) -> List[str]:
        """Get list of available graph algorithms"""
        return ["BFS", "DFS", "Dijkstra", "Kruskal", "Prim", "Floyd-Warshall"]
    
    def execute_bfs(self, graph: Dict, start: str) -> List[Dict[str, Any]]:
        """Execute Breadth-First Search"""
        if not isinstance(graph, dict) or not isinstance(start, str) or start not in graph:
            raise ValueError('Invalid graph format or start node.')

        visited = set()
        queue = [start]
        steps = [{"action": "queue", "node": start, "queue": queue[:], "visited": list(visited)}]
        traversal_path = []

        while queue:
            node = queue.pop(0)
            if node not in visited:
                visited.add(node)
                traversal_path.append(node)
                steps.append({"action": "visit", "node": node, "queue": queue[:], "visited": list(visited)})
                
                for neighbor in graph.get(node, []):
                    if neighbor not in visited and neighbor not in queue:
                        queue.append(neighbor)
                        steps.append({"action": "queue", "node": neighbor, "queue": queue[:], "visited": list(visited)})
        
        steps.append({"action": "final", "traversal_path": traversal_path})
        return steps
    
    def execute_dfs(self, graph: Dict, start: str) -> List[Dict[str, Any]]:
        """Execute Depth-First Search"""
        if not isinstance(graph, dict) or not isinstance(start, str) or start not in graph:
            raise ValueError('Invalid graph format or start node.')

        visited = set()
        stack = [start]
        steps = [{"action": "stack", "node": start, "stack": stack[:], "visited": list(visited)}]
        traversal_path = []

        while stack:
            node = stack.pop()
            if node not in visited:
                visited.add(node)
                traversal_path.append(node)
                steps.append({"action": "visit", "node": node, "stack": stack[:], "visited": list(visited)})
                
                for neighbor in reversed(graph.get(node, [])):
                    if neighbor not in visited and neighbor not in stack:
                        stack.append(neighbor)
                        steps.append({"action": "stack", "node": neighbor, "stack": stack[:], "visited": list(visited)})
        
        steps.append({"action": "final", "traversal_path": traversal_path})
        return steps
    
    def execute_dijkstra(self, graph: Dict, start: str) -> List[Dict[str, Any]]:
        """Execute Dijkstra's shortest path algorithm"""
        if not isinstance(graph, dict) or not isinstance(start, str) or start not in graph:
            raise ValueError('Invalid graph format or start node.')

        distances = {node: float('infinity') for node in graph}
        distances[start] = 0
        previous = {node: None for node in graph}
        unvisited = set(graph.keys())
        steps = []

        while unvisited:
            current = min(unvisited, key=lambda node: distances[node])
            if distances[current] == float('infinity'):
                break
            unvisited.remove(current)
            steps.append({"action": "visit", "node": current, "distance": distances[current]})
            
            for neighbor, weight in graph[current].items():
                if neighbor in unvisited:
                    new_distance = distances[current] + weight
                    if new_distance < distances[neighbor]:
                        distances[neighbor] = new_distance
                        previous[neighbor] = current
                        steps.append({
                            "action": "update", 
                            "node": neighbor, 
                            "distance": new_distance, 
                            "previous": current
                        })
        
        # Build paths
        paths = {}
        for node in graph:
            if node == start or distances[node] == float('infinity'):
                continue
            path = []
            curr = node
            while curr is not None:
                path.append(curr)
                curr = previous[curr]
            path = path[::-1]
            if path and path[0] == start:
                paths[node] = path
        
        steps.append({"action": "final", "distances": distances, "paths": paths})
        return steps
