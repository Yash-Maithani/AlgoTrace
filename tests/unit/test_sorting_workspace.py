"""Phase 6: the sorting workspace, its JSON endpoint, and the three gap fixes.

Parity with commit b202fcb is tested in test_sorting_parity.py and still
holds for everything except insertion sort's frame count, which is the point
of the first fix. These tests cover what Phase 6 added or changed.
"""
import os

import pytest

from paths import PACKAGE
from wsgi import app
from algotrace.algorithms.sorting.heap_sort import heap_sort
from algotrace.algorithms.sorting.insertion_sort import insertion_sort
from algotrace.algorithms.sorting.merge_sort import merge_sort
from algotrace.catalog import SORT_LESSON_IDS, sorting_algo_dict
from algotrace.routes.sorting import SORT_ACTIONS

ALL_ALGORITHMS = sorted(sorting_algo_dict)


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def collect(func, values):
    steps = []

    def draw(array_state, compared=None, meta=None):
        step = {'array': array_state[:], 'compared': list(compared) if compared else []}
        if meta:
            step.update(meta)
        steps.append(step)

    data = list(values)
    stats = {'swaps': 0, 'comparisons': 0}
    func(data, draw, lambda: None, stats)
    return steps, stats


# ---------------------------------------------------------------------------
# Gap 1: insertion sort draws the key landing
# ---------------------------------------------------------------------------

def test_insertion_draws_the_key_landing():
    """One place frame per outer pass, which is what was missing."""
    values = [5, 3, 8, 1, 9]
    steps, _ = collect(insertion_sort, values)

    placements = [s for s in steps if s['line'] == 'place']
    assert len(placements) == len(values) - 1, (
        'expected one landing per outer pass')
    for step in placements:
        assert step['action'] == 'overwrite'
        assert len(step['indices']) == 1
        assert step['array'][step['indices'][0]] == step['values'][0]


def test_insertion_landing_shows_the_key_in_its_slot():
    """After the landing frame the key really is where the frame says."""
    steps, _ = collect(insertion_sort, [4, 1, 3])

    for step in steps:
        if step['line'] != 'place':
            continue
        where = step['indices'][0]
        assert step['array'][where] == step['vars']['key']


def test_the_landing_is_not_counted_as_a_swap():
    """The fix draws a frame. It must not change any count."""
    for values in ([5, 3, 8, 1, 9], [1, 2, 3], [3, 2, 1], [7] * 6):
        _, stats = collect(insertion_sort, values)
        shifts = sum(1 for s in collect(insertion_sort, values)[0]
                     if s['line'] == 'shift')
        assert stats['swaps'] == shifts, (
            'swaps must still count shifts only, not landings')


# ---------------------------------------------------------------------------
# Gap 2: merge sort highlights the real right hand cell
# ---------------------------------------------------------------------------

def test_merge_highlights_the_cell_the_value_is_actually_in():
    steps, _ = collect(merge_sort, [5, 3, 8, 1, 9, 2])

    compares = [s for s in steps if s['line'] == 'merge-compare']
    assert compares, 'expected merge comparisons'
    for step in compares:
        assert step['compared'] == step['indices'], (
            'compared must now agree with indices')
        for index, value in zip(step['indices'], step['values']):
            assert step['array'][index] == value


def test_merge_right_hand_index_is_past_the_left_half():
    """The old bug put it inside the left half."""
    steps, _ = collect(merge_sort, [9, 7, 5, 3, 1, 2, 4, 6])

    for step in steps:
        if step['line'] != 'merge-compare':
            continue
        left_at, right_at = step['indices']
        start = step['vars']['start']
        left_len = step['vars']['left_len']
        assert left_at < start + left_len <= right_at


# ---------------------------------------------------------------------------
# Gap 3: heap sort sends indices, not colour names
# ---------------------------------------------------------------------------

def test_heap_extract_frame_carries_indices():
    steps, _ = collect(heap_sort, [5, 3, 8, 1, 9, 2])

    extracts = [s for s in steps if s['line'] == 'swap-root']
    assert extracts, 'expected extract frames'
    for step in extracts:
        assert step['compared'] == step['indices']
        assert all(isinstance(c, int) for c in step['compared'])
        assert step['indices'][0] == 0


@pytest.mark.parametrize('algo', ALL_ALGORITHMS)
def test_only_the_done_frame_carries_colour_names(algo):
    """The done frame keeps its legacy marker; nothing else may."""
    steps, _ = collect(sorting_algo_dict[algo], [5, 3, 8, 1, 9, 2, 7])

    for position, step in enumerate(steps):
        numeric = all(isinstance(c, int) for c in step['compared'])
        if step['action'] == 'done':
            continue
        assert numeric, (
            '%s frame %d still sends colour names: %r'
            % (algo, position, step['compared']))


