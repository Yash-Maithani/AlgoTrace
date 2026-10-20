"""Phase 13: the C, C++ and Java graph programs behave exactly like the
seven /run_* endpoints.

Each program is compiled and fed every graph request recorded in
tests/baseline_graphs.json, plus generated graphs chosen to hit the places
a translation drifts from Python without failing loudly: tied distances
(Dijkstra's input order tie-break), tied weights (Kruskal's stable sort,
Prim's full tuple comparison), negative weights and negative cycles
(Bellman-Ford, Floyd-Warshall), disconnected graphs (infinity on the wire)
and neighbours listed in an order other than sorted. Every meta entry the
endpoint returns (action, line id, nodes, values) and the final result
must match line for line.

Marked slow, like the Phase 12 compile tests.
"""
import json
import os
import random
import shutil
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from app import app
from test_reference_code import compile_program, _require  # noqa: F401

pytestmark = pytest.mark.slow

with open(os.path.join(HERE, 'baseline_graphs.json'), encoding='utf-8') as fh:
    BASELINE = json.load(fh)

INF = '∞'
GRAPHS = ['bfs', 'dfs', 'dijkstra', 'prim', 'kruskal', 'bellman_ford', 'floyd_warshall',
          'topological_sort']
KIND = {
    'bfs': 'lists', 'dfs': 'lists',
    'dijkstra': 'weighted', 'prim': 'weighted', 'bellman_ford': 'weighted',
    'kruskal': 'edges', 'floyd_warshall': 'edges',
    'topological_sort': 'arrows',
}


# ---------------------------------------------------------------------------
# What the endpoint says
# ---------------------------------------------------------------------------

def _value(v):
    return INF if v == INF else str(v)


def post(algo, request):
    """POST the body exactly as written. The test client's json= sorts the
    keys, but a browser sends them in insertion order, and the endpoints
    walk neighbours in the order they arrive."""
    client = app.test_client()
    return client.post('/run_' + algo, data=json.dumps(request),
                       content_type='application/json').get_json()


def expected_lines(algo, request):
    """The endpoint's meta as trace lines, then its result, then `end`."""
    payload = post(algo, request)
    assert 'error' not in payload, payload
    lines = []
    for meta in payload['meta']:
        words = ['step', meta['action'], meta['line'] or '-']
        words += [str(i) for i in meta['indices']]
        words.append('|')
        words += [_value(v) for v in meta['values']]
        lines.append(' '.join(words))

    # Bellman-Ford's result is its summary fields, and a one node graph
    # gives it no steps at all.
    final = payload['steps'][-1] if algo != 'bellman_ford' else None
    if algo in ('bfs', 'dfs'):
        lines.append(' '.join(['path'] + final[1]))
    elif algo == 'topological_sort':
        lines.append(' '.join(['order'] + payload['order']))
        lines.append(' '.join(['remaining'] + payload['remaining']))
        lines.append(' '.join(['cycle'] + payload['cycle']))
    elif algo == 'dijkstra':
        # Maps in the order they reach the browser: jsonify sorts the keys.
        for node in sorted(final[1]):
            lines.append('distance %s %s' % (node, _value(final[1][node])))
        for node in sorted(final[2]):
            lines.append(' '.join(['path', node] + final[2][node]))
    elif algo in ('prim', 'kruskal'):
        for u, v, w in final[1]:
            lines.append('edge %s %s %s' % (u, v, w))
        lines.append('total %s' % final[2])
    elif algo == 'floyd_warshall':
        for node, row in zip(final[2], final[1]):
            lines.append(' '.join(['row', node] + [_value(d) for d in row]))
        for key in sorted(final[3]):
            entry = final[3][key]
            route = entry['path']
            lines.append(' '.join(['path', route[0], route[-1], _value(entry['distance'])] + route))
    else:
        # Built from a Python set, so only a sorted order is reproducible.
        for node in sorted(payload['distances']):
            lines.append('distance %s %s' % (node, _value(payload['distances'][node])))
        lines.append('negative_cycle %s' % ('true' if payload['has_negative_cycle'] else 'false'))
        lines.append('iterations %d' % payload['iterations'])
    lines.append('end')
    return lines


# ---------------------------------------------------------------------------
# The requests
# ---------------------------------------------------------------------------

def to_input(algo, request):
    """One case in the graph format of reference_code/README.md."""
    kind = KIND[algo]
    out = []
    if kind == 'edges':
        out.append('-')
        out.append(str(len(request['nodes'])))
        out += ['%s 0' % node for node in request['nodes']]
        out.append(str(len(request['edges'])))
        out += ['%s %s %d' % (u, v, w) for u, v, w in request['edges']]
        return out
    graph = request['graph']
    out.append(request.get('start', '-'))
    out.append(str(len(graph)))
    for node, nbrs in graph.items():
        if kind in ('lists', 'arrows'):
            pairs = ['%s 1' % n for n in nbrs]
        else:
            pairs = ['%s %d' % (n, w) for n, w in nbrs.items()]
        out.append(' '.join(['%s %d' % (node, len(pairs))] + pairs))
    out.append('0')
    return out


def _names(n, rng):
    """Node names, shuffled so input order is never alphabetical order."""
    names = ['N%02d' % i for i in range(n)]
    rng.shuffle(names)
    return names


def _random_edges(rng, names, density, low, high):
    edges = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if rng.random() < density:
                edges.append((a, b, rng.randint(low, high)))
    rng.shuffle(edges)
    return edges


