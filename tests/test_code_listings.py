"""Phase 12: the listings extracted from reference_code/.

Fast checks, not marked slow: the generated static/js/lessons/code/*.js
files are current, the validator holds them to the lesson's line ids, and
the extractor refuses malformed markers. Compiling and running the programs
is tests/test_reference_code.py.
"""
import os
import shutil
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import extract_code  # noqa: E402

NODE = shutil.which('node')


def test_generated_code_files_are_up_to_date():
    """Edit a reference program without rerunning the extractor and this
    fails, naming the file to regenerate."""
    assert extract_code.stale() == [], (
        'out of date: %s. Run python tools/extract_code.py'
        % ', '.join(extract_code.stale()))


def test_check_mode_reports_ok():
    result = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'extract_code.py'),
                             '--check'], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize('algo', sorted(extract_code.ALGORITHMS))
def test_every_language_has_every_file(algo):
    for language in extract_code.LANGUAGES:
        assert os.path.isfile(extract_code.source_path(algo, language))
    assert os.path.isfile(extract_code.target(algo))


def test_hidden_wrappers_do_not_indent_the_listing():
    """Bubble sort's early exit runs inside `if (early_exit) {`, which is
    hidden, so the `on` listing shows the break one level in from the outer
    loop, as a program with only that variant would."""
    _, listings = extract_code.parse(extract_code.source_path('bubble_sort', 'c'))
    on = {line['text']: line['indent'] for line in listings['on']}
    off = [line['text'] for line in listings['off']]

    # Function body 1, loop body 2: the hidden `if (early_exit) {` adds none.
    assert on['for (int i = 0; i < n; i++) {'] == 1
    assert on['if (!swapped) break;'] == 2
    assert 'if (!swapped) break;' not in off
    assert not any('comparisons' in text or 'step(' in text for text in off)


def test_merge_listings_show_their_own_comparison():
    for language in extract_code.LANGUAGES:
        _, listings = extract_code.parse(extract_code.source_path('merge_sort', language))
        lt = ' '.join(line['text'] for line in listings['lt'])
        le = ' '.join(line['text'] for line in listings['le'])
        assert 'left[i] < right[j]' in lt and 'left[i] <= right[j]' not in lt
        assert 'left[i] <= right[j]' in le and 'left[i] < right[j]' not in le


@pytest.mark.parametrize('source,message', [
    ('// lesson:start\nint x;\n', 'never closed'),
    ('int x;\n', 'no lesson:start'),
    ('// lesson:variants a b\n// lesson:start\nint x; // @only:c\n// lesson:end\n',
     'not declared'),
    ('// lesson:start\nint x; // @hide @loop\n// lesson:end\n', 'hidden line'),
    ('// lesson:start\n  int x;\n// lesson:end\n', 'multiples'),
    ('// lesson:start\nint x; // @Bad_Id\n// lesson:end\n', 'not a line id'),
    ('// lesson:start\nif (a) { // @hide\n    int x;\n// lesson:end\n', 'still open'),
    ('// lesson:start\nif (a) { // @hide\nint x;\n// lesson:end\n', 'left of its lesson block'),
    ('// lesson:start\n} // @hide\n// lesson:end\n', 'closes more'),
])
def test_extractor_refuses_malformed_markers(tmp_path, source, message):
    path = tmp_path / 'broken.c'
    path.write_text(source, encoding='utf-8')
    with pytest.raises(extract_code.SourceError) as error:
        extract_code.parse(str(path))
    assert message in str(error.value)


