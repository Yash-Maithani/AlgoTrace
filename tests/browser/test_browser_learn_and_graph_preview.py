"""The Phase 22 fixes in a real browser: /learn fills every figure from the
lesson files, and every graph page draws its starter graph before a run and
redraws it when the input is edited.

The same fixes without a browser: tests/unit/test_learn_and_home.py.
"""
import pytest

from browser_helpers import SKIP_REASON, available, page_for


@pytest.mark.skipif(not available(), reason=SKIP_REASON)
def test_learn_cards_match_the_lessons_in_a_browser(browser, base_url):
    page = page_for(browser, base_url, '/learn', width=1440)
    rows = page.evaluate("""() => [...document.querySelectorAll('[data-lesson][data-figure]')].map(d => {
        const l = window.LESSONS[d.dataset.lesson].complexity, f = d.dataset.figure;
        return [d.dataset.lesson, f, d.querySelector('.sr-only').textContent,
                f === 'space' ? l.space.value : l.time[f].value];
    })""")
    assert rows
    for lesson, figure, spoken, value in rows:
        assert spoken == value.replace('O(', 'Big O of ', 1)[:-1], (lesson, figure, spoken, value)
    heap = page.evaluate("""() => [...document.querySelectorAll('[data-lesson="heap_sort"][data-figure="best"]')]
        .map(d => d.querySelector('[aria-hidden]').textContent)""")
    assert heap and set(heap) == {'O(n)'}
    assert page.errors == []
    page.ctx.close()


# ---------------------------------------------------------------------------
# Graph pages draw their starter graph on load
# ---------------------------------------------------------------------------

GRAPHS = ['bfs', 'dfs', 'dijkstra', 'prim', 'kruskal', 'floyd_warshall', 'bellman_ford', 'topological_sort']


@pytest.mark.skipif(not available(), reason=SKIP_REASON)
@pytest.mark.parametrize('algo', GRAPHS)
def test_the_starter_graph_is_drawn_before_run_and_edits_redraw(browser, base_url, algo):
    page = page_for(browser, base_url, '/graph?algo=' + algo, width=1440)
    page.wait_for_selector('#graph-container g.nodes circle')
    drawn = page.evaluate("""() => ({circles: document.querySelectorAll('#graph-container g.nodes circle').length,
        nodes: nodes.length, steps: Workspace.current.steps.length,
        name: document.querySelector('#graph-container svg').getAttribute('aria-label')})""")
    assert drawn['circles'] == drawn['nodes'] > 0 and drawn['steps'] == 0
    assert 'Nodes: ' in drawn['name']
    # Run, then edit: the run goes and the edited graph is drawn and named.
    page.click('#run-button')
    page.wait_for_function('Workspace.current.steps.length > 0', timeout=10000)
    extra = 'Zed' if algo != 'topological_sort' else 'Zed'
    text = page.input_value('#graph-input')
    lines = text.split('\n')
    if algo == 'topological_sort':
        edited = '\n'.join(lines + ['Zed'])
    else:
        head = lines[0].split()
        weight = ' 3' if algo not in ('bfs', 'dfs') else ''
        body = lines[1:1 + int(head[1])] + ['A %s%s' % (extra, weight)]
        tail = lines[1 + int(head[1]):]
        edited = '\n'.join(['%d %d' % (int(head[0]) + 1, int(head[1]) + 1)] + body + tail)
    page.fill('#graph-input', edited)
    page.wait_for_function("nodes.some(n => n.id === 'Zed')", timeout=5000)
    after = page.evaluate("""() => ({steps: Workspace.current.steps.length,
        circles: document.querySelectorAll('#graph-container g.nodes circle').length, nodes: nodes.length,
        name: document.querySelector('#graph-container svg').getAttribute('aria-label')})""")
    assert after['steps'] == 0 and after['circles'] == after['nodes'] == drawn['nodes'] + 1
    assert 'Zed' in after['name']
    assert page.errors == []
    page.ctx.close()