# ---------------------------------------------------------------------------
# /run_sort
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('algo', ALL_ALGORITHMS)
def test_run_sort_answers_every_algorithm(client, algo):
    response = client.post('/run_sort', json={'algorithm': algo, 'values': '5,3,8,1,9'})
    payload = response.get_json()

    assert response.status_code == 200
    assert payload['sorted'] == [1, 3, 5, 8, 9]
    assert payload['array'] == [5, 3, 8, 1, 9]
    assert payload['algorithm'] == algo
    assert payload['result']['n'] == 5
    assert payload['steps'][-1]['action'] == 'done'


@pytest.mark.parametrize('algo', ALL_ALGORITHMS)
def test_run_sort_steps_match_the_contract(client, algo):
    payload = client.post('/run_sort',
                          json={'algorithm': algo, 'values': '4,2,9,1,7,3'}).get_json()

    for position, step in enumerate(payload['steps']):
        where = '%s step %d' % (algo, position)
        for field in ('array', 'compared', 'action', 'indices', 'values',
                      'line', 'vars', 'explain'):
            assert field in step, '%s is missing %s' % (where, field)
        assert step['action'] in SORT_ACTIONS
        assert len(step['indices']) == len(step['values'])
        for index, value in zip(step['indices'], step['values']):
            assert step['array'][index] == value


def test_run_sort_generates_a_random_array_when_given_a_size(client):
    payload = client.post('/run_sort',
                          json={'algorithm': 'Bubble Sort', 'size': 12}).get_json()

    assert len(payload['array']) == 12
    assert payload['sorted'] == sorted(payload['array'])


@pytest.mark.parametrize('body,fragment', [
    ({'algorithm': 'Nope', 'size': 10}, 'Unknown sorting algorithm'),
    ({'algorithm': 'Bubble Sort', 'size': 2}, 'between 5 and 100'),
    ({'algorithm': 'Bubble Sort', 'size': 500}, 'between 5 and 100'),
    ({'algorithm': 'Bubble Sort', 'size': 'big'}, 'whole number'),
    ({'algorithm': 'Bubble Sort', 'values': '1, two'}, 'not a whole number'),
])
def test_run_sort_validation(client, body, fragment):
    response = client.post('/run_sort', json=body)

    assert response.status_code == 400
    assert fragment in response.get_json()['error']


def test_run_sort_and_the_form_agree(client):
    """Both paths go through one builder, so they cannot drift."""
    values = '42,17,93,8,61'
    json_run = client.post('/run_sort',
                           json={'algorithm': 'Quick Sort', 'values': values}).get_json()
    form = client.post('/sorting', data={
        'algorithm': 'Quick Sort', 'input_method': 'manual', 'manual_input': values})

    assert form.status_code == 200
    body = form.get_data(as_text=True)
    assert '"comparisons": %d' % json_run['result']['comparisons'] in body or \
           '"comparisons":%d' % json_run['result']['comparisons'] in body


# ---------------------------------------------------------------------------
# The page
# ---------------------------------------------------------------------------

def test_sorting_page_uses_the_workspace_contract(client):
    body = client.get('/sorting').get_data(as_text=True)

    for required in ('workspace', 'learn-panel', 'control-bar', 'run-button',
                     'play-pause', 'step-back', 'step-forward', 'reset',
                     'step-counter', 'algo-picker', 'teacher.js', 'workspace.js'):
        assert required in body, 'the page is missing %s' % required


def test_sorting_page_loads_every_lesson(client):
    body = client.get('/sorting').get_data(as_text=True)

    for lesson in SORT_LESSON_IDS.values():
        assert 'lessons/%s.js' % lesson in body


def test_form_post_still_delivers_its_run(client):
    """POST /sorting runs the sort server side and the page opens on it."""
    response = client.post('/sorting', data={
        'algorithm': 'Merge Sort', 'input_method': 'manual', 'manual_input': '5,3,8,1'})
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert '"algorithm": "Merge Sort"' in body or '"algorithm":"Merge Sort"' in body
    assert '"steps"' in body


def test_form_post_reports_a_bad_size(client):
    body = client.post('/sorting', data={
        'algorithm': 'Bubble Sort', 'input_method': 'random', 'size': '2'}
    ).get_data(as_text=True)

    assert 'between 5 and 100' in body


def test_no_duplicate_transport_ids_remain():
    """DESIGN section 10: play-btn, play-button and pauseBtn are retired."""
    templates = os.path.join(PACKAGE, 'templates')

    for name in os.listdir(templates):
        if not name.endswith('.html'):
            continue
        with open(os.path.join(templates, name), encoding='utf-8') as fh:
            source = fh.read()
        for retired in ('id="play-btn"', 'id="play-button"', 'pauseBtn'):
            assert retired not in source, '%s still has %s' % (name, retired)


def test_shared_files_name_no_algorithm_family():
    """workspace.js and teacher.js stay reusable for Phase 7."""

    for name in ('workspace.js', 'teacher.js'):
        with open(os.path.join(PACKAGE, 'static', 'js', name), encoding='utf-8') as fh:
            source = fh.read()
        lowered = source.lower()
        for word in ('bubble', 'quicksort', 'bar-container', 'cell-row',
                     'run_sort', 'run_search', 'array-size'):
            assert word not in lowered, (
                '%s mentions %s, which belongs to one page' % (name, word))
