"""Measure how much work a graph endpoint does, without changing it.

The endpoints read a JSON body. Here they are handed the same body built
from two counting types instead:

  Node    a str that counts every hash and every equality test made on it,
          which is every set or dict look-up and every step of a list scan
          such as `neighbor not in queue`
  Weight  an int that counts every comparison made on it, which is every
          comparison a sort or a heap makes between edges

so the count is the endpoint's own work on that input, read off the real
code. Floyd-Warshall and Bellman-Ford index their tables by position and
add fresh numbers, so for those the count is the pairs and edges they
examine, which their step logs record one by one.

Used by tests/unit/test_theta_measured.py.
"""
import contextlib

from wsgi import app
from algotrace.routes import graphs as routes

COUNT = [0]
# Set while measuring Kruskal: count only the comparisons between weights.
WEIGHT_ONLY = [False]


class Node(str):
    def __hash__(self):
        if not WEIGHT_ONLY[0]:
            COUNT[0] += 1
        return str.__hash__(self)

    def __eq__(self, other):
        if not WEIGHT_ONLY[0]:
            COUNT[0] += 1
        return str.__eq__(self, other)

    def __ne__(self, other):
        if not WEIGHT_ONLY[0]:
            COUNT[0] += 1
        return str.__ne__(self, other)


class Weight(int):
    def _count(op):
        def compare(self, other):
            COUNT[0] += 1
            return getattr(int, op)(self, other)
        return compare

    __lt__ = _count('__lt__')
    __le__ = _count('__le__')
    __gt__ = _count('__gt__')
    __ge__ = _count('__ge__')
    __eq__ = _count('__eq__')
    __ne__ = _count('__ne__')
    __hash__ = int.__hash__
    del _count


class _Request:
    def __init__(self, body):
        self.json = body


@contextlib.contextmanager
def _posted(body):
    real = routes.request
    routes.request = _Request(body)
    try:
        with app.app_context():
            yield
    finally:
        routes.request = real


ENDPOINTS = {
    'bfs': routes.run_bfs,
    'dfs': routes.run_dfs,
    'dijkstra': routes.run_dijkstra,
    'prim': routes.run_prim,
    'kruskal': routes.run_kruskal,
    'floyd_warshall': routes.run_floyd_warshall,
    'bellman_ford': routes.run_bellman_ford,
}

# The two table driven algorithms log one step per unit of work: a pair of
# nodes tried through a stopping point (either a `consider` step, or a
# `no_path_via_k` step when one leg is missing), or an edge checked.
EXAMINED = {
    'floyd_warshall': lambda step, meta: (meta['action'] == 'consider'
                                          or step[0] == 'no_path_via_k'),
    'bellman_ford': lambda step, meta: meta['action'] == 'consider',
}


def names(count):
    return [Node('N%d' % i) for i in range(count)]


def body_for(algo, nodes, edges, start=None):
    """The request body each endpoint expects, from one undirected edge list.

    nodes  list of Node
    edges  list of (u, v, weight) with u, v from nodes, weight an int
    """
    start = nodes[0] if start is None else start
    weighted = [(u, v, Weight(w)) for u, v, w in edges]
    if algo in ('bfs', 'dfs'):
        adjacency = {n: [] for n in nodes}
        for u, v, _ in weighted:
            adjacency[u].append(v)
            adjacency[v].append(u)
        return {'graph': adjacency, 'start': start}
    if algo in ('dijkstra', 'prim', 'bellman_ford'):
        adjacency = {n: {} for n in nodes}
        for u, v, w in weighted:
            adjacency[u][v] = w
            adjacency[v][u] = w
        return {'graph': adjacency, 'start': start}
    return {'nodes': list(nodes), 'edges': [[u, v, w] for u, v, w in weighted]}


def measure(algo, nodes, edges, start=None):
    """Run the real endpoint and return (work counted, response payload)."""
    body = body_for(algo, nodes, edges, start)
    COUNT[0] = 0
    with _posted(body):
        response = ENDPOINTS[algo]()
    work = COUNT[0]
    payload = response.get_json()
    assert 'error' not in payload, payload
    if algo in EXAMINED:
        work = sum(1 for step, meta in zip(payload['steps'], payload['meta'])
                   if EXAMINED[algo](step, meta))
    return work, payload
