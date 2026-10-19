"""Two findings from the review, pinned so they cannot come back.

Kruskal called a spanning forest a minimum spanning tree, and its closing
explanation asserted the forest whatever the graph had been, so a connected
run was told it had produced a forest when it had produced a tree.

Merge sort counted every copy back as a swap. It never exchanges a pair, so
the sort that does no swapping at all reported more of them than any other,
and an already sorted list still reported twelve.
"""
import json
import os
import re
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from sorting_algorithms.merge_sort import merge_sort

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def final_meta(client, nodes, edges):
    response = client.post('/run_kruskal',
                           json={'nodes': nodes, 'edges': edges},
                           content_type='application/json')
    assert response.status_code == 200
    return response.get_json()['meta'][-1]


# ---------------------------------------------------------------------------
# Kruskal names what it built
# ---------------------------------------------------------------------------

CONNECTED = (['A', 'B', 'C'], [['A', 'B', 2], ['B', 'C', 1], ['A', 'C', 3]])
DISCONNECTED = (['A', 'B', 'C', 'D'], [['A', 'B', 1], ['C', 'D', 2]])


def test_a_connected_graph_gives_a_tree(client):
    meta = final_meta(client, *CONNECTED)

    assert 'minimum spanning tree' in meta['explain']['beginner']
    assert 'forest' not in meta['explain']['beginner']
    assert 'forest' not in meta['explain']['why'], (
        'a connected run is still told it produced a forest')


def test_a_disconnected_graph_gives_a_forest(client):
    meta = final_meta(client, *DISCONNECTED)

    assert 'minimum spanning forest' in meta['explain']['beginner']
    assert 'disconnected' in meta['explain']['why']


def test_the_closing_line_says_which_it_is(client):
    """The two cases must not share one hedged sentence."""
    connected = final_meta(client, *CONNECTED)['explain']
    disconnected = final_meta(client, *DISCONNECTED)['explain']

    assert connected['why'] != disconnected['why']


def test_the_step_itself_records_whether_it_spans(client):
    for nodes, edges, expected in [CONNECTED + (True,), DISCONNECTED + (False,)]:
        meta = final_meta(client, nodes, edges)
        assert meta['vars']['spans_everything'] is expected


def test_the_result_panel_names_the_forest_too():
    """The panel under the canvas is a second place the result is named."""
    with open(os.path.join(ROOT, 'templates', 'graph_base.html'),
              encoding='utf-8') as fh:
        page = fh.read()

    kruskal = page.split("algorithm === 'kruskal'", 1)[1].split("algorithm === 'prim'", 1)[0]

    assert 'Minimum spanning forest' in kruskal
    assert 'Minimum Spanning Tree' not in kruskal, (
        'the Kruskal result panel still hardcodes a tree')
    assert 'resultEdges.length === nodes.length - 1' in kruskal, (
        'the panel is not deciding from the edge count')
    assert "verdict.textContent = 'in MST'" not in page, (
        'the edge queue verdict still says MST')


# ---------------------------------------------------------------------------
# Merge sort counts writes
# ---------------------------------------------------------------------------

def merge_stats(values):
    stats = {'swaps': 0, 'comparisons': 0}
    merge_sort(list(values), lambda a, c=None, m=None: None, lambda: None, stats)
    return stats


def test_merge_sort_writes_even_when_nothing_moves():
    """The reason the counter needed renaming, stated as a test."""
    sorted_input = merge_stats([1, 3, 5, 8, 9])
    shuffled = merge_stats([5, 3, 8, 1, 9])

    assert sorted_input['swaps'] == 12
    assert shuffled['swaps'] == 12, (
        'the copy back writes every value either way, which is the point')
    assert sorted_input['comparisons'] < shuffled['comparisons']


def test_the_sorts_that_do_not_swap_say_so():
    """Merge, counting and radix sort write, insertion sort shifts. The other four swap."""
    script = (
        "global.window = {};"
        "const fs = require('fs'), path = require('path');"
        "const dir = %s;"
        "fs.readdirSync(dir).filter(f => f.endsWith('.js')).sort()"
        "  .forEach(f => eval(fs.readFileSync(path.join(dir, f), 'utf8')));"
        "process.stdout.write(JSON.stringify(global.window.LESSONS));"
    ) % json.dumps(os.path.join(ROOT, 'static', 'js', 'lessons'))
    try:
        out = subprocess.run(['node', '-e', script], capture_output=True, check=True)
    except Exception:
        pytest.skip('node is needed to read the lesson files')

    lessons = json.loads(out.stdout.decode('utf-8'))
    renamed = {k: v['countLabel'] for k, v in lessons.items() if 'countLabel' in v}

    # Counting and radix sort (Phase 19) write values back from their count
    # list or buckets, so they count writes too.
    assert renamed == {'merge_sort': 'writes',
                       'insertion_sort': 'shifts',
                       'counting_sort': 'writes',
                       'radix_sort': 'writes'}, renamed
    for key in renamed:
        assert lessons[key]['complexity']['countsNote'], (
            '%s renames its counter without explaining it' % key)


def test_the_banner_and_the_panel_both_follow_the_lesson():
    with open(os.path.join(ROOT, 'templates', 'sorting.html'), encoding='utf-8') as fh:
        page = fh.read()
    with open(os.path.join(ROOT, 'static', 'js', 'teacher.js'), encoding='utf-8') as fh:
        teacher = fh.read()

    assert 'lesson.countLabel' in page, 'the run banner still hardcodes swaps'
    assert not re.search(r"' swap' \+", page), 'the banner keeps its own noun'
    assert 'countLabel(this.lesson)' in teacher, (
        'the This Run row still hardcodes swaps')
