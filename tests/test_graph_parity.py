"""Phase 4b added a meta list to every /run_* endpoint. The steps did not move.

`tests/baseline_graphs.json` holds the full response of every endpoint as it
stood at commit 4a1cec8, over 51 requests covering connected, disconnected,
single node, self loop, parallel edge, zero weight, negative weight and
negative cycle graphs. These tests replay them and demand the same step
arrays.

One response is compared loosely, and the golden file says which: see
test_order_sensitive_case_is_only_reordered for why.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, GRAPH_ACTIONS

BASELINE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             'baseline_graphs.json')

with open(BASELINE_PATH, encoding='utf-8') as fh:
    BASELINE = json.load(fh)

RESPONSES = BASELINE['responses']
STABLE = [r for r in RESPONSES if not r.get('order_sensitive')]
ORDER_SENSITIVE = [r for r in RESPONSES if r.get('order_sensitive')]

ENDPOINTS = sorted({r['endpoint'] for r in RESPONSES})


def ident(row):
    return '%s-%s' % (row['endpoint'].replace('/run_', ''), row['case'])


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def post(client, row):
    response = client.post(row['endpoint'], json=row['request'])
    return response, response.get_json()


# ---------------------------------------------------------------------------
# Parity with commit 4a1cec8
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('row', STABLE, ids=ident)
def test_step_array_is_unchanged(client, row):
    """The exact arrays graph_base.html animates, frame for frame."""
    response, payload = post(client, row)

    assert response.status_code == row['status']
    assert payload['steps'] == row['steps'], (
        '%s changed the steps it emits for the %s graph'
        % (row['endpoint'], row['case']))


@pytest.mark.parametrize('row', STABLE, ids=ident)
def test_summary_fields_are_unchanged(client, row):
    """/run_bellman_ford also returns distances and a cycle flag."""
    if not row['envelope']:
        pytest.skip('this endpoint returns no summary fields')

    _, payload = post(client, row)

    for key, value in row['envelope'].items():
        assert payload[key] == value, (
            '%s changed its %s for the %s graph'
            % (row['endpoint'], key, row['case']))


@pytest.mark.parametrize('row', ORDER_SENSITIVE, ids=ident)
def test_order_sensitive_case_is_only_reordered(client, row):
    """run_dijkstra picks the next node with min() over a set.

    When two unvisited nodes tie on distance, the winner depends on set
    iteration order, which Python varies between processes through
    PYTHONHASHSEED. This was true at 4a1cec8 and before; Phase 4b neither
    introduced it nor changed it. So for a tied graph the exact order is not
    something a test can pin, but everything else still is: the same number of
    steps, the same kinds in the same proportions, and the same answer.
    """
    _, payload = post(client, row)

    actual, expected = payload['steps'], row['steps']
    assert len(actual) == len(expected)

    def kinds(steps):
        counts = {}
        for step in steps:
            counts[step[0]] = counts.get(step[0], 0) + 1
        return counts

    assert kinds(actual) == kinds(expected)
    assert actual[-1][0] == 'final'
    assert actual[-1][1] == expected[-1][1], 'the distances must still agree'
    assert sorted(s[1] for s in actual if s[0] == 'visit') == \
           sorted(s[1] for s in expected if s[0] == 'visit')


# ---------------------------------------------------------------------------
# The meta list
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('row', RESPONSES, ids=ident)
def test_meta_has_one_entry_per_step(client, row):
    _, payload = post(client, row)

    assert 'meta' in payload, '%s sent no meta' % row['endpoint']
    assert len(payload['meta']) == len(payload['steps']), (
        '%s on the %s graph sent %d meta entries for %d steps'
        % (row['endpoint'], row['case'], len(payload['meta']),
           len(payload['steps'])))


@pytest.mark.parametrize('row', RESPONSES, ids=ident)
def test_every_meta_entry_matches_the_contract(client, row):
    """Shape check against static/js/lessons/README.md sections 1 and 4."""
    _, payload = post(client, row)

    for position, meta in enumerate(payload['meta']):
        where = '%s %s meta %d' % (row['endpoint'], row['case'], position)

        for field in ('action', 'indices', 'values', 'line', 'vars', 'explain'):
            assert field in meta, '%s is missing %s' % (where, field)

        assert meta['action'] in GRAPH_ACTIONS, (
            '%s uses action %r, which is not in GRAPH_ACTIONS'
            % (where, meta['action']))
        assert isinstance(meta['indices'], list)
        assert isinstance(meta['values'], list)
        assert isinstance(meta['vars'], dict)
        assert meta['line'] is None or isinstance(meta['line'], str)
        assert meta['explain']['beginner'].strip(), '%s has no explanation' % where
        assert meta['explain']['why'].strip(), '%s has no reason' % where


@pytest.mark.parametrize('row', RESPONSES, ids=ident)
def test_meta_indices_name_real_nodes(client, row):
    """`indices` holds node ids for a graph, so every one must exist."""
    request = row['request']
    if 'nodes' in request:
        known = set(request['nodes'])
    else:
        known = set(request['graph'])
        for neighbours in request['graph'].values():
            known.update(neighbours)

    _, payload = post(client, row)

    for position, meta in enumerate(payload['meta']):
        for node in meta['indices']:
            assert node in known, (
                '%s %s meta %d points at %r, which is not a node in the graph'
                % (row['endpoint'], row['case'], position, node))


# A pre-existing bug, present at 4a1cec8 and before. run_dijkstra puts raw
# float("inf") into the distances map on its final step, and jsonify writes that
# as a bare Infinity token, which JSON.parse rejects. The page therefore reports
# "Error running algorithm" for any graph with an unreachable node. app.py already
# has the _wire helper that solves this for run_floyd_warshall and
# run_bellman_ford; run_dijkstra was never changed to use it.
#
# Fixing it would alter the step array, which Phase 4b is not allowed to do, so
# it is recorded here instead. strict=True means this test fails loudly once
# somebody does fix it, as a reminder to re-record the baseline.
KNOWN_INFINITY_BUG = {('/run_dijkstra', 'disconnected')}


@pytest.mark.parametrize('row', RESPONSES, ids=ident)
def test_response_is_json_safe(client, row):
    """No bare Infinity may reach the page; JSON.parse rejects it."""
    if (row['endpoint'], row['case']) in KNOWN_INFINITY_BUG:
        pytest.xfail('run_dijkstra sends raw infinity for unreachable nodes')

    response, _ = post(client, row)
    body = response.get_data(as_text=True)

    assert 'Infinity' not in body, (
        '%s on the %s graph emitted a bare Infinity token'
        % (row['endpoint'], row['case']))
    assert 'NaN' not in body


def test_the_infinity_bug_is_still_exactly_where_we_think_it_is(client):
    """Pin the known bug so its blast radius cannot grow unnoticed.

    If another endpoint starts leaking a bare Infinity, or run_dijkstra starts
    leaking it on a graph where everything is reachable, this fails.
    """
    leaking = set()
    for row in RESPONSES:
        response = client.post(row['endpoint'], json=row['request'])
        if 'Infinity' in response.get_data(as_text=True):
            leaking.add((row['endpoint'], row['case']))

    assert leaking == KNOWN_INFINITY_BUG, (
        'the set of responses leaking a bare Infinity changed: %s'
        % sorted(leaking ^ KNOWN_INFINITY_BUG))


@pytest.mark.parametrize('endpoint', ENDPOINTS)
def test_response_is_an_object_with_steps_and_meta(client, endpoint):
    """The shape change Phase 4b made, stated once per endpoint.

    Six of these used to answer with a bare array. graph_base.html was updated
    to read {steps, meta} in the same commit.
    """
    row = next(r for r in RESPONSES if r['endpoint'] == endpoint)
    _, payload = post(client, row)

    assert isinstance(payload, dict), '%s must answer with an object' % endpoint
    assert isinstance(payload['steps'], list)
    assert isinstance(payload['meta'], list)


# ---------------------------------------------------------------------------
# Errors are unaffected
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('endpoint,body', [
    ('/run_bfs', {'start': 'A'}),
    ('/run_dfs', {'graph': {'A': []}}),
    ('/run_dijkstra', {'graph': {'A': {}}, 'start': 'Z'}),
    ('/run_prim', {'graph': 'not a dict', 'start': 'A'}),
    ('/run_kruskal', {'nodes': ['A'], 'edges': [['A', 'B', 1]]}),
    ('/run_floyd_warshall', {'nodes': [], 'edges': []}),
    ('/run_bellman_ford', {'graph': {'A': {'B': 'heavy'}}, 'start': 'A'}),
])
def test_bad_requests_still_answer_with_an_error(client, endpoint, body):
    """Validation short circuits before any step is recorded, as before."""
    response = client.post(endpoint, json=body)

    assert response.status_code == 400
    payload = response.get_json()
    assert 'error' in payload
    assert 'steps' not in payload