def generated(algo, count=24):
    rng = random.Random(GRAPHS.index(algo) + 7)
    out = []
    for c in range(count):
        n = rng.randint(1, 12)
        names = _names(n, rng)
        # Few distinct weights, so ties are everywhere.
        low, high = (1, 3) if c % 2 else (1, 9)
        if algo in ('bellman_ford', 'floyd_warshall') and c % 3 == 0:
            low = -4
        edges = _random_edges(rng, names, rng.choice([0.2, 0.45, 0.8]), low, high)
        if algo == 'floyd_warshall' and edges and c % 4 == 1:
            edges.append(edges[0][:2] + (edges[0][2] - 1,))   # a cheaper parallel edge
        if KIND[algo] == 'edges':
            out.append({'nodes': names, 'edges': [list(e) for e in edges]})
            continue
        if KIND[algo] == 'arrows':
            out.append({'graph': arrow_graph(rng, names, edges, c)})
            continue
        adjacency = {name: ({} if KIND[algo] == 'weighted' else []) for name in names}
        for a, b, w in edges:
            if algo == 'bellman_ford' and c % 3 == 0:
                # Directed, so a negative edge makes a cycle only sometimes.
                adjacency[a][b] = w
                continue
            if KIND[algo] == 'weighted':
                adjacency[a][b] = w
                adjacency[b][a] = w
            else:
                adjacency[a].append(b)
                adjacency[b].append(a)
        if algo == 'bellman_ford' and c % 6 == 0 and n >= 3:
            # A directed loop weighing -3 in all: a negative cycle for sure.
            a, b, d = names[:3]
            adjacency[a][b], adjacency[b][d], adjacency[d][a] = 1, 1, -5
        for name in names:
            # Neighbour order as given, never sorted.
            items = list(adjacency[name].items()) if KIND[algo] == 'weighted' else list(adjacency[name])
            rng.shuffle(items)
            adjacency[name] = dict(items) if KIND[algo] == 'weighted' else items
        out.append({'graph': adjacency, 'start': names[rng.randrange(n)]})
    return out


def arrow_graph(rng, names, edges, c):
    """A directed graph for Kahn's algorithm. Arrows run from earlier to later
    in a shuffled order, so the graph has no cycle, except that every third
    case adds arrows back (a cycle, sometimes with nodes waiting on it), and
    some add a self loop or a repeated arrow."""
    graph = {name: [] for name in names}
    for a, b, _ in edges:
        graph[a].append(b)
    if c % 3 == 0 and len(names) >= 3:
        k = rng.randint(2, len(names) - 1)
        graph[names[k]].append(names[rng.randrange(k)])
    if c % 7 == 1 and names:
        graph[names[-1]].append(names[-1])
    if c % 5 == 2 and edges:
        graph[edges[0][0]].append(edges[0][1])
    for name in names:
        rng.shuffle(graph[name])
    return graph


def requests_for(algo):
    recorded = [r['request'] for r in BASELINE['responses'] if r['endpoint'] == '/run_' + algo]
    return recorded + generated(algo)


# ---------------------------------------------------------------------------
# Running
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def build_dir(tmp_path_factory):
    return tmp_path_factory.mktemp('reference_graphs')


@pytest.mark.parametrize('language', ['c', 'cpp', 'java'])
@pytest.mark.parametrize('algo', GRAPHS)
def test_graph_program_matches_the_endpoint(language, algo, build_dir):
    run = compile_program(language, algo, build_dir)
    requests = requests_for(algo)
    cases = [(req, expected_lines(algo, req)) for req in requests]
    text = '\n'.join([str(len(cases))] + [line for req, _ in cases for line in to_input(algo, req)]) + '\n'
    result = subprocess.run(run, input=text.encode('utf-8'), capture_output=True, timeout=120)
    output = result.stdout.decode('utf-8')
    assert result.returncode == 0, output[-2000:] + result.stderr.decode('utf-8', 'replace')

    got = output.replace('\r\n', '\n').split('\n')
    if got and got[-1] == '':
        got.pop()
    position = 0
    for request, expected in cases:
        actual = got[position:position + len(expected)]
        if actual != expected:
            k = next((i for i, (a, e) in enumerate(zip(actual, expected)) if a != e),
                     min(len(actual), len(expected)))
            pytest.fail('%s %s differs from /run_%s on %s\nline %d: got %r\n        want %r'
                        % (language, algo, algo, json.dumps(request), k,
                           actual[k] if k < len(actual) else None,
                           expected[k] if k < len(expected) else None))
        position += len(expected)
    assert position == len(got), 'extra output after the last case'


def test_generated_graphs_hit_the_traps():
    """The generated set really contains what it is there to test."""
    bf = generated('bellman_ford')
    cycles = [post('bellman_ford', r)['has_negative_cycle'] for r in bf]
    assert any(cycles) and not all(cycles)
    kruskal = generated('kruskal')
    assert any(len({w for _, _, w in r['edges']}) < len(r['edges']) for r in kruskal), 'no tied weights'
    finals = [post('dijkstra', r)['steps'][-1][1] for r in generated('dijkstra')]
    assert any('∞' in d.values() for d in finals), 'no unreachable node'
    fw = [post('floyd_warshall', r)['steps'][-1][1] for r in generated('floyd_warshall')]
    assert any(any(min(v for v in row if v != '∞') < 0 for row in m if any(v != '∞' for v in row))
               for m in fw), 'no negative distance'


def test_generated_directed_graphs_hit_the_traps():
    """Some generated directed graphs have a cycle, some have nodes waiting on
    one, some are acyclic, and one has a self loop."""
    bodies = [post('topological_sort', r) for r in generated('topological_sort')]
    assert any(b['cycle'] for b in bodies) and any(not b['cycle'] for b in bodies)
    assert any(len(b['remaining']) > len(b['cycle']) for b in bodies)
    assert any(len(b['cycle']) == 1 for b in bodies)
