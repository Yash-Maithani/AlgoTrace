"""Phase 14 in a real browser.

These need Playwright (requirements-dev.txt) and a browser for it to drive.
When they are missing every test here skips, and tests/conftest.py prints a
warning at the top and bottom of the run. To enable them:

    python -m pip install -r requirements-dev.txt
    python -m playwright install chromium

Reduced motion is emulated with the browser's own media emulation, so the CSS
the page ships is what is tested, not a reading of it.
"""
import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_helpers import NODE, SKIP_REASON, available, page_for

HERE = os.path.dirname(os.path.abspath(__file__))

pytestmark = pytest.mark.skipif(not available(), reason=SKIP_REASON)

THETA = {'1': '1', 'log n': 'log n', 'n': 'n', 'n log n': 'n log n', 'n squared': 'n²',
         'V': 'V', 'E': 'E', 'V squared': 'V²', 'V cubed': 'V³',
         'V times E': 'V·E', 'E log E': 'E log E', 'k times E': 'k·E'}


def run_sort(page, algorithm, values='5, 3, 8, 3, 9, 1, 7, 5'):
    page.click('#algo-picker [data-algorithm="%s"]' % algorithm)
    page.check('#manual-input-choice')
    page.fill('#manual-input', values)
    page.click('#run-button')
    page.wait_for_function('Workspace.current.steps.length > 0')
    page.click('#learn-tab-code')


# ---------------------------------------------------------------------------
# Reduced motion, emulated
# ---------------------------------------------------------------------------

def test_reduced_motion_makes_the_tab_slide_and_the_crossfade_instant(browser, base_url):
    page = page_for(browser, base_url, '/sorting', reduced='reduce')
    assert page.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches")
    run_sort(page, 'Bubble Sort')

    for selector in ('.lang-thumb', '.code-stage'):
        assert page.evaluate("getComputedStyle(document.querySelector('%s')).transitionDuration" % selector) == '0s'

    # The swap is synchronous: no fade class, the new listing is already there.
    page.click('.lang-tab[data-language="java"]')
    assert page.evaluate("document.querySelector('.code-stage').classList.contains('is-swapping')") is False
    assert 'Java' in page.get_attribute('#learn-body-code .code-listing', 'aria-label')
    assert page.evaluate("document.querySelector('.lang-thumb').classList.contains('is-instant')")
    assert page.errors == []
    page.ctx.close()


def test_with_motion_allowed_the_tab_slides_for_180ms_and_the_listing_fades(browser, base_url):
    page = page_for(browser, base_url, '/sorting', reduced='no-preference')
    run_sort(page, 'Bubble Sort')
    # The first placement is instant; every move after it slides.
    page.click('.lang-tab[data-language="cpp"]')

    assert page.evaluate("getComputedStyle(document.querySelector('.lang-thumb')).transitionDuration") == '0.18s'
    assert page.evaluate("getComputedStyle(document.querySelector('.lang-thumb')).transitionProperty") == 'transform'
    assert page.evaluate("getComputedStyle(document.querySelector('.code-stage')).transitionDuration") == '0.06s'
    swapped = page.evaluate("""() => new Promise(resolve => {
        document.querySelector('.lang-tab[data-language="c"]').click();
        const during = document.querySelector('.code-stage').classList.contains('is-swapping');
        setTimeout(() => resolve([during, document.querySelector('.code-stage').classList.contains('is-swapping')]), 200);
    })""")
    assert swapped == [True, False]
    page.ctx.close()


