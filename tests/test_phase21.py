"""Phase 21: A* on a grid.

The path is checked against a breadth-first search, which finds a shortest
path on a grid of unit moves by itself: on 400 random grids A* finds a path
exactly when BFS does, of the same length, through free cells one move
apart. A* never expands more cells than Dijkstra (the same code, h = 0) on
the same grid. Also the tie-break, stale entries, the endpoint's refusals,
the lesson's figures and cases measured, the presets, the Predict question,
and the pages. The page in a real browser is tests/test_browser_phase21.py;
the C, C++ and Java translations are tests/test_reference_grid.py.
"""
import json
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
from collections import deque

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from app import app, GRAPH_PICKER, graph_algo_dict, GRID_ROWS, GRID_COLS
from grid_algorithms.astar import astar, heap_push, heap_pop
from test_phase11 import check_growth

NODE = shutil.which('node')
needs_node = pytest.mark.skipif(NODE is None, reason='node is not installed')


@pytest.fixture(scope='module')
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def bfs_length(rows, cols, walls, start, goal):
    seen = {start: 0}
    todo = deque([start])
    while todo:
        cell = todo.popleft()
        if cell == goal:
            return seen[cell]
        for dr, dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):
            nb = (cell[0] + dr, cell[1] + dc)
            if 0 <= nb[0] < rows and 0 <= nb[1] < cols and nb not in walls and nb not in seen:
                seen[nb] = seen[cell] + 1
                todo.append(nb)
    return None


def random_grid(rng):
    rows, cols = rng.randint(5, 20), rng.randint(6, 30)
    density = rng.choice([0.0, 0.1, 0.2, 0.3, 0.4, 0.5])
    walls = {(r, c) for r in range(rows) for c in range(cols) if rng.random() < density}
    free = [(r, c) for r in range(rows) for c in range(cols) if (r, c) not in walls]
    start, goal = rng.sample(free, 2)
    return rows, cols, walls, start, goal


def run(rows, cols, walls, start, goal, heuristic='manhattan'):
    steps, stats = [], {}
    path = astar(rows, cols, walls, start, goal, steps.append, heuristic, stats)
    return path, steps, stats


# ---------------------------------------------------------------------------
# Correctness
# ---------------------------------------------------------------------------

def test_paths_are_shortest_and_valid_and_no_path_is_detected():
    rng = random.Random(2111)
    seen_none = 0
    for _ in range(400):
        rows, cols, walls, start, goal = random_grid(rng)
        want = bfs_length(rows, cols, walls, start, goal)
        for heuristic in ('manhattan', 'zero'):
            path, steps, stats = run(rows, cols, walls, start, goal, heuristic)
            if want is None:
                assert path is None
                assert steps[-1]['line'] == 'no-path'
                continue
            assert path[0] == start and path[-1] == goal
            assert len(path) - 1 == want
            assert all(p not in walls for p in path)
            assert all(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1 for a, b in zip(path, path[1:]))
            assert steps[-1]['line'] == 'path' and steps[-1]['values'] == [want]
        seen_none += want is None
    assert seen_none > 10


def test_astar_never_expands_more_than_dijkstra():
    rng = random.Random(2112)
    fewer = 0
    for _ in range(400):
        grid = random_grid(rng)
        _, _, a = run(*grid)
        _, _, d = run(*grid, heuristic='zero')
        assert a['expanded'] <= d['expanded'], grid
        fewer += a['expanded'] < d['expanded']
    assert fewer > 200


def test_ties_break_by_f_then_h_then_order():
    stats = {'comparisons': 0}
    heap = []
    for entry in [(5, 2, 3), (5, 1, 4), (4, 3, 5), (5, 1, 2), (4, 3, 1)]:
        heap_push(heap, entry + ((0, 0), 0), stats)
    out = [heap_pop(heap, stats)[:3] for _ in range(5)]
    assert out == [(4, 3, 1), (4, 3, 5), (5, 1, 2), (5, 1, 4), (5, 2, 3)]


def test_every_expand_takes_the_best_live_entry():
    """The cell expanded is the first of its candidates, which are the live
    entries sorted by (f, h, order)."""
    rng = random.Random(2113)
    for _ in range(60):
        _, steps, _ = run(*random_grid(rng))
        for s in steps:
            if s['action'] == 'visit':
                assert s['candidates'][0]['cell'] == s['indices'][0]
                keys = [(c['f'], c['h']) for c in s['candidates']]
                assert keys == sorted(keys)
                assert len({c['cell'] for c in s['candidates']}) == len(s['candidates']) <= 4


