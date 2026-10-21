"""/learn and Home from one registry, figures from the lessons, the Merge and
Heap wording, and the graph copy (the Phase 22 fixes).

In a browser: tests/browser/test_browser_learn_and_graph_preview.py. The Predict
changes have their own file, tests/unit/test_predict_neutral.py.
"""
import json
import os
import re
import shutil
import subprocess

import pytest

from paths import ROOT
from wsgi import app
from algotrace.catalog import (GRAPH_PICKER, LEARN_ORDER, SEARCH_ALGORITHMS, SORT_LESSON_IDS,

                               START_HERE_COUNT, sorting_algo_dict)
from algotrace.routes.sorting import sort_payload

NODE = shutil.which('node')
LESSON_DIR = os.path.join(ROOT, 'algotrace', 'static', 'js', 'lessons')


@pytest.fixture(scope='module')
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return f.read()


# ---------------------------------------------------------------------------
# One registry for the order and the counts
# ---------------------------------------------------------------------------

def test_the_registry_covers_every_algorithm_once():
    ids = [entry[0] for entry in LEARN_ORDER]
    lessons = sorted(n[:-3] for n in os.listdir(LESSON_DIR) if n.endswith('.js'))
    assert sorted(ids) == lessons and len(ids) == len(set(ids))
    expected = (set(SORT_LESSON_IDS.values()) | set(SEARCH_ALGORITHMS) |
                {key for key, _, _ in GRAPH_PICKER})
    assert set(ids) == expected
    assert len(ids) == len(sorting_algo_dict) + len(SEARCH_ALGORITHMS) + len(GRAPH_PICKER)


def test_learn_and_home_use_the_same_order(client):
    learn = client.get('/learn').get_data(as_text=True)
    order = re.findall(r'class="order-name"[^>]*>([^<]+)</a>', learn)
    assert order == [entry[1].replace("'", '&#39;') for entry in LEARN_ORDER]
    home = client.get('/').get_data(as_text=True)
    start = home.split('class="start-list"', 1)[1].split('</ol>', 1)[0]
    names = re.findall(r'<a href="[^"]+">([^<]+)</a>', start)
    assert names == [entry[1] for entry in LEARN_ORDER[:START_HERE_COUNT]]
    assert names[0] == order[0]


def test_every_count_comes_from_the_registry(client):
    home = client.get('/').get_data(as_text=True)
    total = len(LEARN_ORDER)
    assert 'See all %d in order' % total in home
    assert '<h1 class="hero-title">Watch %d algorithms run one step at a time</h1>' % total in home
    metas = re.findall(r'<span class="track-meta">(\d+) algorithms</span>', home)
    assert metas == [str(len(sorting_algo_dict)), str(len(SEARCH_ALGORITHMS)), str(len(GRAPH_PICKER))]
    for template in ('landing.html', 'learn.html'):
        source = read('algotrace', 'templates', template)
        assert not re.search(r'See all \d+', source)
        assert not re.search(r'track-meta">\d', source)
        assert not re.search(r'<p>(Two|Three|Six|Seven|Eight|Nine) algorithms', source)


# ---------------------------------------------------------------------------
# /learn figures from the lesson files
# ---------------------------------------------------------------------------

def test_learn_states_no_figure_of_its_own(client):
    source = read('algotrace', 'templates', 'learn.html')
    assert not re.search(r'<dd>O\(', source)
    assert not re.search(r'order-tag">O\(', source)
    html = client.get('/learn').get_data(as_text=True)
    lessons = {entry[0] for entry in LEARN_ORDER}
    slots = re.findall(r'data-lesson="([^"]+)" data-figure="(best|worst|space)"', html)
    assert len(slots) >= 2 * len(LEARN_ORDER)
    assert {lesson for lesson, _ in slots} == lessons
    assert 'js/learnfigures.js' in html


@pytest.mark.skipif(NODE is None, reason='node is not installed')
def test_learnfigures_writes_the_lesson_value():
    script = ("const F=require('./algotrace/static/js/learnfigures.js');"
              "console.log(JSON.stringify(['O(n squared)','O(V times E)','O(square root of n)',"
              "'O(d times (n plus b))','O(n log n)'].map(F.symbols)))")
    out = json.loads(subprocess.run([NODE, '-e', script], capture_output=True, text=True,
                                    encoding='utf-8', cwd=ROOT, check=True).stdout)
    assert out == ['O(n²)', 'O(V·E)', 'O(√n)', 'O(d(n + b))', 'O(n log n)']


# ---------------------------------------------------------------------------
# Wording
# ---------------------------------------------------------------------------

def test_merge_sort_no_longer_claims_to_be_alone():
    text = read('algotrace', 'static', 'js', 'lessons', 'merge_sort.js')
    assert 'only sort here with no bad case' not in text
    assert 'heap sort has the same n log n worst case' in text
    assert 'counting and radix sort cost the same on every input' in text


def test_heap_sort_names_the_parent_and_positions():
    steps = sort_payload('Heap Sort', [3, 5, 3, 1, 8])['steps']
    lefts = [s for s in steps if s['line'] == 'cmp-left']
    rights = [s for s in steps if s['line'] == 'cmp-right']
    assert lefts and rights
    for s in lefts:
        child, parent = s['indices']
        assert s['explain']['beginner'] == ('Is the left child %d at position %d bigger than its parent '
                                            '%d at position %d?' % (s['values'][0], child, s['values'][1], parent))
    for s in rights:
        child, other = s['indices']
        who = 'its parent' if other == s['vars']['i'] else 'the left child'
        assert s['explain']['beginner'] == ('Is the right child %d at position %d bigger than %s %d at '
                                            'position %d?' % (s['values'][0], child, who, s['values'][1], other))


def test_graph_copy(client):
    bfs = client.get('/graph?algo=bfs').get_data(as_text=True)
    assert 'GPS' not in bfs and 'GPS' not in read('algotrace', 'templates', 'dijkstra.html')
    assert 'Animated MST Visualizer' not in read('algotrace', 'templates', 'kruskal.html')
    for old in ('Start Node:', 'Input Method', 'Visualize Algorithm', 'Number of Nodes:',
                'Generate Random Graph', 'Enter a graph in JSON format'):
        assert old not in bfs, old
    for new in ('Start node', '<h3>Input</h3>', 'Run the algorithm', 'Make a random graph'):
        assert new in bfs, new
    home = client.get('/').get_data(as_text=True)
    assert 'Interactive Algorithm Visualizer' not in home
    for key in ('bfs', 'dfs', 'dijkstra', 'prim', 'kruskal', 'floyd_warshall', 'bellman_ford'):
        panel = read('algotrace', 'templates', key + '.html')
        assert '<p><strong>Good for</strong></p>' in panel and 'Use Cases' not in panel
