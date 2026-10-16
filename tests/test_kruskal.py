"""
Test suite for Kruskal's algorithm implementation
"""
import pytest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


class TestKruskalVisualization:
    """Test cases for Kruskal's algorithm visualization"""
    
    @pytest.fixture
    def client(self):
        """Create a test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_kruskal_basic_graph(self, client):
        """Test Kruskal's algorithm with a basic graph"""
        # Test data: simple triangle graph
        test_data = {
            "nodes": ["A", "B", "C"],
            "edges": [
                ["A", "B", 2],
                ["B", "C", 1],
                ["A", "C", 3]
            ]
        }
        
        response = client.post('/run_kruskal', 
                             json=test_data,
                             content_type='application/json')
        
        assert response.status_code == 200
        # Phase 4b: the endpoint answers with {steps, meta} rather than a
        # bare array. The steps themselves are unchanged.
        data = response.get_json()["steps"]
        
        # Should have steps for each edge addition plus final step
        assert len(data) > 0
        
        # Count the MST edges (should be 2 for 3 nodes)
        mst_edges = [step for step in data if step[0] == 'add_edge']
        assert len(mst_edges) == 2
        
        # Verify the final step
        final_step = data[-1]
        assert final_step[0] == 'final'
        assert len(final_step[1]) == 2  # 2 edges in MST
        assert final_step[2] == 3  # Total weight should be 3 (edges 1+2)
    
    def test_kruskal_disconnected_graph(self, client):
        """Test Kruskal's algorithm with disconnected components"""
        test_data = {
            "nodes": ["A", "B", "C", "D"],
            "edges": [
                ["A", "B", 1],
                ["C", "D", 1]
            ]
        }
        
        response = client.post('/run_kruskal', 
                             json=test_data,
                             content_type='application/json')
        
        assert response.status_code == 200
        # Phase 4b: the endpoint answers with {steps, meta} rather than a
        # bare array. The steps themselves are unchanged.
        data = response.get_json()["steps"]
        
        # Should have 2 MST edges (one per component)
        mst_edges = [step for step in data if step[0] == 'add_edge']
        assert len(mst_edges) == 2
    
    def test_kruskal_single_node(self, client):
        """Test Kruskal's algorithm with single node"""
        test_data = {
            "nodes": ["A"],
            "edges": []
        }
        
        response = client.post('/run_kruskal', 
                             json=test_data,
                             content_type='application/json')
        
        assert response.status_code == 200
        # Phase 4b: the endpoint answers with {steps, meta} rather than a
        # bare array. The steps themselves are unchanged.
        data = response.get_json()["steps"]
        
        # Should have only final step with empty MST
        final_step = data[-1]
        assert final_step[0] == 'final'
        assert len(final_step[1]) == 0  # No edges in MST
        assert final_step[2] == 0  # Total weight should be 0
    
    def test_kruskal_invalid_input(self, client):
        """Test Kruskal's algorithm with invalid input"""
        # Missing nodes
        response = client.post('/run_kruskal', 
                             json={"edges": []},
                             content_type='application/json')
        assert response.status_code == 400
        
        # Invalid edge format
        response = client.post('/run_kruskal', 
                             json={
                                 "nodes": ["A", "B"],
                                 "edges": [["A", "B"]]  # Missing weight
                             },
                             content_type='application/json')
        assert response.status_code == 400
    
    def test_kruskal_large_graph(self, client):
        """Test Kruskal's algorithm with a larger graph"""
        # Create a larger test graph
        nodes = [chr(65 + i) for i in range(10)]  # A-J
        edges = []
        
        # Create a connected graph
        for i in range(len(nodes) - 1):
            edges.append([nodes[i], nodes[i + 1], i + 1])
        
        # Add some extra edges
        edges.append([nodes[0], nodes[5], 10])
        edges.append([nodes[2], nodes[7], 15])
        
        test_data = {
            "nodes": nodes,
            "edges": edges
        }
        
        response = client.post('/run_kruskal', 
                             json=test_data,
                             content_type='application/json')
        
        assert response.status_code == 200
        # Phase 4b: the endpoint answers with {steps, meta} rather than a
        # bare array. The steps themselves are unchanged.
        data = response.get_json()["steps"]
        
        # Should have 9 MST edges for 10 nodes
        mst_edges = [step for step in data if step[0] == 'add_edge']
        assert len(mst_edges) == 9


if __name__ == '__main__':
    pytest.main([__file__])
