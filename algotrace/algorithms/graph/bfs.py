"""Breadth-first search, one step per enqueue and per visit.

The queue is a plain list, so taking from the front is pop(0). Called by
POST /run_bfs with a graph already checked: every key maps to a list of
neighbours, and the start is one of the keys.
"""
from .steps import StepLog


def bfs(graph, start):
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
    return log.payload()
