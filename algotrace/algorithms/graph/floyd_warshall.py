"""Floyd-Warshall: the shortest distance between every pair, in one table.

Called by POST /run_floyd_warshall with the nodes and edges already checked:
at least one node, and every edge a [u, v, weight] with both ends in `nodes`.
Edges are undirected; of two parallel edges the cheaper one counts.
"""
from .steps import StepLog, wire


def floyd_warshall(nodes, edges):
    INF = float("inf")
    n = len(nodes)
    index = {node: i for i, node in enumerate(nodes)}

    dist = [[0 if i == j else INF for j in range(n)] for i in range(n)]
    # next_hop[i][j] is the node to step to first when walking i -> j.
    next_hop = [[None] * n for _ in range(n)]

    for u, v, weight in edges:
        i, j = index[u], index[v]
        # Undirected input; keep the cheaper of any parallel edges.
        if weight < dist[i][j]:
            dist[i][j] = dist[j][i] = weight
            next_hop[i][j], next_hop[j][i] = v, u

    def wire_matrix():
        return [[wire(value) for value in row] for row in dist]

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
                    wire(current), dist[i][k], dist[k][j], via_k,
                ], "consider",
                    "%s to %s is %s now, and %s via %s. Which is "
                    "shorter?"
                    % (nodes[i], nodes[j], wire(current), via_k, k_node),
                    "Every pair is re-checked against every stopping "
                    "point, which is where the three nested loops and "
                    "the V cubed come from.",
                    indices=[nodes[i], nodes[j], k_node],
                    values=[wire(current), dist[i][k], dist[k][j], via_k],
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
                               wire(current)),
                            "The table is updated in place, so later "
                            "passes build on the routes found in this "
                            "one.",
                            indices=[nodes[i], nodes[j], k_node],
                            values=[via_k], line="update",
                            variables={"k": k, "i": i, "j": j,
                                       "was": wire(current),
                                       "now": via_k})
                else:
                    log.add(["no_update", nodes[i], nodes[j], k_node,
                             wire(current)], "reject",
                            "Going through %s is no shorter, so %s to "
                            "%s stays at %s."
                            % (k_node, nodes[i], nodes[j], wire(current)),
                            "Most checks end this way. The table only "
                            "changes when a genuinely better route "
                            "turns up.",
                            indices=[nodes[i], nodes[j], k_node],
                            values=[wire(current)], line="keep",
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
    return log.payload()
