"""The launch build in a real browser: the Content-Security-Policy on, the
network off, every page and every algorithm.

A violation is recorded two ways: the page's own `securitypolicyviolation`
event, and any console message that mentions the policy. A single one fails.

Needs Playwright; see tests/test_browser_phase14.py and requirements-dev.txt.
"""
import os
import sys
from urllib.parse import urlparse

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import GRAPH_PICKER, SEARCH_PICKER, sorting_algo_dict
from browser_helpers import SKIP_REASON, available, returning_visitor

pytestmark = pytest.mark.skipif(not available(), reason=SKIP_REASON)

WATCH = """
window.__csp = [];
document.addEventListener('securitypolicyviolation', e => {
    window.__csp.push([e.violatedDirective, e.blockedURI, (e.sample || '').slice(0, 60)]);
});
"""

PAGES = ['/', '/learn', '/sorting', '/searching', '/compare', '/big-o', '/privacy', '/terms',
         '/no-such-page'] + ['/graph?algo=%s' % key for key, _, _ in GRAPH_PICKER]
GRAPH_KEYS = [key for key, _, _ in GRAPH_PICKER]


def until(page, expression, timeout=10000):
    """Wait for a JavaScript expression to be true by evaluating it again and again
    from outside the page. page.wait_for_function does the same inside the page with
    eval, which the Content-Security-Policy refuses."""
    import time
    deadline = time.time() + timeout / 1000
    while time.time() < deadline:
        if page.evaluate(expression):
            return
        time.sleep(0.05)
    raise AssertionError('timed out waiting for: %s' % expression)


class Visit:
    """A page opened with the violation watcher, and optionally the network off."""

    def __init__(self, browser, base_url, path, width=1280, height=900, scheme='light', offline=False, tour_seen=True):
        self.ctx = browser.new_context(viewport={'width': width, 'height': height}, color_scheme=scheme)
        if tour_seen:
            returning_visitor(self.ctx)
        self.ctx.add_init_script(WATCH)
        self.page = self.ctx.new_page()
        self.errors, self.console, self.blocked, self.requested = [], [], [], []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        self.page.on('console', lambda m: self.console.append(m.text) if 'Content Security Policy' in m.text
                     or 'Refused to' in m.text else None)
        self.page.on('request', lambda r: self.requested.append(r.url))
        local = urlparse(base_url).netloc

        if offline:
            def gate(route):
                if urlparse(route.request.url).netloc == local:
                    route.continue_()
                else:
                    self.blocked.append(route.request.url)
                    route.abort()
            self.ctx.route('**/*', gate)
        self.page.goto(base_url + path)
        self.page.wait_for_load_state('load')

    def violations(self):
        return self.page.evaluate('window.__csp') + self.console

    def check(self, label=''):
        assert self.errors == [], (label, self.errors)
        assert self.violations() == [], (label, self.violations())

    def close(self):
        self.ctx.close()


def run_graph(visit):
    visit.page.click('#run-button')
    until(visit.page, 'Workspace.current && Workspace.current.steps.length > 0', timeout=15000)
    visit.page.evaluate('Workspace.current.go(Workspace.current.steps.length - 1)')


# ---------------------------------------------------------------------------
# The policy is really on
# ---------------------------------------------------------------------------

def test_an_inline_script_without_the_nonce_does_not_run_and_is_reported(browser, base_url):
    v = Visit(browser, base_url, '/')
    v.page.evaluate("""() => {
        const s = document.createElement('script');
        s.textContent = 'window.__injected = 1';
        document.head.appendChild(s);
    }""")
    assert v.page.evaluate('window.__injected') is None
    reported = v.page.evaluate('window.__csp')
    assert reported and reported[0][0].startswith('script-src'), reported
    v.close()


def test_an_inline_event_handler_does_not_run(browser, base_url):
    v = Visit(browser, base_url, '/')
    v.page.evaluate("""() => {
        const b = document.createElement('button'); b.id = 'trap';
        b.setAttribute('onclick', 'window.__clicked = 1');
        document.body.appendChild(b);
    }""")
    v.page.click('#trap')
    assert v.page.evaluate('window.__clicked') is None
    assert any(item[0].startswith('script-src') for item in v.page.evaluate('window.__csp'))
    v.close()


def test_a_script_from_another_site_is_refused(browser, base_url):
    v = Visit(browser, base_url, '/', offline=True)
    v.page.evaluate("""() => {
        const s = document.createElement('script'); s.src = 'https://example.com/x.js';
        document.head.appendChild(s);
    }""")
    v.page.wait_for_timeout(300)
    assert any('example.com' in item[1] for item in v.page.evaluate('window.__csp'))
    v.close()


