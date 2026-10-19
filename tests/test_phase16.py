"""Phase 16: Predict mode, the question builders.

The builders (static/js/predict.js) run under node over real runs from the
endpoints. This file re-derives every answer from the steps themselves, so a
builder that agreed with itself but not with the run would fail here.
The flow in a browser is tests/test_browser_phase16.py.
"""
import json
import os
import random
import re
import shutil
import subprocess
import tempfile

import pytest

from app import app, SORT_VARIANTS

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NODE = shutil.which('node')
needs_node = pytest.mark.skipif(NODE is None, reason='node is not installed')


@pytest.fixture(scope='module')
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return f.read()


# ---------------------------------------------------------------------------
# Real runs
# ---------------------------------------------------------------------------

SORT_NAMES = ['Bubble Sort', 'Selection Sort', 'Insertion Sort', 'Merge Sort', 'Quick Sort', 'Heap Sort']
SORT_INPUTS = ['5, 3, 8, 1, 9, 2', '1, 2, 3, 4, 5, 6, 7', '9, 8, 7, 6, 5, 4, 3', '4, 4, 2, 4, 2, 2, 9',
               '17, 11, 32, 45, 9', '40, 12, 33, 7, 21, 18, 3, 29', '1']


def sort_runs(client):
    runs = []
    for name in SORT_NAMES:
        spec = SORT_VARIANTS.get(name)
        for option in ([o[0] for o in spec['options']] if spec else [None]):
            for values in SORT_INPUTS:
                body = {'algorithm': name, 'values': values}
                if option:
                    body['variant'] = option
                payload = client.post('/run_sort', json=body).get_json()
                runs.append({'id': 'sort|%s|%s|%s' % (name, option, values), 'family': 'sorting',
                             'metas': payload['steps']})
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
            w = rng.randint(1, 9)
            graph[a][b] = graph[b][a] = w
    for _ in range(extra):
        a, b = rng.sample(names, 2)
        w = rng.randint(1, 9)
        graph[a][b] = graph[b][a] = w
    return graph


def graph_runs(client):
    rng = random.Random(16)
    runs = []
    graphs = [random_graph(rng, rng.randint(4, 9), rng.randint(0, 8), rng.random() < 0.8) for _ in range(14)]
    graphs.append({'A': {'B': 4, 'C': 1, 'D': 7}, 'B': {'A': 4, 'C': 2, 'E': 5}, 'C': {'A': 1, 'B': 2, 'D': 3},
                   'D': {'A': 7, 'C': 3, 'E': 1}, 'E': {'B': 5, 'D': 1}})
    for gi, graph in enumerate(graphs):
        start = sorted(graph)[0]
        for algo in ('bfs', 'dfs', 'dijkstra', 'prim', 'bellman_ford'):
            reply = client.post('/run_' + algo, json={'graph': graph, 'start': start})
            payload = reply.get_json()
            metas = payload['meta']
            runs.append({'id': 'graph|%s|%d' % (algo, gi), 'family': 'graph', 'metas': metas})
        nodes = sorted(graph)
        edges = sorted({tuple(sorted((a, b))) + (w,) for a, adj in graph.items() for b, w in adj.items()})
        for algo in ('kruskal', 'floyd_warshall'):
            payload = client.post('/run_' + algo, json={'nodes': nodes, 'edges': [list(e) for e in edges]}).get_json()
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
        out = subprocess.run([NODE, os.path.join(HERE, 'predict_check.js'), f.name],
                             capture_output=True, text=True, check=True)
        os.unlink(f.name)
        _BUILT = (runs, json.loads(out.stdout))
    return _BUILT


def by_family(client, family):
    runs, questions = built(client)
    return [(r, questions[r['id']]) for r in runs if r['family'] == family]


def same(a, b):
    return sorted(a) == sorted(b)


# ---------------------------------------------------------------------------
# Every question, whatever the family
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
    assert asked > 200


@needs_node
def test_no_step_is_asked_about_twice_and_never_the_first_or_last_without_context(client):
    runs, questions = built(client)
    for run in runs:
        steps = [q['step'] for q in questions[run['id']]]
        assert len(set(steps)) == len(steps), run['id']
        # A question needs a step before it (the current one) and a step to play.
        assert all(1 <= s <= len(run['metas']) - 1 for s in steps), run['id']


# ---------------------------------------------------------------------------
# Sorting: "Will these two swap?"
# ---------------------------------------------------------------------------

@needs_node
def test_sorting_answers_match_what_the_next_step_really_does(client):
    checked = swaps = stays = 0
    for run, qs in by_family(client, 'sorting'):
        metas = run['metas']
        for q in qs:
            asked, after = metas[q['step']], metas[q['step'] + 1]
            assert asked['action'] == 'compare' and len(asked['indices']) == 2
            really_swaps = after['action'] == 'swap' and same(after['indices'], asked['indices'])
            assert q['answer'] == ('yes' if really_swaps else 'no'), (run['id'], q)
            assert [o['id'] for o in q['options']] == ['yes', 'no']
            # The real values and positions are in the prompt.
            a, b = asked['values']
            assert re.search(r'\b%s and %s\b' % (a, b), q['prompt']), (run['id'], q['prompt'])
            assert 'positions %d and %d' % tuple(asked['indices']) in q['prompt']
            assert q['explain'].endswith(after['explain']['beginner']) or q['explain'] == after['explain']['beginner']
            checked += 1
            swaps += really_swaps
            stays += not really_swaps
    assert checked > 100 and swaps > 20 and stays > 20