def test_stale_entries_are_skipped():
    rng = random.Random(2114)
    stale = 0
    for _ in range(200):
        path, steps, stats = run(*random_grid(rng))
        stale += sum(1 for s in steps if s['line'] == 'stale')
        expanded = [s['indices'][0] for s in steps if s['action'] == 'visit']
        assert len(expanded) == len(set(expanded)) == stats['expanded']
    # With h steering the search a cell can first be reached the long way
    # round and improve while it waits, so older entries really do occur.
    assert stale > 0


def test_the_lesson_worked_example():
    path, _, a = run(3, 4, {(1, 1), (1, 2)}, (1, 0), (1, 3))
    _, _, d = run(3, 4, {(1, 1), (1, 2)}, (1, 0), (1, 3), 'zero')
    assert len(path) - 1 == 5 and a['expanded'] == 6 and d['expanded'] == 10
    assert a['comparisons'] == 5 and d['comparisons'] == 8


# ---------------------------------------------------------------------------
# The endpoint
# ---------------------------------------------------------------------------

def post(client, body):
    return client.post('/run_astar', data=json.dumps(body), content_type='application/json')


BASE = {'rows': 6, 'cols': 8, 'walls': [[2, 3], [3, 3]], 'start': [2, 1], 'goal': [2, 6]}


def test_endpoint_runs_both_and_compares(client):
    body = post(client, BASE).get_json()
    r = body['result']
    assert body['heuristic'] == 'manhattan' and r['found'] and r['length'] == 7
    assert r['other']['heuristic'] == 'zero' and r['other']['length'] == 7
    assert r['expanded'] < r['other']['expanded']
    d = post(client, dict(BASE, heuristic='zero')).get_json()['result']
    assert d['expanded'] == r['other']['expanded'] and d['other']['expanded'] == r['expanded']


@pytest.mark.parametrize('change,message', [
    ({'rows': 4}, 'The grid needs 5 to 20 rows.'),
    ({'cols': 31}, 'The grid needs 6 to 30 columns.'),
    ({'start': [9, 9]}, 'outside the 6 by 8 grid'),
    ({'goal': [2, 1]}, 'must be different cells'),
    ({'walls': [[2, 1]]}, 'cannot be walls'),
    ({'heuristic': 'euclid'}, 'The heuristic is manhattan'),
    ({'start': 'A'}, 'must be a cell'),
])
def test_endpoint_refusals(client, change, message):
    r = post(client, dict(BASE, **change))
    assert r.status_code == 400 and message in r.get_json()['error']


# ---------------------------------------------------------------------------
# The lesson's cases, measured in heap comparisons
# ---------------------------------------------------------------------------

