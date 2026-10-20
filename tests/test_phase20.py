"""Phase 20: Topological Sort (Kahn's algorithm) and directed graphs.

The endpoint is checked against what a topological order means: on many
random graphs with no cycle every arrow u -> v has u before v and every node
is placed; on graphs with a cycle the run stops, names the nodes left, and
the cycle it reports really is one. Also the step meta, the figures the
lesson states, Theta(V + E) measured, the Predict question, and the pages.
The page in a real browser is tests/test_browser_phase20.py; the C, C++ and
Java translations are in tests/test_reference_graphs.py.
"""
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from app import app, GRAPH_ACTIONS, graph_algo_dict, sorting_algo_dict, SEARCH_ALGORITHMS
from test_phase11 import check_growth

NODE = shutil.which('node')
needs_node = pytest.mark.skipif(NODE is None, reason='node is not installed')


@pytest.fixture(scope='module')
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def post(client, graph):
    """Send the body as a browser does, keys in insertion order."""
    return client.post('/run_topological_sort', data=json.dumps({'graph': graph}),
                       content_type='application/json').get_json()


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return f.read()


def random_dag(rng, n, density):
    names = ['N%02d' % i for i in range(n)]
    rank = names[:]
    rng.shuffle(rank)                        # the hidden order arrows respect
    graph = {name: [] for name in rng.sample(names, n)}     # input order shuffled too
    for i, a in enumerate(rank):
        for b in rank[i + 1:]:
            if rng.random() < density:
                graph[a].append(b)
    for name in graph:
        rng.shuffle(graph[name])
    return graph


def arrows(graph):
    return [(u, v) for u in graph for v in graph[u]]


# ---------------------------------------------------------------------------
# Correctness
# ---------------------------------------------------------------------------

def test_every_order_respects_every_arrow(client):
    rng = random.Random(2001)
    for case in range(300):
        graph = random_dag(rng, rng.randint(1, 14), rng.choice([0.0, 0.15, 0.4, 0.9]))
        body = post(client, graph)
        order = body['order']
        assert sorted(order) == sorted(graph), graph
        place = {u: k for k, u in enumerate(order)}
        assert all(place[u] < place[v] for u, v in arrows(graph)), (graph, order)
        assert body['remaining'] == [] and body['cycle'] == []
        assert body['steps'][-1] == ['final', order, [], []]


def test_kahn_takes_the_queue_in_order(client):
    """No arrows: every node has in-degree 0 and joins the queue in input order."""
    body = post(client, {'C': [], 'A': [], 'B': []})
    assert body['order'] == ['C', 'A', 'B']
    body = post(client, {'A': ['B', 'C'], 'B': ['D'], 'C': ['D'], 'D': ['E'], 'E': []})
    assert body['order'] == ['A', 'B', 'C', 'D', 'E']


def is_cycle(graph, cycle):
    return bool(cycle) and all(cycle[(k + 1) % len(cycle)] in graph[u] for k, u in enumerate(cycle))


def test_a_cycle_stops_the_run_and_is_named(client):
    rng = random.Random(2002)
    seen_waiting = False
    for case in range(300):
        graph = random_dag(rng, rng.randint(2, 12), rng.choice([0.2, 0.5]))
        names = list(graph)
        # Plant a cycle: an arrow back along a chain of two or more nodes.
        loop = rng.sample(names, rng.randint(1, min(4, len(names))))
        for a, b in zip(loop, loop[1:] + loop[:1]):
            graph[a].append(b)
        body = post(client, graph)
        order, remaining, cycle = body['order'], body['remaining'], body['cycle']
        assert remaining, graph
        assert set(order) | set(remaining) == set(graph) and not set(order) & set(remaining)
        assert set(cycle) <= set(remaining)
        assert is_cycle(graph, cycle), (graph, cycle)
        assert remaining == [u for u in graph if u in remaining]        # input order
        # What was placed still respects the arrows among placed nodes.
        place = {u: k for k, u in enumerate(order)}
        assert all(place[u] < place[v] for u, v in arrows(graph) if u in place and v in place)
        # Every node left has an arrow in from another node left.
        assert all(any(v in graph[u] for u in remaining) for v in remaining)
        meta = body['meta'][-1]
        assert meta['action'] == 'done' and meta['line'] == 'cycle'
        told = meta['explain']['beginner']
        assert told.startswith('No order exists.')
        assert ' → '.join(cycle + [cycle[0]]) in told
        for u in remaining:
            assert u in told
        if len(remaining) > len(cycle):
            seen_waiting = True
            assert 'on the cycle, so' in told
    assert seen_waiting


