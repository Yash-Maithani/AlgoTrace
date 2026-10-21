"""Graphs: the /graph workspace and the eight /run_* graph endpoints.

Each endpoint checks its input here and hands it to its algorithm in
algorithms/graph/. A refusal is a 400 that says what is wrong; anything else
that fails is a 500 that says what happened.
"""
from flask import abort, jsonify, render_template, request

from ..algorithms.graph.bellman_ford import bellman_ford
from ..algorithms.graph.bfs import bfs
from ..algorithms.graph.dfs import dfs
from ..algorithms.graph.dijkstra import dijkstra
from ..algorithms.graph.floyd_warshall import floyd_warshall
from ..algorithms.graph.kruskal import kruskal
from ..algorithms.graph.prim import prim
from ..algorithms.graph.random_graph import random_connected_graph
from ..algorithms.graph.topological_sort import topological_sort
from ..catalog import GRAPH_PICKER, graph_algo_dict
from . import SiteBlueprint
from .grid import GRID_COLS, GRID_ROWS

bp = SiteBlueprint("graphs", __name__)


@bp.app_context_processor
def _graph_picker():
    return {"graph_algos": GRAPH_PICKER}


@bp.route("/graph")
def graph_page():
    """The graph workspace. ?algo= picks which algorithm.

    An unknown name is a 404 rather than a quiet fall back to BFS, which
    served the wrong algorithm under the name that was asked for.
    """
    algo = request.args.get("algo", "bfs").lower()
    if algo not in graph_algo_dict:
        abort(404)

    return render_template("%s.html" % graph_algo_dict[algo], algorithm=algo,
                           grid_rows=GRID_ROWS, grid_cols=GRID_COLS)


def handle_graph():
    selected_algo = request.form.get("algorithm", "bfs").lower()
    if selected_algo not in graph_algo_dict:
        # fallback to the first available graph algorithm
        selected_algo = "bfs"

    # Return the algo key so the right class is highlighted in the template
    return render_template(f"{graph_algo_dict[selected_algo]}.html", algorithm=selected_algo)


def _missing_node_response(graph):
    """A 400 naming the edge that points at a node with no line of its own.

    The graph endpoints index graph[node] for every neighbour they reach, so a
    neighbour that is not a key raised KeyError and came back as a bare 500.
    This runs only after that failure, so a valid graph pays nothing for it.
    Returns None when the KeyError was something else.
    """
    if not isinstance(graph, dict):
        return None
    for u, neighbours in graph.items():
        if not isinstance(neighbours, (dict, list)):
            continue
        for v in neighbours:
            if v not in graph:
                return jsonify({'error': "Node %s lists %s as a neighbour, but "
                                "%s has no node of its own. Add %s to the "
                                "graph or remove the edge." % (u, v, v, v)}), 400
    return None


def _check_weight(weight, u, v):
    # bool is a subclass of int, so reject it explicitly rather than sorting by True.
    if isinstance(weight, bool) or not isinstance(weight, (int, float)):
        return f"Invalid weight {weight!r} on edge {u}-{v}; expected a number."
    return None


def _run_from_start(algorithm):
    """The body of /run_bfs, /run_dfs, /run_dijkstra and /run_prim: a graph
    and a start node in, the algorithm's steps out."""
    try:
        data = request.json
        if not data or 'graph' not in data or 'start' not in data:
            return jsonify({'error': 'Missing graph or start node in request.'}), 400

        graph = data["graph"]
        start = data["start"]

        if not isinstance(graph, dict) or not isinstance(start, str) or start not in graph:
            return jsonify({'error': 'Invalid graph format or start node.'}), 400

        return jsonify(algorithm(graph, start))
    except KeyError as e:
        refusal = _missing_node_response((request.json or {}).get("graph"))
        if refusal:
            return refusal
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@bp.route("/run_bfs", methods=["POST"])
def run_bfs():
    return _run_from_start(bfs)


@bp.route("/run_dfs", methods=["POST"])
def run_dfs():
    return _run_from_start(dfs)


@bp.route("/run_dijkstra", methods=["POST"])
def run_dijkstra():
    return _run_from_start(dijkstra)


@bp.route("/run_prim", methods=["POST"])
def run_prim():
    return _run_from_start(prim)


