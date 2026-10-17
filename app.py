from flask import (Flask, render_template, request, jsonify, redirect, url_for, abort)
import random

# Import sorting algorithm modules
from sorting_algorithms.bubble_sort import bubble_sort
from sorting_algorithms.selection_sort import selection_sort
from sorting_algorithms.insertion_sort import insertion_sort
from sorting_algorithms.heap_sort import heap_sort
from sorting_algorithms.merge_sort import merge_sort
from sorting_algorithms.quick_sort import quick_sort
from searching_algorithms.linear_search import linear_search
from searching_algorithms.binary_search import binary_search, is_sorted

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
        "description": "Bubble Sort repeatedly steps through the list, compares adjacent elements and swaps them if they are in the wrong order. This implementation has no early exit, so it always makes n(n-1)/2 comparisons, even on a sorted list.",
        "time_complexity": {"Best": "O(n^2)", "Average/Worst": "O(n^2)"},
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
        "space_complexity": "O(log n)",
        "stable": False
    },
    "Merge Sort": {
        "description": "Merge Sort divides the array into halves, sorts them recursively, and then merges the sorted halves.",
        "time_complexity": {"Best": "O(n log n)", "Average/Worst": "O(n log n)"},
        "space_complexity": "O(n)",
        "stable": False
    },
    "Quick Sort": {
        "description": "Quick Sort picks a pivot element, partitions the array around the pivot, and recursively sorts the partitions. This implementation always picks the last element, so an already sorted list is its worst case.",
        "time_complexity": {"Best": "O(n log n)", "Average/Worst": "O(n^2)"},
        "space_complexity": "O(n)",
        "stable": False
    }
}


# ---------------------------------------------------------------------------
# Home page demonstration data.
#
# Both of these call the real bubble_sort from sorting_algorithms, the same
# function the /sorting page uses. Nothing here reimplements an algorithm or
# hand writes a step, so if that code changes these change with it.
# ---------------------------------------------------------------------------

HERO_ARRAY = [42, 17, 93, 8, 61, 29, 75, 36]
BAND_ARRAY = [17, 32, 11, 45, 9]


def _bubble_steps(values):
    """Run the real bubble sort over `values` and collect its draw calls."""
    data = list(values)
    steps = []
    stats = {"swaps": 0, "comparisons": 0}

    def draw(array_state, compared_indices=None, meta=None):
        # The hero only needs the bars, so the teacher payload is accepted
        # and dropped. See static/js/lessons/README.md for its shape.
        steps.append({
            "array": array_state[:],
            "compared": compared_indices[:] if compared_indices else [],
        })

    bubble_sort(data, draw, lambda: None, stats)
    return steps, stats


def _band_step(values, wanted):
    """One frozen step for the annotated band on the home page.

    Picks the first step at or after `wanted` where two elements are being
    compared, so the band always shows a real comparison rather than the
    final all-sorted frame.
    """
    steps, _ = _bubble_steps(values)
    chosen = None
    for index in range(min(wanted, len(steps) - 1), len(steps)):
        step = steps[index]
        pair = step["compared"]
        if len(pair) == 2 and all(isinstance(i, int) for i in pair):
            chosen = (index, step)
            break
    if chosen is None:
        chosen = (0, steps[0])

    index, step = chosen
    left, right = step["compared"]
    values_now = step["array"]
    # Comparisons counted up to and including this step.
    comparisons = sum(
        1 for s in steps[: index + 1]
        if len(s["compared"]) == 2 and all(isinstance(i, int) for i in s["compared"])
    )
    n = len(values)
    return {
        "array": values_now,
        "left": left,
        "right": right,
        "left_value": values_now[left],
        "right_value": values_now[right],
        "swaps": values_now[left] > values_now[right],
        "comparisons": comparisons,
        "total_comparisons": n * (n - 1) // 2,
        "n": n,
    }


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        algo_type = request.form.get("algo_type", "sorting")
        if algo_type == "sorting":
            return handle_sorting()
        else:
            return handle_graph()
    hero_steps, hero_stats = _bubble_steps(HERO_ARRAY)
    return render_template(
        "landing.html",
        hero_steps=hero_steps,
        hero_start=HERO_ARRAY,
        hero_sorted=sorted(HERO_ARRAY),
        hero_comparisons=hero_stats["comparisons"],
        band=_band_step(BAND_ARRAY, 4),
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
            sorting_algorithms=list(sorting_algo_dict.keys()),
            selected_algo=selected_algo,
            lesson_ids=SORT_LESSON_IDS,
            pick_notes=SORT_PICK_NOTES,
            initial_run=None,
            error="",
        )

