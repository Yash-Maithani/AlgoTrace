"""Phase 14 part B: Omega and Theta in the interface.

The fast checks are plain file and route checks plus the explorer's model run
under node. tests/browser/test_browser_code_and_complexity.py drives a real browser.
"""
import json
import os
import re
import shutil
import subprocess

import pytest

from paths import ROOT, JS
from wsgi import app

NODE = shutil.which('node')
needs_node = pytest.mark.skipif(NODE is None, reason='node is not installed')


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return f.read()


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Navbar
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('page', ['/', '/learn', '/sorting', '/searching', '/big-o', '/graph?algo=bfs'])
def test_the_navbar_says_complexity_and_still_goes_to_big_o(client, page):
    html = client.get(page).get_data(as_text=True)
    nav = html.split('class="nav-links"', 1)[1].split('</div>', 1)[0]

    assert re.search(r'<a href="/big-o"[^>]*>Complexity</a>', nav), page
    assert '>Big O<' not in nav


def test_the_url_stays_and_the_learn_card_follows_the_new_name(client):
    assert client.get('/big-o').status_code == 200
    learn = client.get('/learn').get_data(as_text=True)

    assert '<h2>Complexity</h2>' in learn and '<h2>Big O</h2>' not in learn
    assert 'href="/big-o"' in learn


def test_no_page_still_calls_the_navbar_entry_big_o():
    assert "'Big O')" not in read('algotrace', 'templates', 'layout.html')
    assert 'Graphs Complexity' in read('docs', 'DESIGN.md')


# ---------------------------------------------------------------------------
# /big-o
# ---------------------------------------------------------------------------

def test_big_o_has_a_three_notations_section_in_the_contents(client):
    html = client.get('/big-o').get_data(as_text=True)

    assert 'id="notations"' in html and 'href="#notations"' in html
    for needle in ('the upper bound', 'the lower bound', 'the tight bound'):
        assert needle in html


def test_the_section_works_the_three_examples_from_the_lessons(client):
    html = client.get('/big-o').get_data(as_text=True)
    table = html.split('notation-table', 1)[1].split('</table>', 1)[0]

    assert 'Bubble sort' in table and 'Insertion sort' in table and 'Linear search' in table
    assert table.count('Theta of n squared') >= 4
    assert 'Omega of n<' in table or 'Omega of n</span>' in table
    assert table.count('<td>none</td>') == 2          # insertion sort and linear search


def test_the_three_examples_agree_with_the_lesson_data():
    """The page's table is written by hand, so hold it to the lessons."""
    out = subprocess.run([NODE, os.path.join(JS, 'dump_lessons.js')], capture_output=True, text=True, check=True)
    lessons = json.loads(out.stdout)

    def overall(name):
        resolved = lessons[name]['resolved']
        return resolved[lessons[name]['default'] or '']['complexity']

    bubble, insertion, linear = overall('bubble_sort'), overall('insertion_sort'), overall('linear_search')
    assert bubble['overall'] == {'O': 'n squared', 'Omega': 'n squared', 'Theta': 'n squared'}
    assert insertion['overall'] == {'O': 'n squared', 'Omega': 'n', 'Theta': None}
    assert linear['overall'] == {'O': 'n', 'Omega': '1', 'Theta': None}
    assert insertion['time']['best']['theta'] == 'n' and insertion['time']['worst']['theta'] == 'n squared'
    assert linear['time']['best']['theta'] == '1' and linear['time']['worst']['theta'] == 'n'


def test_the_misconception_is_called_out_and_explained(client):
    html = client.get('/big-o').get_data(as_text=True)
    box = html.split('class="callout misconception"', 1)[1].split('</div>', 1)[0]

    assert 'O is the worst case, Omega is the best case, Theta is the average' in box
    assert 'wrong' in box and 'Every case has an upper, a lower and a tight bound' in box


def test_the_explorer_has_labelled_sliders_and_an_announced_verdict(client):
    html = client.get('/big-o').get_data(as_text=True)

    for control in ('nt-c1', 'nt-c2', 'nt-n0'):
        assert 'type="range" id="%s"' % control in html
        assert 'for="%s"' % control in html
    assert 'id="nt-verdict" role="status" aria-live="polite"' in html
    assert 'js/notations.js' in html


@needs_node
def test_the_explorer_model_knows_when_a_bound_holds():
    script = (
        "const N=require(process.argv[1]);const f=N.FUNCTIONS,g=N.SHAPES;"
        "const out={"
        # bubble sort against n^2: 0.25 n^2 <= n(n-1)/2 <= 0.5 n^2 from n0 = 2
        "tight:N.check(f.bubble,g.n2.value,0.25,0.5,2),"
        # the floor fails at n0 = 1 only if c1 is too big; here f(1) = 0 < 0.25
        "early:N.check(f.bubble,g.n2.value,0.25,0.5,1),"
        # n^2 outgrows any multiple of n: no ceiling
        "noCeiling:N.check(f.bubble,g.n.value,0.05,10,1),"
        # n - 1 against n^2: a ceiling but never a floor
        "noFloor:N.check(f.insertion,g.n2.value,0.05,1,1),"
        "extras:N.check(f.example,g.n2.value,3,4,24)};"
        "process.stdout.write(JSON.stringify(out));")
    result = json.loads(subprocess.run([NODE, '-e', script, os.path.join(ROOT, 'algotrace', 'static', 'js', 'notations.js')],
                                       capture_output=True, text=True, check=True).stdout)

    assert result['tight']['tight'] is True
    assert result['early']['lower']['holds'] is False and result['early']['lower']['at'] == 1
    assert result['noCeiling']['upper']['holds'] is False
    assert result['noFloor']['upper']['holds'] and not result['noFloor']['lower']['holds']
    # 3n^2 + 20n + 50 <= 4 n^2 once n is large enough (n = 24 is the first), and always >= 3 n^2.
    assert result['extras']['tight'] is True


@needs_node
def test_the_explorer_flags_the_first_size_where_a_bound_breaks():
    script = ("const N=require(process.argv[1]);"
              "process.stdout.write(JSON.stringify(N.check(N.FUNCTIONS.example,N.SHAPES.n2.value,3,4,10)));")
    result = json.loads(subprocess.run([NODE, '-e', script, os.path.join(ROOT, 'algotrace', 'static', 'js', 'notations.js')],
                                       capture_output=True, text=True, check=True).stdout)

    assert result['upper']['holds'] is False
    assert result['upper']['at'] == 10          # 3*100+200+50 = 550 > 400


# ---------------------------------------------------------------------------
# Complexity tab
# ---------------------------------------------------------------------------

def test_the_complexity_tab_builds_a_table_an_overall_line_and_the_note():
    js = read('algotrace', 'static', 'js', 'teacher.js')

    for needle in ["el('table', 'theta-table')", "scope = 'col'", "scope = 'row'",
                   'overallLine(c)', 'thetaTable(c)', 'c.misconception', 'data-no-theta',
                   "'Big O'", "'Omega'", "'Theta'", "'sr-only'", "'aria-hidden', 'true'"]:
        assert needle in js, needle
    # The old description list of values is gone: the table replaces it.
    assert "el('dl', 'complexity-table')" not in js


def test_symbols_are_real_letters_and_spoken_in_words():
    js = read('algotrace', 'static', 'js', 'teacher.js')

    assert "SYMBOL = { O: 'O', Omega: 'Ω', Theta: 'Θ' }" in js
    assert "SPOKEN[kind] + ' of '" in js
