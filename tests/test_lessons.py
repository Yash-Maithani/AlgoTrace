"""The lesson files are JavaScript, so node checks them against the contract.

Everything structural lives in tests/validate_lessons.js, which can also be
run on its own. These tests cover the parts Python can check without node, so
a machine with no node installed still catches a missing or renamed file.
"""
import os
import re
import shutil
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LESSON_DIR = os.path.join(ROOT, 'static', 'js', 'lessons')
VALIDATOR = os.path.join(ROOT, 'tests', 'validate_lessons.js')

SORTING = ['bubble_sort', 'selection_sort', 'insertion_sort',
           'merge_sort', 'quick_sort', 'heap_sort']
SEARCHING = ['linear_search', 'binary_search']
EXPECTED = SORTING + SEARCHING


@pytest.mark.parametrize('name', EXPECTED)
def test_lesson_file_exists(name):
    assert os.path.isfile(os.path.join(LESSON_DIR, '%s.js' % name))


def test_readme_exists():
    """The contract itself. Later phases are told to read it first."""
    readme = os.path.join(LESSON_DIR, 'README.md')
    assert os.path.isfile(readme)

    with open(readme, encoding='utf-8') as fh:
        text = fh.read()

    for field in ('action', 'indices', 'values', 'line', 'vars', 'explain'):
        assert '`%s`' % field in text, 'README does not document %s' % field


@pytest.mark.parametrize('name', EXPECTED)
def test_lesson_registers_under_its_own_name(name):
    with open(os.path.join(LESSON_DIR, '%s.js' % name), encoding='utf-8') as fh:
        source = fh.read()

    assert 'window.LESSONS = window.LESSONS || {};' in source
    assert 'window.LESSONS.%s = {' % name in source
    assert re.search(r"id:\s*'%s'" % name, source)


@pytest.mark.parametrize('name', SORTING + SEARCHING)
def test_no_lesson_is_pending(name):
    """Phase 5 built the searching code, so nothing is deferred any more."""
    with open(os.path.join(LESSON_DIR, '%s.js' % name), encoding='utf-8') as fh:
        source = fh.read()

    assert 'codePending' not in source


@pytest.mark.parametrize('name', SEARCHING)
def test_searching_lesson_has_an_implementation_behind_it(name):
    """The listing is only honest if the module it describes exists."""
    module = os.path.join(ROOT, 'searching_algorithms', '%s.py' % name)

    assert os.path.isfile(module), '%s.js describes code that is not there' % name


@pytest.mark.skipif(shutil.which('node') is None,
                    reason='node is not installed, so the JavaScript contract '
                           'check cannot run here')
def test_lessons_match_the_contract():
    result = subprocess.run(['node', VALIDATOR], capture_output=True, text=True)

    assert result.returncode == 0, result.stdout + result.stderr
