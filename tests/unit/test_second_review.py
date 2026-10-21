"""The second round of review findings, pinned.

Each test here stands for something a reader of the site actually hit: a
refused run that kept playing the run before it, four links that opened the
wrong algorithm, a counter that named the wrong operation, a result panel
that claimed more than the algorithm had reached, and a handful of smaller
things that made the pages look unfinished.
"""
import json
import os
import re
import subprocess

import pytest

from paths import PACKAGE, ROOT, package_source
from wsgi import app
from algotrace.algorithms.sorting.insertion_sort import insertion_sort

TEMPLATES = os.path.join(ROOT, 'algotrace', 'templates')
STATIC = os.path.join(ROOT, 'algotrace', 'static')


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# 1. A refused run leaves nothing of the run before it
# ---------------------------------------------------------------------------

def test_binary_search_still_refuses_unsorted_input(client):
    response = client.post('/run_search', json={
        'algorithm': 'binary_search',
        'array': [42, 17, 93, 8, 61],
        'target': 93,
    })

    assert response.status_code == 400
    body = response.get_json()
    assert body['unsorted'] is True
    assert body['sorted_array'] == [8, 17, 42, 61, 93]


def test_a_refused_run_is_discarded_before_the_page_is_told():
    """The order matters: onError runs after the old run is thrown away."""
    workspace = read('algotrace', 'static', 'js', 'workspace.js')

    assert 'Workspace.prototype.discard' in workspace
    error_path = workspace.split('if (!result.ok || result.body.error) {', 1)[1]
    error_path = error_path.split('}', 1)[0]
    assert 'self.discard();' in error_path, (
        'the refused run does not discard the one before it')
    assert error_path.index('self.discard()') < error_path.index('onError'), (
        'the page is told about the error before the old run is cleared')


def test_discard_clears_every_part_of_the_run():
    workspace = read('algotrace', 'static', 'js', 'workspace.js')
    body = workspace.split('Workspace.prototype.discard = function () {', 1)[1]
    body = body.split('};', 1)[0]

    for cleared in ('this.pause()', 'this.steps = []', 'this.payload = null',
                    'this.lastStats = null', 'clearResult', 'clearStage',
                    'clearStep', 'syncTransport'):
        assert cleared in body, 'discard() leaves %s behind' % cleared


def test_the_learn_panel_can_be_blanked():
    teacher = read('algotrace', 'static', 'js', 'teacher.js')
    body = teacher.split('Panel.prototype.clearStep = function () {', 1)[1]
    body = body.split('\n    };', 1)[0]

    assert "this.explainText.textContent = ''" in body
    assert "this.explainWhy.textContent = ''" in body
    assert 'this.highlight(null)' in body, 'the code line stays highlighted'
    assert 'this.renderThisRun(null)' in body, 'the counters stay'


@pytest.mark.parametrize('page', ['searching', 'sorting'])
def test_each_stage_knows_how_to_empty_itself(page):
    source = read('algotrace', 'templates', '%s.html' % page)

    assert 'clearStage: function ()' in source, '%s cannot empty its stage' % page
    body = source.split('clearStage: function () {', 1)[1].split('},', 1)[0]
    if 'stage.clear()' in body:
        # Phase 17: sorting's bars live in static/js/sortstage.js, shared
        # with /compare, and clear() is where the empty message comes back.
        stage = read('algotrace', 'static', 'js', 'sortstage.js')
        body = stage.split('function clear() {', 1)[1].split('\n        }', 1)[0]
    assert "hidden = false" in body, '%s does not restore its empty message' % page


def test_an_empty_run_disables_the_transport():
    """With no steps the buttons are off, so a refused run cannot be played."""
    workspace = read('algotrace', 'static', 'js', 'workspace.js')
    body = workspace.split('Workspace.prototype.syncTransport', 1)[1]
    # Phase 17: a lone workspace and a /compare group share one function
    # that sets the buttons, so the rule is checked there.
    buttons = workspace.split('function syncButtons', 1)[1].split('\n    }\n', 1)[0]

    assert 'var has = this.steps.length > 0;' in body
    assert "'Step 0 of 0'" in body
    assert 'syncButtons(this.parts, has,' in body
    for button in ("parts['step-back'].disabled = !has", "parts['step-forward'].disabled = !has",
                   'parts.reset.disabled = !has', "parts['play-pause'].disabled = !has"):
        assert button in buttons, 'the transport stays live without steps'