def test_self_loop_and_repeated_arrows(client):
    body = post(client, {'A': ['A'], 'B': []})
    assert body['order'] == ['B'] and body['cycle'] == ['A']
    body = post(client, {'A': ['B', 'B'], 'B': []})
    assert body['order'] == ['A', 'B']


@pytest.mark.parametrize('graph,message', [
    ({'A': ['Z']}, 'Z has no node of its own'),
    ({'A': 'B'}, 'map every node to the list'),
    ({}, 'map every node to the list'),
])
def test_bad_graphs_are_refused(client, graph, message):
    r = client.post('/run_topological_sort', data=json.dumps({'graph': graph}),
                    content_type='application/json')
    assert r.status_code == 400 and message in r.get_json()['error']


# ---------------------------------------------------------------------------
# Step meta: in-degrees, the queue and the order on every step
# ---------------------------------------------------------------------------

def test_meta_follows_the_contract(client):
    rng = random.Random(2003)
    for _ in range(60):
        graph = random_dag(rng, rng.randint(1, 10), 0.4)
        if rng.random() < 0.3 and len(graph) > 1:
            a, b = rng.sample(list(graph), 2)
            graph[a].append(b)
            graph[b].append(a)
        body = post(client, graph)
        assert len(body['steps']) == len(body['meta'])
        for step, meta in zip(body['steps'], body['meta']):
            assert meta['action'] in GRAPH_ACTIONS
            v = meta['vars']
            assert set(v) == {'in_degree', 'queue', 'order'}
            assert set(v['in_degree']) == set(graph)
            if meta['line'] in ('count', 'decrement'):
                u, w = meta['indices']
                assert w in graph[u] and meta['values'] == [v['in_degree'][w]]
            if meta['line'] in ('seed', 'enqueue'):
                assert v['queue'][-1] == meta['indices'][0] and v['in_degree'][meta['indices'][0]] == 0
            if meta['line'] == 'remove':
                assert v['order'][-1] == meta['indices'][0] == step[1]
                assert meta['values'] == [len(v['order'])]


def test_a_graph_with_no_cycle_takes_exactly_2_v_plus_e_steps(client):
    rng = random.Random(2004)
    for _ in range(100):
        graph = random_dag(rng, rng.randint(1, 15), rng.choice([0.1, 0.5]))
        body = post(client, graph)
        assert len(body['steps']) == 2 * (len(graph) + len(arrows(graph))) + 1


# ---------------------------------------------------------------------------
# Theta(V + E), measured on the steps the endpoint logs
# ---------------------------------------------------------------------------

@pytest.mark.slow
@pytest.mark.parametrize('case', ['best', 'average', 'worst'])
def test_work_grows_as_v_plus_e(client, case):
    """Across a grid of sizes and densities the logged work stays within a
    constant of V + E, with or without a cycle, and as the graph grows it tracks
    V + E more closely than a log factor either way."""
    rng = random.Random(len(case))
    for n in (8, 32, 128):
        for density in (0.0, 0.05, 0.3, 0.8):
            graph = random_dag(rng, n, density)
            if case == 'worst' and n > 2:
                # A cycle at the very end of the order: almost everything is placed.
                a, b = rng.sample(list(graph), 2)
                graph[a].append(b)
                graph[b].append(a)
            work = len(post(client, graph)['steps'])
            size = n + len(arrows(graph))
            # The steps log every arrow counted (E) and at most two events per
            # node and per arrow. The V node checks of the seeding loop are
            # work the steps do not log, which is why the lesson's floor is
            # V + E while the floor here is E + 1.
            assert len(arrows(graph)) + 1 <= work <= 2 * size + 1, (n, density, work, size)
            if case != 'worst':
                assert size <= work
    samples = []
    for n in (16, 32, 64, 128, 256):
        graph = random_dag(rng, n, {'best': 0.0, 'average': 0.1, 'worst': 0.5}[case])
        work = len(post(client, graph)['steps'])
        size = n + len(arrows(graph))
        samples.append((work, n, size))
    check_growth('topological sort %s' % case, 'V plus E', samples)


# ---------------------------------------------------------------------------
# The lesson's figures
# ---------------------------------------------------------------------------

_LESSONS = None


def lesson():
    global _LESSONS
    if _LESSONS is None:
        out = subprocess.run([NODE, os.path.join(HERE, 'dump_lessons.js')],
                             capture_output=True, text=True, encoding='utf-8', check=True)
        _LESSONS = json.loads(out.stdout)
    return _LESSONS['topological_sort']['resolved']['']


