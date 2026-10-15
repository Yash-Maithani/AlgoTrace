"""
Graph Algorithm Routes
"""
from flask import Blueprint, render_template, request, jsonify
from services.algorithm_service import GraphService

graph_bp = Blueprint('graph', __name__, url_prefix='/graph')
graph_service = GraphService()


@graph_bp.route('/')
def graph_page():
    """Main graph algorithms page"""
    algo = request.args.get('algo', 'bfs').lower()
    
    available_algos = {
        'bfs': 'bfs',
        'dfs': 'dfs', 
        'dijkstra': 'dijkstra',
        'kruskal': 'kruskal',
        'floyd_warshall': 'floyd_warshall',
        'prim': 'prim'
    }
    
    if algo not in available_algos:
        algo = 'bfs'
    
    template_name = available_algos[algo]
    return render_template(f"{template_name}.html", algorithm=algo)


@graph_bp.route('/api/bfs', methods=['POST'])
def api_bfs():
    """API endpoint for BFS"""
    try:
        data = request.get_json()
        if not data or 'graph' not in data or 'start' not in data:
            return jsonify({'error': 'Missing graph or start node in request.'}), 400

        graph = data["graph"]
        start = data["start"]
        
        steps = graph_service.execute_bfs(graph, start)
        return jsonify(steps)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@graph_bp.route('/api/dfs', methods=['POST'])
def api_dfs():
    """API endpoint for DFS"""
    try:
        data = request.get_json()
        if not data or 'graph' not in data or 'start' not in data:
            return jsonify({'error': 'Missing graph or start node in request.'}), 400

        graph = data["graph"]
        start = data["start"]
        
        steps = graph_service.execute_dfs(graph, start)
        return jsonify(steps)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@graph_bp.route('/api/dijkstra', methods=['POST'])
def api_dijkstra():
    """API endpoint for Dijkstra's algorithm"""
    try:
        data = request.get_json()
        if not data or 'graph' not in data or 'start' not in data:
            return jsonify({'error': 'Missing graph or start node in request.'}), 400

        graph = data["graph"]
        start = data["start"]
        
        steps = graph_service.execute_dijkstra(graph, start)
        return jsonify(steps)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


# Legacy routes for backwards compatibility
@graph_bp.route('/run_bfs', methods=['POST'])
def run_bfs():
    """Legacy BFS route"""
    return api_bfs()


@graph_bp.route('/run_dfs', methods=['POST'])
def run_dfs():
    """Legacy DFS route"""
    return api_dfs()


@graph_bp.route('/run_dijkstra', methods=['POST'])
def run_dijkstra():
    """Legacy Dijkstra route"""
    return api_dijkstra()