@bp.route("/run_kruskal", methods=["POST"])
def run_kruskal():
    try:
        data = request.json
        if not data or "nodes" not in data or "edges" not in data:
            return jsonify({"error": "Missing nodes or edges in request."}), 400

        nodes, edges = data["nodes"], data["edges"]
        if not isinstance(nodes, list) or not isinstance(edges, list):
            return jsonify({"error": "nodes and edges must both be lists."}), 400

        # A set, so checking an edge's ends costs one look-up each rather
        # than a scan of the node list. As a list scan this check alone made
        # the endpoint O(V times E) before Kruskal itself had started.
        try:
            known = set(nodes)
        except TypeError:
            return jsonify({"error": "Node names must be text or numbers."}), 400

        clean_edges = []
        for edge in edges:
            if not isinstance(edge, (list, tuple)) or len(edge) != 3:
                return jsonify({"error": f"Invalid edge {edge!r}; expected [u, v, weight]."}), 400
            u, v, weight = edge
            problem = _check_weight(weight, u, v)
            if problem:
                return jsonify({"error": problem}), 400
            if (isinstance(u, (list, dict)) or isinstance(v, (list, dict))
                    or u not in known or v not in known):
                return jsonify({"error": f"Edge {u}-{v} references a node outside the node list."}), 400
            clean_edges.append((u, v, weight))

        return jsonify(kruskal(nodes, clean_edges))
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@bp.route("/run_floyd_warshall", methods=["POST"])
def run_floyd_warshall():
    try:
        data = request.json
        if not data or "nodes" not in data or "edges" not in data:
            return jsonify({"error": "Missing nodes or edges in request."}), 400

        nodes, edges = data["nodes"], data["edges"]
        if not isinstance(nodes, list) or not isinstance(edges, list):
            return jsonify({"error": "nodes and edges must both be lists."}), 400
        if not nodes:
            return jsonify({"error": "At least one node is required."}), 400

        known = set(nodes)
        for edge in edges:
            if not isinstance(edge, (list, tuple)) or len(edge) != 3:
                return jsonify({"error": f"Invalid edge {edge!r}; expected [u, v, weight]."}), 400
            u, v, weight = edge
            problem = _check_weight(weight, u, v)
            if problem:
                return jsonify({"error": problem}), 400
            if u not in known or v not in known:
                return jsonify({"error": f"Edge {u}-{v} references a node outside the node list."}), 400

        return jsonify(floyd_warshall(nodes, edges))
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@bp.route("/run_bellman_ford", methods=["POST"])
def run_bellman_ford():
    try:
        data = request.json
        if not data or "graph" not in data or "start" not in data:
            return jsonify({"error": "Missing graph or start node in request."}), 400

        graph, start = data["graph"], data["start"]
        if not isinstance(graph, dict) or not isinstance(start, str):
            return jsonify({"error": "Invalid graph format or start node."}), 400
        if start not in graph:
            return jsonify({"error": f"Start node {start!r} is not in the graph."}), 400

        for u, neighbours in graph.items():
            if not isinstance(neighbours, dict):
                return jsonify({"error": f"Node {u!r} must map to a neighbour-to-weight object."}), 400
            for v, weight in neighbours.items():
                problem = _check_weight(weight, u, v)
                if problem:
                    return jsonify({"error": problem}), 400

        return jsonify(bellman_ford(graph, start))
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@bp.route("/run_topological_sort", methods=["POST"])
def run_topological_sort():
    try:
        data = request.json
        if not data or 'graph' not in data:
            return jsonify({'error': 'Missing graph in request.'}), 400
        graph = data["graph"]
        if (not isinstance(graph, dict) or not graph
                or not all(isinstance(s, list) for s in graph.values())):
            return jsonify({'error': 'The graph must map every node to the list of '
                                     'nodes its arrows point to.'}), 400
        for u, successors in graph.items():
            for v in successors:
                if v not in graph:
                    return jsonify({'error': "%s has an arrow to %s, but %s has no "
                                    "node of its own. Add %s to the graph or remove "
                                    "the arrow." % (u, v, v, v)}), 400

        return jsonify(topological_sort(graph))
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@bp.route("/generate_random_graph", methods=["POST"])
def generate_random_graph():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided.'}), 400

        num_nodes = data.get('nodes', 5)
        num_edges = data.get('edges', 7)

        # Validate input
        if not isinstance(num_nodes, int) or num_nodes < 2 or num_nodes > 26:
            return jsonify({'error': 'Number of nodes must be between 2 and 26.'}), 400

        min_edges = num_nodes - 1
        max_edges = (num_nodes * (num_nodes - 1)) // 2

        if not isinstance(num_edges, int) or num_edges < min_edges or num_edges > max_edges:
            return jsonify({'error': f'Number of edges must be between {min_edges} and {max_edges}.'}), 400

        nodes, edges = random_connected_graph(num_nodes, num_edges)
        return jsonify({
            'nodes': nodes,
            'edges': edges,
            'message': f'Generated connected graph with {num_nodes} nodes and {num_edges} edges.'
        })

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
