"""Phase 9: the Searching tile, empty live values, presets, shortcuts."""
import os
import re
import shutil
import subprocess

import pytest

from paths import ROOT, JS
from wsgi import app

NODE = shutil.which('node')


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return f.read()


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def test_home_searching_tile_is_a_live_link(client):
    html = client.get('/').get_data(as_text=True)
    tile = re.search(r'<a[^>]*data-track="searching"[^>]*>', html)

    assert tile, 'the Searching tile is not a link'
    assert 'href="/searching"' in tile.group(0)
    assert 'Coming soon' not in html
    assert 'is-soon' not in tile.group(0)


def test_live_values_has_an_empty_state():
    js = read('algotrace', 'static', 'js', 'teacher.js')

    assert 'Run the algorithm to see values change' in js
    assert 'syncCodeVars' in js


@pytest.mark.parametrize('page', ['/sorting', '/searching'])
def test_pages_load_the_preset_script_and_a_host(client, page):
    html = client.get(page).get_data(as_text=True)

    assert 'js/presets.js' in html
    assert 'id="preset-host"' in html
    assert html.index('presets.js') < html.index('js/workspace.js')


@pytest.mark.skipif(NODE is None, reason='node is not installed, so the preset generators cannot be run')
def test_preset_generators():
    result = subprocess.run([NODE, os.path.join(JS, 'presets_check.js')],
                            capture_output=True, text=True)

    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.skipif(NODE is None, reason='node is not installed, so lesson notes cannot be checked')
def test_every_sorting_and_searching_lesson_has_preset_notes():
    """validate_lessons.js fails on a missing or empty note."""
    result = subprocess.run([NODE, os.path.join(JS, 'validate_lessons.js')],
                            capture_output=True, text=True)

    assert result.returncode == 0, result.stdout + result.stderr
    for name in ['bubble_sort', 'selection_sort', 'insertion_sort', 'merge_sort',
                 'quick_sort', 'heap_sort', 'linear_search', 'binary_search']:
        assert 'presetNotes' in read('algotrace', 'static', 'js', 'lessons', name + '.js')


def test_binary_search_offers_only_sorted_presets():
    js = read('algotrace', 'static', 'js', 'lessons', 'binary_search.js')

    assert "presets: ['sorted', 'equal']" in js


def test_shortcuts_are_wired_once_in_the_shared_shell():
    js = read('algotrace', 'static', 'js', 'workspace.js')

    for needle in ['aria-keyshortcuts', 'Keyboard shortcuts', "'ArrowLeft'", "'ArrowRight'",
                   "'INPUT'", "'TEXTAREA'", "'SELECT'"]:
        assert needle in js, needle


@pytest.mark.parametrize('page', ['/sorting', '/searching', '/graph?algo=bfs'])
def test_every_workspace_loads_the_shared_shell(client, page):
    html = client.get(page).get_data(as_text=True)

    assert 'js/workspace.js' in html
    assert 'class="control-bar"' in html
    assert 'Workspace.start' in html
