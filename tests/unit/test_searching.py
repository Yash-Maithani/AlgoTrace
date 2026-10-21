"""Linear and binary search: the answers, the counts, and the refusal.

The counting convention under test is the one the lesson files state and the
Complexity tab prints: one comparison each time the loop looks at a value.
If the code and the lesson ever disagree, these fail.
"""
import os
import re

import pytest

from paths import ROOT
from wsgi import app
from algotrace.algorithms.searching.binary_search import binary_search, is_sorted
from algotrace.algorithms.searching.linear_search import linear_search
from algotrace.routes.searching import SEARCH_ACTIONS

LESSON_DIR = os.path.join(ROOT, 'algotrace', 'static', 'js', 'lessons')

SORTED_FIVE = [4, 8, 15, 16, 23]


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def run(algorithm, values, target):
    """Collect the steps the way /run_search does."""
    steps = []
    stats = {'comparisons': 0}

    def draw(indices, meta):
        step = {'array': list(values), 'compared': list(indices)}
        step.update(meta)
        steps.append(step)

    index = algorithm(list(values), target, draw, None, stats)
    return index, stats['comparisons'], steps


# ---------------------------------------------------------------------------
# Linear search
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('target,expected_index,expected_comparisons', [
    (4, 0, 1),     # first
    (15, 2, 3),    # middle
    (23, 4, 5),    # last
])
def test_linear_finds_at_each_position(target, expected_index, expected_comparisons):
    index, comparisons, steps = run(linear_search, SORTED_FIVE, target)

    assert index == expected_index
    assert comparisons == expected_comparisons
    assert steps[-1]['action'] == 'found'
    assert steps[-1]['indices'] == [expected_index]


def test_linear_reports_a_missing_target():
    index, comparisons, steps = run(linear_search, SORTED_FIVE, 42)

    assert index == -1
    assert comparisons == len(SORTED_FIVE), 'a failed search must check everything'
    assert steps[-1]['action'] == 'missing'
    assert steps[-1]['indices'] == []


def test_linear_stops_at_the_first_of_several_duplicates():
    values = [7, 3, 7, 7, 1]
    index, comparisons, steps = run(linear_search, values, 7)

    assert index == 0
    assert comparisons == 1
    assert steps[-1]['action'] == 'found'


def test_linear_on_a_single_value():
    assert run(linear_search, [9], 9)[:2] == (0, 1)
    assert run(linear_search, [9], 4)[:2] == (-1, 1)


def test_linear_on_an_empty_list():
    index, comparisons, steps = run(linear_search, [], 1)

    assert index == -1
    assert comparisons == 0
    assert steps[-1]['action'] == 'missing'


def test_linear_works_on_unsorted_input():
    """It makes no assumption about order, unlike binary search."""
    values = [42, 8, 99, 4, 16]
    index, comparisons, _ = run(linear_search, values, 4)

    assert index == 3
    assert comparisons == 4


# ---------------------------------------------------------------------------
# Binary search
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('target,expected_index,expected_comparisons', [
    (4, 0, 2),     # first
    (15, 2, 1),    # middle, found immediately
    (23, 4, 3),    # last
])
def test_binary_finds_at_each_position(target, expected_index, expected_comparisons):
    index, comparisons, steps = run(binary_search, SORTED_FIVE, target)

    assert index == expected_index
    assert comparisons == expected_comparisons
    assert steps[-1]['action'] == 'found'


def test_binary_reports_a_missing_target():
    index, comparisons, steps = run(binary_search, SORTED_FIVE, 42)

    assert index == -1
    assert comparisons == 3, 'n = 5 closes the range in three comparisons'
    assert steps[-1]['action'] == 'missing'


def test_binary_finds_one_of_several_duplicates():
    """With duplicates it finds an occurrence, not necessarily the first."""
    values = [1, 3, 3, 3, 9]
    index, _, steps = run(binary_search, values, 3)

    assert values[index] == 3
    assert steps[-1]['action'] == 'found'