@needs_node
def test_lesson_bounds_and_worked_example(client):
    c = lesson()['complexity']
    assert all(c['time'][k]['theta'] == 'V plus E' for k in ('best', 'average', 'worst'))
    assert c['overall'] == {'O': 'V plus E', 'Omega': 'V plus E', 'Theta': 'V plus E'}
    assert c['growth'] is None and 'O(V plus E)' in c['growthNote']
    assert c['space']['value'] == 'O(V)' and 'queue' in c['space']['what']
    assert 'Best, average and worst are cases' in c['misconception']
    body = post(client, {'A': ['B', 'C'], 'B': ['D'], 'C': ['D'], 'D': ['E'], 'E': []})
    assert c['worked']['input'] == 'A → B, A → C, B → D, C → D, D → E'
    assert c['worked']['comparisons'] == len(body['steps']) - 1 == 20
    assert 'the order A, B, C, D, E' in c['worked']['note']
    assert 'prerequisite' in lesson()['analogy']


@needs_node
def test_every_step_line_is_in_the_listing(client):
    ids = {line['id'] for line in lesson()['code']['python'] if line['id']}
    for graph in ({'A': ['B'], 'B': []}, {'A': ['B'], 'B': ['A'], 'C': ['A']}):
        for meta in post(client, graph)['meta']:
            assert meta['line'] is None or meta['line'] in ids


# ---------------------------------------------------------------------------
# Predict: which node is removed next
# ---------------------------------------------------------------------------

@needs_node
def test_predict_asks_which_node_is_removed_next(client):
    rng = random.Random(2005)
    runs = []
    for k in range(40):
        graph = random_dag(rng, rng.randint(3, 10), rng.choice([0.1, 0.3]))
        runs.append({'id': 'topo|%d' % k, 'family': 'graph', 'metas': post(client, graph)['meta']})
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(runs, f)
    try:
        out = subprocess.run([NODE, os.path.join(HERE, 'predict_check.js'), f.name],
                             capture_output=True, text=True, encoding='utf-8', check=True)
    finally:
        os.unlink(f.name)
    questions = json.loads(out.stdout)
    seen = 0
    for run in runs:
        for q in questions[run['id']]:
            now, step = run['metas'][q['step'] - 1], run['metas'][q['step']]
            assert q['kind'] == 'topo-remove'
            assert step['line'] == 'remove'
            assert q['prompt'].endswith('Which node is removed next?')
            assert [o['id'] for o in q['options']] == now['vars']['queue']
            assert len(q['options']) >= 2
            assert q['answer'] == step['indices'][0] == now['vars']['queue'][0]
            seen += 1
    assert seen > 20


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def test_graph_page_serves_topological_sort(client):
    assert graph_algo_dict['topological_sort'] == 'topological_sort'
    html = client.get('/graph?algo=topological_sort').get_data(as_text=True)
    assert 'Topological Sort on a graph' in html
    assert 'id="directed-format-guide"' in html
    assert 'id="topo-strip"' in html
    stage = html.split('id="stage"', 1)[1].split('class="control-bar"', 1)[0]
    assert 'id="topo-strip"' in stage
    assert 'js/lessons/topological_sort.js' in html
    assert 'aria-current="page"' in html.split('?algo=topological_sort', 1)[1][:200]


def test_other_graph_pages_have_no_strip_or_arrows(client):
    for algo in ('bfs', 'dijkstra', 'kruskal'):
        html = client.get('/graph?algo=' + algo).get_data(as_text=True)
        assert 'class="topo-strip sort-strip"' in html      # in the shared markup, hidden
        assert re.search(r'id="topo-strip"[^>]*hidden', html)


def test_learn_home_and_counts(client):
    html = client.get('/learn').get_data(as_text=True)
    order = re.findall(r'class="order-name"[^>]*>([^<]+)</a>', html)
    assert len(order) == 20                      # A* joined in Phase 21
    assert order.index('Topological Sort') == order.index('Depth-First Search') + 1
    assert '<h3>Topological Sort</h3>' in html
    home = client.get('/').get_data(as_text=True)
    assert '<span class="track-meta">%d algorithms</span>' % len(graph_algo_dict) in home
    assert len(graph_algo_dict) == 9                  # A* joined in Phase 21
    assert len(sorting_algo_dict) == 8 and len(SEARCH_ALGORITHMS) == 3
