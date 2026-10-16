from flask import Flask, render_template, request, jsonify, redirect, url_for
import random

# Import sorting algorithm modules
from sorting_algorithms.bubble_sort import bubble_sort
from sorting_algorithms.selection_sort import selection_sort
from sorting_algorithms.insertion_sort import insertion_sort
from sorting_algorithms.heap_sort import heap_sort
from sorting_algorithms.merge_sort import merge_sort
from sorting_algorithms.quick_sort import quick_sort

app = Flask(__name__)

# Dictionary of sorting algorithms
sorting_algo_dict = {
    "Bubble Sort": bubble_sort,
    "Selection Sort": selection_sort,
    "Insertion Sort": insertion_sort,
    "Heap Sort": heap_sort,
    "Merge Sort": merge_sort,
    "Quick Sort": quick_sort
}

# Dictionary of graph algorithms
graph_algo_dict = {
    "bfs": "bfs",
    "dfs": "dfs",
    "dijkstra": "dijkstra",
    "prim": "prim",
    "kruskal": "kruskal",
    "floyd_warshall": "floyd_warshall",
    "bellman_ford": "bellman_ford"
}

# Add this dictionary after sorting_algo_dict and graph_algo_dict
sorting_algo_details = {
    "Bubble Sort": {
        "description": "Bubble Sort repeatedly steps through the list, compares adjacent elements and swaps them if they are in the wrong order. The process is repeated until the list is sorted.",
        "time_complexity": {"Best": "O(n)", "Average/Worst": "O(n^2)"},
        "space_complexity": "O(1)",
        "stable": True
    },
    "Selection Sort": {
        "description": "Selection Sort repeatedly finds the minimum element from the unsorted part and puts it at the beginning.",
        "time_complexity": {"Best": "O(n^2)", "Average/Worst": "O(n^2)"},
        "space_complexity": "O(1)",
        "stable": False
    },
    "Insertion Sort": {
        "description": "Insertion Sort builds the sorted array one item at a time by repeatedly picking the next item and inserting it into its correct position.",
        "time_complexity": {"Best": "O(n)", "Average/Worst": "O(n^2)"},
        "space_complexity": "O(1)",
        "stable": True
    },
    "Heap Sort": {
        "description": "Heap Sort builds a heap from the input data and repeatedly extracts the maximum element from the heap and rebuilds the heap.",
        "time_complexity": {"Best": "O(n log n)", "Average/Worst": "O(n log n)"},
        "space_complexity": "O(1)",
        "stable": False
    },
    "Merge Sort": {
        "description": "Merge Sort divides the array into halves, sorts them recursively, and then merges the sorted halves.",
        "time_complexity": {"Best": "O(n log n)", "Average/Worst": "O(n log n)"},
        "space_complexity": "O(n)",
        "stable": True
    },
    "Quick Sort": {
        "description": "Quick Sort picks a pivot element, partitions the array around the pivot, and recursively sorts the partitions.",
        "time_complexity": {"Best": "O(n log n)", "Average/Worst": "O(n^2)"},
        "space_complexity": "O(log n)",
        "stable": False
    }
}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        algo_type = request.form.get("algo_type", "sorting")
        if algo_type == "sorting":
            return handle_sorting()
        else:
            return handle_graph()
    # Always provide default values for all variables used in the template
    return render_template(
        "landing.html"
    )

@app.route("/sorting", methods=["GET", "POST"])
def sorting_page():
    if request.method == "POST":
        # Handle form submission - call the handle_sorting function
        return handle_sorting()
    else:
        # GET request - just display the form
        # Get algorithm from query parameter, default to Bubble Sort
        selected_algo = request.args.get('algorithm', 'Bubble Sort')
        if selected_algo not in sorting_algo_dict:
            selected_algo = "Bubble Sort"
        
        return render_template(
            "sorting.html",
            sorting_algorithms=sorting_algo_dict.keys(),
            selected_algo=selected_algo,
            data=[],
            steps=[],
            input_method="random",
            manual_input="",
            size=30,
            error="",
            info=None
        )

@app.route("/privacy")
def privacy():
    """Privacy policy, rendered inside the shared layout."""
    return render_template("privacy.html")


