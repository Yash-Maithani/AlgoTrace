"""Kruskal's minimum spanning forest, with union-find.

Called by POST /run_kruskal with the node list and the edges already
checked: `edges` is a list of (u, v, weight) with both ends in `nodes`.
"""
from .steps import StepLog


def kruskal(nodes, edges):
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

    ordered = sorted(edges, key=lambda e: e[2])
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
    return log.payload()