# ---------------------------------------------------------------------------
# 2. The links on /learn open what they name
# ---------------------------------------------------------------------------

def learn_links(client):
    html = client.get('/learn').get_data(as_text=True)
    return sorted(set(re.findall(r'href="(/[^"]*)"', html)))


def selected(body):
    """Whichever picker entry is marked current, link or button."""
    found = re.findall(r'data-algorithm="([^"]+)"[^>]*aria-current="true"', body)
    if found:
        return found[0]
    found = re.findall(r'\?algo=([a-z_]+)"[^>]*\n?[^>]*aria-current="page"', body)
    return found[0] if found else None


def test_every_link_on_learn_resolves(client):
    for url in learn_links(client):
        assert client.get(url).status_code == 200, url


@pytest.mark.parametrize('key', ['linear_search', 'binary_search'])
def test_the_searching_links_preselect(client, key):
    body = client.get('/searching?algorithm=%s' % key).get_data(as_text=True)

    assert selected(body) == key


@pytest.mark.parametrize('name', ['Bubble Sort', 'Selection Sort',
                                  'Insertion Sort', 'Merge Sort',
                                  'Quick Sort', 'Heap Sort'])
def test_the_sorting_links_preselect(client, name):
    body = client.get('/sorting?algorithm=%s' % name.replace(' ', '+')).get_data(as_text=True)

    assert selected(body) == name


def test_the_four_algorithm_links_on_learn_all_land_right(client):
    """The ones the review found: two searches, named twice each."""
    wanted = {'/searching?algorithm=linear_search': 'linear_search',
              '/searching?algorithm=binary_search': 'binary_search'}
    links = learn_links(client)

    for url, key in wanted.items():
        assert url in links, '%s is not linked from /learn' % url
        assert selected(client.get(url).get_data(as_text=True)) == key

    html = client.get('/learn').get_data(as_text=True)
    assert html.count('?algorithm=binary_search') == 2, (
        'the order list and the card should both link binary search')
    assert html.count('?algorithm=linear_search') == 2


def test_an_unknown_search_algorithm_falls_back_rather_than_erroring(client):
    body = client.get('/searching?algorithm=nonsense').get_data(as_text=True)

    assert selected(body) == 'linear_search'


# ---------------------------------------------------------------------------
# 5. Insertion sort shifts
# ---------------------------------------------------------------------------

def insertion_stats(values):
    stats = {'swaps': 0, 'comparisons': 0}
    insertion_sort(list(values), lambda a, c=None, m=None: None,
                   lambda: None, stats)
    return stats


def test_insertion_sort_shifts_rather_than_swaps():
    """A value walks back by sliding its neighbours right, one at a time."""
    assert insertion_stats([1, 3, 5, 8, 9])['swaps'] == 0
    assert insertion_stats([5, 3, 8, 1, 9])['swaps'] == 4
    assert insertion_stats([9, 8, 5, 3, 1])['swaps'] == 10


def test_the_number_did_not_change(client):
    """Renaming a counter must not move it."""
    payload = client.post('/run_sort', json={
        'algorithm': 'Insertion Sort',
        'values': [5, 3, 8, 1, 9],
    }).get_json()

    assert payload['result']['swaps'] == 4
    assert payload['result']['comparisons'] == 6


def test_the_lesson_names_and_explains_the_shifts():
    lesson = read('algotrace', 'static', 'js', 'lessons', 'insertion_sort.js')

    assert "countLabel: 'shifts'" in lesson
    note = re.search(r"countsNote: '([^']*(?:\\'[^']*)*)'", lesson)
    assert note, 'the renamed counter is unexplained'
    assert 'never exchanges a pair' in note.group(1)


# ---------------------------------------------------------------------------
# 6. Prim reaches one component
# ---------------------------------------------------------------------------

CONNECTED_GRAPH = {'A': {'B': 1, 'C': 4}, 'B': {'A': 1, 'C': 2},
                   'C': {'A': 4, 'B': 2}}
SPLIT_GRAPH = {'A': {'B': 1}, 'B': {'A': 1}, 'C': {'D': 2}, 'D': {'C': 2}}