def test_binary_on_a_single_value():
    assert run(binary_search, [9], 9)[:2] == (0, 1)
    assert run(binary_search, [9], 4)[:2] == (-1, 1)


def test_binary_on_an_empty_list():
    index, comparisons, steps = run(binary_search, [], 1)

    assert index == -1
    assert comparisons == 0
    assert steps[-1]['action'] == 'missing'


def test_binary_never_looks_outside_the_live_range():
    """Every compare must sit between the low and high it reports."""
    values = list(range(0, 60, 2))
    _, _, steps = run(binary_search, values, 41)

    for step in steps:
        if step['action'] != 'compare':
            continue
        vars_ = step['vars']
        assert vars_['low'] <= vars_['mid'] <= vars_['high']
        assert step['indices'] == [vars_['mid']]


def test_binary_halves_the_range_each_time():
    values = list(range(1, 65))
    _, _, steps = run(binary_search, values, 64)

    sizes = [s['vars']['range_size'] for s in steps if s['action'] == 'compare']
    for earlier, later in zip(sizes, sizes[1:]):
        assert later <= earlier // 2 + 1, 'the range must at least halve'


@pytest.mark.parametrize('values,expected', [
    ([], True),
    ([1], True),
    ([1, 2, 3], True),
    ([1, 1, 1], True),
    ([3, 1, 2], False),
    ([1, 2, 1], False),
])
def test_is_sorted(values, expected):
    assert is_sorted(values) is expected


# ---------------------------------------------------------------------------
# The endpoint
# ---------------------------------------------------------------------------

def post(client, **body):
    return client.post('/run_search', json=body)


def test_endpoint_returns_steps_and_a_result(client):
    response = post(client, algorithm='linear_search',
                    array='4, 8, 15, 16, 23', target=16)
    payload = response.get_json()

    assert response.status_code == 200
    assert payload['result'] == {'found': True, 'index': 3, 'comparisons': 4}
    assert payload['array'] == SORTED_FIVE
    assert payload['target'] == 16
    assert len(payload['steps']) == 5


def test_binary_search_on_unsorted_input_is_blocked(client):
    """The run is refused rather than answered wrongly."""
    response = post(client, algorithm='binary_search',
                    array='9, 2, 7, 1', target=7)
    payload = response.get_json()

    assert response.status_code == 400
    assert payload['unsorted'] is True
    assert 'sorted' in payload['error'].lower()
    assert payload['sorted_array'] == [1, 2, 7, 9]
    assert 'steps' not in payload


def test_linear_search_on_unsorted_input_is_allowed(client):
    response = post(client, algorithm='linear_search',
                    array='9, 2, 7, 1', target=7)

    assert response.status_code == 200
    assert response.get_json()['result']['index'] == 2


def test_binary_search_accepts_the_sorted_copy_it_offered(client):
    """The Sort it for me button sends back exactly this."""
    refused = post(client, algorithm='binary_search',
                   array='9, 2, 7, 1', target=7).get_json()

    accepted = post(client, algorithm='binary_search',
                    array=refused['sorted_array'], target=7)

    assert accepted.status_code == 200
    assert accepted.get_json()['result']['found'] is True


@pytest.mark.parametrize('body,fragment', [
    ({'algorithm': 'linear_search', 'array': '', 'target': 1}, 'Enter some numbers'),
    ({'algorithm': 'linear_search', 'array': '1, two, 3', 'target': 1}, 'not a whole number'),
    ({'algorithm': 'linear_search', 'array': '1, 2, 3', 'target': ''}, 'Enter a target'),
    ({'algorithm': 'linear_search', 'array': '1, 2, 3', 'target': 'x'}, 'not a whole number'),
    ({'algorithm': 'nope', 'array': '1', 'target': 1}, 'Unknown search algorithm'),
])
def test_validation_messages(client, body, fragment):
    response = client.post('/run_search', json=body)

    assert response.status_code == 400
    assert fragment in response.get_json()['error']


def test_array_size_is_capped(client):
    response = post(client, algorithm='linear_search',
                    array=','.join(str(i) for i in range(40)), target=1)

    assert response.status_code == 400
    assert '30 or fewer' in response.get_json()['error']