def comparisons(k, kind):
    """Heap comparisons on a k by k grid of each case. No frames are built:
    the count is the heap's own work either way."""
    s = {}
    if kind == 'best':
        astar(k, k, set(), (k // 2, k // 2), (k // 2, k // 2 + 1), None, 'manhattan', s)
    elif kind == 'average':
        mid = k // 2
        walls = {(r, mid) for r in range(1, k)}
        astar(k, k, walls, (k - 1, mid - 1), (k - 1, mid + 1), None, 'manhattan', s)
    else:
        astar(k, k, {(k - 2, k - 1), (k - 1, k - 2)}, (0, 0), (k - 1, k - 1), None, 'manhattan', s)
    return s['comparisons']


@pytest.mark.slow
@pytest.mark.parametrize('case', ['best', 'average', 'worst'])
def test_cases_grow_as_their_theta(case):
    samples = []
    for k in (32, 48, 64, 96, 128):
        V = k * k
        bound = 1.0 if case == 'best' else V * math.log2(V)
        samples.append((comparisons(k, case), V, bound))
    check_growth('astar %s' % case, '1' if case == 'best' else 'V log V', samples)


_LESSONS = None


def lesson():
    global _LESSONS
    if _LESSONS is None:
        out = subprocess.run([NODE, os.path.join(HERE, 'dump_lessons.js')],
                             capture_output=True, text=True, encoding='utf-8', check=True)
        _LESSONS = json.loads(out.stdout)
    return _LESSONS['astar']['resolved']['']


@needs_node
def test_lesson_bounds_and_notes():
    c = lesson()['complexity']
    assert [c['time'][k]['theta'] for k in ('best', 'average', 'worst')] == ['1', 'V log V', 'V log V']
    assert c['overall'] == {'O': 'V log V', 'Omega': '1', 'Theta': None}
    assert c['growth'] == 'nlogn' and c['growthBasis'].startswith('V')
    assert 'never overestimates' in c['countsNote'] and '|dr| + |dc|' in c['countsNote']
    assert 'heap' in c['space']['what']
    assert c['worked']['comparisons'] == 6
    ids = {line['id'] for line in lesson()['code']['python'] if line['id']}
    rng = random.Random(2115)
    for _ in range(30):
        for s in run(*random_grid(rng))[1]:
            assert s['line'] in ids


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------

@needs_node
def test_presets_do_what_their_names_say():
    script = ("const G=require('./static/js/gridstage.js');const out=[];"
              "for(const [r,c] of [[5,6],[8,10],[12,20],[9,7],[20,30],[15,11]])"
              "for(const k of Object.keys(G.PRESETS))out.push([k,r,c,G.PRESETS[k](r,c)]);"
              "console.log(JSON.stringify(out))")
    out = json.loads(subprocess.run([NODE, '-e', script], capture_output=True, text=True,
                                    cwd=ROOT, check=True).stdout)
    for name, rows, cols, p in out:
        walls = {tuple(w) for w in p['walls']}
        start, goal = tuple(p['start']), tuple(p['goal'])
        assert start != goal and start not in walls and goal not in walls, (name, rows, cols)
        assert all(0 <= r < rows and 0 <= c < cols for r, c in walls | {start, goal})
        length = bfs_length(rows, cols, walls, start, goal)
        if name == 'nopath':
            assert length is None
        else:
            assert length is not None
        if name == 'empty':
            assert not walls and length == abs(start[1] - goal[1])
        if name == 'gap':
            assert length > abs(start[1] - goal[1]) + abs(start[0] - goal[0])
        if name == 'maze':
            # The path winds through the corridors: far longer than straight.
            assert length >= (rows // 2) * (cols - 1)


# ---------------------------------------------------------------------------
# Predict: which cell is expanded next
# ---------------------------------------------------------------------------

@needs_node
def test_predict_options_come_from_the_open_set():
    rng = random.Random(2116)
    runs = []
    for k in range(30):
        _, steps, _ = run(*random_grid(rng), heuristic=rng.choice(['manhattan', 'zero']))
        runs.append({'id': 'grid|%d' % k, 'family': 'grid', 'metas': steps})
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(runs, f)
    try:
        out = subprocess.run([NODE, os.path.join(HERE, 'predict_check.js'), f.name],
                             capture_output=True, text=True, encoding='utf-8', check=True)
    finally:
        os.unlink(f.name)
    questions = json.loads(out.stdout)
    seen = 0
    for run_ in runs:
        for q in questions[run_['id']]:
            step = run_['metas'][q['step']]
            assert q['kind'] == 'grid-expand' and step['action'] == 'visit'
            assert q['prompt'].endswith('Which cell is expanded next?')
            ids = [o['id'] for o in q['options']]
            cands = {c['cell']: c for c in step['candidates']}
            assert 2 <= len(ids) <= 4 and set(ids) == set(cands)
            assert q['answer'] == step['indices'][0] in ids
            assert ids == sorted(ids, key=lambda i: tuple(map(int, i.split(','))))
            for o in q['options']:
                c = cands[o['id']]
                assert o['label'] == '(%s): f %d, h %d' % (o['id'].replace(',', ', '), c['f'], c['h'])
            seen += 1
    assert seen > 100


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def test_the_grid_page_is_in_the_graphs_picker(client):
    assert graph_algo_dict['astar'] == 'astar'
    assert ('astar', 'A* on a grid', 'Shortest path, steered towards the goal.') in GRAPH_PICKER
    html = client.get('/graph?algo=astar').get_data(as_text=True)
    assert 'id="grid-board"' in html and 'data-grid-preset="nopath"' in html
    assert 'id="run-dijkstra"' in html and 'Run Dijkstra on the same grid' in html
    assert 'js/gridstage.js' in html and 'js/lessons/astar.js' in html
    for key, _, _ in GRAPH_PICKER:
        assert '?algo=%s' % key in html
    assert 'aria-current="page"' in html.split('?algo=astar', 1)[1][:200]
    stage = html.split('id="stage"', 1)[1].split('class="control-bar"', 1)[0]
    assert 'id="grid-board"' in stage
    other = client.get('/graph?algo=bfs').get_data(as_text=True)
    assert '?algo=astar' in other
    nav = html.split('class="nav-links"', 1)[1].split('</div>', 1)[0]
    assert 'astar' not in nav and 'A*' not in nav


def test_learn_home_and_counts(client):
    import re
    html = client.get('/learn').get_data(as_text=True)
    order = re.findall(r'class="order-name"[^>]*>([^<]+)</a>', html)
    assert len(order) == 20
    assert order.index('A* Search') == order.index("Dijkstra's Algorithm") + 1
    assert '<h3>A* Search</h3>' in html
    home = client.get('/').get_data(as_text=True)
    assert '<span class="track-meta">%d algorithms</span>' % len(GRAPH_PICKER) in home
    assert len(GRAPH_PICKER) == len(graph_algo_dict) == 9
    assert GRID_ROWS == (5, 20) and GRID_COLS == (6, 30)
