"""Phase 17 in a real browser: /compare, and the three workspaces after the
workspace.js refactor that made /compare possible.

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

VALUES = '42, 17, 93, 8, 61, 29, 75, 36, 17, 50, 3, 88'


def run_sort_json(body):
    with app.test_client() as c:
        return c.post('/run_sort', json=body).get_json()


def prepare(page, left, right, left_variant=None, right_variant=None, values=VALUES,
          left_seed=None, right_seed=None):
    """Choose both sides, type the shared input and press Run both."""
    for side, algorithm, variant, seed in (('left', left, left_variant, left_seed),
                                           ('right', right, right_variant, right_seed)):
        page.select_option('#%s-algorithm' % side, algorithm)
        if variant:
            key = page.get_attribute('.compare-pick[data-side="%s"] [data-variant-for="%s"]'
                                     % (side, algorithm), 'data-variant-key')
            page.check('#%s-variant-%s-%s' % (side, key, variant))
        if seed is not None:
            page.fill('#%s-seed' % side, str(seed))
    page.check('#manual-input-choice')
    page.fill('#manual-input', values)
    page.click('#run-button')
    page.wait_for_function('Compare.left.ws.steps.length > 0 && Compare.right.ws.steps.length > 0')


def to_end(page):
    page.evaluate('Compare.group.go(Compare.group.length() - 1)')


def side_counts(page, side):
    return page.evaluate("""s => ({
        comparisons: Number(document.querySelector('#compare-' + s + ' [data-role="comparisons"]').textContent),
        second: Number(document.querySelector('#compare-' + s + ' [data-role="second"]').textContent),
        label: document.querySelector('#compare-' + s + ' [data-role="second-label"]').textContent
    })""", side)


# ---------------------------------------------------------------------------
# Counts are /run_sort's
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('left,lv,right,rv,label_right', [
    ('Bubble Sort', 'off', 'Merge Sort', 'le', 'Writes'),
    ('Bubble Sort', 'on', 'Insertion Sort', None, 'Shifts'),
    ('Quick Sort', 'middle', 'Heap Sort', None, 'Swaps'),
    ('Selection Sort', None, 'Quick Sort', 'last', 'Swaps'),
])
def test_final_counts_match_run_sort(browser, base_url, left, lv, right, rv, label_right):
    page = page_for(browser, base_url, '/compare')
    prepare(page, left, right, lv, rv)
    to_end(page)

    values = [int(v) for v in VALUES.split(',')]
    for side, algorithm, variant in (('left', left, lv), ('right', right, rv)):
        body = {'algorithm': algorithm, 'values': values}
        if variant:
            body['variant'] = variant
        want = run_sort_json(body)['result']
        got = side_counts(page, side)
        assert (got['comparisons'], got['second']) == (want['comparisons'], want['swaps']), (side, algorithm)
    assert side_counts(page, 'right')['label'] == label_right
    assert page.errors == []
    page.ctx.close()


def test_live_counters_follow_each_step(browser, base_url):
    page = page_for(browser, base_url, '/compare')
    prepare(page, 'Bubble Sort', 'Merge Sort')
    for tick in (0, 3, 10):
        page.evaluate('t => Compare.group.go(t)', tick)
        for side in ('left', 'right'):
            want = page.evaluate("""([s, t]) => {
                const ws = Compare[s].ws; const step = ws.steps[Math.min(t, ws.steps.length - 1)];
                return [step.vars.comparisons, step.vars.swaps];
            }""", [side, tick])
            got = side_counts(page, side)
            assert [got['comparisons'], got['second']] == want
    page.ctx.close()


def test_seed_row_is_not_shown_without_a_random_pivot(browser, base_url):
    page = page_for(browser, base_url, '/compare')
    prepare(page, 'Bubble Sort', 'Quick Sort', None, 'middle')
    for side in ('left', 'right'):
        assert not page.is_visible('#compare-%s [data-role="seed-shown"]' % side)
    page.ctx.close()


def test_random_pivot_shows_its_seed_and_replays(browser, base_url):
    page = page_for(browser, base_url, '/compare')
    prepare(page, 'Quick Sort', 'Quick Sort', 'random', 'random', left_seed=4821)
    first = page.evaluate('JSON.stringify([Compare.left.ws.steps, Compare.right.ws.steps])')
    left_seed = page.input_value('#left-seed')
    right_seed = page.input_value('#right-seed')

    assert left_seed == '4821'
    assert right_seed.isdigit()                       # the server chose one
    assert page.inner_text('#compare-left [data-role="seed-value"]') == '4821'
    assert page.inner_text('#compare-right [data-role="seed-value"]') == right_seed

    page.click('#run-button')                         # the seeds stay in the fields
    page.wait_for_function('Compare.left.ws.steps.length > 0')
    page.wait_for_timeout(300)
    again = page.evaluate('JSON.stringify([Compare.left.ws.steps, Compare.right.ws.steps])')
    assert again == first

    values = [int(v) for v in VALUES.split(',')]
    want = run_sort_json({'algorithm': 'Quick Sort', 'variant': 'random', 'seed': 4821,
                          'values': values})
    assert json.loads(first)[0] == want['steps']
    page.ctx.close()


# ---------------------------------------------------------------------------
# One transport, both finish, the shorter one waits
# ---------------------------------------------------------------------------

def test_both_sides_finish_and_the_shorter_waits(browser, base_url):
    page = page_for(browser, base_url, '/compare')
    prepare(page, 'Bubble Sort', 'Merge Sort')
    lengths = page.evaluate('[Compare.left.ws.steps.length, Compare.right.ws.steps.length]')
    short, long_ = min(lengths), max(lengths)
    shorter = 'left' if lengths[0] < lengths[1] else 'right'

    page.evaluate('t => Compare.group.go(t)', short + 3)
    state = page.evaluate("""s => ({
        index: Compare[s].ws.index, last: Compare[s].ws.steps.length - 1,
        status: document.querySelector('#compare-' + s + ' [data-role="status"]').textContent,
        banner: document.getElementById('run-banner').textContent
    })""", shorter)
    assert state['index'] == state['last']
    assert 'Waiting for the other side' in state['status']
    assert state['banner'] == ''

    # Play at full speed to the end: both reach their last step.
    page.evaluate("document.getElementById('speed').value = 200")
    page.click('#play-pause')
    page.wait_for_function('Compare.group.tick >= Compare.group.length() - 1 && !Compare.group.timer',
                           timeout=30000)
    done = page.evaluate("""[Compare.left.ws.index === Compare.left.ws.steps.length - 1,
                             Compare.right.ws.index === Compare.right.ws.steps.length - 1]""")
    assert done == [True, True]
    assert page.inner_text('#step-counter').strip() == 'Step %d of %d' % (long_, long_)
    banner = page.inner_text('#run-banner')
    assert 'fewer comparisons than' in banner
    assert 'this one input' in banner
    for side in ('left', 'right'):
        assert page.inner_text('#compare-%s [data-role="status"]' % side).startswith('Finished in')

    # Stepping back off the end takes the banner away again.
    page.click('#step-back')
    assert page.inner_text('#run-banner') == ''
    assert page.errors == []
    page.ctx.close()


def test_banner_names_the_winner_and_the_margin(browser, base_url):
    page = page_for(browser, base_url, '/compare')
    prepare(page, 'Insertion Sort', 'Quick Sort', None, 'last', values='1, 2, 3, 4, 5, 6, 7, 8, 9, 10')
    to_end(page)
    # Sorted input: insertion makes n-1 = 9, quick (last pivot) n(n-1)/2 = 45.
    assert page.inner_text('#run-banner').startswith(
        'Insertion Sort used 36 fewer comparisons than Quick Sort (Pivot: Last): 9 against 45.')
    page.ctx.close()


def test_the_same_algorithm_on_both_sides_is_told_apart(browser, base_url):
    page = page_for(browser, base_url, '/compare')
    prepare(page, 'Heap Sort', 'Heap Sort')
    to_end(page)
    assert page.inner_text('#run-banner').startswith('Both used ')
    page.ctx.close()


def test_keyboard_shortcuts_drive_both_sides(browser, base_url):
    page = page_for(browser, base_url, '/compare')
    prepare(page, 'Bubble Sort', 'Merge Sort')
    page.focus('#compare-left .compare-stage')
    page.keyboard.press('ArrowRight')
    page.keyboard.press('ArrowRight')
    assert page.evaluate('[Compare.group.tick, Compare.left.ws.index, Compare.right.ws.index]') == [2, 2, 2]
    page.keyboard.press('ArrowLeft')
    assert page.evaluate('Compare.group.tick') == 1
    page.keyboard.press('r')
    assert page.evaluate('Compare.group.tick') == 0
    page.keyboard.press(' ')
    assert page.evaluate('!!Compare.group.timer')
    page.keyboard.press(' ')
    assert page.evaluate('!Compare.group.timer')
    assert page.get_attribute('#play-pause', 'aria-keyshortcuts') == 'Space'
    assert page.query_selector('.control-bar .shortcuts') is not None
    page.ctx.close()


def test_changing_a_side_clears_the_comparison(browser, base_url):
    page = page_for(browser, base_url, '/compare')
    prepare(page, 'Bubble Sort', 'Merge Sort')
    to_end(page)
    page.select_option('#right-algorithm', 'Heap Sort')
    assert page.evaluate('[Compare.left.ws.steps.length, Compare.right.ws.steps.length]') == [0, 0]
    assert page.inner_text('#run-banner') == ''
    assert page.inner_text('#step-counter').strip() == 'Step 0 of 0'
    assert page.inner_text('#compare-right [data-role="title"]') == 'Heap Sort'
    page.ctx.close()


def test_what_to_try_sets_up_and_runs(browser, base_url):
    page = page_for(browser, base_url, '/compare')
    page.click('[data-try="2"]')       # Quick last vs Quick middle on Already sorted
    page.wait_for_function('Compare.left.ws.steps.length > 0 && Compare.right.ws.steps.length > 0')
    assert page.inner_text('#compare-left [data-role="title"]') == 'Quick Sort (Pivot: Last)'
    assert page.inner_text('#compare-right [data-role="title"]') == 'Quick Sort (Pivot: Middle)'
    values = page.evaluate('Compare.left.ws.payload.array')
    assert values == sorted(values) and len(values) == 20
    assert page.evaluate('Compare.right.ws.payload.array') == values
    assert page.get_attribute('[data-preset="sorted"]', 'aria-pressed') == 'true'
    page.ctx.close()


def test_a_random_array_is_shared_and_kept_for_replay(browser, base_url):
    page = page_for(browser, base_url, '/compare')
    page.fill('#array-size', '15')
    page.click('#run-button')
    page.wait_for_function('Compare.left.ws.steps.length > 0 && Compare.right.ws.steps.length > 0')
    left = page.evaluate('Compare.left.ws.payload.array')
    assert len(left) == 15
    assert page.evaluate('Compare.right.ws.payload.array') == left
    assert page.input_value('#manual-input') == ', '.join(str(v) for v in left)
    page.ctx.close()


def test_no_learn_panel_and_no_predict(browser, base_url):
    page = page_for(browser, base_url, '/compare')
    assert page.query_selector('#learn-panel') is None
    assert page.query_selector('#predict-toggle') is None
    assert page.evaluate('typeof Workspace.current') == 'undefined'
    assert page.get_attribute('#compare-left [data-role="open"]', 'href') == '/sorting?algorithm=Bubble%20Sort'
    page.ctx.close()


# ---------------------------------------------------------------------------
# Layout, themes, reduced motion
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('width', [375, 768, 899, 900, 1440])
@pytest.mark.parametrize('scheme', ['light', 'dark'])
def test_layout(browser, base_url, width, scheme):
    page = page_for(browser, base_url, '/compare', width=width, scheme=scheme)
    prepare(page, 'Bubble Sort', 'Merge Sort')
    page.evaluate('Compare.group.go(5)')
    layout = page.evaluate("""() => {
        const box = s => document.querySelector(s).getBoundingClientRect();
        const l = box('#compare-left .compare-stage'), r = box('#compare-right .compare-stage');
        const bars = [...document.querySelectorAll('.compare-stage .bar')].map(b => b.getBoundingClientRect());
        return {
            hscroll: document.documentElement.scrollWidth > innerWidth,
            sideBySide: Math.abs(l.top - r.top) < 1 && r.left >= l.right,
            stacked: r.top >= l.bottom,
            barsInside: bars.every(b => b.width > 0 && b.right <= innerWidth + 0.5),
            bg: getComputedStyle(document.body).backgroundColor,
            theme: document.documentElement.getAttribute('data-theme')
        };
    }""")
    assert not layout['hscroll'], 'horizontal scroll at %d' % width
    if width >= 900:
        assert layout['sideBySide'], 'stages are not side by side at %d' % width
    else:
        assert layout['stacked'], 'stages are not stacked at %d' % width
    assert layout['barsInside']
    assert layout['theme'] == scheme
    assert page.errors == []
    page.ctx.close()


def test_reduced_motion_stops_the_bars_moving_but_keeps_colour(browser, base_url):
    page = page_for(browser, base_url, '/compare', reduced='reduce')
    prepare(page, 'Bubble Sort', 'Merge Sort')
    transition = page.evaluate("""() => {
        const s = getComputedStyle(document.querySelector('.compare-stage .bar'));
        return [s.transitionProperty, s.transitionDuration];
    }""")
    assert transition[0] == 'background-color'
    # The same rule as /sorting, because it is the same bar.
    other = page_for(browser, base_url, '/sorting', reduced='reduce')
    other.check('#manual-input-choice')
    other.fill('#manual-input', VALUES)
    other.click('#run-button')
    other.wait_for_function('Workspace.current.steps.length > 0')
    assert other.evaluate("getComputedStyle(document.querySelector('.bar')).transitionProperty") == transition[0]
    page.ctx.close()
    other.ctx.close()


# ---------------------------------------------------------------------------
# The three workspaces after the refactor
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('path,ready', [
    ('/sorting', "document.getElementById('run-button').click()"),
    ('/searching', "document.getElementById('run-button').click()"),
    # The graph page needs a graph before Run does anything.
    ('/graph?algo=bfs', "generateRandomGraph(); setTimeout(() => document.getElementById('run-button').click(), 800)"),
])
def test_single_workspaces_still_run_play_and_step(browser, base_url, path, ready):
    page = page_for(browser, base_url, path)
    page.evaluate(ready)
    page.wait_for_function('Workspace.current && Workspace.current.steps.length > 1', timeout=15000)
    assert page.inner_text('#step-counter').strip().startswith('Step 1 of ')
    page.click('#step-forward')
    assert page.evaluate('Workspace.current.index') == 1
    page.keyboard.press('r')
    assert page.evaluate('Workspace.current.index') == 0
    assert page.query_selector('.control-bar .shortcuts') is not None
    page.evaluate("document.getElementById('speed').value = document.getElementById('speed').max")
    page.click('#play-pause')
    page.wait_for_function('Workspace.current.index === Workspace.current.steps.length - 1', timeout=60000)
    if page.query_selector('#run-banner'):         # the graph page has a results panel instead
        assert page.inner_text('#run-banner').strip() != ''
    assert page.errors == []
    page.ctx.close()
