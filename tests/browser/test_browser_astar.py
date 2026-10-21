"""Phase 21 in a real browser: the A* grid workspace.

Drawing and erasing walls by pointer and by keyboard, moving the start and
the goal, the presets, the Dijkstra button and the result line, Predict on
the grid, the page at 375, 768 and 1440 in both themes, and reduced motion.

Needs Playwright (requirements-dev.txt); skips with a warning without it.
Marked slow through tests/conftest.py, like every browser test.
"""
import json

import pytest

from browser_helpers import SKIP_REASON, available, page_for
from wsgi import app

pytestmark = pytest.mark.skipif(not available(), reason=SKIP_REASON)

PAGE = '/graph?algo=astar'


def state(page):
    return page.evaluate('GridPage.grid.state()')


def kinds(page):
    return page.evaluate("""() => Object.fromEntries([...document.querySelectorAll('.grid-cell')]
        .map(c => [c.dataset.r + ',' + c.dataset.c, c.dataset.kind]))""")


def center(page, r, c):
    page.locator('#grid-board').scroll_into_view_if_needed()
    box = page.locator('#cell-%d-%d' % (r, c)).bounding_box()
    return box['x'] + box['width'] / 2, box['y'] + box['height'] / 2


def run(page, button='#run-button'):
    page.click(button)
    page.wait_for_function('Workspace.current.steps.length > 0')


def endpoint(body):
    with app.test_client() as c:
        return c.post('/run_astar', data=json.dumps(body), content_type='application/json').get_json()


# ---------------------------------------------------------------------------
# Layout, at every width and in both themes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('width', [375, 768, 1440])
@pytest.mark.parametrize('scheme', ['light', 'dark'])
def test_layout(browser, base_url, width, scheme):
    page = page_for(browser, base_url, PAGE, width=width, scheme=scheme)
    s = state(page)
    assert (s['rows'], s['cols']) == ((8, 10) if width < 600 else (12, 20))
    run(page)
    page.evaluate('Workspace.current.go(Math.floor(Workspace.current.steps.length / 2))')
    info = page.evaluate("""() => {
        const box = el => el.getBoundingClientRect();
        const stage = document.getElementById('stage'), board = document.getElementById('grid-board');
        const cell = box(document.querySelector('.grid-cell'));
        return {
            scroll: document.documentElement.scrollWidth - document.documentElement.clientWidth,
            inside: box(board).left >= box(stage).left - 1 && box(board).right <= box(stage).right + 1,
            next: stage.nextElementSibling.classList.contains('control-bar'),
            cell: cell.width,
            open: document.querySelectorAll('.grid-cell[data-state="open"]').length,
            closed: document.querySelectorAll('.grid-cell[data-state="closed"]').length,
            current: document.querySelectorAll('.grid-cell[data-state="current"]').length,
            shownF: [...document.querySelectorAll('.grid-cell[data-state="closed"] .cell-f')]
                .some(f => getComputedStyle(f).display !== 'none' && f.textContent !== '')
        };
    }""")
    assert info['scroll'] <= 0 and info['inside'] and info['next']
    assert info['cell'] >= 24
    assert info['open'] > 0 and info['closed'] > 0 and info['current'] == 1
    assert info['shownF']
    assert page.errors == []
    page.ctx.close()


def test_a_big_cell_shows_g_h_and_f(browser, base_url):
    page = page_for(browser, base_url, PAGE, width=1440)
    page.fill('#grid-rows', '5')
    page.fill('#grid-cols', '6')
    page.dispatch_event('#grid-cols', 'change')
    page.dispatch_event('#grid-rows', 'change')
    page.click('[data-grid-preset="empty"]')
    run(page)
    page.evaluate('Workspace.current.go(3)')
    info = page.evaluate("""() => {
        const board = document.getElementById('grid-board');
        const open = document.querySelector('.grid-cell[data-state="open"], .grid-cell[data-state="current"]');
        return {detail: board.dataset.detail, f: open.querySelector('.cell-f').textContent,
                gh: open.querySelector('.cell-gh').textContent,
                ghShown: getComputedStyle(open.querySelector('.cell-gh')).display !== 'none',
                label: open.getAttribute('aria-label')};
    }""")
    assert info['detail'] == 'full' and info['ghShown']
    g, h = map(int, info['gh'].split())
    assert int(info['f']) == g + h
    assert ('g %d, h %d, f %s' % (g, h, info['f'])) in info['label']
    page.ctx.close()


