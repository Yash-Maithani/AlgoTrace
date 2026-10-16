"""Phase 7A: the graph page in the workspace layout, driven by workspace.js.

Part A is layout and controls only, so there is deliberately no Learn panel
yet. The endpoints and their step arrays are covered by test_graph_parity.py
and are untouched here.
"""
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, graph_algo_dict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPH_BASE = os.path.join(ROOT, 'templates', 'graph_base.html')

ALGORITHMS = sorted(graph_algo_dict)

CONTRACT_IDS = ['run-button', 'play-pause', 'step-back', 'step-forward',
                'reset', 'speed', 'step-counter']


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


@pytest.fixture(scope='module')
def template():
    with open(GRAPH_BASE, encoding='utf-8') as fh:
        return fh.read()


@pytest.mark.parametrize('algo', ALGORITHMS)
def test_page_renders(client, algo):
    response = client.get('/graph?algo=%s' % algo)

    assert response.status_code == 200


@pytest.mark.parametrize('algo', ALGORITHMS)
def test_page_uses_the_workspace_shell(client, algo):
    body = client.get('/graph?algo=%s' % algo).get_data(as_text=True)

    for needed in ('class="workspace"', 'workspace-setup', 'workspace-stage-col',
                   'class="stage"', 'control-bar', 'algo-picker',
                   'graph-container', 'workspace.js'):
        assert needed in body, '%s is missing %s' % (algo, needed)


@pytest.mark.parametrize('algo', ALGORITHMS)
@pytest.mark.parametrize('element_id', CONTRACT_IDS)
def test_transport_contract_ids_present(client, algo, element_id):
    """The ids workspace.js documents at the top of the file."""
    body = client.get('/graph?algo=%s' % algo).get_data(as_text=True)

    assert 'id="%s"' % element_id in body


def test_no_learn_panel_in_part_a(client):
    """Part A is layout and controls. The Learn panel lands in part B."""
    body = client.get('/graph?algo=bfs').get_data(as_text=True)

    assert 'id="learn-panel"' not in body
    assert 'teacher.js' not in body


def test_workspace_tolerates_a_missing_learn_panel():
    """Which is only safe because workspace.js guards every use of it."""
    with open(os.path.join(ROOT, 'static', 'js', 'workspace.js'), encoding='utf-8') as fh:
        source = fh.read()

    assert 'panelHost && window.Teacher' in source
    for guarded in ('if (this.panel) this.panel.setLesson',
                    'if (this.panel) this.panel.showStep'):
        assert guarded in source, 'unguarded panel use: %s' % guarded


# ---------------------------------------------------------------------------
# Every function an inline handler calls must still exist
# ---------------------------------------------------------------------------

def test_every_inline_handler_has_a_function(template):
    """onclick="foo()" with no `function foo` is a click that throws."""
    called = set(re.findall(r'on[a-z]+="([a-zA-Z_$][\w$]*)\(', template))
    assert called, 'expected inline handlers in this template'

    defined = set(re.findall(r'function\s+([a-zA-Z_$][\w$]*)\s*\(', template))

    missing = called - defined
    assert not missing, 'inline handlers with no function: %s' % sorted(missing)


@pytest.mark.parametrize('name', [
    'visualize', 'generateRandomGraph', 'toggleFormatGuide',
    'loadMSTDemo', 'loadDijkstraDemo', 'loadPrimDemo', 'loadKruskalDemo',
    'loadComplexKruskalDemo', 'loadShortestPathDemo', 'loadFloydWarshallDemo',
    'loadBellmanFordDemo', 'loadBellmanFordNegativeDemo', 'loadNegativeWeightDemo',
])
def test_named_global_survives(template, name):
    assert re.search(r'function\s+%s\s*\(' % name, template), (
        '%s was removed but inline handlers still call it' % name)


@pytest.mark.parametrize('name', ['playSteps', 'pauseSteps', 'resetSteps'])
def test_old_transport_names_still_answer(template, name):
    """Kept as thin forwarders so nothing that calls them breaks."""
    assert re.search(r'function\s+%s\s*\(' % name, template)


def test_retired_ids_are_gone(template):
    """The old transport markup and the ids DESIGN section 10 retired."""
    for retired in ('id="pause-button"', 'id="play-btn"', 'id="play-button"',
                    'pauseBtn', 'id="step-display"'):
        assert retired not in template, '%s survived' % retired


def test_page_no_longer_drives_its_own_playback(template):
    """The transport is workspace.js now."""
    assert 'function applyNextStep' not in template
    assert 'animationTimeout = createTrackedTimeout(applyNextStep' not in template
    assert 'Workspace.start({' in template
    assert 'Workspace.current.load({ steps: steps })' in template


def test_canvas_code_is_still_there(template):
    """The D3 canvas, its colours and its drag behaviour are untouched."""
    for kept in ('d3.drag()', 'dragstarted', 'dragged', 'dragended',
                 'd3.forceSimulation', 'function initializeGraph',
                 'function updateGraph', 'function applyStep',
                 'renderPositions', 'const dur ='):
        assert kept in template, '%s went missing' % kept


def test_replay_rebuilds_before_going_backwards(template):
    """applyStep is cumulative, so a backward step has to replay from 0."""
    assert 'function rebuildCanvas' in template
    assert 'lastRendered' in template
    assert 'if (target <= lastRendered)' in template


def test_legend_markup_and_styling_survive(client):
    body = client.get('/graph?algo=bfs').get_data(as_text=True)

    assert 'class="legend"' in body
    assert body.count('legend-item') >= 5
    assert 'legend-swatch is-node' in body
    assert 'legend-swatch is-edge' in body

    with open(os.path.join(ROOT, 'static', 'styles.css'), encoding='utf-8') as fh:
        css = fh.read()
    assert '.legend-swatch.is-node' in css, 'the node swatch shape is unstyled'
    assert '.legend-swatch.is-edge' in css, 'the edge swatch shape is unstyled'
    assert re.search(r'\.legend \{[^}]*background-color: var\(--sunken\)', css), (
        'the legend lost its panel styling')
