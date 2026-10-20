"""Review findings, each checked in a real browser as a visitor would meet it.

  2  A run on screen is cleared when the input it was made from changes.
  3  Graph pages open with a graph to run, and every Learn panel says what to do
     before a run.
  4  The graph canvas and the A* grid have a role and a name.
  5  The Counting Sort count list reads at 4.5:1 or better in both themes.

(Finding 1, hidden things staying hidden, is tests/test_browser_visibility.py.)

Needs Playwright; see tests/test_browser_phase14.py and requirements-dev.txt.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_helpers import SKIP_REASON, available, page_for

pytestmark = pytest.mark.skipif(not available(), reason=SKIP_REASON)

IDLE = 'Run the algorithm to see each step explained'
GRAPHS = ['bfs', 'dfs', 'dijkstra', 'prim', 'kruskal', 'floyd_warshall', 'bellman_ford', 'topological_sort']


# ---------------------------------------------------------------------------
# 2. Changing the input clears the run
# ---------------------------------------------------------------------------

def sorting_with_a_run(page, algorithm='Bubble Sort'):
    page.click('#algo-picker [data-algorithm="%s"]' % algorithm)
    page.check('#manual-input-choice')
    page.fill('#manual-input', '5, 3, 8, 1, 9, 2')
    page.click('#run-button')
    page.wait_for_function('Workspace.current.steps.length > 0')
    page.evaluate('Workspace.current.go(4)')
    assert page.is_visible('#array-container')


def assert_sorting_cleared(page):
    assert page.evaluate('Workspace.current.steps.length') == 0
    assert page.evaluate('Workspace.current.payload') is None
    assert page.inner_text('#step-counter').strip() == 'Step 0 of 0'
    assert page.is_visible('#stage-empty') and not page.is_visible('#array-container')
    assert page.inner_text('#run-banner').strip() == ''
    assert page.is_disabled('#play-pause') and page.is_disabled('#step-forward')


SORTING_EDITS = [
    ('a preset', lambda p: p.click('[data-preset="reversed"]')),
    ('another preset', lambda p: p.click('[data-preset="random"]')),
    ('typing in the values', lambda p: p.type('#manual-input', '7')),
    ('replacing the values', lambda p: p.fill('#manual-input', '4, 2, 9')),
    ('switching to a random array', lambda p: p.check('#random-input')),
    ('changing the array size', lambda p: p.fill('#array-size', '12') if p.is_visible('#array-size') else None),
]


@pytest.mark.parametrize('name,edit', SORTING_EDITS, ids=[n for n, _ in SORTING_EDITS])
def test_sorting_clears_the_run_when_the_input_changes(browser, base_url, name, edit):
    page = page_for(browser, base_url, '/sorting')
    sorting_with_a_run(page)
    if name == 'changing the array size':
        page.check('#random-input')                     # the size field only shows for a random array
        page.click('#run-button')
        page.wait_for_function('Workspace.current.steps.length > 0')
    edit(page)
    assert_sorting_cleared(page)
    # And Run makes a fresh one from what is in the box now.
    page.click('#run-button')
    page.wait_for_function('Workspace.current.steps.length > 0')
    assert page.is_visible('#array-container')
    page.ctx.close()


def test_the_call_tree_and_predict_state_go_with_the_cleared_run(browser, base_url):
    page = page_for(browser, base_url, '/sorting', width=1440, height=900)
    sorting_with_a_run(page, 'Merge Sort')
    page.check('#predict-toggle')
    assert page.evaluate("document.querySelectorAll('.ct-node').length") > 0
    page.click('[data-preset="sorted"]')
    assert page.evaluate("document.querySelectorAll('.ct-node').length") == 0
    assert page.query_selector('.predict-card') is None and not page.is_visible('.predict-score')
    page.ctx.close()


def test_choosing_a_preset_with_no_run_changes_nothing_else(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    page.click('[data-preset="reversed"]')
    assert page.is_visible('#stage-empty') and page.errors == []
    page.ctx.close()


def searching_with_a_run(page, algorithm='linear_search'):
    page.click('#algo-picker [data-algorithm="%s"]' % algorithm)
    page.fill('#array-input', '4, 8, 15, 16, 23, 42, 50')
    page.fill('#target-input', '23')
    page.click('#run-button')
    page.wait_for_function('Workspace.current.steps.length > 0')
    page.evaluate('Workspace.current.go(2)')
    assert page.is_visible('#cell-row')


def assert_searching_cleared(page):
    assert page.evaluate('Workspace.current.steps.length') == 0
    assert page.inner_text('#step-counter').strip() == 'Step 0 of 0'
    assert page.is_visible('#stage-empty') and not page.is_visible('#cell-row')
    assert page.inner_text('#run-banner').strip() == ''
    assert page.is_disabled('#play-pause')


SEARCHING_EDITS = [
    ('a preset', lambda p: p.click('[data-preset="reversed"]')),
    ('the sorted preset', lambda p: p.click('[data-preset="sorted"]')),
    ('typing in the values', lambda p: p.type('#array-input', '9')),
    ('typing a target', lambda p: p.fill('#target-input', '8')),
    ('a random array', lambda p: p.click('#random-array')),
    ('sorting the values', lambda p: p.click('#sort-array')),
    ('picking a target that exists', lambda p: p.click('#pick-present')),
    ('picking a target that does not', lambda p: p.click('#pick-absent')),
]


@pytest.mark.parametrize('name,edit', SEARCHING_EDITS, ids=[n for n, _ in SEARCHING_EDITS])
def test_searching_clears_the_run_when_the_input_changes(browser, base_url, name, edit):
    page = page_for(browser, base_url, '/searching')
    searching_with_a_run(page)
    edit(page)
    assert_searching_cleared(page)
    page.ctx.close()


def test_searching_binary_run_is_cleared_by_a_preset_too(browser, base_url):
    page = page_for(browser, base_url, '/searching')
    searching_with_a_run(page, 'binary_search')
    page.click('[data-preset="equal"]')
    assert_searching_cleared(page)
    page.ctx.close()


# ---------------------------------------------------------------------------
# 3. A graph to run, and a message before the run
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('algo', GRAPHS)
def test_every_graph_page_opens_with_a_graph_that_runs_at_once(browser, base_url, algo):
    page = page_for(browser, base_url, '/graph?algo=' + algo, width=1440)
    text = page.input_value('#graph-input')
    assert text.strip()
    first = text.splitlines()[0].split()
    assert len(first) == 2 and all(part.isdigit() for part in first), text      # "nodes edges"
    if algo in ('bfs', 'dfs', 'dijkstra', 'prim', 'bellman_ford'):
        assert page.input_value('#start-node') == 'A'
        assert text.splitlines()[-1] == 'A'

    page.click('#run-button')                                                   # nothing else first
    page.wait_for_function('Workspace.current.steps.length > 0', timeout=10000)
    assert not page.is_visible('#graph-error'), page.inner_text('#graph-error')
    assert page.evaluate('Workspace.current.steps.length') > 3
    assert page.errors == []
    page.ctx.close()


def test_the_directed_sort_opens_with_a_graph_that_has_no_cycle(browser, base_url):
    page = page_for(browser, base_url, '/graph?algo=topological_sort', width=1440)
    assert page.input_value('#graph-input').startswith('7 7\nMath Calc')
    page.click('#run-button')
    page.wait_for_function('Workspace.current.steps.length > 0', timeout=10000)
    last = page.evaluate("Workspace.current.metaAt(Workspace.current.steps.length - 2)")
    assert 'cycle' not in last['explain']['beginner'].lower()
    done = page.evaluate("Workspace.current.metaAt(Workspace.current.steps.length - 1)")
    assert done['action'] == 'done' and len(done['indices']) == 7                 # every course is in the order
    page.ctx.close()


def test_a_typed_graph_is_not_overwritten_by_the_starter(browser, base_url):
    page = page_for(browser, base_url, '/graph?algo=bfs')
    page.fill('#graph-input', '3 2\nA B\nB C\nA')
    page.reload()
    # A reload gives the starter again; typing after load is what must survive a later edit.
    assert page.input_value('#graph-input').startswith('6 7')
    page.fill('#graph-input', '3 2\nA B\nB C\nA')
    page.click('#run-button')
    page.wait_for_function('Workspace.current.steps.length > 0')
    assert page.input_value('#graph-input').startswith('3 2')
    page.ctx.close()


LEARN_PAGES = [
    ('/sorting', 'sorting'), ('/searching', 'searching'), ('/graph?algo=bfs', 'graph'),
    ('/graph?algo=topological_sort', 'graph'), ('/graph?algo=astar', 'astar'),
]


@pytest.mark.parametrize('path,kind', LEARN_PAGES)
def test_every_learn_panel_says_what_to_do_before_a_run(browser, base_url, path, kind):
    page = page_for(browser, base_url, path, width=1440, height=900)
    assert page.is_visible('.explain-idle') and page.inner_text('.explain-idle').strip() == IDLE
    for gone in ('.explain-head', '.explain-text', '.explain-why'):
        assert not page.is_visible('#learn-body-explain ' + gone), gone         # no blank lines
    # The other tabs have content of their own, not blank space.
    for tab in ('about', 'complexity', 'code'):
        page.click('#learn-tab-' + tab)
        assert page.inner_text('#learn-body-' + tab).strip(), tab
    page.ctx.close()


def run_any(page, kind):
    if kind == 'sorting':
        page.check('#manual-input-choice')
        page.fill('#manual-input', '5, 3, 8, 1')
    elif kind == 'searching':
        page.fill('#array-input', '4, 8, 15, 16')
        page.fill('#target-input', '15')
    page.click('#run-button')
    page.wait_for_function('Workspace.current.steps.length > 0', timeout=10000)


@pytest.mark.parametrize('path,kind', LEARN_PAGES[:3])
def test_the_message_gives_way_to_the_step_and_returns_when_the_run_goes(browser, base_url, path, kind):
    page = page_for(browser, base_url, path, width=1440, height=900)
    run_any(page, kind)
    page.click('#learn-tab-explain')
    assert not page.is_visible('.explain-idle') and page.is_visible('#learn-body-explain .explain-text')
    assert page.inner_text('#learn-body-explain .explain-text').strip()
    if kind in ('sorting', 'searching'):
        page.click('[data-preset="sorted"]')                                   # the run is thrown away
        page.click('#learn-tab-explain')
        assert page.is_visible('.explain-idle')
    page.ctx.close()


def test_compare_has_no_learn_panel_to_fill(browser, base_url):
    page = page_for(browser, base_url, '/compare')
    assert page.query_selector('#learn-panel') is None
    page.ctx.close()


# ---------------------------------------------------------------------------
# 4. A role and a name for the canvas and the grid
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('algo', GRAPHS)
def test_the_graph_canvas_is_an_image_with_a_name_that_says_what_it_shows(browser, base_url, algo):
    page = page_for(browser, base_url, '/graph?algo=' + algo, width=1440)
    svg = '#graph-container svg.graph-svg'
    assert page.get_attribute(svg, 'role') == 'img'
    assert 'empty' in page.get_attribute(svg, 'aria-label') and 'Run the algorithm' in page.get_attribute(svg, 'aria-label')

    page.click('#run-button')
    page.wait_for_function('Workspace.current.steps.length > 0', timeout=10000)
    page.evaluate('Workspace.current.go(Workspace.current.steps.length - 1)')
    label = page.get_attribute(svg, 'aria-label')
    nodes, edges = page.evaluate("[nodes.length, links.length]")
    assert page.get_attribute(svg, 'role') == 'img'
    assert ('%d nodes and %d edges' % (nodes, edges)) in label, label
    assert label.startswith('Directed graph' if algo == 'topological_sort' else 'Graph'), label
    assert 'Nodes: ' in label
    assert (' to ' in label) if algo == 'topological_sort' else (' and ' in label)
    if algo in ('dijkstra', 'prim', 'kruskal', 'floyd_warshall', 'bellman_ford'):
        assert '(weight ' in label                                              # weighted edges say so
    page.ctx.close()


def test_the_astar_grid_has_a_role_and_a_name_from_the_start(browser, base_url):
    page = page_for(browser, base_url, '/graph?algo=astar', width=1440)
    host = '#grid-board'
    assert page.get_attribute(host, 'role') == 'grid'
    label = page.get_attribute(host, 'aria-label')
    assert label.startswith('Grid, ') and ' rows by ' in label and ' columns' in label
    assert 'Start at row' in label and 'goal at row' in label and 'walls' in label
    assert page.get_attribute(host, 'aria-describedby') == 'grid-help'
    assert page.evaluate("document.querySelectorAll('#grid-board [role=\"row\"]').length") > 3
    cell = page.evaluate("(() => { const c = document.querySelector('#grid-board [role=\"gridcell\"]');"
                         " return [c.getAttribute('aria-label'), c.closest('[role=\"row\"]') !== null]; })()")
    assert cell[0] and cell[1]
    page.ctx.close()


# ---------------------------------------------------------------------------
# 5. The count list reads at 4.5:1
# ---------------------------------------------------------------------------

CONTRAST = """() => {
    const parse = c => c.match(/[\\d.]+/g).map(Number);
    const over = (fg, bg) => { const a = fg[3] === undefined ? 1 : fg[3];
        return [0, 1, 2].map(i => fg[i] * a + bg[i] * (1 - a)); };
    const lum = ([r, g, b]) => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
                                 return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
    const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
    const opacity = e => { let o = 1; for (; e; e = e.parentElement) o *= Number(getComputedStyle(e).opacity); return o; };
    const out = {};
    for (const cell of document.querySelectorAll('.count-cell:not([hidden])')) {
        const state = cell.dataset.state;
        const value = cell.querySelector('.count-value');
        const bg = parse(getComputedStyle(cell).backgroundColor);
        const fg = over(parse(getComputedStyle(value).color), bg);
        const r = ratio(fg, bg.slice(0, 3));
        if (!(state in out) || r < out[state].ratio) out[state] = {ratio: r, opacity: opacity(cell)};
    }
    return out;
}"""


@pytest.mark.parametrize('scheme', ['light', 'dark'])
def test_every_count_list_state_reads_at_4_5_to_1_in_both_themes(browser, base_url, scheme):
    page = page_for(browser, base_url, '/sorting?algorithm=Counting+Sort', width=1440, height=900, scheme=scheme)
    page.check('#manual-input-choice')
    page.fill('#manual-input', '5, 3, 8, 1, 9, 3, 12, 0, 47, 99, 47')
    page.click('#run-button')
    page.wait_for_function('Workspace.current.steps.length > 0')
    seen = {}
    for i in range(page.evaluate('Workspace.current.steps.length')):
        page.evaluate('Workspace.current.go(%d)' % i)
        for state, info in page.evaluate(CONTRAST).items():
            if state not in seen or info['ratio'] < seen[state]['ratio']:
                seen[state] = info
    assert {'empty', 'counted', 'read', 'active'} <= set(seen), seen          # the read slot was reached
    for state, info in seen.items():
        assert info['ratio'] >= 4.5, (scheme, state, info)
        assert info['opacity'] == 1, (scheme, state, 'dimmed with opacity again')
    page.ctx.close()


def test_the_read_slot_is_still_told_apart_without_colour_or_opacity(browser, base_url):
    page = page_for(browser, base_url, '/sorting?algorithm=Counting+Sort', width=1440, height=900)
    page.check('#manual-input-choice')
    page.fill('#manual-input', '5, 3, 8, 1, 9, 3, 12, 0, 47, 99, 47')
    page.click('#run-button')
    page.wait_for_function('Workspace.current.steps.length > 0')
    for i in range(page.evaluate('Workspace.current.steps.length')):
        page.evaluate('Workspace.current.go(%d)' % i)
        if page.query_selector('.count-cell[data-state="read"]'):
            break
    got = page.evaluate("""() => {
        const read = getComputedStyle(document.querySelector('.count-cell[data-state="read"]'));
        const counted = document.querySelector('.count-cell[data-state="counted"]');
        return {read: [read.borderStyle, read.fontWeight],
                counted: counted ? [getComputedStyle(counted).borderStyle, getComputedStyle(counted).fontWeight] : null};
    }""")
    assert got['read'][0] == 'dashed' and got['read'][1] == '400', got
    page.ctx.close()
