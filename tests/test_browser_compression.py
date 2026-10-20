"""Compression over a real connection: the browser asks for gzip, gets it, and
every run still plays. Needs Playwright; see tests/test_browser_phase14.py.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_helpers import SKIP_REASON, available, page_for

pytestmark = pytest.mark.skipif(not available(), reason=SKIP_REASON)

HUNDRED = ', '.join(str((i * 37) % 97 + 1) for i in range(100))


def capture(page, fragment):
    seen = []
    page.on('response', lambda r: seen.append(r) if fragment in r.url else None)
    return seen


def test_a_100_value_bubble_sort_arrives_gzipped_and_plays(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    seen = capture(page, '/run_sort')
    page.check('#manual-input-choice')
    page.fill('#manual-input', HUNDRED)
    page.click('#run-button')
    page.wait_for_function('Workspace.current.steps.length > 1000', timeout=30000)

    reply = seen[-1]
    headers = reply.headers
    assert headers['content-encoding'] == 'gzip'
    assert 'accept-encoding' in headers['vary'].lower()
    assert int(headers['content-length']) < 500_000                  # on the wire: a few hundred KB
    assert len(reply.body()) > 5_000_000                             # what the page received: the full 7 MB
    # The decompressed run is the one it always was: it plays to its end.
    page.evaluate('Workspace.current.go(Workspace.current.steps.length - 1)')
    assert page.evaluate("Workspace.current.metaAt(Workspace.current.steps.length - 1).action") == 'done'
    assert page.errors == []
    page.ctx.close()


def test_a_large_floyd_warshall_run_arrives_gzipped_and_plays(browser, base_url):
    page = page_for(browser, base_url, '/graph?algo=floyd_warshall', width=1440)
    seen = capture(page, '/run_floyd_warshall')
    nodes = [chr(65 + i) for i in range(12)]
    edges = ['%s %s %d' % (nodes[i], nodes[j], (i * 3 + j) % 9 + 1)
             for i in range(12) for j in range(i + 1, 12) if (i + j) % 3 != 0]
    text = '12 %d\n' % len(edges) + '\n'.join(edges)
    page.evaluate("t => { const e = document.getElementById('graph-input'); e.value = t; }", text)
    page.click('#run-button')
    page.wait_for_function('Workspace.current.steps.length > 500', timeout=30000)

    headers = seen[-1].headers
    assert headers['content-encoding'] == 'gzip'
    assert int(headers['content-length']) < len(seen[-1].body()) / 10
    page.evaluate('Workspace.current.go(Workspace.current.steps.length - 1)')
    assert page.errors == []
    page.ctx.close()


@pytest.mark.parametrize('path', ['/', '/learn', '/sorting', '/searching', '/compare', '/big-o', '/privacy',
                                  '/terms', '/graph?algo=bfs', '/graph?algo=astar'])
def test_every_page_arrives_gzipped_and_loads_without_errors(browser, base_url, path):
    ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
    page = ctx.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    document = []
    page.on('response', lambda r: document.append(r) if r.request.resource_type == 'document' else None)
    page.goto(base_url + path)
    page.wait_for_load_state('load')

    assert document[0].headers.get('content-encoding') == 'gzip', path
    assert page.inner_text('main').strip(), path                       # the decompressed page rendered
    assert errors == []
    ctx.close()


def test_a_run_from_every_workspace_still_works(browser, base_url):
    page = page_for(browser, base_url, '/searching')
    page.fill('#array-input', '4, 8, 15, 16, 23, 42')
    page.fill('#target-input', '16')
    page.click('#run-button')
    page.wait_for_function('Workspace.current.steps.length > 0')
    assert page.errors == []
    page.ctx.close()

    page = page_for(browser, base_url, '/compare')
    page.check('#manual-input-choice')
    page.fill('#manual-input', '5, 3, 8, 1, 9, 2')
    page.click('#run-button')
    page.wait_for_function('Compare.left.ws.steps.length > 0 && Compare.right.ws.steps.length > 0')
    page.ctx.close()