# ---------------------------------------------------------------------------
# Searching.
#
# Steps follow section 1 of static/js/lessons/README.md: array and compared
# drive the stage, the six teacher fields drive the Learn panel. The search
# actions extend the shared vocabulary rather than overloading it:
#   compare   a value was read and tested against the target
#   discard   binary search threw away the half that cannot hold the target
#   found     the target was located at this position
#   missing   the search ended without a match
# ---------------------------------------------------------------------------

SEARCH_ACTIONS = {"compare", "discard", "found", "missing"}

SEARCH_ALGORITHMS = {
    "linear_search": linear_search,
    "binary_search": binary_search,
}

MAX_SEARCH_SIZE = 30


def _parse_values(raw, limit=None):
    """Read the comma separated list the user typed. Returns (values, error)."""
    if limit is None:
        limit = MAX_SEARCH_SIZE
    if isinstance(raw, list):
        items = raw
    else:
        text = (raw or "").replace("\n", ",").strip()
        if not text:
            return None, "Enter some numbers, separated by commas."
        items = [part.strip() for part in text.split(",") if part.strip()]

    if not items:
        return None, "Enter some numbers, separated by commas."
    if len(items) > limit:
        return None, "That is %d values. Use %d or fewer so the cells stay readable." % (
            len(items), limit)

    values = []
    for item in items:
        if isinstance(item, bool) or not isinstance(item, (int, float, str)):
            return None, "%r is not a whole number." % (item,)
        try:
            values.append(int(str(item).strip()))
        except ValueError:
            return None, "%s is not a whole number. Use digits separated by commas." % item
    return values, None


# Display name to lesson file id, so the picker and the Learn panel agree.
SORT_LESSON_IDS = {
    "Bubble Sort": "bubble_sort",
    "Selection Sort": "selection_sort",
    "Insertion Sort": "insertion_sort",
    "Merge Sort": "merge_sort",
    "Quick Sort": "quick_sort",
    "Heap Sort": "heap_sort",
}

SORT_PICK_NOTES = {
    "Bubble Sort": "Swap neighbours until nothing is out of order.",
    "Selection Sort": "Find the smallest, place it, repeat.",
    "Insertion Sort": "Slide each value back into a sorted prefix.",
    "Merge Sort": "Split, sort the halves, merge them back.",
    "Quick Sort": "Partition around a pivot, then recurse.",
    "Heap Sort": "Build a heap, pull the largest off the top.",
}


def _sort_payload(name, values):
    """One run, in the shape /run_sort answers with.

    POST /sorting and /run_sort both go through here, so the page cannot be
    served one thing and the endpoint another.
    """
    steps = []

    def draw(array_state, compared_indices=None, meta=None):
        step_data = {
            "array": array_state[:],
            "compared": compared_indices[:] if compared_indices else [],
        }
        if meta:
            step_data.update(meta)
        # The work done so far, read off the counter the result reports, so
        # the running total on screen cannot drift from the final one. The
        # Learn panel shows these as the run plays.
        step_data.setdefault("vars", {})
        step_data["vars"] = dict(step_data["vars"],
                                 comparisons=stats["comparisons"],
                                 swaps=stats["swaps"])
        steps.append(step_data)

    stats = {"swaps": 0, "comparisons": 0}
    working = list(values)
    sorting_algo_dict[name](working, draw, lambda: None, stats)
    details = sorting_algo_details[name]

    return {
        "steps": steps,
        "array": list(values),
        "sorted": working,
        "algorithm": name,
        "result": {
            "comparisons": stats["comparisons"],
            "swaps": stats["swaps"],
            "n": len(values),
        },
        "info": {
            "stable": details["stable"],
            "time_complexity": details["time_complexity"],
            "space_complexity": details["space_complexity"],
            "description": details["description"],
        },
    }


# ---------------------------------------------------------------------------
# Sorting over JSON.
#
# POST /sorting still renders the page with its steps embedded, which is how
# the form has always worked. /run_sort answers the same run as JSON so the
# workspace can start one without reloading. Both call the same six
# functions, so neither can drift from the other.
# ---------------------------------------------------------------------------

SORT_ACTIONS = {"compare", "swap", "overwrite", "select", "place", "done"}

MAX_SORT_SIZE = 100


@app.route("/run_sort", methods=["POST"])
def run_sort():
    try:
        data = request.json or {}
        name = data.get("algorithm", "Bubble Sort")
        if name not in sorting_algo_dict:
            return jsonify({"error": "Unknown sorting algorithm %r." % name}), 400

        if data.get("values") in (None, "", []):
            try:
                size = int(data.get("size", 30))
            except (TypeError, ValueError):
                return jsonify({"error": "Array size must be a whole number."}), 400
            if not 5 <= size <= MAX_SORT_SIZE:
                return jsonify({
                    "error": "Array size must be between 5 and %d." % MAX_SORT_SIZE
                }), 400
            values = [random.randint(1, 100) for _ in range(size)]
        else:
            values, problem = _parse_values(data.get("values"), MAX_SORT_SIZE)
            if problem:
                return jsonify({"error": problem}), 400

        return jsonify(_sort_payload(name, values))
    except Exception as e:
        return jsonify({"error": "An error occurred: %s" % e}), 500


