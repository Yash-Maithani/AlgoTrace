"""Phase 22 fix: Predict options never give the answer away by position.

Builders whose options come from the run's own data (queues, stacks, open
sets, count slots, buckets, grid cells) list them by name or by position, not
in the order the algorithm will take them. Over many random runs of each
algorithm, no option position may hold the right answer more than about 60
percent of the time. Fixed pairs such as Yes and No keep one order, which
says nothing about which is right, so they are not measured here.

Also: no prompt says which end of a queue or stack is taken, and A* never
asks a question whose answer ties another option on both f and h.
"""
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
from collections import Counter

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from app import app, _sort_payload
from grid_algorithms.astar import astar

NODE = shutil.which('node')
pytestmark = pytest.mark.skipif(NODE is None, reason='node is not installed')


def post(path, body):
    with app.test_client() as c:
        return c.post(path, data=json.dumps(body), content_type='application/json').get_json()


def random_graph(rng, weighted):
    n = rng.randint(4, 9)
    names = ['N%d' % i for i in range(n)]
    rng.shuffle(names)
    g = {x: ({} if weighted else []) for x in names}

    def add(a, b):
        if b in g[a] or a == b:
            return
        w = rng.randint(1, 9)
        if weighted:
            g[a][b] = g[b][a] = w
        else:
            g[a].append(b)
            g[b].append(a)
    for i in range(1, n):
        add(names[rng.randrange(i)], names[i])
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < 0.3:
                add(names[i], names[j])
    return g, names[0]


def runs_for(algo, rng, count=60):
    out = []
    for k in range(count):
        if algo in ('bfs', 'dfs', 'dijkstra', 'prim'):
            g, start = random_graph(rng, algo in ('dijkstra', 'prim'))
            metas = post('/run_' + algo, {'graph': g, 'start': start})['meta']
            family = 'graph'
        elif algo == 'topological_sort':
            names = ['N%d' % i for i in range(rng.randint(4, 10))]
            rank = names[:]
            rng.shuffle(rank)
            g = {x: [] for x in names}
            for i, a in enumerate(rank):
                for b in rank[i + 1:]:
                    if rng.random() < 0.25:
                        g[a].append(b)
            metas = post('/run_topological_sort', {'graph': g})['meta']
            family = 'graph'
        elif algo in ('Counting Sort', 'Radix Sort'):
            values = [rng.randint(0, 99) for _ in range(rng.randint(4, 14))]
            metas = _sort_payload(algo, values)['steps']
            family = 'sorting'
        else:
            rows, cols = rng.randint(5, 12), rng.randint(6, 16)
            walls = {(r, c) for r in range(rows) for c in range(cols) if rng.random() < 0.2}
            free = [(r, c) for r in range(rows) for c in range(cols) if (r, c) not in walls]
            s, t = rng.sample(free, 2)
            metas = []
            astar(rows, cols, walls, s, t, metas.append, rng.choice(['manhattan', 'zero']), {})
            family = 'grid'
        out.append({'id': '%s|%d' % (algo, k), 'family': family, 'metas': metas})
    return out


def questions(runs):
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(runs, f)
    try:
        out = subprocess.run([NODE, os.path.join(HERE, 'predict_check.js'), f.name],
                             capture_output=True, text=True, encoding='utf-8', check=True)
    finally:
        os.unlink(f.name)
    return json.loads(out.stdout)


ALGORITHMS = ['bfs', 'dfs', 'dijkstra', 'prim', 'topological_sort', 'Counting Sort',
              'Radix Sort', 'astar']


@pytest.mark.parametrize('algo', ALGORITHMS)
def test_the_answer_is_not_given_away_by_its_position(algo):
    rng = random.Random(ALGORITHMS.index(algo) + 2200)
    runs = runs_for(algo, rng)
    asked = questions(runs)
    first, last, total = Counter(), Counter(), 0
    for run in runs:
        for q in asked[run['id']]:
            ids = [o['id'] for o in q['options']]
            total += 1
            first[q['answer'] == ids[0]] += 1
            last[q['answer'] == ids[-1]] += 1
    assert total >= 40, (algo, total)
    share_first, share_last = first[True] / total, last[True] / total
    assert share_first <= 0.6 and share_last <= 0.6, (algo, total, share_first, share_last)


@pytest.mark.parametrize('algo', ['bfs', 'dfs', 'dijkstra', 'prim', 'topological_sort', 'astar'])
def test_data_options_are_in_a_neutral_order(algo):
    rng = random.Random(ALGORITHMS.index(algo) + 2300)
    runs = runs_for(algo, rng, count=20)
    asked = questions(runs)
    for run in runs:
        for q in asked[run['id']]:
            ids = [o['id'] for o in q['options']]
            if algo == 'astar':
                key = [tuple(map(int, i.split(','))) for i in ids]
            else:
                key = [int(i[1:]) for i in ids]          # N0, N1, ... by name
            assert key == sorted(key), q['options']
            for words in ('front first', 'top last'):
                assert words not in q['prompt'], q['prompt']


def test_astar_asks_nothing_push_order_decides():
    rng = random.Random(2400)
    runs = runs_for('astar', rng, count=120)
    asked = questions(runs)
    seen = 0
    for run in runs:
        for q in asked[run['id']]:
            step = run['metas'][q['step']]
            won = [c for c in step['candidates'] if c['cell'] == q['answer']][0]
            ties = [c for c in step['candidates'] if c['f'] == won['f'] and c['h'] == won['h']]
            assert len(ties) == 1, (q['prompt'], step['candidates'])
            seen += 1
    assert seen > 100


def test_the_expand_sentence_names_what_decided_it():
    """Lowest h is claimed only when h decided it; a tie on f and h says the
    cell was added first."""
    rng = random.Random(2401)
    claims = Counter()
    for _ in range(80):
        rows, cols = rng.randint(5, 12), rng.randint(6, 16)
        walls = {(r, c) for r in range(rows) for c in range(cols) if rng.random() < 0.2}
        free = [(r, c) for r in range(rows) for c in range(cols) if (r, c) not in walls]
        s, t = rng.sample(free, 2)
        metas = []
        astar(rows, cols, walls, s, t, metas.append, 'manhattan', {})
        for m in metas:
            if m['action'] != 'visit':
                continue
            cands = m['candidates']
            me = cands[0]
            others = [c for c in cands[1:] if c['f'] == me['f']]
            text = m['explain']['beginner']
            if not others:
                assert 'lowest h' not in text and 'tied' not in text
                claims['f'] += 1
            elif all(c['h'] > me['h'] for c in others):
                assert 'the lowest h among the cells with that f' in text
                claims['h'] += 1
            else:
                assert 'tied on f and h' in text and 'lowest h' not in text
                claims['order'] += 1
    assert min(claims.values()) > 10, claims
