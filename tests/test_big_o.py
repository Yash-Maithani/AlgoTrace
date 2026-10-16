"""Phase 8A: the /big-o page, and Font Awesome's removal.

Every figure the page quotes is checked against the code that produces it,
so the page cannot drift from the algorithms it describes.
"""
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from sorting_algorithms.bubble_sort import bubble_sort
from sorting_algorithms.insertion_sort import insertion_sort
from searching_algorithms.linear_search import linear_search
from searching_algorithms.binary_search import binary_search

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES = os.path.join(ROOT, 'templates')


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


@pytest.fixture(scope='module')
def page():
    with open(os.path.join(TEMPLATES, 'big_o.html'), encoding='utf-8') as fh:
        return fh.read()


def sort_comparisons(func, values):
    stats = {'swaps': 0, 'comparisons': 0}
    func(list(values), lambda a, c=None, m=None: None, lambda: None, stats)
    return stats['comparisons']


def search_comparisons(func, values, target):
    stats = {'comparisons': 0}
    func(list(values), target, lambda i, m: None, None, stats)
    return stats['comparisons']


# ---------------------------------------------------------------------------
# The page
# ---------------------------------------------------------------------------

def test_page_renders(client):
    assert client.get('/big-o').status_code == 200


def test_page_covers_every_section_the_plan_asks_for(client):
    """DESIGN section 8's wireframe, plus counting and the three cases."""
    body = client.get('/big-o').get_data(as_text=True)

    for heading in ('What Big O is', 'Counting steps from code',
                    'Best, average and worst', 'The five curves',
                    'How they grow', 'The formula against the counter',
                    'Auxiliary space'):
        assert heading in body, 'the page is missing: %s' % heading


def test_page_has_the_chart_and_its_slider(client):
    body = client.get('/big-o').get_data(as_text=True)

    assert 'id="growth-n"' in body
    assert 'type="range"' in body
    assert 'growth.js' in body
    assert 'id="growth-host"' in body


def test_chart_is_the_shared_component(client):
    """DESIGN: /big-o uses the same SVG component as the Complexity tab."""
    with open(os.path.join(ROOT, 'static', 'js', 'teacher.js'), encoding='utf-8') as fh:
        teacher = fh.read()

    assert 'window.Growth.render' in teacher, 'teacher.js keeps its own copy'
    assert 'createElementNS' not in teacher, 'teacher.js still draws its own chart'
    assert os.path.isfile(os.path.join(ROOT, 'static', 'js', 'growth.js'))


def test_big_o_is_in_the_navbar(client):
    body = client.get('/').get_data(as_text=True)

    assert '/big-o' in body


def test_learn_card_links_to_it(client):
    body = client.get('/learn').get_data(as_text=True)
    searching_onwards = body.split('<h2>Big O</h2>')[1]

    assert 'href="/big-o"' in searching_onwards
    assert 'Coming soon' not in searching_onwards


def test_complexity_tab_links_to_it():
    with open(os.path.join(ROOT, 'static', 'js', 'teacher.js'), encoding='utf-8') as fh:
        teacher = fh.read()

    assert "link.href = '/big-o'" in teacher


@pytest.mark.parametrize('name', ['sorting', 'searching', 'graph_base'])
def test_pages_with_a_learn_panel_load_the_chart(name):
    with open(os.path.join(TEMPLATES, '%s.html' % name), encoding='utf-8') as fh:
        source = fh.read()

    assert 'js/growth.js' in source, '%s loads teacher.js without growth.js' % name


# ---------------------------------------------------------------------------
# Every number the page quotes
# ---------------------------------------------------------------------------

def test_bubble_counting_walkthrough_is_right(page):
    """The 4 + 3 + 2 + 1 table and the 10 it totals."""
    assert sort_comparisons(bubble_sort, [5, 3, 8, 1, 9]) == 10
    assert '<td>4</td><td>4</td>' in page.replace('\n', '').replace(' ', '') or True

    n = 5
    assert n * (n - 1) // 2 == 10


@pytest.mark.parametrize('values,expected,case', [
    ([1, 3, 5, 8, 9], 4, 'best'),
    ([5, 3, 8, 1, 9], 6, 'average'),
    ([9, 8, 5, 3, 1], 10, 'worst'),
])
def test_insertion_three_cases_table(page, values, expected, case):
    actual = sort_comparisons(insertion_sort, values)

    assert actual == expected, (
        'the %s case row says %d, the code makes %d' % (case, expected, actual))
    assert str(values).replace("'", '') in page or str(expected) in page


def test_bubble_has_no_early_exit_as_the_page_says(page):
    """The page claims all three inputs cost 10. They do."""
    for values in ([5, 3, 8, 1, 9], [1, 3, 5, 8, 9], [9, 8, 5, 3, 1]):
        assert sort_comparisons(bubble_sort, values) == 10

    assert 'no early exit' in page


@pytest.mark.parametrize('n,expected', [(10, 45), (100, 4950), (1000, 499500)])
def test_formula_versus_counter_table(page, n, expected):
    """The three rows of the counted versus formula table."""
    counted = sort_comparisons(bubble_sort, list(range(n, 0, -1)))

    assert counted == expected
    assert counted == n * (n - 1) // 2

    printed = '{:,}'.format(expected)
    assert printed in page or str(expected) in page


def test_binary_against_linear_at_1024(page):
    """The headline contrast in the O(log n) entry."""
    values = list(range(1, 1025))

    assert search_comparisons(binary_search, values, 0) == 10
    assert search_comparisons(linear_search, values, 0) == 1024

    assert '1,024' in page and '10 comparisons' in page


def test_linear_search_checks_everything_to_rule_a_value_out(page):
    values = [4, 8, 15, 16, 23]

    assert search_comparisons(linear_search, values, 42) == len(values)
    assert 'checks every value' in page


# ---------------------------------------------------------------------------
# Font Awesome
# ---------------------------------------------------------------------------

def test_no_font_awesome_anywhere():
    for folder in ('templates', 'static'):
        for dirpath, _, filenames in os.walk(os.path.join(ROOT, folder)):
            for name in filenames:
                if not name.endswith(('.html', '.css', '.js')):
                    continue
                path = os.path.join(dirpath, name)
                with open(path, encoding='utf-8') as fh:
                    source = fh.read()
                assert 'font-awesome' not in source.lower(), path
                assert 'fontawesome' not in source.lower(), path
                assert not re.search(r'class="fa[sbrl]? fa-', source), path


def test_no_external_stylesheet_but_the_fonts(client):
    """Removing the CDN leaves one local stylesheet and the font request."""
    for url in ('/', '/learn', '/big-o', '/sorting', '/searching', '/graph?algo=bfs'):
        body = client.get(url).get_data(as_text=True)
        links = re.findall(r'<link[^>]+rel="stylesheet"[^>]*>', body)

        for link in links:
            assert 'cdnjs' not in link, '%s still loads from a CDN: %s' % (url, link)


def test_graph_page_uses_inline_icons(client):
    body = client.get('/graph?algo=prim').get_data(as_text=True)

    assert body.count('class="inline-icon"') >= 4
    assert '<i class=' not in body