# ---------------------------------------------------------------------------
# Every page, no violations
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('path', PAGES)
def test_every_page_loads_with_the_policy_on_and_no_violation(browser, base_url, path):
    v = Visit(browser, base_url, path)
    v.check(path)
    head = v.page.evaluate("""() => ({
        title: document.title,
        description: (document.querySelector('meta[name=description]') || {}).content,
        og: (document.querySelector('meta[property="og:title"]') || {}).content,
        card: (document.querySelector('meta[name="twitter:card"]') || {}).content,
        canonical: (document.querySelector('link[rel=canonical]') || {}).href,
    })""")
    assert 'AlgoTrace' in head['title'] and head['description'] and head['og'] == head['title']
    assert head['card'] == 'summary_large_image' and head['canonical'].startswith('http')
    assert v.page.inner_text('.logo').strip() == 'AlgoTrace'
    v.close()


# ---------------------------------------------------------------------------
# Every algorithm, with the policy on
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('algorithm', sorted(sorting_algo_dict))
def test_every_sort_runs_to_the_end_with_the_policy_on(browser, base_url, algorithm):
    v = Visit(browser, base_url, '/sorting')
    v.page.click('#algo-picker [data-algorithm="%s"]' % algorithm)
    v.page.check('#manual-input-choice')
    v.page.fill('#manual-input', '5, 3, 8, 1, 9, 2, 7, 4')
    v.page.click('#run-button')
    until(v.page, 'Workspace.current.steps.length > 0')
    v.page.evaluate('Workspace.current.go(Workspace.current.steps.length - 1)')
    assert v.page.inner_text('#run-banner').strip()
    v.check(algorithm)
    v.close()


@pytest.mark.parametrize('key', [k for k, _, _ in SEARCH_PICKER])
def test_every_search_runs_to_the_end_with_the_policy_on(browser, base_url, key):
    v = Visit(browser, base_url, '/searching')
    v.page.click('#algo-picker [data-algorithm="%s"]' % key)
    v.page.fill('#array-input', '4, 8, 15, 16, 23, 42, 50')
    v.page.fill('#target-input', '23')
    v.page.click('#run-button')
    until(v.page, 'Workspace.current.steps.length > 0')
    v.page.evaluate('Workspace.current.go(Workspace.current.steps.length - 1)')
    v.check(key)
    v.close()


@pytest.mark.parametrize('key', GRAPH_KEYS)
def test_every_graph_algorithm_runs_with_the_policy_on(browser, base_url, key):
    v = Visit(browser, base_url, '/graph?algo=' + key)
    run_graph(v)
    v.check(key)
    v.close()


def test_the_inline_buttons_that_became_data_actions_still_work(browser, base_url):
    v = Visit(browser, base_url, '/graph?algo=prim')
    v.page.evaluate("document.getElementById('format-toggle').click()")
    assert v.page.get_attribute('#format-toggle', 'aria-expanded') == 'true'
    v.page.evaluate("document.querySelector('[data-action=\"loadPrimDemo\"]').click()")
    until(v.page, "document.getElementById('graph-input').value.startsWith('5 7')")
    assert v.page.input_value('#start-node') == 'A'
    until(v.page, 'Workspace.current && Workspace.current.steps.length > 0', timeout=10000)
    v.page.evaluate("document.getElementById('randomRadio').click()")
    v.page.evaluate("document.querySelector('[data-action=\"generateRandomGraph\"]').click()")
    until(v.page, 'Workspace.current.steps.length > 0', timeout=10000)
    v.check('demo buttons')
    v.close()


def test_the_theme_toggle_the_code_tabs_and_the_expand_dialog_work_with_the_policy_on(browser, base_url):
    v = Visit(browser, base_url, '/sorting')
    before = v.page.get_attribute('html', 'data-theme')
    v.page.click('#theme-toggle')
    assert v.page.get_attribute('html', 'data-theme') != before
    assert v.page.evaluate("localStorage.getItem('theme')") in ('dark', 'light')

    v.page.check('#manual-input-choice')
    v.page.fill('#manual-input', '5, 3, 8, 1')
    v.page.click('#run-button')
    until(v.page, 'Workspace.current.steps.length > 0')
    v.page.click('#learn-tab-code')
    for language in ('pseudocode', 'c', 'cpp', 'java', 'python'):
        v.page.click('.lang-tab[data-language="%s"]' % language)
        v.page.wait_for_timeout(120)
        assert v.page.evaluate("localStorage.getItem('pbl2.codeLanguage')") == language
        assert v.page.query_selector('.code-line')
    v.page.click('text=Expand code')
    assert v.page.is_visible('dialog.code-dialog')
    v.page.keyboard.press('Escape')
    v.page.check('#predict-toggle')
    v.page.click('#step-forward')
    v.check('theme, code, predict')
    v.close()


