"""The first-visit tour, checked without a browser: where it is loaded, what it stores,
and that it adds nothing the Content-Security-Policy would have to allow.
(tests/browser/test_browser_tour.py drives it in a real browser.)"""
import os
import re

import pytest

from paths import ROOT
from wsgi import app
from algotrace.core.siteconfig import csp_for

client = app.test_client()
TOUR_JS = os.path.join(ROOT, 'algotrace', 'static', 'js', 'tour.js')

WORKSPACE_PAGES = {
    '/sorting': 'sorting', '/searching': 'searching',
    '/graph?algo=bfs': 'graph', '/graph?algo=dijkstra': 'graph', '/graph?algo=topological_sort': 'graph',
    '/graph?algo=astar': 'astar',
}
OTHER_PAGES = ['/', '/learn', '/compare', '/big-o', '/privacy', '/terms', '/nope']


def source():
    with open(TOUR_JS, encoding='utf-8') as handle:
        return handle.read()


@pytest.mark.parametrize('path,name', sorted(WORKSPACE_PAGES.items()))
def test_each_workspace_page_loads_the_tour_for_its_own_workspace(path, name):
    html = client.get(path).get_data(as_text=True)
    tags = re.findall(r'<script[^>]*js/tour\.js[^>]*>', html)
    assert len(tags) == 1, path
    assert 'data-workspace="%s"' % name in tags[0]
    assert 'nonce' not in tags[0] and 'onload' not in tags[0]          # an external file, allowed by script-src 'self'
    assert html.index('js/workspace.js') < html.index('js/tour.js')


@pytest.mark.parametrize('path', OTHER_PAGES)
def test_no_other_page_loads_it(path):
    assert 'tour.js' not in client.get(path).get_data(as_text=True)


def test_it_stores_one_key_and_only_through_guarded_calls():
    text = source()
    assert re.findall(r"STORAGE_KEY = '([^']+)'", text) == ['pbl2.tourSeen']
    assert "'pbl2." not in text.replace("STORAGE_KEY = 'pbl2.tourSeen'", '')
    calls = re.findall(r'localStorage\.\w+Item', text)
    assert calls and all(c in ('localStorage.getItem', 'localStorage.setItem') for c in calls)
    for call in re.finditer(r'localStorage\.(?:get|set)Item', text):
        before = text[max(0, call.start() - 200):call.start()]
        assert 'try {' in before, 'a storage call outside try/catch'
    assert 'sessionStorage' not in text and 'document.cookie' not in text and 'indexedDB' not in text


def test_the_names_it_stores_are_the_ones_the_privacy_page_lists():
    text = source()
    declared = set(re.findall(r"^\s{8}(sorting|searching|graph|astar): \[", text, re.M))
    assert declared == {'sorting', 'searching', 'graph', 'astar'}
    page = client.get('/privacy').get_data(as_text=True)
    assert '<code>pbl2.tourSeen</code>' in page
    for name in declared:
        assert '<code>%s</code>' % name in page


def test_it_adds_nothing_the_policy_would_have_to_allow():
    text = source()
    for forbidden in ('eval(', 'new Function', 'setAttribute(\'style\'', 'setAttribute("style"', 'innerHTML',
                      'insertAdjacentHTML', 'document.write', 'fetch(', 'XMLHttpRequest', 'import(', 'http://', 'https://'):
        assert forbidden not in text, forbidden
    assert 'createElement(\'script\')' not in text and 'createElement(\'style\')' not in text
    policy = csp_for('x')
    assert "script-src 'self' 'nonce-x'" in policy and 'unsafe-eval' not in policy
    assert "style-src 'self' 'nonce-x' https://fonts.googleapis.com" in policy
    assert "connect-src 'self'" in policy


def test_the_tour_is_not_a_library_and_loads_none():
    text = source()
    assert 'require(' not in text and 'define(' not in text
    for name in os.listdir(os.path.join(ROOT, 'algotrace', 'static', 'vendor')):
        assert 'tour' not in name.lower()


def test_the_words_have_no_dashes_and_five_steps_per_workspace():
    text = source()
    assert chr(8212) not in text and chr(8211) not in text
    block = text[text.index('var COPY = {'):text.index('function buildSteps')]
    for name in ('sorting', 'searching', 'graph', 'astar'):
        part = block.split('        %s: [' % name)[1]
        part = part.split('        ]')[0]
        assert part.count("            ['") == 5, name


def test_the_replay_button_and_overlay_styles_exist():
    with open(os.path.join(ROOT, 'algotrace', 'static', 'styles.css'), encoding='utf-8') as handle:
        css = handle.read()
    for selector in ('.tour {', '.tour-spot {', '.tour-card {', '.tour-actions {', '.control-bar-foot {', '.tour-replay {'):
        assert selector in css, selector
    assert 'prefers-reduced-motion: no-preference' in css.split('GUIDED TOUR')[1]
    assert 'transition: all' not in css.split('GUIDED TOUR')[1]
