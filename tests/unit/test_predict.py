"""Phase 16 and 16b: Predict mode, the question builders.

The builders (static/js/predict.js) run under node over many real runs from the
endpoints, for all 15 algorithms and every variant. This file re-derives every
answer itself, from the values in the steps and from what the algorithm does,
so a builder that agreed with itself but not with the run would fail here.
The flow in a browser is tests/browser/test_browser_predict.py.
"""
import json
import os
import random
import re
import shutil
import subprocess
import tempfile

import pytest

from paths import ROOT, JS
from wsgi import app
from algotrace.routes.sorting import SORT_VARIANTS

NODE = shutil.which('node')
needs_node = pytest.mark.skipif(NODE is None, reason='node is not installed')
INF = float('inf')


@pytest.fixture(scope='module')
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return f.read()


# ---------------------------------------------------------------------------
# Real runs: many random inputs, every algorithm, every variant
# ---------------------------------------------------------------------------

SORT_NAMES = ['Bubble Sort', 'Selection Sort', 'Insertion Sort', 'Merge Sort', 'Quick Sort', 'Heap Sort']
FIXED_SORT_INPUTS = [[5, 3, 8, 1, 9, 2], [1, 2, 3, 4, 5, 6, 7], [9, 8, 7, 6, 5, 4, 3], [4, 4, 2, 4, 2, 2, 9],
                     [17, 11, 32, 45, 9], [40, 12, 33, 7, 21, 18, 3, 29], [1], [2, 1]]


def sort_inputs():
    rng = random.Random(1602)
    inputs = [list(v) for v in FIXED_SORT_INPUTS]
    for _ in range(26):
        size = rng.randint(2, 14)
        top = rng.choice([3, 9, 99])                    # small ranges force ties
        inputs.append([rng.randint(1, top) for _ in range(size)])
    return inputs


def sort_runs(client):
    runs = []
    for name in SORT_NAMES:
        spec = SORT_VARIANTS.get(name)
        for option in ([o[0] for o in spec['options']] if spec else [None]):
            for number, values in enumerate(sort_inputs()):
                body = {'algorithm': name, 'values': ', '.join(map(str, values))}
                if option:
                    body['variant'] = option
                if option == 'random':
                    body['seed'] = number + 1
                payload = client.post('/run_sort', json=body).get_json()
                runs.append({'id': 'sort|%s|%s|%d' % (name, option, number), 'family': 'sorting',
                             'metas': payload['steps'], 'values': values, 'variant': option})
    return runs