def prim_final(client, graph):
    response = client.post('/run_prim', json={'graph': graph, 'start': 'A'})
    assert response.status_code == 200
    return response.get_json()['meta'][-1]


def test_prim_on_a_whole_graph_says_it_reached_everything(client):
    meta = prim_final(client, CONNECTED_GRAPH)

    assert meta['vars']['reached_everything'] is True
    assert 'reaching 3 of the 3 nodes' in meta['explain']['beginner']
    assert 'minimum spanning tree of the whole graph' in meta['explain']['why']


def test_prim_on_a_split_graph_says_what_it_missed(client):
    meta = prim_final(client, SPLIT_GRAPH)

    assert meta['vars']['reached_everything'] is False
    assert 'reaching 2 of the 4 nodes' in meta['explain']['beginner']
    assert 'separate piece' in meta['explain']['why']
    assert 'spanning tree of the whole graph' not in meta['explain']['why']


def test_the_two_cases_do_not_share_one_hedged_sentence(client):
    whole = prim_final(client, CONNECTED_GRAPH)['explain']['why']
    split = prim_final(client, SPLIT_GRAPH)['explain']['why']

    assert whole != split


def test_the_prim_result_panel_does_not_promise_an_mst():
    page = read('algotrace', 'templates', 'graph_base.html')
    prim = page.split("algorithm === 'prim'", 1)[1].split('function ', 1)[0]

    assert 'reachedEverything' in prim, 'the panel is not checking what it spanned'
    assert "start node\\'s component" in prim
    assert 'Total MST Weight' not in prim
    assert 'Minimum Spanning Tree' not in prim


# ---------------------------------------------------------------------------
# 7. The smaller things
# ---------------------------------------------------------------------------

def test_an_unknown_graph_algorithm_is_a_404(client):
    assert client.get('/graph?algo=notanalgorithm').status_code == 404
    assert client.get('/graph?algo=').status_code == 404


@pytest.mark.parametrize('algo', ['bfs', 'dfs', 'dijkstra', 'prim', 'kruskal',
                                  'floyd_warshall', 'bellman_ford'])
def test_every_real_graph_algorithm_still_serves(client, algo):
    response = client.get('/graph?algo=%s' % algo)

    assert response.status_code == 200
    assert 'BFS' in response.get_data(as_text=True)


def test_the_graph_default_is_still_bfs(client):
    body = client.get('/graph').get_data(as_text=True)

    assert '<title>Breadth-First Search' in body


def test_no_debug_logging_ships():
    for folder in ('templates', 'static'):
        for dirpath, _, filenames in os.walk(os.path.join(PACKAGE, folder)):
            for name in filenames:
                if not name.endswith(('.html', '.js')):
                    continue
                path = os.path.join(dirpath, name)
                with open(path, encoding='utf-8') as fh:
                    source = fh.read()
                assert 'console.log' not in source, (
                    '%s still logs to the console' % os.path.basename(path))


def test_the_server_does_not_print_on_every_request():
    source = package_source()

    assert 'print(f"Request for graph' not in source
    assert 'For debugging' not in source


def test_bar_values_come_back_when_there_is_room():
    css = read('algotrace', 'static', 'styles.css')
    # Phase 17 moved the bars into static/js/sortstage.js, shared by
    # /sorting and /compare; both pages load it.
    page = read('algotrace', 'static', 'js', 'sortstage.js')
    for template in ('sorting.html', 'compare.html'):
        assert 'js/sortstage.js' in read('algotrace', 'templates', template), template

    assert '.bar-container.shows-values .bar-value { display: block; }' in css
    assert "classList.toggle('shows-values'" in page
    threshold = re.search(r"toggle\('shows-values', data\.length <= (\d+)\)", page)
    assert threshold, 'no size threshold for showing values'
    assert 5 <= int(threshold.group(1)) <= 15


def test_kruskal_has_no_stray_spaces_where_its_emoji_were():
    source = read('algotrace', 'templates', 'kruskal.html')

    for stray in ('<li> ', '<strong> ', '<p> <strong>'):
        assert stray not in source, 'kruskal.html still has a gap at %r' % stray


# ---------------------------------------------------------------------------
# 4. The banner and the counters, checked where they are wired
# ---------------------------------------------------------------------------