@app.route("/terms")
def terms():
    """Terms and conditions, rendered inside the shared layout."""
    return render_template("terms.html")


@app.route("/graph")
def graph_page():
    # Get algorithm from query parameter, default to BFS
    algo = request.args.get('algo', 'bfs')
    # Convert to lowercase for consistent key lookup
    algo = algo.lower()
    
    # Check if the algo exists in our dictionary
    if algo not in graph_algo_dict:
        # Default to BFS if not found
        algo = 'bfs'
    
    # Get the template name from the algorithm
    template_name = graph_algo_dict[algo]
    
    # For debugging
    print(f"Request for graph algorithm: {algo}, template: {template_name}")
    
    return render_template(f"{template_name}.html", algorithm=algo)

def handle_sorting():
    data = []
    steps = []
    selected_algo = request.form.get("algorithm", "Bubble Sort")
    input_method = request.form.get("input_method", "random")
    size = 30
    manual_input = ""
    error = ""

    if input_method == "random":
        try:
            size = int(request.form.get("size", 30))
            data = [random.randint(1, 100) for _ in range(size)]
        except ValueError:
            error = "Invalid array size. Please enter a valid number."
    elif input_method == "manual":
        manual_input = request.form.get("manual_input", "")
        try:
            data = [int(x.strip()) for x in manual_input.split(',') if x.strip() != '']
            if not data:
                raise ValueError
        except ValueError:
            error = "Invalid manual input. Please enter comma-separated integers only."
            return render_template(
                "sorting.html",
                sorting_algorithms=sorting_algo_dict.keys(),
                selected_algo=selected_algo,
                data=[],
                steps=[],
                input_method=input_method,
                manual_input=manual_input,
                size=size,
                error=error,
                info=None
            )

    info = None
    if not error:
        def draw(array_state, compared_indices=None):
            steps.append({'array': array_state[:], 'compared': compared_indices[:] if compared_indices else []})

        sort_func = sorting_algo_dict[selected_algo]
        stats = {'swaps': 0, 'comparisons': 0}
        # Pass stats to the sorting function
        sort_func(data, draw, lambda: None, stats)
        algo_info = sorting_algo_details[selected_algo]
        info = {
            'swaps': stats['swaps'],
            'comparisons': stats['comparisons'],
            'stable': 'Yes' if algo_info['stable'] else 'No',
            'time_complexity': algo_info['time_complexity'],
            'space_complexity': algo_info['space_complexity'],
            'description': algo_info['description']
        }

    return render_template(
        "sorting.html",
        sorting_algorithms=sorting_algo_dict.keys(),
        selected_algo=selected_algo,
        data=data,
        steps=steps,
        input_method=input_method,
        manual_input=manual_input,
        size=size,
        error=error,
        info=info
    )

def handle_graph():
    selected_algo = request.form.get("algorithm", "bfs").lower()
    if selected_algo not in graph_algo_dict:
        # fallback to the first available graph algorithm
        selected_algo = "bfs"
    
    # Return the algo key so the right class is highlighted in the template
    return render_template(f"{graph_algo_dict[selected_algo]}.html", algorithm=selected_algo)

