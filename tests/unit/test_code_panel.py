"""Phase 14 part A: the code panel, and the Prim crash fixed in step 0."""
import json
import os
import shutil
import subprocess

import pytest

from paths import ROOT, JS
from wsgi import app
from algotrace.routes.sorting import SORT_VARIANTS

NODE = shutil.which('node')
needs_node = pytest.mark.skipif(NODE is None, reason='node is not installed, so the panel code cannot be run')
LANGUAGES = ['pseudocode', 'python', 'c', 'cpp', 'java']


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return f.read()


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Step 0: a neighbour with no node line
# ---------------------------------------------------------------------------

GAP = {'A': {'B': 1}, 'B': {'A': 1, 'C': 2}}          # C is named, never defined
GAP_AT_START = {'A': {'B': 1, 'Z': 4}, 'B': {'A': 1}}


@pytest.mark.parametrize('graph,missing', [(GAP, 'C'), (GAP_AT_START, 'Z')])
def test_prim_answers_a_missing_node_with_a_400_that_names_it(client, graph, missing):
    reply = client.post('/run_prim', json={'graph': graph, 'start': 'A'})

    assert reply.status_code == 400
    message = reply.get_json()['error']
    assert missing in message and 'no node of its own' in message
    assert 'An error occurred' not in message


@pytest.mark.parametrize('route', ['bfs', 'dfs', 'dijkstra', 'prim', 'bellman_ford'])
def test_no_graph_endpoint_answers_a_missing_node_with_a_500(client, route):
    reply = client.post('/run_' + route, json={'graph': GAP, 'start': 'A'})

    assert reply.status_code in (200, 400), route


def test_a_complete_graph_still_runs_in_prim(client):
    graph = {'A': {'B': 1}, 'B': {'A': 1, 'C': 2}, 'C': {'B': 2}}
    reply = client.post('/run_prim', json={'graph': graph, 'start': 'A'})

    assert reply.status_code == 200


def test_the_graph_page_shows_the_server_message():
    html = read('algotrace', 'templates', 'graph_base.html')

    assert "setGraphError('graph-error', data.error)" in html


# ---------------------------------------------------------------------------
# The listings the panel reads
# ---------------------------------------------------------------------------

_LISTINGS = None


def listings():
    global _LISTINGS
    if _LISTINGS is None:
        out = subprocess.run([NODE, os.path.join(JS, 'codeview_check.js'), 'listings'],
                             capture_output=True, text=True, check=True)
        _LISTINGS = json.loads(out.stdout)
    return _LISTINGS


@needs_node
def test_every_lesson_variant_and_language_has_a_listing():
    for name, by_language in listings().items():
        for language in LANGUAGES:
            assert by_language[language] and by_language[language]['lines'], (name, language)


@needs_node
def test_every_language_offers_the_same_line_ids():
    """What lets a highlighted line stay on the same id when the language
    changes."""
    for name, by_language in listings().items():
        reference = by_language['python']['ids']
        for language in LANGUAGES:
            assert by_language[language]['ids'] == reference, (name, language)


@needs_node
def test_only_c_c_plus_plus_and_java_have_helpers_and_none_carry_an_id():
    found = False
    for name, by_language in listings().items():
        for language in ('pseudocode', 'python'):
            assert by_language[language]['helpers'] == [], (name, language)
        for language in ('c', 'cpp', 'java'):
            for line in by_language[language]['helpers']:
                found = True
                assert line['id'] is None, (name, language)
    assert found


@needs_node
def test_the_c_swap_helper_keeps_its_whole_body():
    """A line that begins with `*` was read as a comment and dropped, which
    left swap() as `int t = *a;` and nothing else."""
    helper = [l['text'] for l in listings()['bubble_sort/off']['c']['helpers']]

    assert '*a = *b;' in helper and '*b = t;' in helper


@needs_node
def test_a_variant_shows_its_own_listing_in_every_language():
    for language in ('c', 'cpp', 'java'):
        assert any('swapped' in line for line in listings()['bubble_sort/on'][language]['lines']), language
        assert not any('swapped' in line for line in listings()['bubble_sort/off'][language]['lines']), language