def test_the_banner_waits_for_the_last_step():
    workspace = read('algotrace', 'static', 'js', 'workspace.js')
    load = workspace.split('Workspace.prototype.load = function', 1)[1]
    load = load.split('};', 1)[0]

    assert 'renderResult' not in load, 'the banner still appears on load'
    assert 'showResultIfFinished' in workspace
    shown = workspace.split('showResultIfFinished = function () {', 1)[1]
    assert 'this.index === this.steps.length - 1' in shown


def test_the_sorting_counter_counts_up(client):
    """Every step carries the work done so far, ending at the result."""
    payload = client.post('/run_sort', json={
        'algorithm': 'Bubble Sort',
        'values': [5, 3, 8, 1, 9],
    }).get_json()

    tallies = [step['vars']['comparisons'] for step in payload['steps']]

    assert tallies[0] == 0 or tallies[0] == 1
    assert tallies == sorted(tallies), 'the running count goes backwards'
    assert tallies[-1] == payload['result']['comparisons']
    assert len(set(tallies)) > 1, 'the count never moves'


def test_the_sorting_page_reads_the_step_not_the_total():
    page = read('algotrace', 'templates', 'sorting.html')
    stats = page.split('context.stats({', 1)[1].split('});', 1)[0]

    assert 'step.vars.comparisons' in stats
    assert 'payload.result' not in stats, (
        'the This Run box still shows the final totals from step 1')


def test_graph_lessons_do_not_promise_a_counter():
    script = (
        "global.window = {};"
        "const fs = require('fs'), path = require('path');"
        "const dir = %s;"
        "fs.readdirSync(dir).filter(f => f.endsWith('.js')).sort()"
        "  .forEach(f => eval(fs.readFileSync(path.join(dir, f), 'utf8')));"
        "process.stdout.write(JSON.stringify(global.window.LESSONS));"
    ) % json.dumps(os.path.join(STATIC, 'js', 'lessons'))
    try:
        out = subprocess.run(['node', '-e', script], capture_output=True, check=True)
    except Exception:
        pytest.skip('node is needed to read the lesson files')

    lessons = json.loads(out.stdout.decode('utf-8'))
    for key, lesson in lessons.items():
        sentence = lesson['complexity']['thisRun']
        if lesson['family'] == 'graph':
            assert 'The counter shows' not in sentence, (
                '%s promises a counter its box does not have' % key)
        else:
            assert 'The counter shows' in sentence, key


# ---------------------------------------------------------------------------
# The inline script, which no other test parses
# ---------------------------------------------------------------------------

def test_the_graph_pages_inline_script_parses():
    """graph_base.html holds 3,000 lines of JavaScript inside a template.

    Nothing checked it, so removing a line from a call that spanned several
    left the rest of its arguments stranded and took the whole page down
    while every other check stayed green.
    """
    page = read('algotrace', 'templates', 'graph_base.html')
    block = re.search(r'\{% block page_js %\}(.*?)\{% endblock %\}', page, re.S)
    assert block, 'the page_js block is gone'

    body = re.sub(r'<script[^>]*src=[^>]*></script>', '', block.group(1))
    body = body.replace('<script nonce="{{ csp_nonce }}">', '').replace('</script>', '')
    # Jinja expressions stand in as a literal, since node cannot read them.
    body = re.sub(r'\{\{.*?\}\}', 'null', body)

    import tempfile
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False,
                                     encoding='utf-8') as fh:
        fh.write(body)
        path = fh.name
    try:
        result = subprocess.run(['node', '--check', path], capture_output=True)
    except Exception:
        pytest.skip('node is needed to parse the inline script')
    finally:
        os.unlink(path)

    assert result.returncode == 0, result.stderr.decode('utf-8', 'replace')[:500]


@pytest.mark.parametrize('name', ['workspace.js', 'teacher.js', 'growth.js',
                                  'nav.js', 'theme.js'])
def test_each_shared_script_parses(name):
    try:
        result = subprocess.run(
            ['node', '--check', os.path.join(STATIC, 'js', name)],
            capture_output=True)
    except Exception:
        pytest.skip('node is needed to parse the scripts')

    assert result.returncode == 0, result.stderr.decode('utf-8', 'replace')[:300]
