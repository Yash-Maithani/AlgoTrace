"""Topological sort (Phase 20): Kahn's algorithm on a directed graph.

The request is {graph: {node: [successors]}}: an arrow from every node to
each node in its list, keys in input order. Every step carries the whole
state (in-degrees, the queue of nodes with nothing left pointing at them,
the order so far), so the page can draw any step on its own.

Step arrays:
  ["count", u, v, in_degree]                the arrow u -> v is counted
  ["queue", v, queue, in_degree, order]     v reached in-degree 0
  ["remove", u, queue, in_degree, order]    u leaves the queue and is placed
  ["decrement", u, v, queue, in_degree, order]  u's arrow to v is removed
  ["final", order, remaining, cycle]        the result; remaining and cycle
                                            are empty when every node fitted

Called by POST /run_topological_sort with a graph already checked: every
key maps to a list of nodes that are keys too.
"""
from collections import deque

from .steps import StepLog


def _find_cycle(graph, remaining):
    """One cycle among the nodes Kahn could not place.

    Every node left over still has an arrow coming in from another node left
    over (its in-degree never reached 0), so walking backwards along those
    arrows from the first one must come round to a node already walked. The
    walk always takes the first such arrow in input order, so the answer is
    the same every time. Returned in the direction the arrows point."""
    left = set(remaining)
    first_in = {}
    for u in graph:
        if u not in left:
            continue
        for v in graph[u]:
            if v in left and v not in first_in:
                first_in[v] = u
    walk = []
    seen = set()
    node = remaining[0]
    while node not in seen:
        seen.add(node)
        walk.append(node)
        node = first_in[node]
    loop = walk[walk.index(node):]
    loop.reverse()
    # Start from the node of the loop that comes first in the input.
    position = {u: k for k, u in enumerate(graph)}
    first = min(range(len(loop)), key=lambda k: position[loop[k]])
    return loop[first:] + loop[:first]


def topological_sort(graph):
    log = StepLog()
    why_count = ("A node can only go once nothing still points at it, so "
                 "the first job is to count the arrows coming into each node.")

    in_degree = {u: 0 for u in graph}
    for u in graph:
        for v in graph[u]:
            in_degree[v] += 1
            log.add(["count", u, v, dict(in_degree)], "consider",
                    "The arrow %s → %s comes into %s, so %s's in-degree is "
                    "now %d." % (u, v, v, v, in_degree[v]), why_count,
                    indices=[u, v], values=[in_degree[v]], line="count",
                    variables={"in_degree": dict(in_degree), "queue": [], "order": []})

    queue = deque()
    order = []

    def state():
        return {"in_degree": dict(in_degree), "queue": list(queue), "order": list(order)}

    for u in graph:
        if in_degree[u] == 0:
            queue.append(u)
            log.add(["queue", u, list(queue), dict(in_degree), list(order)], "enqueue",
                    "No arrow comes into %s, so it can go first. It joins the "
                    "queue." % u,
                    "A node with in-degree 0 depends on nothing still waiting, "
                    "so it is safe to place now.",
                    indices=[u], values=[0], line="seed", variables=state())

    while queue:
        u = queue.popleft()
        order.append(u)
        log.add(["remove", u, list(queue), dict(in_degree), list(order)], "visit",
                "Take %s from the front of the queue and place it %s in the "
                "order." % (u, _ordinal(len(order))),
                "Everything that had to come before %s is already placed, so "
                "putting it next cannot break any arrow." % u,
                indices=[u], values=[len(order)], line="remove", variables=state())
        for v in graph[u]:
            in_degree[v] -= 1
            log.add(["decrement", u, v, list(queue), dict(in_degree), list(order)],
                    "consider",
                    "%s is placed, so its arrow to %s no longer counts. %s's "
                    "in-degree drops to %d." % (u, v, v, in_degree[v]),
                    "Removing a placed node's arrows is how the nodes that "
                    "were waiting on it become free.",
                    indices=[u, v], values=[in_degree[v]], line="decrement",
                    variables=state())
            if in_degree[v] == 0:
                queue.append(v)
                log.add(["queue", v, list(queue), dict(in_degree), list(order)],
                        "enqueue",
                        "%s has no arrows left coming in, so it joins the back "
                        "of the queue." % v,
                        "Every node %s waited on is now placed." % v,
                        indices=[v], values=[0], line="enqueue", variables=state())

    if len(order) == len(graph):
        log.add(["final", list(order), [], []], "done",
                "Every node is placed. A valid order: %s." % ", ".join(order),
                "Each node came after every node with an arrow into it, which "
                "is all a topological order asks.",
                indices=list(order), line=None, variables=state())
        return log.payload(order=order, remaining=[], cycle=[])

    remaining = [u for u in graph if in_degree[u] > 0]
    cycle = _find_cycle(graph, remaining)
    loop = " → ".join(cycle + [cycle[0]])
    waiting = [u for u in remaining if u not in cycle]
    told = ("No order exists. %s %s left, %s an arrow still coming in. "
            "%s is a cycle, so none of its nodes can ever reach in-degree 0."
            % (_name_list(remaining), "is" if len(remaining) == 1 else "are",
               "with" if len(remaining) == 1 else "each with", loop))
    if waiting:
        told += " %s %s on the cycle, so %s cannot be placed either." % (
            _name_list(waiting), "waits" if len(waiting) == 1 else "wait",
            "it" if len(waiting) == 1 else "they")
    log.add(["final", list(order), remaining, cycle], "done", told,
            "A topological order puts every node after the nodes that point "
            "at it, and round a cycle each node would have to come after itself.",
            indices=remaining, values=[], line="cycle", variables=state())
    return log.payload(order=order, remaining=remaining, cycle=cycle)


def _ordinal(k):
    if 10 <= k % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(k % 10, "th")
    return "%d%s" % (k, suffix)


def _name_list(names):
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]
