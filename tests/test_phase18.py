"""Phase 18: the call tree of Merge Sort and Quick Sort.

static/js/calltree.js builds the tree from the steps of a run. Here it runs
under node over many real runs and is held to the recursion the algorithm
really performed, which is recorded by profiling the real functions and has
nothing to do with the step meta. The panel in a browser is
tests/test_browser_phase18.py.
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

from app import app, SORT_VARIANTS
from sorting_algorithms.merge_sort import merge_sort
from sorting_algorithms.quick_sort import quick_sort

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
# The real recursion, recorded by profiling the real functions
# ---------------------------------------------------------------------------

def trace_calls(sort_function, values, **kwargs):
    """Every call of the algorithm's recursive `sort`, in the order made:
    [(depth, lo, hi, parent index or None)], with hi inclusive.

    Nothing here reads a step: the arguments are taken from the frames.
    """
    calls = []
    stack = []

    def profiler(frame, event, arg):
        if frame.f_code.co_name != 'sort' or not frame.f_code.co_filename.endswith(
                ('merge_sort.py', 'quick_sort.py')):
            return
        if event == 'call':
            a = frame.f_locals
            if 'start' in a:                       # merge sort: sort(start, end, depth), end exclusive
                depth, lo, hi = a['depth'], a['start'], a['end'] - 1
            else:                                  # quick sort: sort(low, high, depth)
                depth, lo, hi = a['depth'], a['low'], a['high']
            parent = stack[-1] if stack else None
            calls.append((depth, lo, hi, parent))
            stack.append(len(calls) - 1)
        elif event == 'return':
            stack.pop()

    data = list(values)
    sys.setprofile(profiler)
    try:
        sort_function(data, lambda *a, **k: None, lambda *a, **k: None, **kwargs)
    finally:
        sys.setprofile(None)
    return calls


def kwargs_for(name, option, seed):
    if name == 'Merge Sort':
        return merge_sort, {'stable': option == 'le'}
    kw = {'pivot_rule': option}
    if option == 'random':
        kw['seed'] = seed
    return quick_sort, kw


def inputs():
    rng = random.Random(1801)
    out = [[1], [2, 1], [1, 2], [3, 1, 2], [5, 3, 8, 1, 9, 2], [1, 2, 3, 4, 5, 6, 7], [9, 8, 7, 6, 5, 4, 3, 2],
           [4, 4, 4, 4], [7, 7, 1, 7, 1, 1, 7], [17, 11, 32, 45, 9]]
    for _ in range(30):
        size = rng.randint(2, 20)
        out.append([rng.randint(1, rng.choice([3, 9, 99])) for _ in range(size)])
    return out


def build_runs(client):
    runs = []
    for name in ('Merge Sort', 'Quick Sort'):
        for option in [o[0] for o in SORT_VARIANTS[name]['options']]:
            for number, values in enumerate(inputs()):
                seed = number + 1
                body = {'algorithm': name, 'values': ', '.join(map(str, values)), 'variant': option}
                if option == 'random':
                    body['seed'] = seed
                payload = client.post('/run_sort', json=body).get_json()
                runs.append({'id': '%s|%s|%d' % (name, option, number), 'name': name, 'option': option,
                             'seed': seed, 'values': values, 'steps': payload['steps'], 'array': payload['array']})
    return runs


_BUILT = None


def built(client):
    global _BUILT
    if _BUILT is None:
        runs = build_runs(client)
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump([{'id': r['id'], 'steps': r['steps'], 'array': r['array']} for r in runs], f)
        out = subprocess.run([NODE, os.path.join(HERE, 'calltree_check.js'), f.name],
                             capture_output=True, text=True, encoding='utf-8', check=True)
        os.unlink(f.name)
        _BUILT = (runs, json.loads(out.stdout))
    return _BUILT


# ---------------------------------------------------------------------------
# The tree is the recursion
# ---------------------------------------------------------------------------

@needs_node
def test_the_tree_has_exactly_the_calls_the_algorithm_made(client):
    runs, trees = built(client)
    checked = 0
    for run in runs:
        function, kwargs = kwargs_for(run['name'], run['option'], run['seed'])
        calls = trace_calls(function, run['values'], **kwargs)
        tree = trees[run['id']]
        real = [(d, lo, hi) for d, lo, hi, _ in calls if lo <= hi]          # a call over no values is nothing
        # Calls of two or more values do work, and are the tree's boxes.
        boxes = sorted((n['depth'], n['lo'], n['hi']) for n in tree['nodes'] if not n['leaf'])
        assert boxes == sorted(c for c in real if c[2] > c[1]), run['id']
        # Calls of one value do nothing, and are its leaves.
        leaves = sorted((n['depth'], n['lo'], n['hi']) for n in tree['nodes'] if n['leaf'])
        assert leaves == sorted(c for c in real if c[2] == c[1]), run['id']
        assert tree['calls'] == sum(1 for c in real if c[2] > c[1])
        assert tree['leaves'] == sum(1 for c in real if c[2] == c[1])
        checked += 1
    assert checked == 200


@needs_node
def test_nesting_matches_who_called_whom(client):
    runs, trees = built(client)
    for run in runs:
        function, kwargs = kwargs_for(run['name'], run['option'], run['seed'])
        calls = trace_calls(function, run['values'], **kwargs)
        tree = trees[run['id']]
        index = {(n['depth'], n['lo'], n['hi']): n for n in tree['nodes']}
        for depth, lo, hi, parent in calls:
            if lo > hi:
                continue
            node = index[(depth, lo, hi)]
            if parent is None:
                assert node['parent'] is None, run['id']
            else:
                pd, plo, phi, _ = calls[parent]
                assert tree['nodes'][node['parent']]['depth'] == pd
                assert (tree['nodes'][node['parent']]['lo'], tree['nodes'][node['parent']]['hi']) == (plo, phi), run['id']


@needs_node
def test_every_call_is_a_leaf_or_has_children_that_cover_its_values(client):
    runs, trees = built(client)
    for run in runs:
        tree = trees[run['id']]
        n = len(run['values'])
        for node in tree['nodes']:
            kids = [m for m in tree['nodes'] if m['parent'] == node['id']]
            covered = sorted(p for k in kids for p in range(k['lo'], k['hi'] + 1))
            span = list(range(node['lo'], node['hi'] + 1))
            if node['leaf']:
                assert node['lo'] == node['hi'] and not kids
            elif tree['quick']:
                # Children plus the one position the pivot fixed.
                assert sorted(covered + [node['pivot']]) == span, (run['id'], node)
            else:
                assert covered == span, (run['id'], node)
        # Every value is either a leaf or a pivot: n = leaves + calls (quick) or leaves (merge).
        if tree['quick']:
            assert tree['calls'] + tree['leaves'] == n
        else:
            assert tree['leaves'] == n and tree['calls'] == n - 1 and len(tree['nodes']) == 2 * n - 1


@needs_node
def test_calls_appear_in_the_order_they_started_and_finish_inside_their_parent(client):
    runs, trees = built(client)
    for run in runs:
        function, kwargs = kwargs_for(run['name'], run['option'], run['seed'])
        calls = trace_calls(function, run['values'], **kwargs)
        tree = trees[run['id']]
        index = {(n['depth'], n['lo'], n['hi']): n for n in tree['nodes']}
        starts = [index[(d, lo, hi)]['start'] for d, lo, hi, _ in calls if lo <= hi]
        assert starts == sorted(starts), ('a call appeared before one that started earlier', run['id'])
        for node in tree['nodes']:
            if node['parent'] is not None:
                parent = tree['nodes'][node['parent']]
                assert parent['start'] <= node['start'], run['id']
                if not node['leaf']:
                    assert node['finish'] <= parent['finish'], run['id']


@needs_node
def test_each_step_lights_the_call_that_ran_it(client):
    """The active box at a step is the one whose depth and range the step carries."""
    runs, trees = built(client)
    for run in runs:
        tree = trees[run['id']]
        for i, step in enumerate(run['steps']):
            state = tree['states'][i]
            if step['action'] == 'done':
                assert state['active'] is None and state['done'] and set(state['letters']) == {'f'}
                continue
            node = tree['nodes'][state['active']]
            assert (node['depth'], node['lo'], node['hi']) == (step['depth'], step['range'][0], step['range'][1]), (run['id'], i)
            assert state['text'] == 'Sorting positions %d to %d, depth %d' % (node['lo'], node['hi'], node['depth'])


@needs_node
def test_the_tree_only_grows_forward_and_never_loses_an_ancestor(client):
    runs, trees = built(client)
    for run in runs:
        tree = trees[run['id']]
        appeared = 0
        for i, state in enumerate(tree['states']):
            now = sum(1 for c in state['letters'] if c != 'p')
            assert now >= appeared, (run['id'], i)               # calls never un-start
            appeared = now
            for node in tree['nodes']:
                if state['letters'][node['id']] != 'p' and node['parent'] is not None:
                    assert state['letters'][node['parent']] != 'p', (run['id'], i, node)
                if state['letters'][node['id']] == 'f':
                    # A finished call has no unfinished call beneath it.
                    for kid in tree['nodes']:
                        if kid['parent'] == node['id'] and not kid['leaf']:
                            assert state['letters'][kid['id']] == 'f', (run['id'], i)


@needs_node
def test_a_finished_box_shows_the_sorted_values_of_its_positions(client):
    runs, trees = built(client)
    merged = 0
    for run in runs:
        tree = trees[run['id']]
        for i, state in enumerate(tree['states']):
            for node in tree['nodes']:
                values = state['results'][node['id']]
                if values is None or node['leaf']:
                    continue
                # The values the call was handed: the positions as they stood when it began.
                before = run['steps'][node['start'] - 1]['array'] if node['start'] > 0 else run['array']
                assert values == sorted(before[node['lo']:node['hi'] + 1]), (run['id'], i, node)
                merged += 1
    assert merged > 500


@needs_node
def test_merge_shows_its_result_when_the_call_finishes_not_before(client):
    runs, trees = built(client)
    for run in runs:
        if run['name'] != 'Merge Sort':
            continue
        tree = trees[run['id']]
        for node in tree['nodes']:
            if node['leaf']:
                continue
            for i, state in enumerate(tree['states']):
                shows = state['results'][node['id']] is not None
                assert shows == (i >= node['finish']), (run['id'], i, node)


@needs_node
def test_a_run_of_one_value_is_one_leaf(client):
    runs, trees = built(client)
    for run in runs:
        if run['values'] == [1]:
            tree = trees[run['id']]
            assert len(tree['nodes']) == 1 and tree['nodes'][0]['leaf'] and tree['calls'] == 0


@needs_node
def test_every_box_has_room_and_none_overlaps_on_its_row(client):
    runs, trees = built(client)
    for run in runs:
        tree = trees[run['id']]
        rows = {}
        for node, (x, y, w, h) in zip(tree['nodes'], tree['boxes']):
            assert x >= -1 and x + w <= tree['width'] + 1 and y + h <= tree['height'] + 1, (run['id'], node)
            rows.setdefault(node['depth'], []).append((x, x + w))
        for depth, spans in rows.items():
            spans.sort()
            for (a0, a1), (b0, b1) in zip(spans, spans[1:]):
                assert a1 <= b0 + 0.001, (run['id'], depth, 'boxes overlap')


@needs_node
def test_a_sort_without_recursion_has_no_tree(client):
    out = subprocess.run([NODE, '-e',
                          "const C=require(process.argv[1]);"
                          "console.log(JSON.stringify([C.build([{array:[1,2],action:'compare',line:'compare'}]),"
                          "C.build([]),C.build(null)]))",
                          os.path.join(ROOT, 'static', 'js', 'calltree.js')],
                         capture_output=True, text=True, encoding='utf-8', check=True)

    assert json.loads(out.stdout) == [None, None, None]
    for name in ('Bubble Sort', 'Selection Sort', 'Insertion Sort', 'Heap Sort'):
        payload = app.test_client().post('/run_sort', json={'algorithm': name, 'values': '3, 1, 2'}).get_json()
        assert all('depth' not in s for s in payload['steps']), name


# ---------------------------------------------------------------------------
# The page
# ---------------------------------------------------------------------------

def test_the_sorting_page_has_a_collapsible_panel_that_starts_hidden(client):
    html = client.get('/sorting').get_data(as_text=True)
    panel = html.split('id="call-tree"', 1)[1].split('</section>', 1)[0]

    assert 'id="call-tree"' in html and re.search(r'id="call-tree"[^>]*\bhidden\b', html)
    assert 'id="call-tree-toggle"' in panel and 'aria-expanded' in panel and 'aria-controls="call-tree-body"' in panel
    assert 'depth' in panel and 'Depth is how many calls deep' in panel
    assert 'role="status"' in panel and 'aria-live="polite"' in panel
    assert 'tabindex="0"' in panel and 'role="region"' in panel
    assert html.index('js/calltree.js') < html.index('js/workspace.js')


def test_the_page_feeds_the_panel_from_the_four_hooks_and_changes_no_other_code():
    page = read('templates', 'sorting.html')

    for hook in ('callTree.load(payload)', 'callTree.show(context.index)', 'callTree.clear()', 'callTree.select('):
        assert hook in page, hook
    # The shell does not know the tree exists.
    for name in ('workspace.js', 'teacher.js', 'predict.js'):
        assert 'calltree' not in read('static', 'js', name).lower(), name


def test_the_tree_is_not_on_the_compare_page_or_the_other_workspaces(client):
    for path in ('/searching', '/graph?algo=bfs'):
        assert 'call-tree' not in client.get(path).get_data(as_text=True), path


def test_the_scroll_box_is_the_only_thing_that_scrolls():
    css = read('static', 'styles.css')
    box = css.split('.call-tree-scroll {', 1)[1].split('}', 1)[0]

    assert 'overflow: auto' in box and 'max-height' in box and 'max-width: 100%' in box
    assert 'min-width: 0' in css.split('.call-tree {', 1)[1].split('}', 1)[0]


def test_reduced_motion_ends_every_transition_the_tree_uses():
    css = read('static', 'styles.css')
    last = css[css.rindex('@media (prefers-reduced-motion: reduce) {'):]

    assert '.ct-node' in last and '.ct-edge' in last and 'transition: none' in last


def test_states_are_told_by_more_than_colour():
    css = read('static', 'styles.css')

    for state in ('active', 'waiting', 'finished', 'pending'):
        assert 'data-state="%s"' % state in css
    active = css.split('.ct-node[data-state="active"] rect {', 1)[1].split('}', 1)[0]
    assert 'stroke-width' in active                               # a heavier outline, not only a fill
