"""Phase 18 in a real browser: the navbar at desktop widths, and the call tree.

Needs Playwright; see tests/test_browser_phase14.py and requirements-dev.txt.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_helpers import SKIP_REASON, available, page_for

pytestmark = pytest.mark.skipif(not available(), reason=SKIP_REASON)

SCHEMES = ['light', 'dark']


# ---------------------------------------------------------------------------
# Step 0: the navbar has seven items
# ---------------------------------------------------------------------------

NAV = """() => {
    const nav = document.querySelector('nav');
    const links = [...document.querySelectorAll('.nav-links .nav-link')];
    const toggle = document.getElementById('nav-toggle');
    const theme = document.getElementById('theme-toggle');
    const logo = document.querySelector('.logo').getBoundingClientRect();
    const box = nav.getBoundingClientRect();
    const rects = links.map(l => l.getBoundingClientRect());
    const active = document.querySelector('.nav-link.active');
    return {
        menu: getComputedStyle(toggle).display !== 'none',
        height: box.height,
        linksShown: links.every(l => l.offsetParent !== null),
        tops: [...new Set(rects.map(r => Math.round(r.top)))],
        heights: [...new Set(rects.map(r => Math.round(r.height)))],
        right: Math.max(...rects.map(r => r.right)),
        left: Math.min(...rects.map(r => r.left)),
        logoRight: logo.right,
        themeRect: theme.getBoundingClientRect().toJSON(),
        toggleRect: toggle.getBoundingClientRect().toJSON(),
        overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        active: active ? {text: active.textContent.trim(), current: active.getAttribute('aria-current')} : null,
        count: links.length,
        width: innerWidth,
    };
}"""


@pytest.mark.parametrize('scheme', SCHEMES)
@pytest.mark.parametrize('width', [1024, 1100, 1280, 1440])
def test_the_seven_item_nav_is_one_row_at_desktop_widths(browser, base_url, width, scheme):
    page = page_for(browser, base_url, '/sorting', width=width, height=800, scheme=scheme)
    got = page.evaluate(NAV)

    assert got['count'] == 7 and not got['menu'] and got['linksShown']
    assert len(got['tops']) == 1, got                        # every link on one row
    assert got['heights'] == [44], got                       # none wrapped onto two lines
    assert got['height'] < 80, got                           # the header is one row tall
    assert got['left'] > got['logoRight'] and got['right'] < got['themeRect']['left'] + 1, got    # no overlap
    assert got['themeRect']['right'] <= width and got['overflow'] <= 0, got
    assert got['active'] == {'text': 'Sorting', 'current': 'page'}
    assert page.evaluate("document.querySelector('.nav-link.active').getBoundingClientRect().right") <= width
    page.ctx.close()


@pytest.mark.parametrize('scheme', SCHEMES)
@pytest.mark.parametrize('width', [900, 1023])
def test_below_1024px_the_nav_is_a_menu_on_one_row(browser, base_url, width, scheme):
    """Between 900px and 1024px it used to wrap to two rows."""
    page = page_for(browser, base_url, '/sorting', width=width, height=800, scheme=scheme)
    got = page.evaluate(NAV)

    assert got['menu'] and not got['linksShown'], got
    assert got['height'] < 80 and got['overflow'] <= 0, got
    assert got['toggleRect']['right'] <= width and got['themeRect']['right'] <= width

    page.click('#nav-toggle')
    opened = page.evaluate(NAV)
    assert opened['linksShown'] and opened['active']['current'] == 'page'
    assert page.evaluate("(() => { const r = document.querySelector('.nav-link.active').getBoundingClientRect();"
                         " return r.left >= 0 && r.right <= innerWidth && r.height > 0; })()")
    assert opened['overflow'] <= 0
    page.ctx.close()


def test_the_breakpoint_is_where_the_row_stops_fitting(browser, base_url):
    """1023px is a menu, 1024px is a row: no width in between wraps."""
    for width, menu in ((1023, True), (1024, False)):
        page = page_for(browser, base_url, '/', width=width, height=800)
        got = page.evaluate(NAV)
        assert got['menu'] is menu and got['height'] < 80, (width, got)
        page.ctx.close()


@pytest.mark.parametrize('path', ['/', '/learn', '/compare', '/searching', '/graph?algo=bfs', '/big-o'])
def test_every_page_keeps_the_nav_on_one_row(browser, base_url, path):
    page = page_for(browser, base_url, path, width=1024, height=800)
    got = page.evaluate(NAV)
    assert len(got['tops']) == 1 and got['height'] < 80 and got['overflow'] <= 0, (path, got)
    assert got['active'] is not None
    page.ctx.close()


# ---------------------------------------------------------------------------
# The call tree
# ---------------------------------------------------------------------------

TREE = "document.getElementById('call-tree')"


def start_sort(page, algorithm, values, variant=None):
    page.click('#algo-picker [data-algorithm="%s"]' % algorithm)
    if variant:
        page.click('[data-variant-for="%s"] input[value="%s"]' % (algorithm, variant))
    page.check('#manual-input-choice')
    page.fill('#manual-input', values)
    page.click('#run-button')
    page.wait_for_function('Workspace.current.steps.length > 0')


def box_states(page):
    return page.evaluate("""() => [...document.querySelectorAll('.ct-node')].map(
        n => n.dataset.state + '|' + n.dataset.result + '|' + n.querySelector('.ct-values').textContent)""")


def active_boxes(page):
    return page.evaluate("[...document.querySelectorAll('.ct-node[data-state=\"active\"]')].map("
                         "n => n.querySelector('.ct-label').textContent)")


@pytest.mark.parametrize('algorithm', ['Bubble Sort', 'Selection Sort', 'Insertion Sort', 'Heap Sort'])
def test_the_panel_is_hidden_for_sorts_without_recursion(browser, base_url, algorithm):
    page = page_for(browser, base_url, '/sorting')
    page.click('#algo-picker [data-algorithm="%s"]' % algorithm)
    assert page.evaluate(TREE + '.hidden') is True and not page.is_visible('#call-tree')
    start_sort(page, algorithm, '5, 3, 8, 1, 9, 2')
    page.evaluate('Workspace.current.go(6)')
    assert not page.is_visible('#call-tree')
    page.ctx.close()


@pytest.mark.parametrize('algorithm', ['Merge Sort', 'Quick Sort'])
def test_the_panel_shows_for_merge_and_quick_sort_even_before_a_run(browser, base_url, algorithm):
    page = page_for(browser, base_url, '/sorting')
    page.click('#algo-picker [data-algorithm="%s"]' % algorithm)
    assert page.is_visible('#call-tree') and 'Run the sort to see its calls' in page.inner_text('#call-tree')
    start_sort(page, algorithm, '5, 3, 8, 1, 9, 2')
    assert page.query_selector('.ct-node') and not page.is_visible('.call-tree-empty')
    # And it goes again when another algorithm is chosen and run.
    start_sort(page, 'Bubble Sort', '5, 3, 8')
    assert not page.is_visible('#call-tree')
    page.ctx.close()


def test_the_caption_says_what_depth_is(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    start_sort(page, 'Merge Sort', '5, 3, 8, 1')
    caption = page.inner_text('.call-tree-caption')
    assert 'Depth is how many calls deep' in caption and 'depth 0' in caption
    page.ctx.close()


def test_it_is_open_by_default_on_a_desktop_and_the_toggle_collapses_it(browser, base_url):
    page = page_for(browser, base_url, '/sorting', width=1440, height=900)
    start_sort(page, 'Merge Sort', '5, 3, 8, 1, 9, 2')
    assert page.get_attribute('#call-tree-toggle', 'aria-expanded') == 'true'
    assert page.inner_text('#call-tree-toggle') == 'Hide call tree' and page.is_visible('.call-tree-scroll')

    page.click('#call-tree-toggle')
    assert page.get_attribute('#call-tree-toggle', 'aria-expanded') == 'false'
    assert page.inner_text('#call-tree-toggle') == 'Show call tree' and not page.is_visible('.call-tree-scroll')
    assert page.get_attribute('#call-tree-toggle', 'aria-controls') == 'call-tree-body'
    assert page.evaluate("document.getElementById('call-tree-body').hidden") is True

    # It stays as the visitor left it across a new run.
    start_sort(page, 'Quick Sort', '5, 3, 8, 1, 9, 2')
    assert page.get_attribute('#call-tree-toggle', 'aria-expanded') == 'false'
    page.focus('#call-tree-toggle')
    page.keyboard.press('Enter')                                   # the keyboard opens it too
    assert page.is_visible('.call-tree-scroll')
    page.ctx.close()


def test_it_is_closed_by_default_below_900px(browser, base_url):
    page = page_for(browser, base_url, '/sorting', width=375, height=812)
    start_sort(page, 'Merge Sort', '5, 3, 8, 1, 9, 2')
    assert page.get_attribute('#call-tree-toggle', 'aria-expanded') == 'false'
    assert page.inner_text('#call-tree-toggle') == 'Show call tree' and not page.is_visible('.call-tree-scroll')
    page.click('#call-tree-toggle')
    assert page.is_visible('.call-tree-scroll') and page.is_visible('.ct-svg')
    page.ctx.close()


def test_the_panel_is_at_the_bottom_of_the_stage_column_under_the_stage(browser, base_url):
    page = page_for(browser, base_url, '/sorting', width=1440, height=900)
    start_sort(page, 'Merge Sort', '5, 3, 8, 1, 9, 2')
    order = page.evaluate("""() => {
        const y = s => document.querySelector(s).getBoundingClientRect().top;
        return [y('#stage'), y('.control-bar'), y('#call-tree')];
    }""")
    assert order == sorted(order) and order[2] > order[0]
    page.ctx.close()


@pytest.mark.parametrize('algorithm,variant', [
    ('Merge Sort', 'lt'), ('Merge Sort', 'le'),
    ('Quick Sort', 'last'), ('Quick Sort', 'middle'), ('Quick Sort', 'random'),
])
def test_the_lit_box_follows_every_step_forward_and_backward(browser, base_url, algorithm, variant):
    page = page_for(browser, base_url, '/sorting')
    start_sort(page, algorithm, '5, 3, 8, 3, 9, 1, 7, 2', variant)
    steps = page.evaluate("Workspace.current.steps.map(s => [s.action, s.depth, s.range])")
    forward = []
    appeared = 0
    for i, (action, depth, rng) in enumerate(steps):
        page.evaluate('Workspace.current.go(%d)' % i)
        lit = active_boxes(page)
        if action == 'done':
            assert lit == []
        else:
            assert lit == ['%d-%d' % tuple(rng)], (i, lit, rng)
            assert page.inner_text('.call-tree-live') == 'Sorting positions %d to %d, depth %d' % (rng[0], rng[1], depth)
        now = page.evaluate("[...document.querySelectorAll('.ct-node')].filter(n => n.dataset.state !== 'pending').length")
        assert now >= appeared                                     # calls appear as they start and stay
        appeared = now
        forward.append(box_states(page))
    # Back, from the end to the start: every step shows exactly what it showed going forward.
    for i in range(len(steps) - 1, -1, -1):
        page.evaluate('Workspace.current.go(%d)' % i)
        assert box_states(page) == forward[i], i
    assert page.evaluate("document.querySelectorAll('.ct-node').length") == 2 * 8 - 1 or algorithm == 'Quick Sort'
    page.ctx.close()


def test_calls_start_top_down_in_merge_sort_and_a_finished_call_shows_its_merged_result(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    start_sort(page, 'Merge Sort', '5, 3, 8, 1', 'lt')
    page.evaluate('Workspace.current.go(0)')
    ROOT = "[...document.querySelectorAll('.ct-node')].find(n => n.querySelector('.ct-label').textContent === '0-3')"
    assert page.evaluate(ROOT + '.dataset.state') == 'waiting'       # the root has started, though it merges last
    assert page.evaluate(ROOT + '.dataset.result') == 'false'

    total = page.evaluate('Workspace.current.steps.length')
    page.evaluate('Workspace.current.go(%d)' % (total - 2))          # the root's last write
    assert page.evaluate(ROOT + '.dataset.result') == 'true'
    assert page.evaluate(ROOT + ".querySelector('.ct-values').textContent") == '1 3 5 8'
    page.evaluate('Workspace.current.go(%d)' % (total - 1))          # done: everything is finished and dim
    states = page.evaluate("[...document.querySelectorAll('.ct-node')].map(n => n.dataset.state)")
    assert set(states) == {'finished'}
    # Dimmed: the fade takes 150ms, so wait for it.
    page.wait_for_function("getComputedStyle(document.querySelector('.ct-node')).opacity < 0.7", timeout=2000)
    page.ctx.close()


def test_the_tree_does_not_change_the_stage_the_steps_or_the_counts(browser, base_url):
    page = page_for(browser, base_url, '/sorting', width=1440, height=900)
    start_sort(page, 'Quick Sort', '5, 3, 8, 3, 9, 1, 7, 2')
    steps_open = page.evaluate("Workspace.current.steps.length")
    page.evaluate('Workspace.current.go(9)')
    bars_open = page.evaluate("[...document.querySelectorAll('.bar')].map(b => [b.style.height, b.className])")
    counter_open = page.inner_text('#step-counter')
    page.click('#call-tree-toggle')
    bars_closed = page.evaluate("[...document.querySelectorAll('.bar')].map(b => [b.style.height, b.className])")
    assert bars_open == bars_closed and counter_open == page.inner_text('#step-counter')
    # The same run, fetched on its own, has the same steps and counts.
    reply = page.evaluate("""() => fetch('/run_sort', {method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({algorithm: 'Quick Sort', values: '5, 3, 8, 3, 9, 1, 7, 2'})}).then(r => r.json())""")
    assert len(reply['steps']) == steps_open
    page.ctx.close()


def test_predict_mode_and_the_keyboard_shortcuts_keep_the_tree_in_step(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    start_sort(page, 'Quick Sort', '5, 3, 8, 1, 9, 2, 7')
    page.check('#predict-toggle')
    for _ in range(60):
        if page.query_selector('.predict-card'):
            page.click('.predict-option >> nth=0')
        elif page.evaluate('Workspace.current.index < Workspace.current.steps.length - 1'):
            page.click('#step-forward')
        else:
            break
        i = page.evaluate('Workspace.current.index')
        step = page.evaluate('Workspace.current.steps[%d]' % i)
        lit = active_boxes(page)
        assert lit == ([] if step['action'] == 'done' else ['%d-%d' % tuple(step['range'])]), (i, lit)

    page.uncheck('#predict-toggle')
    page.evaluate('Workspace.current.go(0)')
    page.evaluate('document.activeElement.blur()')
    page.keyboard.press('ArrowRight')
    page.keyboard.press('ArrowRight')
    assert page.evaluate('Workspace.current.index') == 2
    assert active_boxes(page) == ['%d-%d' % tuple(page.evaluate('Workspace.current.steps[2].range'))]
    page.keyboard.press('ArrowLeft')
    assert page.evaluate('Workspace.current.index') == 1
    page.keyboard.press('r')
    assert page.evaluate('Workspace.current.index') == 0
    assert page.errors == []
    page.ctx.close()


def test_the_arrow_keys_scroll_the_tree_and_do_not_step_the_sort(browser, base_url):
    page = page_for(browser, base_url, '/sorting', width=1440, height=900)
    values = ', '.join(str((i * 7) % 50 + 1) for i in range(40))
    start_sort(page, 'Merge Sort', values)
    page.evaluate('Workspace.current.go(0)')
    page.focus('.call-tree-scroll')
    assert page.evaluate("document.activeElement.classList.contains('call-tree-scroll')")
    before = page.evaluate('Workspace.current.index')
    left = page.evaluate("document.querySelector('.call-tree-scroll').scrollLeft")
    page.keyboard.press('ArrowRight')
    page.keyboard.press('ArrowRight')
    page.keyboard.press('Space')
    assert page.evaluate('Workspace.current.index') == before                   # the sort did not move
    assert page.evaluate("!Workspace.current.timer")                             # and Space did not start it
    # The browser scrolls a focused box smoothly, so give it a moment.
    page.wait_for_function("document.querySelector('.call-tree-scroll').scrollLeft > %d" % left, timeout=3000)
    page.ctx.close()


def test_a_large_array_scrolls_inside_the_panel_and_does_not_widen_the_page(browser, base_url):
    page = page_for(browser, base_url, '/sorting', width=768, height=900)
    values = ', '.join(str((i * 37) % 90 + 5) for i in range(60))
    start_sort(page, 'Merge Sort', values)
    page.click('#call-tree-toggle') if not page.is_visible('.call-tree-scroll') else None
    box = page.evaluate("""() => {
        const s = document.querySelector('.call-tree-scroll');
        const panel = document.getElementById('call-tree').getBoundingClientRect();
        return {scrollW: s.scrollWidth, clientW: s.clientWidth, scrollH: s.scrollHeight, clientH: s.clientHeight,
                panelRight: panel.right, w: innerWidth, page: document.documentElement.scrollWidth - innerWidth};
    }""")
    assert box['scrollW'] > box['clientW'] * 2, box                  # far wider than the box
    assert box['page'] <= 0 and box['panelRight'] <= box['w'], box   # and the page did not grow
    # Stepping keeps the lit box in view inside the scroll box.
    for index in (0, 40, 90, 140):
        page.evaluate('Workspace.current.go(%d)' % index)
        inside = page.evaluate("""() => {
            const lit = document.querySelector('.ct-node[data-state="active"]');
            if (!lit) return true;
            const a = lit.getBoundingClientRect(), s = document.querySelector('.call-tree-scroll').getBoundingClientRect();
            return a.left >= s.left - 1 && a.right <= s.right + 1 && a.top >= s.top - 1 && a.bottom <= s.bottom + 1;
        }""")
        assert inside, index
    page.ctx.close()


def test_motion_is_instant_under_reduced_motion_and_short_otherwise(browser, base_url):
    page = page_for(browser, base_url, '/sorting', reduced='reduce')
    start_sort(page, 'Merge Sort', '5, 3, 8, 1')
    for selector in ('.ct-node', '.ct-edge'):
        assert page.evaluate("getComputedStyle(document.querySelector('%s')).transitionDuration" % selector) == '0s'
    page.evaluate('Workspace.current.go(3)')
    assert active_boxes(page)                                         # and it still works
    page.ctx.close()

    page = page_for(browser, base_url, '/sorting', reduced='no-preference')
    start_sort(page, 'Merge Sort', '5, 3, 8, 1')
    assert page.evaluate("getComputedStyle(document.querySelector('.ct-node')).transitionDuration") == '0.15s'
    page.ctx.close()


@pytest.mark.parametrize('scheme', SCHEMES)
@pytest.mark.parametrize('width,height', [(375, 812), (768, 1024), (1440, 900)])
def test_the_panel_fits_and_is_readable_at_every_width_in_both_themes(browser, base_url, width, height, scheme):
    page = page_for(browser, base_url, '/sorting', width=width, height=height, scheme=scheme)
    start_sort(page, 'Merge Sort', '5, 3, 8, 1, 9, 2, 7, 4')
    if not page.is_visible('.call-tree-scroll'):
        page.click('#call-tree-toggle')
    page.evaluate('Workspace.current.go(6)')

    assert page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth") <= 0
    box = page.evaluate("""() => {
        const r = document.getElementById('call-tree').getBoundingClientRect();
        const b = document.getElementById('call-tree-toggle').getBoundingClientRect();
        return {left: r.left, right: r.right, w: innerWidth, toggleH: b.height};
    }""")
    assert box['left'] >= 0 and box['right'] <= box['w'] and box['toggleH'] >= 43, box

    # The lit box is readable: its label against its own fill, and the plain labels against the panel.
    colours = page.evaluate("""() => {
        const parse = c => c.match(/[\\d.]+/g).slice(0, 3).map(Number);
        const lum = ([r, g, b]) => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
                                     return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
        const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
        const lit = document.querySelector('.ct-node[data-state="active"]');
        const plain = document.querySelector('.ct-node[data-state="waiting"]');
        const sunken = getComputedStyle(document.querySelector('.call-tree-scroll')).backgroundColor;
        const out = {};
        if (lit) out.lit = ratio(parse(getComputedStyle(lit.querySelector('.ct-label')).fill),
                                 parse(getComputedStyle(lit.querySelector('rect')).fill));
        if (plain) out.plain = ratio(parse(getComputedStyle(plain.querySelector('.ct-label')).fill),
                                     parse(getComputedStyle(plain.querySelector('rect')).fill));
        out.heading = ratio(parse(getComputedStyle(document.querySelector('.call-tree-title')).color),
                            parse(getComputedStyle(document.getElementById('call-tree')).backgroundColor));
        return out;
    }""")
    assert colours.get('lit', 99) >= 4.5 and colours.get('plain', 99) >= 4.5 and colours['heading'] >= 4.5, colours
    page.ctx.close()


def test_focus_is_visible_on_the_toggle_and_the_scroll_box(browser, base_url):
    page = page_for(browser, base_url, '/sorting', width=1440, height=900)
    start_sort(page, 'Merge Sort', '5, 3, 8, 1, 9, 2')
    for selector in ('#call-tree-toggle', '.call-tree-scroll'):
        page.focus(selector)
        page.keyboard.press('Tab')
        page.keyboard.press('Shift+Tab')
        style = page.evaluate("(() => { const s = getComputedStyle(document.activeElement); return [s.outlineStyle, s.outlineWidth]; })()")
        assert style[0] != 'none' and float(style[1].replace('px', '')) >= 2, (selector, style)
    page.ctx.close()


def test_no_script_errors_across_every_variant_run_to_the_end(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    for algorithm, variant in (('Merge Sort', 'lt'), ('Merge Sort', 'le'), ('Quick Sort', 'last'),
                               ('Quick Sort', 'middle'), ('Quick Sort', 'random')):
        start_sort(page, algorithm, '4, 4, 2, 4, 2, 2, 9, 1', variant)
        for i in range(page.evaluate('Workspace.current.steps.length')):
            page.evaluate('Workspace.current.go(%d)' % i)
    assert page.errors == []
    page.ctx.close()