# ---------------------------------------------------------------------------
# Editing
# ---------------------------------------------------------------------------

def test_drag_draws_and_erases_walls_and_moves_start_and_goal(browser, base_url):
    page = page_for(browser, base_url, PAGE, width=1440)
    page.click('[data-grid-preset="empty"]')
    points = [center(page, 2, c) for c in (3, 4, 5, 6)]
    page.mouse.move(*points[0])
    page.mouse.down()
    for point in points[1:]:
        page.mouse.move(*point)
    page.mouse.up()
    walls = {tuple(w) for w in state(page)['walls']}
    assert walls == {(2, 3), (2, 4), (2, 5), (2, 6)}
    # Pressing on a wall rubs out.
    page.mouse.move(*center(page, 2, 4))
    page.mouse.down()
    page.mouse.move(*center(page, 2, 5))
    page.mouse.up()
    assert {tuple(w) for w in state(page)['walls']} == {(2, 3), (2, 6)}
    # Dragging S moves the start, and a wall under it goes.
    s = state(page)['start']
    page.mouse.move(*center(page, *s))
    page.mouse.down()
    page.mouse.move(*center(page, 2, 3))
    page.mouse.up()
    assert state(page)['start'] == [2, 3] and [2, 3] not in state(page)['walls']
    assert kinds(page)['2,3'] == 'start'
    page.ctx.close()


def test_keyboard_draws_walls_and_places_start_and_goal(browser, base_url):
    page = page_for(browser, base_url, PAGE, width=1440)
    page.click('[data-grid-preset="empty"]')
    page.focus('#grid-board')
    assert page.get_attribute('#grid-board', 'role') == 'grid'
    assert page.get_attribute('#grid-board', 'aria-describedby') == 'grid-help'
    for key in ('ArrowDown', 'ArrowRight', 'ArrowRight'):
        page.keyboard.press(key)
    assert page.get_attribute('#grid-board', 'aria-activedescendant') == 'cell-1-2'
    page.keyboard.press('Space')
    assert [1, 2] in state(page)['walls']
    assert 'Wall added at row 1, column 2.' in page.text_content('#grid-status')
    page.keyboard.press('ArrowRight')
    page.keyboard.press('Enter')
    page.keyboard.press('ArrowLeft')
    page.keyboard.press('Space')
    assert state(page)['walls'] == [[1, 3]]
    page.keyboard.press('ArrowDown')
    page.keyboard.press('s')
    assert state(page)['start'] == [2, 2]
    page.keyboard.press('ArrowRight')
    page.keyboard.press('ArrowRight')
    page.keyboard.press('g')
    assert state(page)['goal'] == [2, 4]
    # The workspace's own Space, Left and Right do nothing while the grid has focus.
    assert page.evaluate('Workspace.current.steps.length') == 0
    run(page)
    page.focus('#grid-board')
    page.keyboard.press('ArrowRight')
    assert page.evaluate('Workspace.current.index') == 0
    # An edit throws the run away, because it no longer describes the grid.
    page.keyboard.press('Space')
    assert page.evaluate('Workspace.current.steps.length') == 0
    assert page.text_content('#step-counter').strip() == 'Step 0 of 0'
    page.ctx.close()