SEARCH_PICKER = [
    ("linear_search", "Linear Search", "Check every value until you find it."),
    ("binary_search", "Binary Search", "Halve a sorted list over and over."),
]


@app.route("/searching")
def searching_page():
    """The searching workspace. The run itself goes through /run_search.

    ?algorithm= opens on that one, the same way /sorting does, because the
    Learn page links straight to a named algorithm.
    """
    selected = request.args.get("algorithm", "linear_search")
    if selected not in SEARCH_ALGORITHMS:
        selected = "linear_search"

    return render_template(
        "searching.html",
        algorithms=SEARCH_PICKER,
        selected_algo=selected,
    )


@app.route("/run_search", methods=["POST"])
def run_search():
    try:
        data = request.json or {}
        name = data.get("algorithm", "linear_search")
        if name not in SEARCH_ALGORITHMS:
            return jsonify({"error": "Unknown search algorithm %r." % name}), 400

        values, problem = _parse_values(data.get("array"))
        if problem:
            return jsonify({"error": problem}), 400

        raw_target = data.get("target")
        if isinstance(raw_target, bool) or raw_target is None or raw_target == "":
            return jsonify({"error": "Enter a target to search for."}), 400
        try:
            target = int(str(raw_target).strip())
        except (ValueError, TypeError):
            return jsonify({"error": "%s is not a whole number." % raw_target}), 400

        # Binary search is only correct on a sorted list, so the run is
        # blocked rather than quietly returning a wrong answer. The sorted
        # copy travels with the refusal so the page can offer to fix it.
        if name == "binary_search" and not is_sorted(values):
            return jsonify({
                "error": "Binary search only works on a sorted list, because "
                         "it throws away half the range based on the value in "
                         "the middle.",
                "unsorted": True,
                "sorted_array": sorted(values),
            }), 400

        steps = []

        def draw(indices, meta):
            step_data = {
                "array": list(values),
                "compared": list(indices),
            }
            step_data.update(meta)
            steps.append(step_data)

        stats = {"comparisons": 0}
        found_at = SEARCH_ALGORITHMS[name](values, target, draw, None, stats)

        return jsonify({
            "steps": steps,
            "array": values,
            "target": target,
            "algorithm": name,
            "result": {
                "found": found_at != -1,
                "index": found_at,
                "comparisons": stats["comparisons"],
            },
        })
    except Exception as e:
        return jsonify({"error": "An error occurred: %s" % e}), 500


@app.route("/learn")
def learn():
    """Algorithm index with a suggested beginner order."""
    return render_template("learn.html")


@app.route("/big-o")
def big_o_page():
    """How complexity works. Every figure on it comes from this repository."""
    return render_template("big_o.html")


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
    """The graph workspace. ?algo= picks which algorithm.

    An unknown name is a 404 rather than a quiet fall back to BFS, which
    served the wrong algorithm under the name that was asked for.
    """
    algo = request.args.get("algo", "bfs").lower()
    if algo not in graph_algo_dict:
        abort(404)

    return render_template("%s.html" % graph_algo_dict[algo], algorithm=algo)



def handle_sorting():
    """The form POST. Still runs the sort here and still renders the page.

    The page is the workspace now, so the run travels as initial_run in the
    shape /run_sort answers with, and the workspace loads it on arrival.
    """
    selected_algo = request.form.get("algorithm", "Bubble Sort")
    if selected_algo not in sorting_algo_dict:
        selected_algo = "Bubble Sort"
    input_method = request.form.get("input_method", "random")
    error = ""
    values = []

    if input_method == "manual":
        values, error = _parse_values(request.form.get("manual_input", ""),
                                      MAX_SORT_SIZE)
        if error:
            values = []
    else:
        try:
            size = int(request.form.get("size", 30))
        except ValueError:
            error = "Invalid array size. Please enter a valid number."
            size = None
        if size is not None:
            if not 5 <= size <= MAX_SORT_SIZE:
                error = "Array size must be between 5 and %d." % MAX_SORT_SIZE
            else:
                values = [random.randint(1, 100) for _ in range(size)]

    return render_template(
        "sorting.html",
        sorting_algorithms=list(sorting_algo_dict.keys()),
        selected_algo=selected_algo,
        lesson_ids=SORT_LESSON_IDS,
        pick_notes=SORT_PICK_NOTES,
        initial_run=None if error else _sort_payload(selected_algo, values),
        error=error,
    )