@app.route("/run_bfs", methods=["POST"])
def run_bfs():
    try:
        data = request.json
        if not data or 'graph' not in data or 'start' not in data:
            return jsonify({'error': 'Missing graph or start node in request.'}), 400

        graph = data["graph"]
        start = data["start"]

        if not isinstance(graph, dict) or not isinstance(start, str) or start not in graph:
            return jsonify({'error': 'Invalid graph format or start node.'}), 400

        visited = set()
        queue = [start]
        steps = [["queue", start]]
        traversal_path = []  # Track the order of visited nodes

        while queue:
            node = queue.pop(0)
            if node not in visited:
                visited.add(node)
                traversal_path.append(node)
                steps.append(["visit", node])
                for neighbor in graph.get(node, []):
                    if neighbor not in visited and neighbor not in queue:
                        queue.append(neighbor)
                        steps.append(["queue", neighbor])
        
        # Add final result step
        steps.append(["final", traversal_path])
        return jsonify(steps)
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route("/run_dfs", methods=["POST"])
def run_dfs():
    try:
        data = request.json
        if not data or 'graph' not in data or 'start' not in data:
            return jsonify({'error': 'Missing graph or start node in request.'}), 400

        graph = data["graph"]
        start = data["start"]

        if not isinstance(graph, dict) or not isinstance(start, str) or start not in graph:
            return jsonify({'error': 'Invalid graph format or start node.'}), 400

        visited = set()
        stack = [start]
        steps = [["stack", start]]
        traversal_path = []  # Track the order of visited nodes

        while stack:
            node = stack.pop()
            if node not in visited:
                visited.add(node)
                traversal_path.append(node)
                steps.append(["visit", node])
                for neighbor in reversed(graph.get(node, [])):
                    if neighbor not in visited and neighbor not in stack:
                        stack.append(neighbor)
                        steps.append(["stack", neighbor])
        
        # Add final result step
        steps.append(["final", traversal_path])
        return jsonify(steps)
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route("/run_dijkstra", methods=["POST"])
def run_dijkstra():
    try:
        data = request.json
        if not data or 'graph' not in data or 'start' not in data:
            return jsonify({'error': 'Missing graph or start node in request.'}), 400

        graph = data["graph"]
        start = data["start"]

        if not isinstance(graph, dict) or not isinstance(start, str) or start not in graph:
            return jsonify({'error': 'Invalid graph format or start node.'}), 400

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
            steps.append(["visit", current])
            for neighbor, weight in graph[current].items():
                if neighbor in unvisited:
                    new_distance = distances[current] + weight
                    if new_distance < distances[neighbor]:
                        distances[neighbor] = new_distance
                        previous[neighbor] = current
                        steps.append(["update", neighbor, new_distance, current])
        # Add final answer: shortest paths from start to all nodes
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
        steps.append(["final", distances, paths])
        return jsonify(steps)
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route("/run_prim", methods=["POST"])
def run_prim():
    try:
        data = request.json
        if not data or 'graph' not in data or 'start' not in data:
            return jsonify({'error': 'Missing graph or start node in request.'}), 400

        graph = data["graph"]
        start = data["start"]

        if not isinstance(graph, dict) or not isinstance(start, str) or start not in graph:
            return jsonify({'error': 'Invalid graph format or start node.'}), 400

        import heapq

        visited = set()
        mst_edges = []
        steps = []
        min_heap = []

        # Start with the starting node
        visited.add(start)
        steps.append(["start", start])
        
        # Add all edges from start node to the priority queue
        frontier_nodes = []
        for neighbor, weight in graph[start].items():
            heapq.heappush(min_heap, (weight, start, neighbor))
            if neighbor not in visited:
                frontier_nodes.append(neighbor)
        
        if frontier_nodes:
            steps.append(["add_frontier", frontier_nodes])

        while min_heap:
            weight, u, v = heapq.heappop(min_heap)
            
            if v in visited:
                # This edge connects to an already visited node, ignore it
                steps.append(["ignore_edge", u, v, weight])
                continue
            
            # Consider this edge
            steps.append(["consider_edge", u, v, weight])
            
            # Add edge to MST
            mst_edges.append((u, v, weight))
            visited.add(v)
            steps.append(["add_edge", u, v, weight])
            
            # Add all edges from the newly visited node to unvisited nodes
            new_frontier = []
            for neighbor, w in graph[v].items():
                if neighbor not in visited:
                    heapq.heappush(min_heap, (w, v, neighbor))
                    new_frontier.append(neighbor)
            
            if new_frontier:
                steps.append(["add_frontier", new_frontier])
        
        # Add final result
        total_weight = sum(e[2] for e in mst_edges)
        steps.append(["final", mst_edges, total_weight])
        
        return jsonify(steps)
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

# JSON has no literal for infinity: json.dumps(float("inf")) emits a bare Infinity
# token, which JSON.parse rejects. The graph templates already compare rendered
# distances against the string "∞", so unreachable values travel as that label.
INF_LABEL = "∞"


def _wire(value):
    # Translate an internal float("inf") into the wire form the templates expect.
    return INF_LABEL if value == float("inf") else value


def _check_weight(weight, u, v):
    # bool is a subclass of int, so reject it explicitly rather than sorting by True.
    if isinstance(weight, bool) or not isinstance(weight, (int, float)):
        return f"Invalid weight {weight!r} on edge {u}-{v}; expected a number."
    return None