# ---------------------------------------------------------------------------
# Running: presets, the result line, Dijkstra
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('preset', ['empty', 'gap', 'maze', 'nopath'])
def test_presets_run_to_their_result(browser, base_url, preset):
    page = page_for(browser, base_url, PAGE, width=1440)
    page.click('[data-grid-preset="%s"]' % preset)
    run(page)
    body = endpoint(dict(state(page), heuristic='manhattan'))
    page.evaluate('Workspace.current.go(Workspace.current.steps.length - 1)')
    banner = page.text_content('#run-banner')
    r = body['result']
    if preset == 'nopath':
        assert page.get_attribute('#run-banner', 'data-outcome') == 'missing'
        assert banner.startswith('No path: walls cut the goal off from the start.')
        assert page.evaluate("document.querySelectorAll('.grid-cell[data-state=\"path\"]').length") == 0
    else:
        assert banner.startswith('A* found a shortest path of %d steps after expanding %d cells.'
                                 % (r['length'], r['expanded']))
        assert 'Dijkstra (A* with h = 0) on the same grid expands %d cells' % r['other']['expanded'] in banner
        assert page.evaluate("document.querySelectorAll('.grid-cell[data-state=\"path\"], "
                             ".grid-cell[data-kind=\"start\"][data-state=\"path\"]').length") == r['length'] + 1
    assert 'These counts are for this one grid' in banner
    page.ctx.close()


def test_dijkstra_button_runs_the_same_grid_with_h_zero(browser, base_url):
    page = page_for(browser, base_url, PAGE, width=1440)
    page.click('[data-grid-preset="gap"]')
    run(page, '#run-dijkstra')
    payload = page.evaluate('Workspace.current.payload')
    assert payload['heuristic'] == 'zero'
    assert all(s['values'][1] == 0 for s in payload['steps'] if s['action'] in ('visit', 'enqueue'))
    page.evaluate('Workspace.current.go(Workspace.current.steps.length - 1)')
    banner = page.text_content('#run-banner')
    r = payload['result']
    assert banner.startswith('Dijkstra (A* with h = 0) found a shortest path')
    assert 'A* on the same grid expands %d cells' % r['other']['expanded'] in banner
    assert r['other']['expanded'] <= r['expanded']
    # Run A* again: the heuristic goes back to Manhattan.
    run(page)
    assert page.evaluate('Workspace.current.payload.heuristic') == 'manhattan'
    page.ctx.close()


def test_predict_asks_which_cell_is_expanded_next(browser, base_url):
    page = page_for(browser, base_url, PAGE, width=1440)
    page.click('[data-grid-preset="gap"]')
    run(page)
    first = page.evaluate("Predict.questionsFor('grid', Workspace.current.steps)[0].step")
    page.evaluate('n => Workspace.current.go(n)', first - 1)
    page.check('#predict-toggle')
    page.click('#step-forward')
    page.wait_for_selector('.predict-option')
    prompt = page.inner_text('.predict-prompt')
    options = page.evaluate("[...document.querySelectorAll('.predict-option')].map(b => b.dataset.option)")
    asked = page.evaluate('Workspace.current.steps[Workspace.current.index + 1]')
    assert prompt.endswith('Which cell is expanded next?')
    assert 2 <= len(options) <= 4
    assert set(options) == {c['cell'] for c in asked['candidates']}
    page.click('.predict-option[data-option="%s"]' % asked['indices'][0])
    assert page.get_attribute('.predict-result', 'data-correct') == 'true'
    page.ctx.close()


def test_learn_panel_and_reduced_motion(browser, base_url):
    page = page_for(browser, base_url, PAGE, width=1440, reduced='reduce')
    run(page)
    assert page.evaluate("getComputedStyle(document.querySelector('.grid-cell')).transitionDuration") == '0s'
    page.click('#step-forward')
    assert 'Expand' in page.inner_text('#learn-panel')
    page.click('#learn-tab-code')
    assert 'heap_push' in page.inner_text('#learn-panel')
    assert page.errors == []
    page.ctx.close()