@pytest.mark.skipif(NODE is None, reason='node is not installed')
@pytest.mark.parametrize('mutation,replacement', [
    ('{ id: "swap", text: "swap(&arr[j], &arr[j + 1]);"',
     '{ id: "swop", text: "swap(&arr[j], &arr[j + 1]);"'),
    ('            "on": [', '            "maybe": ['),
    ('    java: {', '    jav: {'),
])
def test_validator_rejects_a_listing_that_drifts(tmp_path, mutation, replacement):
    source = os.path.join(ROOT, 'static', 'js', 'lessons')
    shutil.copytree(source, tmp_path / 'lessons', ignore=shutil.ignore_patterns('*.md'))
    target = tmp_path / 'lessons' / 'code' / 'bubble_sort.js'
    text = target.read_text(encoding='utf-8')
    assert mutation in text, 'the mutation no longer matches code/bubble_sort.js'
    target.write_text(text.replace(mutation, replacement, 1), encoding='utf-8')

    result = subprocess.run([NODE, os.path.join(HERE, 'validate_lessons.js')],
                            capture_output=True, text=True,
                            env=dict(os.environ, LESSON_DIR=str(tmp_path / 'lessons')))
    assert result.returncode != 0, result.stdout


# ---------------------------------------------------------------------------
# Phase 13: helpers behind "Show helpers"
# ---------------------------------------------------------------------------

def test_prim_listing_shows_the_algorithm_and_hides_the_heap():
    """The binary heap Prim needs in C is real code in the file, but it is
    a helper: the listing calls it, the helpers listing defines it."""
    path = extract_code.source_path('prim', 'c')
    _, listings = extract_code.parse(path)
    helpers = extract_code.parse_helpers(path)
    main = ' '.join(line['text'] for line in listings['default'])
    extra = ' '.join(line['text'] for line in helpers)

    assert 'heap_push(' in main and 'heap_pop()' in main
    assert 'static void heap_push' in extra and 'static Edge heap_pop' in extra
    assert 'static void heap_push' not in main
    assert all(line['id'] is None for line in helpers)


@pytest.mark.parametrize('algo', ['bfs', 'dfs', 'dijkstra', 'prim', 'kruskal',
                                  'bellman_ford', 'floyd_warshall'])
def test_graph_helpers_are_recorded_for_every_language(algo):
    for language in extract_code.LANGUAGES:
        helpers = extract_code.parse_helpers(extract_code.source_path(algo, language))
        text = ' '.join(line['text'] for line in helpers)
        # Every graph program looks nodes up by name through a helper.
        assert 'node_index' in text or 'nodeIndex' in text, (algo, language)


def test_a_helper_line_cannot_carry_a_line_id(tmp_path):
    path = tmp_path / 'broken.c'
    path.write_text('// lesson:helpers\nint x; // @loop\n// lesson:end\n'
                    '// lesson:start\nint y;\n// lesson:end\n', encoding='utf-8')
    with pytest.raises(extract_code.SourceError) as error:
        extract_code.parse(str(path))
    assert 'helper line' in str(error.value)


def test_multi_line_comments_stay_out_of_listings():
    for algo in extract_code.ALGORITHMS:
        for language in extract_code.LANGUAGES:
            path = extract_code.source_path(algo, language)
            _, listings = extract_code.parse(path)
            lines = [l for listing in listings.values() for l in listing]
            lines += extract_code.parse_helpers(path)
            assert not any(l['text'].endswith('*/') and '/*' not in l['text'] for l in lines), (algo, language)


@pytest.mark.skipif(NODE is None, reason='node is not installed')
def test_validator_rejects_a_helper_with_an_id(tmp_path):
    source = os.path.join(ROOT, 'static', 'js', 'lessons')
    shutil.copytree(source, tmp_path / 'lessons', ignore=shutil.ignore_patterns('*.md'))
    target = tmp_path / 'lessons' / 'code' / 'prim.js'
    text = target.read_text(encoding='utf-8')
    mutation = '{ id: null, text: "static int heap_size;"'
    assert mutation in text
    target.write_text(text.replace(mutation, '{ id: "start", text: "static int heap_size;"', 1),
                      encoding='utf-8')
    result = subprocess.run([NODE, os.path.join(HERE, 'validate_lessons.js')],
                            capture_output=True, text=True,
                            env=dict(os.environ, LESSON_DIR=str(tmp_path / 'lessons')))
    assert result.returncode != 0, result.stdout