@needs_node
def test_only_runs_that_swap_a_compared_pair_are_asked_about(client):
    """Selection, insertion, merge and quick sort never swap the pair they just
    compared, so there is nothing true to ask. Bubble and heap sort do."""
    asked = {}
    for run, qs in by_family(client, 'sorting'):
        name = run['id'].split('|')[1]
        asked[name] = asked.get(name, 0) + len(qs)

    assert asked['Bubble Sort'] > 0 and asked['Heap Sort'] > 0
    for name in ('Selection Sort', 'Insertion Sort', 'Merge Sort', 'Quick Sort'):
        assert asked[name] == 0, name


@needs_node
def test_a_sorted_list_asks_nothing_about_swaps_it_never_makes(client):
    runs = {r['id']: qs for r, qs in by_family(client, 'sorting')}
    qs = runs['sort|Bubble Sort|off|1, 2, 3, 4, 5, 6, 7']

    assert qs == [] or all(q['answer'] == 'no' for q in qs)


# ---------------------------------------------------------------------------
# Searching: "Found it, go left, or go right?"
# ---------------------------------------------------------------------------

@needs_node
def test_search_answers_match_the_step_that_follows(client):
    seen = set()
    for run, qs in by_family(client, 'searching'):
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
            # The compared value and the target, from the step itself.
            assert str(asked['values'][0]) in q['prompt'] and str(asked['vars']['target']) in q['prompt']
            assert ('position %d' % asked['indices'][0]) in q['prompt']
            seen.add((binary, expected))
    assert seen == {(True, 'found'), (True, 'left'), (True, 'right'), (False, 'found'), (False, 'onward')}


@needs_node
def test_search_asks_before_every_comparison(client):
    for run, qs in by_family(client, 'searching'):
        compares = [i for i, m in enumerate(run['metas']) if m['action'] == 'compare']
        # Step 0 is a comparison with no step before it, so it cannot be asked.
        assert [q['step'] for q in qs] == [i for i in compares if i >= 1], run['id']


# ---------------------------------------------------------------------------
# Graphs: "Which node is visited next?"
# ---------------------------------------------------------------------------

FRONTIER_KEYS = ('queue', 'stack', 'unvisited')


@needs_node
def test_graph_answers_and_options_come_from_the_run(client):
    kinds = set()
    for run, qs in by_family(client, 'graph'):
        algo = run['id'].split('|')[1]
        metas = run['metas']
        if algo in ('kruskal', 'floyd_warshall', 'bellman_ford'):
            assert qs == [], run['id']              # nothing is visited or joined
            continue
        for q in qs:
            now, nxt = metas[q['step'] - 1], metas[q['step']]
            options = [o['id'] for o in q['options']]
            assert len(options) >= 2
            if algo == 'prim':
                assert nxt['action'] == 'consider' and q['answer'] == str(nxt['indices'][1])
                reached = {str(n) for m in metas[:q['step']] if m['action'] == 'enqueue' for n in m['indices']}
                waiting = reached - {str(n) for n in now['vars']['visited']}
                assert set(options) == waiting, (run['id'], q)
            else:
                assert nxt['action'] == 'visit' and q['answer'] == str(nxt['indices'][0])
                key = next(k for k in FRONTIER_KEYS if k in now['vars'])
                assert set(options) == {str(n) for n in now['vars'][key]}, (run['id'], q)
                assert options == [str(n) for n in dict.fromkeys(now['vars'][key])], 'order is the structure\'s order'
            assert q['explain'] == nxt['explain']['beginner']
            kinds.add(algo)
    assert kinds == {'bfs', 'dfs', 'dijkstra', 'prim'}


@needs_node
def test_graph_options_are_real_nodes_of_that_graph(client):
    for run, qs in by_family(client, 'graph'):
        metas = run['metas']
        everyone = {str(n) for m in metas for n in m['indices']}
        for q in qs:
            assert {o['id'] for o in q['options']} <= everyone, (run['id'], q)


@needs_node
def test_a_single_waiting_node_is_not_a_question(client):
    """With one node in the queue there is nothing to choose between."""
    for run, qs in by_family(client, 'graph'):
        for q in qs:
            assert len(q['options']) >= 2


# ---------------------------------------------------------------------------
# The module stays out of the shared shell
# ---------------------------------------------------------------------------

def test_no_family_or_algorithm_names_in_the_shared_shell():
    """Question building lives in predict.js; the shell only asks a gate."""
    for name in ('workspace.js', 'teacher.js'):
        source = read('static', 'js', name)
        code = re.sub(r'/\*.*?\*/', '', source, flags=re.S)
        code = re.sub(r'//.*', '', code).lower()
        for banned in ('sorting', 'searching', 'bubble', 'binary', 'frontier', 'visited', 'pairswap'):
            assert banned not in code, (name, banned)
    assert 'Predict.mount' in read('static', 'js', 'workspace.js')
    # And the families are all in the one module.
    predict = read('static', 'js', 'predict.js')
    for builder in ('buildSorting', 'buildSearching', 'buildGraph'):
        assert builder in predict


def test_every_workspace_loads_predict_before_the_shell_and_opts_in():
    wanted = {'sorting.html': "predict: { family: 'sorting' }",
              'searching.html': "predict: { family: 'searching' }",
              'graph_base.html': "predict: { family: 'graph' }"}
    for name, option in wanted.items():
        source = read('templates', name)
        assert option in source, name
        assert source.index('js/predict.js') < source.index('js/workspace.js'), name