SORT_KEYS = {'Bubble Sort': 'bubble_sort', 'Selection Sort': 'selection_sort',
             'Insertion Sort': 'insertion_sort', 'Merge Sort': 'merge_sort',
             'Quick Sort': 'quick_sort', 'Heap Sort': 'heap_sort'}
GRAPH = {'A': {'B': 4, 'C': 1}, 'B': {'A': 4, 'C': 2, 'D': 5}, 'C': {'A': 1, 'B': 2, 'D': 8},
         'D': {'B': 5, 'C': 8}}


def emitted(client, route, body):
    reply = client.post(route, json=body)
    assert reply.status_code == 200, (route, reply.get_json())
    payload = reply.get_json()
    steps = payload.get('meta') or payload['steps']
    return {s['line'] for s in steps if isinstance(s, dict) and s.get('line')}


@needs_node
def test_every_line_a_run_emits_is_in_every_language(client):
    runs = []
    for display, key in SORT_KEYS.items():
        spec = SORT_VARIANTS.get(display)
        options = [o[0] for o in spec['options']] if spec else [None]
        for option in options:
            body = {'algorithm': display, 'values': '5, 3, 8, 3, 9, 1, 7, 5'}
            if option:
                body['variant'] = option
            runs.append(('/run_sort', body, key + '/' + (option or 'default')))
    for algo in ('linear_search', 'binary_search'):
        runs.append(('/run_search', {'algorithm': algo, 'array': '1, 3, 5, 7, 9, 11', 'target': '7'},
                     algo + '/default'))
    for algo in ('bfs', 'dfs', 'dijkstra', 'prim', 'bellman_ford'):
        runs.append(('/run_' + algo, {'graph': GRAPH, 'start': 'A'}, algo + '/default'))
    nodes = list(GRAPH)
    edges = [['A', 'B', 4], ['A', 'C', 1], ['B', 'C', 2], ['B', 'D', 5]]
    for algo in ('kruskal', 'floyd_warshall'):
        runs.append(('/run_' + algo, {'nodes': nodes, 'edges': edges}, algo + '/default'))

    table = listings()
    for route, body, name in runs:
        lines = emitted(client, route, body)
        assert lines, name
        for language in LANGUAGES:
            missing = lines - set(table[name][language]['ids'])
            assert not missing, (name, language, missing)


# ---------------------------------------------------------------------------
# The saved language
# ---------------------------------------------------------------------------

@needs_node
def test_the_saved_language_defaults_to_python_and_survives_broken_storage():
    result = subprocess.run([NODE, os.path.join(JS, 'codeview_check.js'), 'storage'],
                            capture_output=True, text=True)

    assert result.returncode == 0, result.stdout + result.stderr


# ---------------------------------------------------------------------------
# Wiring and styling
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('page,lessons', [
    ('/sorting', ['bubble_sort', 'quick_sort', 'heap_sort']),
    ('/searching', ['linear_search', 'binary_search']),
    ('/graph?algo=prim', ['prim']),
    ('/graph?algo=floyd_warshall', ['floyd_warshall']),
    ('/', ['bubble_sort']),
])
def test_every_page_with_a_code_panel_loads_the_panel_and_its_listings(client, page, lessons):
    html = client.get(page).get_data(as_text=True)

    assert 'js/codeview.js' in html
    for name in lessons:
        assert 'js/lessons/code/%s.js' % name in html, (page, name)


@pytest.mark.parametrize('page', ['/sorting', '/searching', '/graph?algo=bfs'])
def test_codeview_loads_before_the_panel_and_the_workspace(client, page):
    html = client.get(page).get_data(as_text=True)

    assert html.index('js/codeview.js') < html.index('js/teacher.js') < html.index('js/workspace.js')


def test_the_home_code_card_follows_the_saved_language(client):
    html = client.get('/').get_data(as_text=True)

    assert 'id="home-code-lang"' in html
    assert 'js/home_code.js' in html
    # No JavaScript: the card still holds the Python it was served with.
    assert 'class="band-code"' in html and 'range(0, n-i-1)' in html


