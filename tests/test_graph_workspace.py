"""Phase 7A and 7B: the graph page in the workspace, with its Learn panel.

This module spells out the escaped forms the banned pattern check hunts, so
it carries the pragma: banned-check: documents-the-patterns


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

    # A* draws on a grid board instead of the D3 graph canvas (Phase 21).
    canvas = 'grid-board' if algo == 'astar' else 'graph-container'
    for needed in ('class="workspace"', 'workspace-setup', 'workspace-stage-col',
                   'class="stage', 'control-bar', 'algo-picker',
                   canvas, 'workspace.js'):
        assert needed in body, '%s is missing %s' % (algo, needed)


@pytest.mark.parametrize('algo', ALGORITHMS)
@pytest.mark.parametrize('element_id', CONTRACT_IDS)
def test_transport_contract_ids_present(client, algo, element_id):
    """The ids workspace.js documents at the top of the file."""
    body = client.get('/graph?algo=%s' % algo).get_data(as_text=True)

    assert 'id="%s"' % element_id in body


@pytest.mark.parametrize('algo', ALGORITHMS)
def test_learn_panel_is_wired(client, algo):
    """Part B: the panel, teacher.js and this algorithm's own lesson."""
    body = client.get('/graph?algo=%s' % algo).get_data(as_text=True)

    assert 'id="learn-panel"' in body
    assert 'teacher.js' in body
    assert 'lessons/%s.js' % algo in body, 'the lesson for %s is not loaded' % algo


def test_workspace_tolerates_a_missing_learn_panel():
    """Which is only safe because workspace.js guards every use of it."""
    with open(os.path.join(ROOT, 'static', 'js', 'workspace.js'), encoding='utf-8') as fh:
        source = fh.read()

    assert 'panelHost && window.Teacher' in source
    assert 'if (this.panel) this.panel.setLesson' in source
    assert 'if (this.panel) {' in source, 'the showStep call is unguarded'


# ---------------------------------------------------------------------------
# Every function an inline handler calls must still exist
# ---------------------------------------------------------------------------

def test_every_inline_handler_has_a_function(template):
    """data-action="foo" with no `function foo` is a click that does nothing. The
    page has no inline onclick handlers (the Content-Security-Policy forbids them);
    its buttons name an action and one listener runs it."""
    assert not re.search(r'\son[a-z]+="', template), 'an inline event handler is back'
    called = set(re.findall(r'data-action="([a-zA-Z_$][\w$]*)"', template))
    assert called, 'expected data-action buttons in this template'

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


def test_the_status_panel_is_a_state_line(template):
    """It used to narrate every step a second time, in its own voice.

    Six generators wrote their own sentences from the raw step arrays, so on
    a disconnected graph the panel said all shortest paths had been found
    while the Learn panel said two of four nodes were reached. The panel now
    reads the same meta the Learn panel reads, which makes disagreement
    impossible rather than merely corrected.
    """
    for gone in ('getKruskalStatus', 'getPrimStatus', 'getDijkstraStatus',
                 'getFloydWarshallStatus', 'getBellmanFordStatus',
                 'getTraversalStatus', 'STATUS_ICON'):
        assert gone not in template, '%s is back' % gone

    assert 'function updateStatusDisplay(stepIndex)' in template
    assert 'meta.explain.beginner' in template, (
        'the finished line is no longer the Learn panel sentence')


def test_the_status_panel_is_written_as_text_not_markup(template):
    """Its old lines carried inline styles and bold tags of their own."""
    start = template.index('function updateStatusDisplay(stepIndex)')
    end = template.index('function applyKruskalStep')
    body = template[start:end]

    assert '<strong>' not in body and 'style=' not in body, (
        'the status panel is styling itself again')


def test_repository_has_no_banned_patterns():
    """Runs the check REBUILD_PLAN's definition of done names.

    It decodes escapes and entities before looking, which a grep cannot do,
    and which is how six emoji and an em dash survived six phases here.
    """
    import subprocess

    checker = os.path.join(ROOT, 'tools', 'check_banned_patterns.py')
    assert os.path.isfile(checker), 'the banned pattern check is missing'

    result = subprocess.run([sys.executable, '-I', checker, ROOT],
                            capture_output=True, text=True, encoding='utf-8')

    assert result.returncode == 0, result.stdout + result.stderr


BS = chr(92)


@pytest.mark.parametrize('written,kind', [
    (BS + 'u2014', 'em dash'),
    (BS + 'u{1F680}', 'emoji'),
    (BS + 'uD83D' + BS + 'uDE80', 'emoji'),
    ('&mdash;', 'em dash'),
    ('&#8212;', 'em dash'),
    ('&#x2014;', 'em dash'),
])
def test_the_check_catches_every_escaped_form(tmp_path, written, kind):
    """The forms that slipped past a plain grep for six phases."""
    sys.path.insert(0, os.path.join(ROOT, 'tools'))
    import importlib
    checker = importlib.import_module('check_banned_patterns')

    sample = tmp_path / 'sample.js'
    sample.write_text('const label = `%s ready`;' % written, encoding='utf-8')

    hits = checker.problems_in(str(sample))

    assert hits, '%s written as %s was not caught' % (kind, written)
    assert any(kind in found[1] for found in hits), hits


@pytest.mark.parametrize('written', [BS + 'u221E', BS + 'u2192', '&amp;', '&lt;'])
def test_the_check_allows_the_typography_we_use(tmp_path, written):
    sys.path.insert(0, os.path.join(ROOT, 'tools'))
    import importlib
    checker = importlib.import_module('check_banned_patterns')

    sample = tmp_path / 'sample.js'
    sample.write_text('const label = `a %s b`;' % written, encoding='utf-8')

    assert checker.problems_in(str(sample)) == []
