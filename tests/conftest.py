"""Fixtures and a loud warning for the browser tests.

A skipped test is easy to miss in a green run, and the browser tests are the
only ones that check the real CSS (reduced motion, widths, themes). So when
Playwright is not installed, say so at the top of the run and again at the
bottom, with the two commands that fix it.
"""
import os
import threading

import pytest

# The rate limit on /run_* would throttle the thousands of runs these tests make
# from one address. tests/test_rate_limit.py turns it back on for itself. This has
# to be set before anything imports app.
os.environ.setdefault('RATE_LIMIT_PER_MINUTE', '0')

import browser_helpers as bh


def pytest_collection_modifyitems(config, items):
    """A browser test starts a real browser, so it counts as slow: the quick
    run, `pytest -m "not slow"`, leaves every one of them out."""
    for item in items:
        if 'browser' in getattr(item, 'fixturenames', ()):
            item.add_marker(pytest.mark.slow)


def pytest_report_header(config):
    if bh.sync_playwright is None:
        return 'browser tests: DISABLED, Playwright is not installed. Run: ' + bh.INSTALL
    if bh.NODE is None:
        return 'browser tests: DISABLED, node is not installed'
    return 'browser tests: enabled (Playwright)'


def pytest_terminal_summary(terminalreporter):
    if bh.available():
        return
    skipped = [r for r in terminalreporter.stats.get('skipped', [])
               if 'browser tests need' in str(getattr(r, 'longrepr', ''))]
    terminalreporter.write_sep('!', 'WARNING: %d browser tests did not run' % len(skipped), yellow=True, bold=True)
    terminalreporter.write_line('They check reduced motion, widths and themes in a real browser.')
    terminalreporter.write_line('Install them with:  ' + bh.INSTALL, yellow=True)


@pytest.fixture(scope='session')
def base_url():
    from werkzeug.serving import make_server
    from app import app
    app.config['TESTING'] = True
    server = make_server('127.0.0.1', 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield 'http://127.0.0.1:%d' % server.server_port
    server.shutdown()


@pytest.fixture(scope='session')
def browser():
    if not bh.available():
        pytest.skip(bh.SKIP_REASON)
    with bh.sync_playwright() as p:
        b = bh.launch(p)
        if b is None:
            pytest.skip('browser tests need a browser: python -m playwright install chromium')
        yield b
        b.close()