def test_the_old_two_button_toggle_is_gone():
    assert 'code-toggle' not in read('algotrace', 'static', 'js', 'teacher.js')
    assert 'code-toggle' not in read('algotrace', 'static', 'styles.css')
    assert "'pseudocode', 'python'" not in read('algotrace', 'static', 'js', 'teacher.js')


def css_block(selector):
    css = read('algotrace', 'static', 'styles.css')
    start = css.index(selector + ' {')
    return css[start:css.index('}', start)]


def test_language_tabs_are_rectangles_with_a_6px_radius():
    assert '--radius-sm: 6px' in read('algotrace', 'static', 'styles.css')
    for selector in ('.lang-tabs', '.lang-tab', '.lang-thumb', '.lang-select', '.code-action'):
        block = css_block(selector)
        assert 'radius-sm' in block, selector
        assert '999' not in block and '50%' not in block and 'pill' not in block, selector


def test_the_selected_tab_slides_by_transform_for_180ms():
    thumb = css_block('.lang-thumb')

    assert 'transition: transform var(--dur-base) var(--ease-out)' in thumb
    assert '--dur-base: 180ms' in read('algotrace', 'static', 'styles.css')
    assert 'left var' not in thumb and 'width var' not in thumb


def test_the_listing_crossfades_in_about_120ms():
    assert 'var FADE_MS = 60;' in read('algotrace', 'static', 'js', 'codeview.js')   # out, then in: 120ms
    assert 'opacity 60ms' in read('algotrace', 'static', 'styles.css')


def test_reduced_motion_makes_both_animations_instant():
    css = read('algotrace', 'static', 'styles.css')
    block = css[css.rindex('@media (prefers-reduced-motion: reduce) {'):]

    assert '.lang-thumb' in block and '.code-stage' in block and 'transition: none' in block
    assert 'reducedMotion()' in read('algotrace', 'static', 'js', 'codeview.js')


def test_below_520px_the_tabs_become_a_select():
    css = read('algotrace', 'static', 'styles.css')
    narrow = css.split('@media (max-width: 519.98px)', 1)[1][:160]

    assert '.lang-tabs { display: none; }' in narrow
    assert '.lang-select { display: block' in narrow
    assert 'display: none;' in css_block('.lang-select')


def test_long_lines_wrap_with_a_hanging_indent_and_never_scroll_sideways():
    line = css_block('.code-line code')

    assert 'white-space: pre-wrap' in line and 'overflow-wrap: anywhere' in line
    assert 'text-indent: -2ch' in line and '+ 2ch' in line
    assert 'overflow-x' not in css_block('.code-listing')
    assert 'white-space: pre;' not in css_block('.code-line')


def test_tabs_are_a_real_tablist_with_arrow_home_and_end():
    js = read('algotrace', 'static', 'js', 'codeview.js')

    for needle in ["setAttribute('role', 'tablist')", "setAttribute('role', 'tab')",
                   "'ArrowRight'", "'ArrowLeft'", "'Home'", "'End'", 'aria-selected', 'tabIndex']:
        assert needle in js, needle


def test_expand_is_a_native_modal_dialog_that_follows_the_run():
    js = read('algotrace', 'static', 'js', 'codeview.js')

    assert "document.createElement('dialog')" in js
    assert '.showModal()' in js
    assert 'aria-labelledby' in js
    assert 'this.dialog.highlight(this.currentLine)' in js       # live while open
    assert 'helpersOpen: true' in js                              # the full listing


def test_helpers_start_collapsed_and_the_button_reports_it():
    js = read('algotrace', 'static', 'js', 'codeview.js')

    assert "'Show helpers'" in js and "'Hide helpers'" in js
    assert "setAttribute('aria-expanded'" in js
    assert 'this.expanded = !!options.helpersOpen;' in js


def test_storage_access_is_always_guarded():
    js = read('algotrace', 'static', 'js', 'codeview.js')

    for call in ('localStorage.getItem', 'localStorage.setItem'):
        at = js.index(call)
        assert 'try {' in js[at - 120:at], call
