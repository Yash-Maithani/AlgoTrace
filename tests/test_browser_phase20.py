"""Phase 20 in a real browser: the directed graph page for Topological Sort.

Arrowheads on every arrow and on no undirected page, the in-degree badges,
the queue and order strip at 375, 768 and 1440 in both themes, the cycle
message, the random DAG generator, stepping back, and reduced motion.

Needs Playwright (requirements-dev.txt); skips with a warning without it.
Marked slow through tests/conftest.py, like every browser test.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_helpers import SKIP_REASON, available, page_for
from app import app

pytestmark = pytest.mark.skipif(not available(), reason=SKIP_REASON)

COURSE = {'Math': ['Calc', 'Phys'], 'Calc': ['Stat'], 'Phys': ['Stat'], 'Stat': ['Proj'],
          'Proj': [], 'Intro': ['Proj', 'Code'], 'Code': []}


def load(page, demo):
    page.evaluate(demo + '()')
    page.wait_for_function('Workspace.current && Workspace.current.steps.length > 0')
    page.wait_for_timeout(300)


def endpoint(graph):
    with app.test_client() as c:
        return c.post('/run_topological_sort', data=json.dumps({'graph': graph}),
                      content_type='application/json').get_json()


def test_arrows_point_and_stop_at_the_target(browser, base_url):
    page = page_for(browser, base_url, '/graph?algo=topological_sort', width=1440)
    load(page, 'loadCourseDemo')
    page.evaluate('Workspace.current.go(0)')
    # Each arrow is drawn on a tick of the force layout, from where the nodes are
    # at that tick. Going to step 0 rebuilds the canvas and restarts the layout, so
    # measuring straight away can catch nodes already moved and arrows not yet
    # redrawn (gaps of hundreds of pixels, on about one run in three). Wait for the
    # layout to come to rest: its last tick draws every arrow where its node is.
    page.wait_for_function(
        "typeof simulation !== 'undefined' && simulation && simulation.alpha() < simulation.alphaMin()",
        timeout=15000)
    info = page.evaluate("""() => {
        const links = [...document.querySelectorAll('#graph-container line.link')];
        return {
            count: links.length,
            marked: links.filter(l => l.getAttribute('marker-end') === 'url(#arrowhead)').length,
            marker: !!document.querySelector('#graph-container marker#arrowhead'),
            gaps: links.map(l => {
                const d = l.__data__;
                return Math.hypot(d.target.x - Number(l.getAttribute('x2')),
                                  d.target.y - Number(l.getAttribute('y2')));
            })
        };
    }""")
    assert info['count'] == 7 and info['marked'] == 7 and info['marker']
    assert all(abs(g - 27) < 0.5 for g in info['gaps']), info['gaps']
    assert page.errors == []
    page.ctx.close()


@pytest.mark.parametrize('algo', ['bfs', 'dfs', 'dijkstra', 'prim', 'kruskal', 'floyd_warshall', 'bellman_ford'])
def test_undirected_pages_are_unchanged(browser, base_url, algo):
    page = page_for(browser, base_url, '/graph?algo=' + algo, width=1440)
    page.evaluate("document.getElementById('randomRadio').click()")
    page.evaluate('generateRandomGraph()')
    page.wait_for_function('Workspace.current && Workspace.current.steps.length > 0', timeout=10000)
    page.evaluate('Workspace.current.go(Workspace.current.steps.length - 1)')
    info = page.evaluate("""() => ({
        marked: document.querySelectorAll('#graph-container line[marker-end]').length,
        marker: !!document.querySelector('#arrowhead'),
        badges: document.querySelectorAll('.indegree-badge').length,
        stripClass: document.getElementById('stage').classList.contains('has-strip'),
    })""")
    assert info == {'marked': 0, 'marker': False, 'badges': 0, 'stripClass': False}
    assert not page.is_visible('#topo-strip') and page.is_visible('.input-section')
    assert page.errors == []
    page.ctx.close()


@pytest.mark.parametrize('width', [375, 768, 1440])
@pytest.mark.parametrize('scheme', ['light', 'dark'])
def test_strip_and_badges(browser, base_url, width, scheme):
    page = page_for(browser, base_url, '/graph?algo=topological_sort', width=width, scheme=scheme)
    load(page, 'loadCourseDemo')
    body = endpoint(COURSE)
    k = 14
    page.evaluate('n => Workspace.current.go(n)', k)
    state = page.evaluate("""() => {
        const box = el => el.getBoundingClientRect();
        const stage = document.getElementById('stage'), strip = document.getElementById('topo-strip');
        return {
            scroll: document.documentElement.scrollWidth - document.documentElement.clientWidth,
            queue: [...document.querySelectorAll('#topo-queue .topo-chip')].map(c => c.textContent),
            order: [...document.querySelectorAll('#topo-order .topo-chip')].map(c => c.textContent),
            badges: Object.fromEntries([...document.querySelectorAll('.indegree-badge')]
                        .map(b => [b.dataset.node, b.querySelector('text').textContent])),
            inside: box(strip).top >= box(document.getElementById('graph-container')).bottom - 1
                    && box(strip).bottom <= box(stage).bottom + 1,
            nextToStage: stage.nextElementSibling.classList.contains('control-bar'),
            visible: box(strip).height > 40 && getComputedStyle(strip).display !== 'none'
        };
    }""")
    meta = body['meta'][k]['vars']
    assert state['scroll'] <= 0
    assert state['visible'] and state['inside'] and state['nextToStage']
    assert state['queue'] == (meta['queue'] or ['empty'])
    assert state['order'] == (meta['order'] or ['empty'])
    assert state['badges'] == {n: str(d) for n, d in meta['in_degree'].items()}
    # The finish: every node in order, and the message says so.
    page.evaluate('Workspace.current.go(Workspace.current.steps.length - 1)')
    assert page.evaluate("[...document.querySelectorAll('#topo-order .topo-chip')].map(c => c.textContent)") \
        == body['order']
    assert page.get_attribute('#topo-message', 'data-outcome') == 'found'
    assert page.errors == []
    page.ctx.close()


@pytest.mark.parametrize('scheme', ['light', 'dark'])
def test_a_cycle_is_named_and_drawn(browser, base_url, scheme):
    page = page_for(browser, base_url, '/graph?algo=topological_sort', width=768, scheme=scheme)
    load(page, 'loadCycleDemo')
    page.evaluate('Workspace.current.go(Workspace.current.steps.length - 1)')
    state = page.evaluate("""() => ({
        message: document.getElementById('topo-message').textContent,
        outcome: document.getElementById('topo-message').dataset.outcome,
        path: [...document.querySelectorAll('#graph-container line.shortest-path')]
                .map(l => l.__data__.source.id + '>' + l.__data__.target.id).sort(),
        current: [...document.querySelectorAll('#graph-container circle.node-current')].map(c => c.__data__.id).sort()
    })""")
    assert state['outcome'] == 'missing'
    assert state['message'].startswith('No order exists.')
    assert 'Wash → Dress → Tea → Wash is a cycle' in state['message']
    assert 'Go waits on the cycle' in state['message']
    assert state['path'] == ['Dress>Tea', 'Tea>Wash', 'Wash>Dress']
    assert state['current'] == ['Dress', 'Tea', 'Wash']
    page.ctx.close()


def test_step_back_rebuilds_the_state(browser, base_url):
    page = page_for(browser, base_url, '/graph?algo=topological_sort', width=1440)
    load(page, 'loadCourseDemo')
    page.evaluate('Workspace.current.go(16)')
    page.click('#step-back')
    page.wait_for_timeout(300)
    body = endpoint(COURSE)
    meta = body['meta'][15]['vars']
    got = page.evaluate("""() => ({
        order: [...document.querySelectorAll('#topo-order .topo-chip')].map(c => c.textContent),
        badges: Object.fromEntries([...document.querySelectorAll('.indegree-badge')]
                    .map(b => [b.dataset.node, b.querySelector('text').textContent]))})""")
    assert got['order'] == (meta['order'] or ['empty'])
    assert got['badges'] == {n: str(d) for n, d in meta['in_degree'].items()}
    page.ctx.close()


def test_random_graphs_are_dags(browser, base_url):
    """The generator puts every arrow forward in a hidden order: no cycle,
    the graph in one piece, and the asked number of arrows when it fits."""
    page = page_for(browser, base_url, '/graph?algo=topological_sort', width=1440)
    results = page.evaluate("""() => {
        const out = [];
        for (let t = 0; t < 300; t++) {
            const n = 2 + (t % 9), ids = Array.from({length: n}, (_, i) => String.fromCharCode(65 + i));
            const asked = t % 20;
            out.push({n, asked, edges: randomDag(ids, asked)});
        }
        return out;
    }""")
    for r in results:
        n, edges = r['n'], r['edges']
        graph = {chr(65 + i): [] for i in range(n)}
        for u, v in edges:
            graph[u].append(v)
        body = endpoint(graph)
        assert body['cycle'] == [] and len(body['order']) == n
        assert len({tuple(e) for e in edges}) == len(edges)
        assert len(edges) == max(n - 1, min(r['asked'], n * (n - 1) // 2))
        # One piece: ignoring direction, every node is reached from A.
        seen, todo = {'A'}, ['A']
        while todo:
            u = todo.pop()
            for a, b in edges:
                for x, y in ((a, b), (b, a)):
                    if x == u and y not in seen:
                        seen.add(y)
                        todo.append(y)
        assert len(seen) == n
    # And the button: a random DAG goes straight to a run with an order.
    page.evaluate("document.getElementById('randomRadio').click()")
    page.evaluate('generateRandomGraph()')
    page.wait_for_function('Workspace.current && Workspace.current.steps.length > 0')
    page.evaluate('Workspace.current.go(Workspace.current.steps.length - 1)')
    assert page.get_attribute('#topo-message', 'data-outcome') == 'found'
    assert page.errors == []
    page.ctx.close()


def test_typed_directed_input_and_its_errors(browser, base_url):
    page = page_for(browser, base_url, '/graph?algo=topological_sort', width=1440)
    assert page.is_visible('#directed-format-guide') or page.evaluate(
        "document.getElementById('directed-format-guide').style.display") == 'block'
    assert not page.is_visible('.input-section')
    page.fill('#graph-input', '3 2\nA B\nB A\nLone')
    page.click('#run-button')
    page.wait_for_function('Workspace.current.steps.length > 0')
    page.evaluate('Workspace.current.go(Workspace.current.steps.length - 1)')
    assert page.evaluate("[...document.querySelectorAll('#topo-order .topo-chip')].map(c => c.textContent)") == ['Lone']
    assert 'A → B → A is a cycle' in page.text_content('#topo-message')
    page.fill('#graph-input', '2 1\nA B 5')
    page.click('#run-button')
    page.wait_for_function("document.getElementById('graph-input-error').textContent.length > 0 || "
                           "document.getElementById('graph-error').textContent.length > 0")
    text = page.text_content('#graph-input-error') + page.text_content('#graph-error')
    assert 'the node the arrow leaves and the node it reaches' in text
    page.ctx.close()


def test_reduced_motion_settles_at_once(browser, base_url):
    page = page_for(browser, base_url, '/graph?algo=topological_sort', width=1440, reduced='reduce')
    load(page, 'loadCycleDemo')
    page.evaluate('Workspace.current.go(Workspace.current.steps.length - 1)')
    # The simulation is stopped and the colours are still there.
    first = page.evaluate("[...document.querySelectorAll('#graph-container circle')].map(c => c.getAttribute('cx'))")
    page.wait_for_timeout(400)
    second = page.evaluate("[...document.querySelectorAll('#graph-container circle')].map(c => c.getAttribute('cx'))")
    assert first == second
    assert page.evaluate("document.querySelectorAll('#graph-container circle.node-current').length") == 3
    assert page.errors == []
    page.ctx.close()
