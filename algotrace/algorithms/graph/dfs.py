"""Depth-first search with an explicit stack, one step per push and per visit.

Neighbours are pushed in reverse, so the first one listed is explored
first. Called by POST /run_dfs with a graph already checked.
"""
from .steps import StepLog


def dfs(graph, start):
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
    return log.payload()
