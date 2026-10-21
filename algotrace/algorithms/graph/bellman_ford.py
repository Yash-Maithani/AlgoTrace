"""Bellman-Ford shortest paths from one start, which survives negative weights
and reports a negative cycle instead of looping on one.

Called by POST /run_bellman_ford with a graph already checked: every key maps
to a neighbour-to-weight object of numbers, and the start is one of the keys.
"""
from .steps import StepLog, wire


def bellman_ford(graph, start):
    # Collect nodes from both ends of every edge. A node that appears only as a
    # neighbour has no key of its own, and indexing graph[node] for it is exactly
    # what makes /run_prim raise KeyError on hand-written JSON.
    nodes = set(graph.keys())
    edge_list = []
    for u, neighbours in graph.items():
        for v, weight in neighbours.items():
            nodes.add(v)
            edge_list.append((u, v, weight))

    INF = float("inf")
    distances = {node: INF for node in nodes}
    distances[start] = 0

    def wire_distances():
        return {node: wire(value) for node, value in distances.items()}

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
                               "from": wire(distances[u]),
                               "to": wire(distances[v])})
            if distances[u] != INF and distances[u] + weight < distances[v]:
                was = wire(distances[v])
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
                                   "from": wire(distances[u]),
                                   "to": wire(distances[v])})
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

    return log.payload(
        has_negative_cycle=has_negative_cycle,
        distances=wire_distances(),
        iterations=iteration,
    )