def handle_graph():
    selected_algo = request.form.get("algorithm", "bfs").lower()
    if selected_algo not in graph_algo_dict:
        # fallback to the first available graph algorithm
        selected_algo = "bfs"
    
    # Return the algo key so the right class is highlighted in the template
    return render_template(f"{graph_algo_dict[selected_algo]}.html", algorithm=selected_algo)

# ---------------------------------------------------------------------------
# Graph step recording.
#
# The step arrays the /run_* endpoints emit are the ones graph_base.html has
# always drawn, and they do not change. StepLog keeps a parallel meta list in
# lockstep with them, one teacher payload per step, as described in section 4
# of static/js/lessons/README.md.
#
# Graph actions extend the sorting vocabulary rather than overloading it:
#   visit      a node is settled and will not be looked at again
#   enqueue    a node joins the queue, stack or frontier
#   consider   an edge or a route through a node is being examined
#   relax      a distance improved
#   reject     an edge or route was looked at and not taken
#   include    an edge joins the tree or the answer
#   milestone  a marker that changes no state, such as a pass finishing
#   done       the final frame
# ---------------------------------------------------------------------------

GRAPH_ACTIONS = {
    "visit", "enqueue", "consider", "relax", "reject", "include",
    "milestone", "done",
}


class StepLog:
    """A step array and its parallel meta list, always appended to together."""

    def __init__(self):
        self.steps = []
        self.meta = []

    def add(self, step, action, beginner, why, indices=(), values=(),
            line=None, variables=None):
        self.steps.append(step)
        self.meta.append({
            "action": action,
            "indices": list(indices),
            "values": list(values),
            "line": line,
            "vars": dict(variables or {}),
            "explain": {"beginner": beginner, "why": why},
        })
        return step

    def payload(self, **extra):
        """The response body: the steps, their meta, and any summary fields."""
        body = {"steps": self.steps, "meta": self.meta}
        body.update(extra)
        return body


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
        log = StepLog()
        log.add(["queue", start], "enqueue",
                "Start at %s, so it is the only node waiting." % start,
                "Breadth first search always takes the next node from the "
                "front of the queue, so the order nodes join decides the "
                "order they are visited.",
                indices=[start], line="start",
                variables={"queue": [start], "visited": []})
        traversal_path = []  # Track the order of visited nodes

        while queue:
            node = queue.pop(0)
            if node not in visited:
                visited.add(node)
                traversal_path.append(node)
                log.add(["visit", node], "visit",
                        "Take %s off the front of the queue and visit it." % node,
                        "Every node one step from the start is visited before "
                        "any node two steps away, which is what makes the "
                        "search spread out in rings.",
                        indices=[node], line="pop",
                        variables={"queue": list(queue),
                                   "visited": sorted(visited)})
                for neighbor in graph.get(node, []):
                    if neighbor not in visited and neighbor not in queue:
                        queue.append(neighbor)
                        log.add(["queue", neighbor], "enqueue",
                                "%s is a neighbour of %s that has not been seen "
                                "yet, so it joins the back of the queue."
                                % (neighbor, node),
                                "Joining at the back is what keeps the ring "
                                "order: everything already waiting is at least "
                                "as close to the start.",
                                indices=[neighbor], line="enqueue",
                                variables={"queue": list(queue),
                                           "visited": sorted(visited)})
        
        # Add final result step
        log.add(["final", traversal_path], "done",
                "The queue is empty. %d node%s were reached from %s: %s."
                % (len(traversal_path), "" if len(traversal_path) == 1 else "s",
                   start, ", ".join(traversal_path)),
                "Anything not in that list has no path from the start at all.",
                indices=list(traversal_path), line=None,
                variables={"queue": [], "visited": sorted(visited)})
        return jsonify(log.payload())
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
        log = StepLog()
        log.add(["stack", start], "enqueue",
                "Start at %s, so it is the only node on the stack." % start,
                "Depth first search always takes the node from the top of the "
                "stack, so the most recently added node is explored next.",
                indices=[start], line="start",
                variables={"stack": [start], "visited": []})
        traversal_path = []  # Track the order of visited nodes

        while stack:
            node = stack.pop()
            if node not in visited:
                visited.add(node)
                traversal_path.append(node)
                log.add(["visit", node], "visit",
                        "Take %s off the top of the stack and visit it." % node,
                        "Taking from the top means the search follows one path "
                        "as far as it goes before it backs up and tries "
                        "another.",
                        indices=[node], line="pop",
                        variables={"stack": list(stack),
                                   "visited": sorted(visited)})
                for neighbor in reversed(graph.get(node, [])):
                    if neighbor not in visited and neighbor not in stack:
                        stack.append(neighbor)
                        log.add(["stack", neighbor], "enqueue",
                                "%s is a neighbour of %s that has not been seen "
                                "yet, so it goes on the stack."
                                % (neighbor, node),
                                "The neighbours are pushed in reverse order, so "
                                "the first one listed ends up on top and is "
                                "explored first.",
                                indices=[neighbor], line="push",
                                variables={"stack": list(stack),
                                           "visited": sorted(visited)})
        
        # Add final result step
        log.add(["final", traversal_path], "done",
                "The stack is empty. %d node%s were reached from %s: %s."
                % (len(traversal_path), "" if len(traversal_path) == 1 else "s",
                   start, ", ".join(traversal_path)),
                "Depth first search reaches exactly the same set of nodes as "
                "breadth first search does. Only the order differs.",
                indices=list(traversal_path), line=None,
                variables={"stack": [], "visited": sorted(visited)})
        return jsonify(log.payload())
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
        # node_order fixes the tie-break: min() returns the first smallest it
        # meets, so walking the nodes in the order they arrived makes the
        # choice depend on the input. Selecting straight from the set left it
        # depending on set iteration order, which Python varies per process,
        # so a graph with tied distances animated differently after a restart.
        node_order = list(graph.keys())
        unvisited = set(graph.keys())
        log = StepLog()

        while unvisited:
            current = min((node for node in node_order if node in unvisited),
                          key=lambda node: distances[node])
            if distances[current] == float('infinity'):
                break
            unvisited.remove(current)
            log.add(["visit", current], "visit",
                    "%s is the nearest unvisited node, %s away from the "
                    "start, so its distance is now final."
                    % (current, _wire(distances[current])),
                    "Every other route to it would have to pass through a "
                    "node that is already further away, so nothing can "
                    "improve it.",
                    indices=[current], values=[_wire(distances[current])],
                    line="pick-min",
                    variables={"unvisited": sorted(unvisited),
                               "settled": len(graph) - len(unvisited)})
            for neighbor, weight in graph[current].items():
                if neighbor in unvisited:
                    new_distance = distances[current] + weight
                    if new_distance < distances[neighbor]:
                        was = _wire(distances[neighbor])
                        distances[neighbor] = new_distance
                        previous[neighbor] = current
                        log.add(["update", neighbor, new_distance, current],
                                "relax",
                                "Going through %s reaches %s in %s, which "
                                "beats the %s on record."
                                % (current, neighbor, new_distance, was),
                                "A shorter route is only ever found through a "
                                "node whose own distance is already settled.",
                                indices=[neighbor], values=[new_distance],
                                line="relax",
                                variables={"current": current, "weight": weight,
                                           "was": was,
                                           "unvisited": sorted(unvisited)})
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
        reached = [n for n in graph if distances[n] != float('infinity')]
        wired = {node: _wire(value) for node, value in distances.items()}
        log.add(["final", wired, paths], "done",
                "Distances from %s are settled. %d of %d node%s could be "
                "reached." % (start, len(reached), len(graph),
                              "" if len(graph) == 1 else "s"),
                "A node still at infinity has no path from the start at all.",
                indices=sorted(graph), line=None,
                variables={"distances": {k: _wire(v)
                                         for k, v in distances.items()}})
        return jsonify(log.payload())
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
        log = StepLog()
        min_heap = []

        # Start with the starting node
        visited.add(start)
        log.add(["start", start], "visit",
                "The tree starts as the single node %s." % start,
                "Prim grows one connected tree outwards, so it needs "
                "somewhere to grow from. Any node will do.",
                indices=[start], line="start",
                variables={"visited": [start], "tree_edges": 0})
        
        # Add all edges from start node to the priority queue
        frontier_nodes = []
        for neighbor, weight in graph[start].items():
            heapq.heappush(min_heap, (weight, start, neighbor))
            if neighbor not in visited:
                frontier_nodes.append(neighbor)
        
        if frontier_nodes:
            log.add(["add_frontier", frontier_nodes], "enqueue",
                    "Every edge leaving %s goes into the heap, which puts "
                    "%s within reach."
                    % (start, ", ".join(frontier_nodes)),
                    "The heap always hands back the cheapest edge leaving "
                    "the tree, so edges have to be in it before they can be "
                    "chosen.",
                    indices=list(frontier_nodes), line="push-edges",
                    variables={"heap_size": len(min_heap),
                               "visited": sorted(visited)})

        while min_heap:
            weight, u, v = heapq.heappop(min_heap)
            
            if v in visited:
                # This edge connects to an already visited node, ignore it
                log.add(["ignore_edge", u, v, weight], "reject",
                        "%s to %s costs %s, but %s is already in the tree, "
                        "so this edge would close a loop."
                        % (u, v, weight, v),
                        "An edge is only useful if it reaches something new. "
                        "Stale entries like this are why the heap can hold "
                        "more edges than the tree will ever use.",
                        indices=[u, v], values=[weight],
                        line="skip-visited",
                        variables={"heap_size": len(min_heap),
                                   "visited": sorted(visited)})
                continue
            
            # Consider this edge
            log.add(["consider_edge", u, v, weight], "consider",
                    "The cheapest edge leaving the tree is %s to %s at %s."
                    % (u, v, weight),
                    "Taking the cheapest edge out of the tree every time is "
                    "the whole of Prim, and it is enough to guarantee the "
                    "lightest spanning tree.",
                    indices=[u, v], values=[weight], line="pop-min",
                    variables={"heap_size": len(min_heap),
                               "visited": sorted(visited)})
            
            # Add edge to MST
            mst_edges.append((u, v, weight))
            visited.add(v)
            log.add(["add_edge", u, v, weight], "include",
                    "%s joins the tree, which now holds %d edge%s."
                    % (v, len(mst_edges),
                       "" if len(mst_edges) == 1 else "s"),
                    "The tree stays in one piece because every edge added "
                    "has one end already inside it.",
                    indices=[u, v], values=[weight], line="add-edge",
                    variables={"tree_edges": len(mst_edges),
                               "tree_weight": sum(e[2] for e in mst_edges),
                               "visited": sorted(visited)})
            
            # Add all edges from the newly visited node to unvisited nodes
            new_frontier = []
            for neighbor, w in graph[v].items():
                if neighbor not in visited:
                    heapq.heappush(min_heap, (w, v, neighbor))
                    new_frontier.append(neighbor)
            
            if new_frontier:
                log.add(["add_frontier", new_frontier], "enqueue",
                        "Joining %s puts %s within reach."
                        % (v, ", ".join(new_frontier)),
                        "Each new node widens the choice of edges, and the "
                        "heap keeps the cheapest of them at the front.",
                        indices=list(new_frontier), line="push-edges",
                        variables={"heap_size": len(min_heap),
                                   "visited": sorted(visited)})
        
        # Add final result
        total_weight = sum(e[2] for e in mst_edges)
        # Prim grows one tree from the start node, so it reaches that node's
        # component and no further. Saying which happened beats one sentence
        # that hedges both.
        reached_everything = len(visited) == len(graph)
        log.add(["final", mst_edges, total_weight], "done",
                "The tree holds %d edge%s and weighs %s in total, reaching "
                "%d of the %d node%s."
                % (len(mst_edges), "" if len(mst_edges) == 1 else "s",
                   total_weight, len(visited), len(graph),
                   "" if len(graph) == 1 else "s"),
                ("The heap is empty, so nothing is left that would reach a "
                 "new node. Every node was reached, so this is a minimum "
                 "spanning tree of the whole graph.") if reached_everything else
                ("The heap is empty, so nothing is left that would reach a "
                 "new node. Prim grows one tree outward from where it "
                 "started, so the %d node%s it never reached are in a "
                 "separate piece of the graph with no edge across to them."
                 % (len(graph) - len(visited),
                    "" if len(graph) - len(visited) == 1 else "s")),
                indices=sorted(visited), values=[total_weight], line=None,
                variables={"tree_edges": len(mst_edges),
                           "tree_weight": total_weight,
                           "visited": sorted(visited),
                           "reached_everything": reached_everything})
        
        return jsonify(log.payload())
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
        log = StepLog()
        log.add(["sort_edges", [[u, v, w] for u, v, w in ordered]],
                "milestone",
                "All %d edge%s sorted by weight, cheapest first."
                % (len(ordered), "" if len(ordered) == 1 else "s"),
                "Kruskal only ever wants the cheapest edge it has not "
                "tried yet, so sorting once up front is what makes the "
                "rest of the run a single pass.",
                indices=[], values=[w for _, _, w in ordered],
                line="sort",
                variables={"edges": len(ordered), "nodes": len(nodes)})

        mst_edges = []
        spanning_total = max(len(nodes) - 1, 0)
        for u, v, weight in ordered:
            log.add(["consider_edge", u, v, weight], "consider",
                    "Next cheapest edge: %s to %s at %s." % (u, v, weight),
                    "Edges arrive in weight order, so the only question "
                    "left for each one is whether it would close a loop.",
                    indices=[u, v], values=[weight], line="take-next",
                    variables={"tree_edges": len(mst_edges),
                               "needed": spanning_total})
            if union(u, v):
                mst_edges.append([u, v, weight])
                log.add(["add_edge", u, v, weight], "include",
                        "%s and %s were in different groups, so the edge "
                        "joins them and enters the forest."
                        % (u, v),
                        "Union-Find answers the only question that matters "
                        "here, whether two nodes are already connected, in "
                        "very nearly constant time.",
                        indices=[u, v], values=[weight], line="union",
                        variables={"tree_edges": len(mst_edges),
                                   "tree_weight": sum(e[2] for e in mst_edges),
                                   "needed": spanning_total})
                if len(mst_edges) == spanning_total:
                    log.add(["mst_complete"], "milestone",
                            "The forest now has %d edge%s, which spans "
                            "every node. Nothing further can be added."
                            % (spanning_total,
                               "" if spanning_total == 1 else "s"),
                            "A spanning tree over n nodes has exactly n-1 "
                            "edges, so reaching that count means the job is "
                            "done even if edges remain unexamined.",
                            indices=[], line="mst-complete",
                            variables={"tree_edges": len(mst_edges),
                                       "needed": spanning_total})
            else:
                # Endpoints already share a root, so this edge would close a cycle.
                log.add(["reject_edge", u, v, weight], "reject",
                        "%s and %s are already connected, so this edge "
                        "would close a loop and is skipped." % (u, v),
                        "A loop adds weight without connecting anything "
                        "new, so it can never belong to a minimum spanning "
                        "tree.",
                        indices=[u, v], values=[weight], line="cycle",
                        variables={"tree_edges": len(mst_edges),
                                   "needed": spanning_total})

        # n-1 edges spans every node, so anything short of that is a forest
        # of one tree per component rather than a single spanning tree.
        spans_everything = len(mst_edges) == spanning_total
        result_name = ("minimum spanning tree" if spans_everything
                       else "minimum spanning forest")
        log.add(["final", mst_edges, sum(e[2] for e in mst_edges)], "done",
                "%d edge%s chosen, weighing %s in total: a %s."
                % (len(mst_edges), "" if len(mst_edges) == 1 else "s",
                   sum(e[2] for e in mst_edges), result_name),
                ("Every node is connected by %d edges, which is n-1, so this "
                 "is one tree." % spanning_total) if spans_everything else
                ("Only %d of the %d edges a spanning tree needs could be "
                 "added, so the graph is disconnected and this is a forest "
                 "of one tree per connected piece."
                 % (len(mst_edges), spanning_total)),
                indices=list(nodes),
                values=[sum(e[2] for e in mst_edges)], line=None,
                variables={"tree_edges": len(mst_edges),
                           "needed": spanning_total,
                           "spans_everything": spans_everything})
        return jsonify(log.payload())
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

        log = StepLog()
        log.add(["init", wire_matrix(), nodes], "milestone",
                "Start from the direct edges only. Every pair with no edge "
                "between them is infinity for now.",
                "The table answers one question for every pair of nodes at "
                "once, so it starts holding what is known without going "
                "through anything.",
                indices=list(nodes), line="init",
                variables={"n": n})

        for k in range(n):
            k_node = nodes[k]
            log.add(["start_iteration", k, k_node], "milestone",
                    "Pass %d of %d: allow routes that go through %s."
                    % (k + 1, n, k_node),
                    "After this pass the table holds the best route using "
                    "only the nodes considered so far as stopping points.",
                    indices=[k_node], line="k-loop",
                    variables={"k": k, "k_node": k_node, "n": n})
            updates = 0
            for i in range(n):
                for j in range(n):
                    if i == j:
                        continue
                    current = dist[i][j]
                    if dist[i][k] == INF or dist[k][j] == INF:
                        log.add(["no_path_via_k", nodes[i], nodes[j], k_node],
                                "reject",
                                "There is still no route from %s to %s "
                                "through %s, because one half of it is "
                                "missing."
                                % (nodes[i], nodes[j], k_node),
                                "A route through %s needs both halves to "
                                "exist, and one of them is infinity." % k_node,
                                indices=[nodes[i], nodes[j], k_node],
                                line="check-inf",
                                variables={"k": k, "i": i, "j": j})
                        continue
                    via_k = dist[i][k] + dist[k][j]
                    log.add([
                        "consider_path", nodes[i], nodes[j], k_node,
                        _wire(current), dist[i][k], dist[k][j], via_k,
                    ], "consider",
                        "%s to %s is %s now, and %s via %s. Which is "
                        "shorter?"
                        % (nodes[i], nodes[j], _wire(current), via_k, k_node),
                        "Every pair is re-checked against every stopping "
                        "point, which is where the three nested loops and "
                        "the V cubed come from.",
                        indices=[nodes[i], nodes[j], k_node],
                        values=[_wire(current), dist[i][k], dist[k][j], via_k],
                        line="compare",
                        variables={"k": k, "i": i, "j": j, "via_k": via_k})
                    if via_k < current:
                        dist[i][j] = via_k
                        next_hop[i][j] = next_hop[i][k]
                        updates += 1
                        log.add(["update_distance", nodes[i], nodes[j],
                                 k_node, via_k, i, j], "relax",
                                "Going through %s makes %s to %s shorter, "
                                "%s instead of %s."
                                % (k_node, nodes[i], nodes[j], via_k,
                                   _wire(current)),
                                "The table is updated in place, so later "
                                "passes build on the routes found in this "
                                "one.",
                                indices=[nodes[i], nodes[j], k_node],
                                values=[via_k], line="update",
                                variables={"k": k, "i": i, "j": j,
                                           "was": _wire(current),
                                           "now": via_k})
                    else:
                        log.add(["no_update", nodes[i], nodes[j], k_node,
                                 _wire(current)], "reject",
                                "Going through %s is no shorter, so %s to "
                                "%s stays at %s."
                                % (k_node, nodes[i], nodes[j], _wire(current)),
                                "Most checks end this way. The table only "
                                "changes when a genuinely better route "
                                "turns up.",
                                indices=[nodes[i], nodes[j], k_node],
                                values=[_wire(current)], line="keep",
                                variables={"k": k, "i": i, "j": j,
                                           "via_k": via_k})
            log.add(["iteration_complete", k, k_node, wire_matrix(), updates],
                    "milestone",
                    "Pass %d is done. Routes through %s improved %d "
                    "distance%s." % (k + 1, k_node, updates,
                                     "" if updates == 1 else "s"),
                    "Once every node has had a pass, the table holds the "
                    "shortest route between every pair.",
                    indices=[k_node], values=[updates], line="k-done",
                    variables={"k": k, "updates": updates, "n": n})

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

        log.add(["final", wire_matrix(), nodes, all_paths], "done",
                "Every pair is settled. %d ordered pair%s have a route."
                % (len(all_paths), "" if len(all_paths) == 1 else "s"),
                "Any pair still at infinity sits in a different piece of a "
                "disconnected graph.",
                indices=list(nodes), line=None,
                variables={"n": n, "pairs_with_a_route": len(all_paths)})
        return jsonify(log.payload())
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

        log = StepLog()
        iteration = 0
        # |V| - 1 passes suffice for a shortest path tree; stop early if a pass is quiet.
        for iteration in range(1, max(len(nodes), 1)):
            changed = False
            for u, v, weight in edge_list:
                log.add(["check_edge", u, v, weight], "consider",
                        "Look at the edge %s to %s, weight %s."
                        % (u, v, weight),
                        "Bellman-Ford sweeps every edge on every pass "
                        "rather than choosing the nearest node, which is "
                        "how it copes with negative weights.",
                        indices=[u, v], values=[weight], line="edge-loop",
                        variables={"pass": iteration,
                                   "from": _wire(distances[u]),
                                   "to": _wire(distances[v])})
                if distances[u] != INF and distances[u] + weight < distances[v]:
                    was = _wire(distances[v])
                    distances[v] = distances[u] + weight
                    changed = True
                    log.add(["relax", u, v, weight, wire_distances(),
                             iteration], "relax",
                            "Reaching %s through %s costs %s, which beats "
                            "the %s on record."
                            % (v, u, distances[v], was),
                            "Each pass lets a shortest path grow by one "
                            "more edge, so n-1 passes are enough for any "
                            "path without a cycle.",
                            indices=[u, v], values=[distances[v]],
                            line="relax",
                            variables={"pass": iteration, "was": was,
                                       "now": distances[v]})
                else:
                    log.add(["no_relax", u, v, weight], "reject",
                            "That edge gives no shorter route to %s, so "
                            "nothing changes." % v,
                            "An edge from a node still at infinity cannot "
                            "help anything yet, and neither can one that "
                            "arrives no sooner.",
                            indices=[u, v], values=[weight],
                            line="no-improve",
                            variables={"pass": iteration,
                                       "from": _wire(distances[u]),
                                       "to": _wire(distances[v])})
            log.add(["iteration_complete", iteration, wire_distances()],
                    "milestone",
                    "Pass %d is done and %s."
                    % (iteration,
                       "something improved" if changed
                       else "nothing improved, so the answer is settled"),
                    "A pass that changes nothing means no path can grow "
                    "any further, so the remaining passes are skipped.",
                    indices=[], values=[iteration], line="pass-done",
                    variables={"pass": iteration, "changed": changed})
            if not changed:
                break

        # One pass beyond the bound: anything still improvable sits on a negative cycle.
        has_negative_cycle = any(
            distances[u] != INF and distances[u] + weight < distances[v]
            for u, v, weight in edge_list
        )

        return jsonify(log.payload(
            has_negative_cycle=has_negative_cycle,
            distances=wire_distances(),
            iterations=iteration,
        ))
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