def test_the_highlighted_line_keeps_its_id_when_the_language_changes_mid_run(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    run_sort(page, 'Bubble Sort')
    page.evaluate('Workspace.current.go(4)')
    wanted = page.evaluate('Workspace.current.steps[4].line')
    for language in ('c', 'cpp', 'java', 'pseudocode', 'python'):
        page.click('.lang-tab[data-language="%s"]' % language)
        page.wait_for_timeout(150)
        lit = page.evaluate("[...document.querySelectorAll('#learn-body-code .code-line.is-current')].map(l => l.dataset.line)")
        assert lit and set(lit) == {wanted}, (language, lit, wanted)
    page.ctx.close()


# ---------------------------------------------------------------------------
# A statement over several lines lights whole
# ---------------------------------------------------------------------------

def step_with_line(page, line):
    return page.evaluate("Workspace.current.steps.findIndex(s => s.line === '%s')" % line)


@pytest.mark.parametrize('algorithm,line', [('Bubble Sort', 'swap'), ('Selection Sort', 'swap')])
def test_javas_three_line_swap_lights_all_three_lines(browser, base_url, algorithm, line):
    page = page_for(browser, base_url, '/sorting')
    run_sort(page, algorithm)
    page.click('.lang-tab[data-language="java"]')
    page.wait_for_timeout(150)
    page.evaluate('Workspace.current.go(%d)' % step_with_line(page, line))

    panel = page.evaluate("[...document.querySelectorAll('#learn-body-code .code-body .code-listing:not(.code-helpers) .code-line.is-current')].map(l => l.textContent)")
    assert len(panel) == 3 and panel[0].startswith('int t = '), panel

    # The Expand dialog follows the run, and lights the same three.
    page.click('text=Expand code')
    dialog = page.evaluate("[...document.querySelectorAll('dialog.code-dialog .code-line.is-current')].map(l => l.textContent)")
    assert dialog == panel
    page.evaluate('Workspace.current.go(0)')
    start = page.evaluate("[...document.querySelectorAll('#learn-body-code .code-body .code-listing:not(.code-helpers) .code-line.is-current')].map(l => l.textContent)")
    in_dialog = page.evaluate("[...document.querySelectorAll('dialog.code-dialog .code-line.is-current')].map(l => l.textContent)")
    assert in_dialog == start and len(start) < 3          # it moved with the run
    page.evaluate('Workspace.current.go(%d)' % step_with_line(page, line))
    assert page.evaluate("document.querySelectorAll('dialog.code-dialog .code-line.is-current').length") == 3
    page.ctx.close()


def test_the_home_card_marks_every_line_of_the_active_statement(browser, base_url):
    page = page_for(browser, base_url, '/')
    page.evaluate("CodeView.setLanguage('java')")
    page.wait_for_timeout(100)
    page.evaluate("HomeCode.light('swap')")
    marked = page.evaluate("[...document.querySelectorAll('.band-code mark')].map(m => m.textContent.trim())")
    assert len(marked) == 3 and marked[0].startswith('int t = '), marked
    page.evaluate("HomeCode.light('compare')")
    assert page.evaluate("document.querySelectorAll('.band-code mark').length") == 1
    page.evaluate("CodeView.setLanguage('c')")
    page.evaluate("HomeCode.light('swap')")
    assert page.evaluate("document.querySelectorAll('.band-code mark').length") == 1
    page.evaluate("CodeView.setLanguage('python')")
    page.ctx.close()


# ---------------------------------------------------------------------------
# The Complexity tab: every algorithm and every variant
# ---------------------------------------------------------------------------

_LESSONS = None


def lessons():
    global _LESSONS
    if _LESSONS is None:
        out = subprocess.run([NODE, os.path.join(HERE, 'dump_lessons.js')], capture_output=True, text=True, check=True)
        _LESSONS = json.loads(out.stdout)
    return _LESSONS


READ_TAB = """() => {
    const body = document.querySelector('#learn-body-complexity');
    const rows = [...body.querySelectorAll('.theta-table tbody tr')].map(r => ({
        case: r.querySelector('th').textContent.trim(),
        theta: r.querySelector('.theta-cell [aria-hidden]').textContent,
        spoken: r.querySelector('.theta-cell .sr-only').textContent,
        reason: r.querySelector('.complexity-reason').textContent
    }));
    const overall = body.querySelector('.overall-line');
    return {
        rows,
        heads: [...body.querySelectorAll('.theta-table thead th')].map(h => h.textContent),
        scopes: [...body.querySelectorAll('.theta-table th')].map(h => h.scope),
        overall: overall.textContent,
        noTheta: overall.getAttribute('data-no-theta') === 'true',
        notations: [...body.querySelectorAll('.notation')].map(n => [n.children[0].getAttribute('aria-hidden'), n.children[1].className, n.children[1].textContent]),
        mix: (body.querySelector('.misconception') || {}).textContent || '',
        text: body.textContent
    };
}"""


def fig(token):
    return THETA[token]


def check_complexity(page, lesson):
    c = lesson['complexity']
    got = page.evaluate(READ_TAB)
    assert [r['case'] for r in got['rows']] == ['Best', 'Average', 'Worst']
    for row, case in zip(got['rows'], ('best', 'average', 'worst')):
        assert row['theta'] == 'Θ(%s)' % fig(c['time'][case]['theta']), (lesson['id'], case)
        assert row['spoken'].startswith('Theta of ')
        assert row['reason'] == c['time'][case]['reason']
    assert got['scopes'][:3] == ['col', 'col', 'col'] and set(got['scopes'][3:]) == {'row'}
    o = c['overall']
    assert 'O(%s)' % fig(o['O']) in got['overall'] and 'Ω(%s)' % fig(o['Omega']) in got['overall']
    if o['Theta']:
        assert not got['noTheta'] and 'Θ(%s)' % fig(o['Theta']) in got['overall']
    else:
        assert got['noTheta'] and 'no single Θ' in got['overall'] and 'so no one function fits' in got['overall']
    assert got['mix'].endswith(c['misconception'])
    # Every symbol is hidden from a screen reader and has its name in words.
    assert got['notations'] and all(n[0] == 'true' and n[1] == 'sr-only' for n in got['notations'])
    assert all(n[2].split(' of ')[0] in ('Big O', 'Omega', 'Theta') for n in got['notations'])


def resolved(name, option):
    entry = lessons()[name]
    return entry['resolved'][option if option is not None else (entry['default'] or '')]


def test_the_complexity_tab_on_every_sorting_algorithm_and_variant(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    ids = page.evaluate("[...document.querySelectorAll('#algo-picker [data-algorithm]')].map(b => [b.dataset.algorithm, b.dataset.lesson])")
    checked = 0
    for display, lesson_id in ids:
        page.click('#algo-picker [data-algorithm="%s"]' % display)
        page.click('#learn-tab-complexity')
        entry = lessons()[lesson_id]
        radios = page.evaluate("[...document.querySelectorAll('[data-variant-for=\"%s\"] input[type=radio]')].map(r => r.value)" % display)
        for option in (radios or [None]):
            if option is not None:
                page.click('[data-variant-for="%s"] input[value="%s"]' % (display, option))
            check_complexity(page, resolved(lesson_id, option))
            checked += 1
        assert entry
    assert checked >= 10          # six algorithms and the extra options of three
    assert page.errors == []
    page.ctx.close()


def test_the_complexity_tab_on_both_searches(browser, base_url):
    page = page_for(browser, base_url, '/searching')
    for name in ('linear_search', 'binary_search'):
        page.click('#algo-picker [data-algorithm="%s"]' % name)
        page.click('#learn-tab-complexity')
        check_complexity(page, resolved(name, None))
    assert page.errors == []
    page.ctx.close()


@pytest.mark.parametrize('algo', ['bfs', 'dfs', 'dijkstra', 'prim', 'kruskal', 'floyd_warshall', 'bellman_ford'])
def test_the_complexity_tab_on_every_graph_algorithm(browser, base_url, algo):
    page = page_for(browser, base_url, '/graph?algo=' + algo)
    page.click('#learn-tab-complexity')
    check_complexity(page, resolved(algo, None))
    assert page.errors == []
    page.ctx.close()


def test_a_variant_shows_its_own_figures(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    page.click('#algo-picker [data-algorithm="Bubble Sort"]')
    page.click('#learn-tab-complexity')
    off = page.evaluate(READ_TAB)
    page.click('[data-variant-for="Bubble Sort"] input[value="on"]')
    on = page.evaluate(READ_TAB)

    assert off['rows'][0]['theta'] == 'Θ(n²)' and not off['noTheta']
    assert on['rows'][0]['theta'] == 'Θ(n)' and on['noTheta']
    assert off['overall'] != on['overall']
    page.ctx.close()


# ---------------------------------------------------------------------------
# /big-o
# ---------------------------------------------------------------------------

def test_the_explorer_answers_the_sliders(browser, base_url):
    page = page_for(browser, base_url, '/big-o')
    verdict = lambda: page.inner_text('#nt-verdict')
    assert 'f is Θ(n²)' in verdict()
    assert page.evaluate("document.querySelector('#nt-chart svg path.nt-f').getAttribute('d').length") > 100

    page.fill('#nt-c2', '0.2') if False else page.evaluate(
        "() => { const s = document.getElementById('nt-c2'); s.value = '0.3'; s.dispatchEvent(new Event('input')); }")
    assert 'ceiling fails' in verdict() and 'not' in verdict()
    page.select_option('#nt-g', 'n')
    page.evaluate("() => { const s = document.getElementById('nt-c2'); s.value = '10'; s.dispatchEvent(new Event('input')); }")
    assert 'ceiling fails' in verdict()                   # n squared outgrows any multiple of n
    assert page.get_attribute('#nt-chart svg', 'aria-label').startswith('Chart of f(n)')
    assert page.evaluate("document.getElementById('nt-verdict').getAttribute('aria-live')") == 'polite'
    assert page.errors == []
    page.ctx.close()


def test_the_navbar_reads_complexity_in_the_browser(browser, base_url):
    page = page_for(browser, base_url, '/big-o')
    link = page.query_selector('.nav-links a[href="/big-o"]')

    assert link.inner_text().strip() == 'Complexity'
    assert link.get_attribute('aria-current') == 'page'
    page.ctx.close()


# ---------------------------------------------------------------------------
# Width and theme
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('scheme', ['light', 'dark'])
@pytest.mark.parametrize('width,height', [(375, 812), (768, 1024), (1440, 900)])
@pytest.mark.parametrize('path', ['/big-o', '/sorting', '/searching', '/graph?algo=prim', '/'])
def test_nothing_scrolls_sideways_and_the_new_parts_fit(browser, base_url, path, width, height, scheme):
    page = page_for(browser, base_url, path, width=width, height=height, scheme=scheme)
    if path != '/big-o' and path != '/':
        page.click('#learn-tab-complexity')
    over = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    assert over <= 0, (path, width, scheme, over)

    if path == '/big-o':
        box = page.evaluate("(() => { const r = document.querySelector('#nt-chart svg').getBoundingClientRect(); return [r.left, r.right]; })()")
        assert box[0] >= 0 and box[1] <= width
        table = page.evaluate("(() => { const t = document.querySelector('.notation-table'); return [t.scrollWidth, t.clientWidth]; })()")
        assert table[0] >= table[1]                        # may scroll inside its own box, never the page
    if path in ('/sorting', '/searching', '/graph?algo=prim'):
        wide = page.evaluate("(() => { const t = document.querySelector('.theta-table'); const r = t.getBoundingClientRect(); return [r.left, r.right, innerWidth]; })()")
        assert wide[0] >= 0 and wide[1] <= wide[2], wide
    page.ctx.close()
