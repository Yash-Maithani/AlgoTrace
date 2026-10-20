"""The privacy page names exactly what the site stores in the browser.

The page promised "nothing" while theme.js and codeview.js were writing to
localStorage. This reads every file that touches browser storage, finds the
keys, and holds the page to them, so a new key cannot ship unlisted.
"""
import os
import re

import pytest

from app import app

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPECTED = {'theme', 'pbl2.codeLanguage', 'pbl2.tourSeen'}


def sources():
    out = {}
    for folder in ('static/js', 'templates'):
        for dirpath, _, files in os.walk(os.path.join(ROOT, folder)):
            if os.sep + 'lessons' in dirpath:
                continue
            for name in files:
                if name.endswith(('.js', '.html')):
                    path = os.path.join(dirpath, name)
                    with open(path, encoding='utf-8') as f:
                        out[os.path.relpath(path, ROOT)] = f.read()
    return out


def storage_keys():
    """Every localStorage key the site's own code reads or writes."""
    keys = set()
    for path, text in sources().items():
        if 'localStorage' not in text:
            continue
        constant = re.search(r"STORAGE_KEY\s*=\s*['\"]([^'\"]+)['\"]", text)
        for call in re.finditer(r"localStorage\.(?:get|set|remove)Item\(\s*([^,)]+)", text):
            arg = call.group(1).strip()
            if arg[0] in '\'"':
                keys.add(arg.strip('\'"'))
            elif arg == 'STORAGE_KEY' and constant:
                keys.add(constant.group(1))
            else:
                pytest.fail('%s reads a storage key this test cannot resolve: %s' % (path, arg))
    return keys


@pytest.fixture(scope='module')
def page():
    app.config['TESTING'] = True
    with app.test_client() as c:
        return c.get('/privacy').get_data(as_text=True)


def test_the_keys_the_code_uses_are_exactly_the_three_the_page_names():
    assert storage_keys() == EXPECTED


def test_the_page_names_every_key_and_what_it_holds(page):
    for key in EXPECTED:
        assert '<code>%s</code>' % key in page, key
    for value in ('light', 'dark', 'pseudocode', 'python', 'cpp', 'java', 'sorting', 'searching', 'graph', 'astar'):
        assert '<code>%s</code>' % value in page, value


def test_the_page_says_nothing_is_sent_to_the_server_and_how_to_clear_it(page):
    assert 'not sent to the server' in page
    assert 'localStorage.clear()' in page
    for browser in ('Chrome and Edge', 'Firefox', 'Safari'):
        assert browser in page
    assert 'complete list' in page


def test_the_page_no_longer_claims_nothing_is_stored(page):
    assert 'does not store' not in page
    assert 'anything in your browser between visits' not in page


def test_nothing_else_is_stored_and_no_cookie_is_set():
    for path, text in sources().items():
        for forbidden in ('document.cookie', 'sessionStorage', 'indexedDB', 'openDatabase'):
            assert forbidden not in text, (path, forbidden)
    with app.test_client() as c:
        for url in ('/', '/sorting', '/learn', '/privacy', '/run_sort'):
            reply = c.get(url) if url != '/run_sort' else c.post(url, json={'algorithm': 'Bubble Sort', 'values': '3, 1'})
            assert 'Set-Cookie' not in reply.headers, url


def test_the_values_the_page_lists_are_the_ones_the_code_accepts():
    codeview = sources()[os.path.join('static', 'js', 'codeview.js')]
    ids = set(re.findall(r"id: '([a-z]+)', label", codeview))

    assert ids == {'pseudocode', 'python', 'c', 'cpp', 'java'}
    assert "v === 'dark' || v === 'light'" in sources()[os.path.join('static', 'js', 'theme.js')]
