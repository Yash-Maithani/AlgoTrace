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


def test_no_response_is_order_sensitive_any_more():
    """Every row is now compared exactly, including the tied Dijkstra graph."""
    assert ORDER_SENSITIVE == [], (
        'the baseline still marks rows as order sensitive: %s'
        % [ident(r) for r in ORDER_SENSITIVE])


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


@pytest.mark.parametrize('row', RESPONSES, ids=ident)
def test_response_is_json_safe(client, row):
    """No bare Infinity may reach the page; JSON.parse rejects it.

    run_dijkstra used to send raw float("inf") for an unreachable node, which
    made the whole response unparseable and broke Dijkstra on any disconnected
    graph. It now uses the same _wire helper as the other endpoints.
    """
    response, _ = post(client, row)
    body = response.get_data(as_text=True)

    assert 'Infinity' not in body, (
        '%s on the %s graph emitted a bare Infinity token'
        % (row['endpoint'], row['case']))
    assert 'NaN' not in body


def test_unreachable_distances_travel_as_the_infinity_label(client):
    """The wire form the templates already compare against."""
    graph = {'A': {'B': 3}, 'B': {'A': 3}, 'C': {'D': 1}, 'D': {'C': 1}, 'E': {}}
    payload = client.post('/run_dijkstra',
                          json={'graph': graph, 'start': 'A'}).get_json()

    final = payload['steps'][-1]
    assert final[0] == 'final'
    assert final[1] == {'A': 0, 'B': 3, 'C': '\u221e', 'D': '\u221e', 'E': '\u221e'}


def test_tie_breaking_follows_input_order(client):
    """A tie is resolved by the order the nodes arrived in, not by set order.

    Three nodes all one apart means B and C tie after A is settled. Feeding
    the same graph with the keys in each order must settle them in that order,
    which is only true if the choice reads the input rather than a set.
    """
    forward = {'A': {'B': 1, 'C': 1}, 'B': {'A': 1, 'C': 1}, 'C': {'A': 1, 'B': 1}}
    backward = {'A': {'C': 1, 'B': 1}, 'C': {'A': 1, 'B': 1}, 'B': {'A': 1, 'C': 1}}

    def visits(graph):
        # Posted as a raw body on purpose. The test client serialises a json=
        # argument through the app provider, which sorts keys, and that would
        # erase the very ordering this test is about. A browser sends the
        # object in the order the page built it.
        body = json.dumps({'graph': graph, 'start': 'A'}, sort_keys=False)
        payload = client.post('/run_dijkstra', data=body,
                              content_type='application/json').get_json()
        return [step[1] for step in payload['steps'] if step[0] == 'visit']

    assert visits(forward) == ['A', 'B', 'C']
    assert visits(backward) == ['A', 'C', 'B']


@pytest.mark.parametrize('run', range(5))
def test_dijkstra_is_repeatable_within_a_process(client, run):
    """The same request must give the same steps every time it is made."""
    graph = {'A': {'B': 1, 'C': 1}, 'B': {'A': 1, 'C': 1}, 'C': {'A': 1, 'B': 1}}
    first = client.post('/run_dijkstra',
                        json={'graph': graph, 'start': 'A'}).get_json()['steps']
    again = client.post('/run_dijkstra',
                        json={'graph': graph, 'start': 'A'}).get_json()['steps']

    assert first == again


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
