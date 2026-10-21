"""Prim's minimum spanning tree, grown from one start node with a heapq heap.

Called by POST /run_prim with a graph already checked. A graph in more than
one piece gives the tree of the start node's piece, and the final step says
so.
"""
import heapq

from .steps import StepLog


def prim(graph, start):
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

    return log.payload()
