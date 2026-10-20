"""A student who hits the rate limit is told so on every page that runs an algorithm.

The real limiter runs, set to one run a minute and already used up from this
address, so the page gets the real 429 from the real server.

Needs Playwright; see tests/test_browser_phase14.py and requirements-dev.txt.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_helpers import SKIP_REASON, available, page_for

pytestmark = pytest.mark.skipif(not available(), reason=SKIP_REASON)

PAGES = [
    ('/sorting', 'sorting'),
    ('/searching', 'searching'),
    ('/compare', 'compare'),
    ('/graph?algo=bfs', 'graphs'),
    ('/graph?algo=bellman_ford', 'graphs, directed weights'),
    ('/graph?algo=topological_sort', 'graphs, directed'),
    ('/graph?algo=astar', 'the A* grid'),
]
FRIENDLY = 'faster than this site allows'


@pytest.fixture
def one_run_a_minute(base_url):
    from app import app
    old = app.config['RATE_LIMIT_PER_MINUTE']
    app.config['RATE_LIMIT_PER_MINUTE'] = 1
    app.extensions['rate_limiter'].reset()
    yield
    app.config['RATE_LIMIT_PER_MINUTE'] = old
    app.extensions['rate_limiter'].reset()


@pytest.mark.parametrize('path,name', PAGES)
def test_the_page_tells_the_student_to_wait(browser, base_url, one_run_a_minute, path, name):
    page = page_for(browser, base_url, path)
    try:
        used = page.request.post(base_url + '/run_sort', data={'algorithm': 'Bubble Sort', 'values': [2, 1]})
        assert used.status == 200                                     # this one is allowed, and uses the minute
        page.click('#run-button')
        page.wait_for_function(
            "(text) => [...document.querySelectorAll('[role=alert]')].some(n => n.offsetParent !== null && n.textContent.includes(text))",
            arg=FRIENDLY, timeout=8000)
        shown = page.evaluate(
            "() => [...document.querySelectorAll('[role=alert]')].filter(n => n.offsetParent !== null).map(n => n.textContent.trim())")
        message = [m for m in shown if FRIENDLY in m][0]
        assert 'try again' in message and 'second' in message
        assert 'Could not reach the server' not in ' '.join(shown)
        assert 'failed' not in message.lower()
        assert page.errors == []
    finally:
        page.ctx.close()


def test_a_page_runs_again_once_the_limit_is_lifted(browser, base_url, one_run_a_minute):
    from app import app
    page = page_for(browser, base_url, '/sorting')
    try:
        page.request.post(base_url + '/run_sort', data={'algorithm': 'Bubble Sort', 'values': [2, 1]})
        page.click('#run-button')
        page.wait_for_function(
            "(text) => document.body.textContent.includes(text)", arg=FRIENDLY, timeout=8000)
        app.config['RATE_LIMIT_PER_MINUTE'] = 0
        page.click('#run-button')
        page.wait_for_function("() => !document.getElementById('step-forward').disabled", timeout=8000)
        assert FRIENDLY not in page.evaluate("() => document.body.textContent")
    finally:
        page.ctx.close()