@pytest.mark.parametrize('algorithm', ['linear_search', 'binary_search'])
def test_every_step_matches_the_contract(client, algorithm):
    """Shape check against static/js/lessons/README.md section 1."""
    payload = post(client, algorithm=algorithm,
                   array='1, 2, 3, 4, 5, 6, 7', target=6).get_json()

    for position, step in enumerate(payload['steps']):
        where = '%s step %d' % (algorithm, position)
        for field in ('array', 'compared', 'action', 'indices', 'values',
                      'line', 'vars', 'explain'):
            assert field in step, '%s is missing %s' % (where, field)

        assert step['action'] in SEARCH_ACTIONS
        assert len(step['indices']) == len(step['values'])
        assert all(isinstance(i, int) for i in step['indices'])
        assert all(0 <= i < len(step['array']) for i in step['indices'])
        for index, value in zip(step['indices'], step['values']):
            assert step['array'][index] == value
        assert step['explain']['beginner'].strip()
        assert step['explain']['why'].strip()
        assert step['line'] is None or isinstance(step['line'], str)


@pytest.mark.parametrize('algorithm', ['linear_search', 'binary_search'])
def test_line_ids_exist_in_the_lesson(client, algorithm):
    """Every line a step points at must be a line the Code tab can show."""
    with open(os.path.join(LESSON_DIR, '%s.js' % algorithm), encoding='utf-8') as fh:
        lesson = fh.read()
    declared = set(re.findall(r"id:\s*'([^']+)'", lesson))

    payload = post(client, algorithm=algorithm,
                   array='1, 2, 3, 4, 5, 6, 7', target=99).get_json()
    emitted = {s['line'] for s in payload['steps'] if s['line']}

    assert emitted <= declared, (
        '%s emits line ids the lesson does not define: %s'
        % (algorithm, sorted(emitted - declared)))


# ---------------------------------------------------------------------------
# The figures the Complexity tab prints
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('algorithm,func,target,expected', [
    ('linear_search', linear_search, 16, 4),
    ('binary_search', binary_search, 4, 2),
])
def test_worked_example_matches_the_lesson(algorithm, func, target, expected):
    """The number printed in the Complexity tab is the one the code makes."""
    with open(os.path.join(LESSON_DIR, '%s.js' % algorithm), encoding='utf-8') as fh:
        lesson = fh.read()
    quoted = int(re.search(r'comparisons:\s*(\d+)', lesson).group(1))

    _, actual, _ = run(func, SORTED_FIVE, target)

    assert quoted == expected
    assert actual == expected, (
        '%s.js quotes %d comparisons but the code makes %d'
        % (algorithm, quoted, actual))


def test_linear_worst_case_quoted_in_its_lesson():
    """"Searching for 42 costs the full 5" in linear_search.js."""
    _, comparisons, _ = run(linear_search, SORTED_FIVE, 42)
    assert comparisons == 5


def test_binary_worst_case_quoted_in_its_lesson():
    """"The worst case here is 3 comparisons" in binary_search.js."""
    worst = max(run(binary_search, SORTED_FIVE, t)[1]
                for t in [4, 8, 15, 16, 23, 42, 0])
    assert worst == 3


# ---------------------------------------------------------------------------
# The page
# ---------------------------------------------------------------------------

def test_searching_page_renders(client):
    response = client.get('/searching')

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    for required in ('workspace', 'learn-panel', 'control-bar', 'run-button',
                     'teacher.js', 'workspace.js'):
        assert required in body, 'the page is missing %s' % required


def test_searching_is_in_the_navbar(client):
    body = client.get('/').get_data(as_text=True)

    assert '/searching' in body


def test_learn_links_to_both_searches(client):
    body = client.get('/learn').get_data(as_text=True)

    assert '/searching?algorithm=linear_search' in body
    assert '/searching?algorithm=binary_search' in body
    assert 'Coming soon' not in body.split('<h2>Searching</h2>')[1].split('<h2>')[0]