def test_compare_the_call_tree_and_the_home_player_work_with_the_policy_on(browser, base_url):
    v = Visit(browser, base_url, '/compare')
    v.page.check('#manual-input-choice')
    v.page.fill('#manual-input', '5, 3, 8, 1, 9, 2')
    v.page.click('#run-button')
    until(v.page, 'Compare.left.ws.steps.length > 0 && Compare.right.ws.steps.length > 0')
    v.check('compare')
    v.close()

    v = Visit(browser, base_url, '/sorting?algorithm=Merge+Sort', width=1440)
    v.page.check('#manual-input-choice')
    v.page.fill('#manual-input', '5, 3, 8, 1, 9, 2')
    v.page.click('#run-button')
    until(v.page, 'Workspace.current.steps.length > 0')
    v.page.evaluate('Workspace.current.go(5)')
    assert v.page.query_selector('.ct-node[data-state="active"]')
    v.check('call tree')
    v.close()

    v = Visit(browser, base_url, '/')
    v.page.click('.player-step')
    assert v.page.inner_text('.player-status').startswith('Step')
    v.check('home player')
    v.close()


def test_an_algorithm_page_in_both_themes_has_no_violation(browser, base_url):
    for scheme in ('light', 'dark'):
        v = Visit(browser, base_url, '/graph?algo=dijkstra', scheme=scheme)
        run_graph(v)
        v.check(scheme)
        v.close()


# ---------------------------------------------------------------------------
# The network off
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('key', GRAPH_KEYS)
def test_every_graph_page_works_with_the_network_off(browser, base_url, key):
    v = Visit(browser, base_url, '/graph?algo=' + key, offline=True)
    if key != 'astar':                                                             # the grid draws without D3
        assert v.page.evaluate("typeof d3 === 'object' && d3.version") == '7.9.0'   # from this site
    run_graph(v)
    assert v.page.evaluate("document.querySelectorAll('#graph-container circle, #grid-board [role=gridcell]').length") > 0
    v.check(key)
    # Only fonts were ever refused, and never D3 or anything else.
    hosts = {urlparse(u).netloc for u in v.blocked}
    assert hosts <= {'fonts.googleapis.com', 'fonts.gstatic.com'}, hosts
    assert not any('d3js.org' in u for u in v.requested)
    assert any(u.split('?')[0].endswith('/static/vendor/d3.v7.min.js') for u in v.requested) or key == 'astar'
    v.close()


@pytest.mark.parametrize('path', ['/', '/sorting', '/searching', '/compare', '/learn', '/big-o'])
def test_the_other_pages_work_with_the_network_off(browser, base_url, path):
    v = Visit(browser, base_url, path, offline=True)
    v.check(path)
    assert {urlparse(u).netloc for u in v.blocked} <= {'fonts.googleapis.com', 'fonts.gstatic.com'}
    v.close()


# ---------------------------------------------------------------------------
# What the browser was told
# ---------------------------------------------------------------------------

def test_d3_and_the_stylesheet_arrive_with_a_year_long_immutable_cache(browser, base_url):
    ctx = returning_visitor(browser.new_context())
    page = ctx.new_page()
    seen = {}
    page.on('response', lambda r: seen.__setitem__(urlparse(r.url).path, r))
    page.goto(base_url + '/graph?algo=bfs')
    page.wait_for_load_state('load')

    d3 = seen['/static/vendor/d3.v7.min.js']
    assert d3.status == 200 and 'javascript' in d3.headers['content-type']
    assert d3.headers['cache-control'] == 'public, max-age=31536000, immutable'
    assert '?v=' in d3.url and seen['/static/styles.css'].headers['cache-control'].endswith('immutable')
    doc = seen['/graph']
    assert doc.headers['x-content-type-options'] == 'nosniff'
    assert doc.headers['referrer-policy'] == 'strict-origin-when-cross-origin'
    assert "script-src 'self' 'nonce-" in doc.headers['content-security-policy']
    ctx.close()
