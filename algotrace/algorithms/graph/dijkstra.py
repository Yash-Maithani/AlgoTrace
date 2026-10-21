"""Dijkstra's shortest paths from one start, with a linear scan for the
nearest unvisited node.

Called by POST /run_dijkstra with a graph already checked: every key maps
to a neighbour-to-weight object, and the start is one of the keys.
"""
from .steps import StepLog, wire


def dijkstra(graph, start):
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
                % (current, wire(distances[current])),
                "Every other route to it would have to pass through a "
                "node that is already further away, so nothing can "
                "improve it.",
                indices=[current], values=[wire(distances[current])],
                line="pick-min",
                variables={"unvisited": sorted(unvisited),
                           "settled": len(graph) - len(unvisited)})
        for neighbor, weight in graph[current].items():
            if neighbor in unvisited:
                new_distance = distances[current] + weight
                if new_distance < distances[neighbor]:
                    was = wire(distances[neighbor])
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
    wired = {node: wire(value) for node, value in distances.items()}
    log.add(["final", wired, paths], "done",
            "Distances from %s are settled. %d of %d node%s could be "
            "reached." % (start, len(reached), len(graph),
                          "" if len(graph) == 1 else "s"),
            "A node still at infinity has no path from the start at all.",
            indices=sorted(graph), line=None,
            variables={"distances": {k: wire(v)
                                     for k, v in distances.items()}})
    return log.payload()