@app.route("/run_kruskal", methods=["POST"])
def run_kruskal():
    try:
        data = request.json
        if not data or "nodes" not in data or "edges" not in data:
            return jsonify({"error": "Missing nodes or edges in request."}), 400

        nodes, edges = data["nodes"], data["edges"]
        if not isinstance(nodes, list) or not isinstance(edges, list):
            return jsonify({"error": "nodes and edges must both be lists."}), 400

        clean_edges = []
        for edge in edges:
            if not isinstance(edge, (list, tuple)) or len(edge) != 3:
                return jsonify({"error": f"Invalid edge {edge!r}; expected [u, v, weight]."}), 400
            u, v, weight = edge
            problem = _check_weight(weight, u, v)
            if problem:
                return jsonify({"error": problem}), 400
            if u not in nodes or v not in nodes:
                return jsonify({"error": f"Edge {u}-{v} references a node outside the node list."}), 400
            clean_edges.append((u, v, weight))

        # Union-Find with path halving and union by rank. Keyed on the declared node
        # set so a disconnected graph yields a spanning forest instead of failing.
        parent = {node: node for node in nodes}
        rank = {node: 0 for node in nodes}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra == rb:
                return False
            if rank[ra] < rank[rb]:
                ra, rb = rb, ra
            parent[rb] = ra
            if rank[ra] == rank[rb]:
                rank[ra] += 1
            return True

        ordered = sorted(clean_edges, key=lambda e: e[2])
        steps = [["sort_edges", [[u, v, w] for u, v, w in ordered]]]

        mst_edges = []
        spanning_total = max(len(nodes) - 1, 0)
        for u, v, weight in ordered:
            steps.append(["consider_edge", u, v, weight])
            if union(u, v):
                mst_edges.append([u, v, weight])
                steps.append(["add_edge", u, v, weight])
                if len(mst_edges) == spanning_total:
                    steps.append(["mst_complete"])
            else:
                # Endpoints already share a root, so this edge would close a cycle.
                steps.append(["reject_edge", u, v, weight])

        steps.append(["final", mst_edges, sum(e[2] for e in mst_edges)])
        return jsonify(steps)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route("/run_floyd_warshall", methods=["POST"])
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

        INF = float("inf")
        n = len(nodes)
        index = {node: i for i, node in enumerate(nodes)}

        dist = [[0 if i == j else INF for j in range(n)] for i in range(n)]
        # next_hop[i][j] is the node to step to first when walking i -> j.
        next_hop = [[None] * n for _ in range(n)]

        for edge in edges:
            if not isinstance(edge, (list, tuple)) or len(edge) != 3:
                return jsonify({"error": f"Invalid edge {edge!r}; expected [u, v, weight]."}), 400
            u, v, weight = edge
            problem = _check_weight(weight, u, v)
            if problem:
                return jsonify({"error": problem}), 400
            if u not in index or v not in index:
                return jsonify({"error": f"Edge {u}-{v} references a node outside the node list."}), 400
            i, j = index[u], index[v]
            # Undirected input; keep the cheaper of any parallel edges.
            if weight < dist[i][j]:
                dist[i][j] = dist[j][i] = weight
                next_hop[i][j], next_hop[j][i] = v, u

        def wire_matrix():
            return [[_wire(value) for value in row] for row in dist]

        steps = [["init", wire_matrix(), nodes]]

        for k in range(n):
            k_node = nodes[k]
            steps.append(["start_iteration", k, k_node])
            updates = 0
            for i in range(n):
                for j in range(n):
                    if i == j:
                        continue
                    current = dist[i][j]
                    if dist[i][k] == INF or dist[k][j] == INF:
                        steps.append(["no_path_via_k", nodes[i], nodes[j], k_node])
                        continue
                    via_k = dist[i][k] + dist[k][j]
                    steps.append([
                        "consider_path", nodes[i], nodes[j], k_node,
                        _wire(current), dist[i][k], dist[k][j], via_k,
                    ])
                    if via_k < current:
                        dist[i][j] = via_k
                        next_hop[i][j] = next_hop[i][k]
                        updates += 1
                        steps.append(["update_distance", nodes[i], nodes[j], k_node, via_k, i, j])
                    else:
                        steps.append(["no_update", nodes[i], nodes[j], k_node, _wire(current)])
            steps.append(["iteration_complete", k, k_node, wire_matrix(), updates])

        # Rebuild one shortest path per reachable ordered pair for the results panel.
        all_paths = {}
        for i in range(n):
            for j in range(n):
                if i == j or dist[i][j] == INF or next_hop[i][j] is None:
                    continue
                path = [nodes[i]]
                while path[-1] != nodes[j] and len(path) <= n:
                    step_to = next_hop[index[path[-1]]][j]
                    if step_to is None:
                        break
                    path.append(step_to)
                if path[-1] == nodes[j]:
                    all_paths[f"{nodes[i]} → {nodes[j]}"] = {
                        "path": path,
                        "distance": dist[i][j],
                    }

        steps.append(["final", wire_matrix(), nodes, all_paths])
        return jsonify(steps)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route("/run_bellman_ford", methods=["POST"])
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

        # Collect nodes from both ends of every edge. A node that appears only as a
        # neighbour has no key of its own, and indexing graph[node] for it is exactly
        # what makes /run_prim raise KeyError on hand-written JSON.
        nodes = set(graph.keys())
        edge_list = []
        for u, neighbours in graph.items():
            if not isinstance(neighbours, dict):
                return jsonify({"error": f"Node {u!r} must map to a neighbour-to-weight object."}), 400
            for v, weight in neighbours.items():
                problem = _check_weight(weight, u, v)
                if problem:
                    return jsonify({"error": problem}), 400
                nodes.add(v)
                edge_list.append((u, v, weight))

        INF = float("inf")
        distances = {node: INF for node in nodes}
        distances[start] = 0

        def wire_distances():
            return {node: _wire(value) for node, value in distances.items()}

        steps = []
        iteration = 0
        # |V| - 1 passes suffice for a shortest path tree; stop early if a pass is quiet.
        for iteration in range(1, max(len(nodes), 1)):
            changed = False
            for u, v, weight in edge_list:
                steps.append(["check_edge", u, v, weight])
                if distances[u] != INF and distances[u] + weight < distances[v]:
                    distances[v] = distances[u] + weight
                    changed = True
                    steps.append(["relax", u, v, weight, wire_distances(), iteration])
                else:
                    steps.append(["no_relax", u, v, weight])
            steps.append(["iteration_complete", iteration, wire_distances()])
            if not changed:
                break

        # One pass beyond the bound: anything still improvable sits on a negative cycle.
        has_negative_cycle = any(
            distances[u] != INF and distances[u] + weight < distances[v]
            for u, v, weight in edge_list
        )

        return jsonify({
            "steps": steps,
            "has_negative_cycle": has_negative_cycle,
            "distances": wire_distances(),
            "iterations": iteration,
        })
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route("/generate_random_graph", methods=["POST"])
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
        
        # Generate nodes (A, B, C, ...)
        nodes = [chr(ord('A') + i) for i in range(num_nodes)]
        
        # Generate a connected graph
        import random
        
        # First, create a spanning tree to ensure connectivity
        edges = []
        used_nodes = [nodes[0]]
        remaining_nodes = nodes[1:]
        
        while remaining_nodes:
            # Pick a random used node and a random remaining node
            u = random.choice(used_nodes)
            v = remaining_nodes.pop(random.randint(0, len(remaining_nodes) - 1))
            weight = random.randint(1, 20)
            edges.append([u, v, weight])
            used_nodes.append(v)
        
        # Add additional random edges if needed
        edge_set = {tuple(sorted([e[0], e[1]])) for e in edges}
        
        while len(edges) < num_edges:
            u = random.choice(nodes)
            v = random.choice(nodes)
            
            if u != v:  # No self-loops
                edge_key = tuple(sorted([u, v]))
                if edge_key not in edge_set:
                    weight = random.randint(1, 20)
                    edges.append([u, v, weight])
                    edge_set.add(edge_key)
        
        return jsonify({
            'nodes': nodes,
            'edges': edges,
            'message': f'Generated connected graph with {num_nodes} nodes and {num_edges} edges.'
        })
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5002)