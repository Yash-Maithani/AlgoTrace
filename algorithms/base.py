"""
Base classes for algorithm visualization
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable, Optional


class AlgorithmBase(ABC):
    """Base class for all algorithms"""
    
    def __init__(self):
        self.stats = {'comparisons': 0, 'swaps': 0, 'steps': 0}
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the name of the algorithm"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Return description of the algorithm"""
        pass
    
    @abstractmethod
    def get_time_complexity(self) -> Dict[str, str]:
        """Return time complexity information"""
        pass
    
    @abstractmethod
    def get_space_complexity(self) -> str:
        """Return space complexity information"""
        pass


class SortingAlgorithm(AlgorithmBase):
    """Base class for sorting algorithms"""
    
    @abstractmethod
    def sort(self, data: List[int], draw_callback: Callable = None) -> List[Dict[str, Any]]:
        """
        Sort the data and return visualization steps
        
        Args:
            data: List of integers to sort
            draw_callback: Optional callback function for visualization
            
        Returns:
            List of steps for visualization
        """
        pass
    
    @abstractmethod
    def is_stable(self) -> bool:
        """Return whether the algorithm is stable"""
        pass


class GraphAlgorithm(AlgorithmBase):
    """Base class for graph algorithms"""
    
    @abstractmethod
    def execute(self, graph: Dict, **kwargs) -> List[Dict[str, Any]]:
        """
        Execute the graph algorithm
        
        Args:
            graph: Graph representation
            **kwargs: Algorithm-specific parameters
            
        Returns:
            List of steps for visualization
        """
        pass
