"""Shared by the tests that drive a real browser (see tests/conftest.py).

Playwright is not needed to run the site, only to test it in a browser, so it
lives in requirements-dev.txt and every browser test skips, with a warning
printed at the top and the bottom of the run, when it is missing.
"""
import shutil

try:
    from playwright.sync_api import sync_playwright
except ImportError:                                   # pragma: no cover
    sync_playwright = None

NODE = shutil.which('node')

INSTALL = ('python -m pip install -r requirements-dev.txt  &&  '
           'python -m playwright install chromium')

SKIP_REASON = 'browser tests need Playwright and node: ' + INSTALL


def available():
    return sync_playwright is not None and NODE is not None


def launch(playwright):
    """The bundled Chromium if it was installed, else Chrome, else Edge."""
    errors = []
    for options in ({}, {'channel': 'chrome'}, {'channel': 'msedge'}):
        try:
            return playwright.chromium.launch(headless=True, **options)
        except Exception as error:                    # noqa: BLE001
            errors.append(str(error).splitlines()[0])
    return None


def page_for(browser, base_url, path, width=1280, height=900, scheme='light', reduced='no-preference'):
    ctx = browser.new_context(viewport={'width': width, 'height': height}, color_scheme=scheme,
                              reduced_motion=reduced)
    page = ctx.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(base_url + path)
    page.errors = errors
    page.ctx = ctx
    return page