def search_runs(client):
    runs = []
    arrays = ['4, 8, 15, 16, 23, 42, 50', '1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21', '7', '2, 2, 2, 2, 2', '3, 9']
    for algo in ('linear_search', 'binary_search'):
        for array in arrays:
            values = [int(v) for v in array.split(',')]
            targets = values + [min(values) - 1, max(values) + 1, (min(values) + max(values)) // 2 + 1]
            for target in targets:
                payload = client.post('/run_search', json={'algorithm': algo, 'array': array,
                                                           'target': str(target)}).get_json()
                runs.append({'id': 'search|%s|%s|%s' % (algo, array, target), 'family': 'searching',
                             'metas': payload['steps']})
    return runs


def random_graph(rng, n, extra, connected=True):
    names = [chr(65 + i) for i in range(n)]
    graph = {v: {} for v in names}
    order = names[:]
    rng.shuffle(order)
    if connected:
        for i in range(1, n):
            a, b = order[i], order[rng.randrange(i)]
            graph[a][b] = graph[b][a] = rng.randint(1, 9)
    for _ in range(extra):
        a, b = rng.sample(names, 2)
        graph[a][b] = graph[b][a] = rng.randint(1, 9)
    return graph


def graph_runs(client):
    rng = random.Random(1603)
    runs = []
    graphs = [random_graph(rng, rng.randint(3, 9), rng.randint(0, 9), rng.random() < 0.8) for _ in range(40)]
    graphs.append({'A': {'B': 4, 'C': 1, 'D': 7}, 'B': {'A': 4, 'C': 2, 'E': 5}, 'C': {'A': 1, 'B': 2, 'D': 3},
                   'D': {'A': 7, 'C': 3, 'E': 1}, 'E': {'B': 5, 'D': 1}})
    graphs.append({'A': {'B': 4, 'C': 2}, 'B': {'A': 4, 'C': -1, 'D': 3}, 'C': {'A': 2, 'B': -1, 'D': 5},
                   'D': {'B': 3, 'C': 5}})                                   # a negative edge
    for gi, graph in enumerate(graphs):
        start = sorted(graph)[0]
        for algo in ('bfs', 'dfs', 'dijkstra', 'prim', 'bellman_ford'):
            payload = client.post('/run_' + algo, json={'graph': graph, 'start': start}).get_json()
            if 'meta' not in payload:                                          # a refused input
                continue
            runs.append({'id': 'graph|%s|%d' % (algo, gi), 'family': 'graph', 'metas': payload['meta']})
        nodes = sorted(graph)
        edges = sorted({tuple(sorted((a, b))) + (w,) for a, adj in graph.items() for b, w in adj.items()})
        if not edges:
            continue
        for algo in ('kruskal', 'floyd_warshall'):
            payload = client.post('/run_' + algo, json={'nodes': nodes, 'edges': [list(e) for e in edges]}).get_json()
            if 'meta' in payload:
                runs.append({'id': 'graph|%s|%d' % (algo, gi), 'family': 'graph', 'metas': payload['meta']})
    return runs


_BUILT = None


def built(client):
    """(runs, questions): every real run and what the builders ask about it."""
    global _BUILT
    if _BUILT is None:
        runs = sort_runs(client) + search_runs(client) + graph_runs(client)
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump([{'id': r['id'], 'family': r['family'], 'metas': r['metas']} for r in runs], f)
        out = subprocess.run([NODE, os.path.join(JS, 'predict_check.js'), f.name],
                             capture_output=True, text=True, encoding='utf-8', check=True)
        os.unlink(f.name)
        _BUILT = (runs, json.loads(out.stdout))
    return _BUILT


def of(client, family, name=None):
    runs, questions = built(client)
    return [(r, questions[r['id']]) for r in runs
            if r['family'] == family and (name is None or r['id'].split('|')[1] == name)]


def number(v):
    return INF if v == '∞' else v


# ---------------------------------------------------------------------------
# Every question, whatever the algorithm
# ---------------------------------------------------------------------------

@needs_node
def test_options_are_never_empty_or_duplicated_and_hold_the_answer(client):
    runs, questions = built(client)
    asked = 0
    for run in runs:
        for q in questions[run['id']]:
            ids = [o['id'] for o in q['options']]
            labels = [o['label'] for o in q['options']]
            assert ids and len(set(ids)) == len(ids), (run['id'], q)
            assert len(set(labels)) == len(labels), (run['id'], q)
            assert q['answer'] in ids, (run['id'], q)
            assert all(isinstance(i, str) and i for i in ids)
            assert q['prompt'].strip() and q['explain'].strip(), (run['id'], q)
            asked += 1
    assert asked > 3000


@needs_node
def test_no_step_is_asked_about_twice_and_each_has_a_step_before_it(client):
    runs, questions = built(client)
    for run in runs:
        steps = [q['step'] for q in questions[run['id']]]
        assert len(set(steps)) == len(steps), run['id']
        assert all(1 <= s <= len(run['metas']) - 1 for s in steps), run['id']


@needs_node
def test_every_algorithm_and_every_variant_has_questions(client):
    """The "nothing to predict" message is now only for a run with no askable step."""
    runs, questions = built(client)
    counts = {}
    for run in runs:
        parts = run['id'].split('|')
        key = '%s/%s' % (parts[1], parts[2]) if parts[0] == 'sort' else parts[1]
        counts[key] = counts.get(key, 0) + len(questions[run['id']])
    expected = set()
    for name in SORT_NAMES:
        spec = SORT_VARIANTS.get(name)
        for option in ([o[0] for o in spec['options']] if spec else [None]):
            expected.add('%s/%s' % (name, option))
    expected |= {'linear_search', 'binary_search', 'bfs', 'dfs', 'dijkstra', 'prim', 'kruskal',
                 'bellman_ford', 'floyd_warshall'}
    assert set(counts) == expected
    assert all(counts[k] > 0 for k in expected), {k: v for k, v in counts.items() if not v}


# ---------------------------------------------------------------------------
# Sorting, one question per algorithm, each answer re-derived
# ---------------------------------------------------------------------------

def sorting(client, name):
    out = of(client, 'sorting', name)
    assert out
    return out


@needs_node
def test_bubble_sort_swap_answers_match_the_values_and_the_next_step(client):
    checked = swaps = 0
    for run, qs in sorting(client, 'Bubble Sort'):
        metas = run['metas']
        for q in qs:
            asked, after = metas[q['step']], metas[q['step'] + 1]
            left, right = asked['values']
            assert q['kind'] == 'sorting-swap'
            assert q['answer'] == ('yes' if left > right else 'no'), (run['id'], q)
            assert (after['action'] == 'swap') == (q['answer'] == 'yes')
            assert re.search(r'\b%s and %s\b' % (left, right), q['prompt'])
            if q['answer'] == 'yes':
                assert q['explain'] == after['explain']['beginner']
            checked += 1
            swaps += q['answer'] == 'yes'
    assert checked > 100 and 20 < swaps < checked


@needs_node
def test_selection_sort_asks_whether_the_candidate_is_the_new_smallest(client):
    yes = no = 0
    for run, qs in sorting(client, 'Selection Sort'):
        metas = run['metas']
        for q in qs:
            asked, after = metas[q['step']], metas[q['step'] + 1]
            smallest, candidate = asked['values']
            assert q['kind'] == 'selection-min' and 'new smallest value?' in q['prompt']
            assert q['answer'] == ('yes' if candidate < smallest else 'no'), (run['id'], q)
            # (A `select` that follows a final comparison with no swap is the next
            # slot's starting minimum, not an update.)
            assert (after['action'] == 'select' and after['line'] == 'update-min') == (q['answer'] == 'yes')
            assert str(candidate) in q['prompt'] and str(smallest) in q['prompt']
            if q['answer'] == 'yes':
                assert q['explain'] == after['explain']['beginner']
            yes += q['answer'] == 'yes'
            no += q['answer'] == 'no'
    assert yes > 10 and no > 10


@needs_node
def test_insertion_sort_asks_whether_the_value_shifts_right(client):
    yes = no = 0
    for run, qs in sorting(client, 'Insertion Sort'):
        metas = run['metas']
        for q in qs:
            asked, after = metas[q['step']], metas[q['step'] + 1]
            key, value = asked['vars']['key'], asked['values'][0]
            assert q['kind'] == 'insertion-shift' and 'shift one place right?' in q['prompt']
            assert q['answer'] == ('yes' if key < value else 'no'), (run['id'], q)
            assert (after['line'] == 'shift') == (q['answer'] == 'yes')
            assert after['action'] == 'overwrite'
            assert after['explain']['beginner'] in q['explain']
            yes += q['answer'] == 'yes'
            no += q['answer'] == 'no'
    assert yes > 10 and no > 10


@needs_node
def test_merge_sort_asks_which_half_is_written_next_in_both_variants(client):
    seen = set()
    for run, qs in sorting(client, 'Merge Sort'):
        metas = run['metas']
        stable = run['variant'] == 'le'
        for q in qs:
            asked = metas[q['step']]
            l, r = asked['values']
            took_left = (l <= r) if stable else (l < r)
            assert q['kind'] == 'merge-take'
            assert q['answer'] == ('left' if took_left else 'right'), (run['id'], q)
            assert asked['taken'] == q['answer']
            assert [o['id'] for o in q['options']] == ['left', 'right']
            assert str(l) in q['options'][0]['label'] and str(r) in q['options'][1]['label']
            seen.add((run['variant'], 'tie' if l == r else 'strict', q['answer']))
            if l == r:
                assert 'They are equal' in q['explain']
    # Both variants, both answers, and the tie where they part ways.
    assert ('lt', 'tie', 'right') in seen and ('le', 'tie', 'left') in seen
    assert ('lt', 'strict', 'left') in seen and ('lt', 'strict', 'right') in seen


@needs_node
def test_the_merge_compare_records_which_half_it_took(client):
    """The one fact the steps did not carry, added on the Python side."""
    runs, _ = built(client)
    for run in runs:
        if run['id'].startswith('sort|Merge Sort'):
            for m in run['metas']:
                if m['action'] == 'compare':
                    assert m['taken'] in ('left', 'right')
                else:
                    assert 'taken' not in m


@needs_node
def test_quick_sort_asks_about_the_pivot_of_the_active_variant(client):
    yes = no = 0
    variants = set()
    for run, qs in sorting(client, 'Quick Sort'):
        metas = run['metas']
        for q in qs:
            asked, after = metas[q['step']], metas[q['step'] + 1]
            value, pivot_value = asked['values']
            assert asked['vars']['pivot'] == pivot_value, 'the pivot the question names is the one in play'
            assert q['kind'] == 'quick-left' and 'smaller than the pivot' in q['prompt']
            assert ', %s.' % pivot_value in q['prompt'] and str(value) in q['prompt']
            assert q['answer'] == ('yes' if value < pivot_value else 'no'), (run['id'], q)
            assert (after['action'] == 'swap') == (q['answer'] == 'yes')
            if q['answer'] == 'yes':
                assert q['explain'] == after['explain']['beginner']
            yes += q['answer'] == 'yes'
            no += q['answer'] == 'no'
            variants.add(run['variant'])
    assert variants == {'last', 'middle', 'random'} and yes > 20 and no > 20


@needs_node
def test_heap_sort_asks_whether_the_parent_moves_down_and_the_array_agrees(client):
    yes = no = 0
    for run, qs in sorting(client, 'Heap Sort'):
        metas = run['metas']
        for q in qs:
            asked = metas[q['step']]
            parent, size = asked['vars']['i'], asked['vars']['heap_size']
            array = asked['array']
            children = [array[c] for c in (2 * parent + 1, 2 * parent + 2) if c < size]
            moves = max(children) > array[parent]
            assert q['kind'] == 'heap-down' and 'Will the parent move down?' in q['prompt']
            assert q['answer'] == ('yes' if moves else 'no'), (run['id'], q['step'], q)
            assert str(array[parent]) in q['prompt']
            if moves:
                assert q['explain'] == next(m['explain']['beginner'] for m in metas[q['step']:] if m['line'] == 'swap-down')
            yes += moves
            no += not moves
    assert yes > 10 and no > 10


@needs_node
def test_the_literal_heap_swap_question_is_gone(client):
    for run, qs in sorting(client, 'Heap Sort'):
        assert all(q['kind'] == 'heap-down' for q in qs)


# ---------------------------------------------------------------------------
# Searching
# ---------------------------------------------------------------------------

@needs_node
def test_search_answers_match_the_step_that_follows(client):
    seen = set()
    for run, qs in of(client, 'searching'):
        metas = run['metas']
        binary = 'binary_search' in run['id']
        for q in qs:
            asked, after = metas[q['step']], metas[q['step'] + 1]
            assert asked['action'] == 'compare'
            if after['action'] == 'found':
                expected = 'found'
            elif after['action'] == 'discard':
                expected = 'left' if after['line'] == 'go-left' else 'right'
            else:
                expected = 'onward'
            assert q['answer'] == expected, (run['id'], q)
            ids = [o['id'] for o in q['options']]
            assert ids == (['found', 'left', 'right'] if binary else ['found', 'onward']), (run['id'], ids)
            assert str(asked['values'][0]) in q['prompt'] and str(asked['vars']['target']) in q['prompt']
            assert ('position %d' % asked['indices'][0]) in q['prompt']
            seen.add((binary, expected))
    assert seen == {(True, 'found'), (True, 'left'), (True, 'right'), (False, 'found'), (False, 'onward')}


@needs_node
def test_search_asks_before_every_comparison_that_has_a_step_before_it(client):
    for run, qs in of(client, 'searching'):
        compares = [i for i, m in enumerate(run['metas']) if m['action'] == 'compare']
        assert [q['step'] for q in qs] == [i for i in compares if i >= 1], run['id']


# ---------------------------------------------------------------------------
# Graphs
# ---------------------------------------------------------------------------

FRONTIER_KEYS = ('queue', 'stack', 'unvisited')


@needs_node
def test_traversal_options_and_answers_come_from_the_run(client):
    kinds = set()
    for algo in ('bfs', 'dfs', 'dijkstra', 'prim'):
        for run, qs in of(client, 'graph', algo):
            metas = run['metas']
            for q in qs:
                now, nxt = metas[q['step'] - 1], metas[q['step']]
                options = [o['id'] for o in q['options']]
                assert len(options) >= 2
                if algo == 'prim':
                    assert q['kind'] == 'graph-join' and q['answer'] == str(nxt['indices'][1])
                    reached = {str(n) for m in metas[:q['step']] if m['action'] == 'enqueue' for n in m['indices']}
                    assert set(options) == reached - {str(n) for n in now['vars']['visited']}, (run['id'], q)
                else:
                    assert q['kind'] == 'graph-visit' and nxt['action'] == 'visit'
                    assert q['answer'] == str(nxt['indices'][0])
                    key = next(k for k in FRONTIER_KEYS if k in now['vars'])
                    # Listed by name, so the order says nothing about the answer.
                    assert options == sorted([str(n) for n in dict.fromkeys(now['vars'][key])], key=lambda n: [int(t) if t.isdigit() else t for t in __import__('re').split(r'(\d+)', n)]), (run['id'], q)
                assert q['explain'] == nxt['explain']['beginner']
                kinds.add(algo)
    assert kinds == {'bfs', 'dfs', 'dijkstra', 'prim'}


@needs_node
def test_kruskal_asks_whether_the_edge_is_added_or_makes_a_cycle(client):
    add = cycle = 0
    for run, qs in of(client, 'graph', 'kruskal'):
        metas = run['metas']
        for q in qs:
            nxt, after = metas[q['step']], metas[q['step'] + 1]
            u, v = nxt['indices']
            # Union-find over the edges added before this step, kept here.
            parent = {}

            def find(x):
                parent.setdefault(x, x)
                while parent[x] != x:
                    parent[x] = parent[parent[x]]
                    x = parent[x]
                return x
            for m in metas[:q['step']]:
                if m['action'] == 'include':
                    parent[find(m['indices'][0])] = find(m['indices'][1])
            makes_cycle = find(u) == find(v)
            assert q['kind'] == 'kruskal-edge'
            assert q['answer'] == ('cycle' if makes_cycle else 'add'), (run['id'], q)
            assert (after['action'] == 'reject') == makes_cycle
            assert q['explain'] == after['explain']['beginner']
            assert [o['id'] for o in q['options']] == ['add', 'cycle']
            assert '%s to %s' % (u, v) in q['prompt'] and 'weight %s' % nxt['values'][0] in q['prompt']
            add += not makes_cycle
            cycle += makes_cycle
    assert add > 10 and cycle > 10


@needs_node
def test_bellman_ford_asks_whether_the_edge_shortens_the_distance(client):
    yes = no = 0
    for run, qs in of(client, 'graph', 'bellman_ford'):
        metas = run['metas']
        for q in qs:
            nxt, after = metas[q['step']], metas[q['step'] + 1]
            w = nxt['values'][0]
            source, target = number(nxt['vars']['from']), number(nxt['vars']['to'])
            shortens = source != INF and source + w < target
            assert q['kind'] == 'bellman-relax'
            assert q['answer'] == ('yes' if shortens else 'no'), (run['id'], q)
            assert (after['action'] == 'relax') == shortens
            assert q['explain'] == after['explain']['beginner']
            yes += shortens
            no += not shortens
    assert yes > 10 and no > 10


@needs_node
def test_floyd_warshall_asks_whether_the_path_through_k_is_shorter(client):
    yes = no = 0
    for run, qs in of(client, 'graph', 'floyd_warshall'):
        metas = run['metas']
        for q in qs:
            nxt, after = metas[q['step']], metas[q['step'] + 1]
            current, ik, kj, via = nxt['values']
            assert via == ik + kj
            shorter = ik + kj < number(current)
            assert q['kind'] == 'floyd-through'
            assert q['answer'] == ('yes' if shorter else 'no'), (run['id'], q)
            assert (after['action'] == 'relax') == shorter
            assert q['explain'] == after['explain']['beginner']
            i, j, k = nxt['indices']
            assert 'through %s' % k in q['prompt'] and '%s to %s' % (i, k) in q['prompt']
            # The prompt gives the pieces, not their sum.
            assert 'is %s and' % ik in q['prompt'] and 'is %s.' % kj in q['prompt']
            yes += shorter
            no += not shorter
    assert yes > 20 and no > 20


@needs_node
def test_graph_options_are_real_nodes_of_that_graph(client):
    for run, qs in of(client, 'graph'):
        metas = run['metas']
        everyone = {str(n) for m in metas for n in m['indices']}
        for q in qs:
            if q['kind'] in ('graph-visit', 'graph-join'):
                assert {o['id'] for o in q['options']} <= everyone, (run['id'], q)
                assert len(q['options']) >= 2


# ---------------------------------------------------------------------------
# The module stays out of the shared shell
# ---------------------------------------------------------------------------

def test_no_family_or_algorithm_names_in_the_shared_shell():
    """Question building lives in predict.js; the shell only asks a gate."""
    for name in ('workspace.js', 'teacher.js'):
        source = read('algotrace', 'static', 'js', name)
        code = re.sub(r'/\*.*?\*/', '', source, flags=re.S)
        code = re.sub(r'//.*', '', code).lower()
        for banned in ('sorting', 'searching', 'bubble', 'binary', 'frontier', 'visited', 'pairswap',
                       'kruskal', 'pivot', 'heap', 'relax', 'smallest'):
            assert banned not in code, (name, banned)
    assert 'Predict.mount' in read('algotrace', 'static', 'js', 'workspace.js')
    predict = read('algotrace', 'static', 'js', 'predict.js')
    for builder in ('buildSorting', 'buildSearching', 'buildGraph'):
        assert builder in predict


def test_every_workspace_loads_predict_before_the_shell_and_opts_in():
    wanted = {'sorting.html': "predict: { family: 'sorting' }",
              'searching.html': "predict: { family: 'searching' }",
              'graph_base.html': "predict: { family: 'graph' }"}
    for name, option in wanted.items():
        source = read('algotrace', 'templates', name)
        assert option in source, name
        assert source.index('js/predict.js') < source.index('js/workspace.js'), name


def test_the_fallback_message_is_about_the_run_not_the_algorithm():
    source = read('algotrace', 'static', 'js', 'predict.js')

    assert 'No step in this run can be predicted' in source
    assert 'nothing to predict yet' not in source
