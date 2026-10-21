"""Phase 14 part B, step 0: nothing the programs teach can go missing from a
listing, and a statement that spans lines lights whole."""
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

from paths import ROOT

sys.path.insert(0, os.path.join(ROOT, 'tools'))

import extract_code  # noqa: E402

NODE = shutil.which('node')
needs_node = pytest.mark.skipif(NODE is None, reason='node is not installed')


def expected_lines(path):
    """What a reader of the source would call the teaching lines, found
    without the extractor's own code: ({variant: [text]}, [helper text]).

    A line is taught when it sits between lesson:start and lesson:end (or
    lesson:helpers and lesson:end), is not blank, is not a comment, and does
    not carry the @hide tag. A line tagged @only:v is taught for those
    variants only."""
    with open(path, encoding='utf-8') as f:
        lines = f.read().splitlines()
    variants = ['default']
    for line in lines:
        m = re.match(r'\s*// lesson:variants\s+(.*)$', line)
        if m:
            variants = m.group(1).split()
    listings = {v: [] for v in variants}
    helpers = []
    block = None
    in_comment = False
    for line in lines:
        s = line.strip()
        if s == '// lesson:start':
            block = 'main'
            continue
        if s == '// lesson:helpers':
            block = 'helpers'
            continue
        if s == '// lesson:end':
            block = None
            continue
        if block is None:
            continue
        # trailing tags are one or more @words after a //
        m = re.search(r'\s*//\s*((?:@\S+\s*)+)$', s)
        tag_words = m.group(1).split() if m else []
        text = s[:m.start()].rstrip() if m else s
        if in_comment:
            in_comment = '*/' not in text
            continue
        if text.startswith('/*'):
            in_comment = '*/' not in text
            continue
        if not text or text.startswith('//'):
            continue
        if '@hide' in tag_words:
            continue
        only = None
        for word in tag_words:
            if word.startswith('@only:'):
                only = word[len('@only:'):].split(',')
        if block == 'helpers':
            helpers.append(text)
        else:
            for v in (only or variants):
                listings[v].append(text)
    return listings, helpers


_DUMP = None


def generated():
    """The generated listings as the page reads them: {algo: {lang: ...}}."""
    global _DUMP
    if _DUMP is None:
        script = (
            "const fs=require('fs'),path=require('path');global.window={};"
            "const d=process.argv[1];"
            "fs.readdirSync(d).forEach(n=>eval(fs.readFileSync(path.join(d,n),'utf8')));"
            "process.stdout.write(JSON.stringify(window.LESSON_CODE));")
        out = subprocess.run([NODE, '-e', script, os.path.join(ROOT, 'algotrace', 'static', 'js', 'lessons', 'code')],
                             capture_output=True, text=True, check=True)
        _DUMP = json.loads(out.stdout)
    return _DUMP


@needs_node
@pytest.mark.parametrize('language', extract_code.LANGUAGES)
@pytest.mark.parametrize('algo', sorted(extract_code.ALGORITHMS))
def test_every_visible_source_line_is_in_the_generated_listing_exactly(algo, language):
    """The extractor once read any line that began with `*` as a comment and
    dropped it, so a program's swap lost half its body and nothing failed.
    This compares the source, read separately, with the file the page loads."""
    listings, helpers = expected_lines(extract_code.source_path(algo, language))
    entry = generated()[algo][language]

    assert set(entry['listings']) == set(listings), (algo, language)
    for variant, texts in listings.items():
        actual = [line['text'] for line in entry['listings'][variant]]
        assert actual == texts, (algo, language, variant)
    assert [line['text'] for line in entry['helpers']] == helpers, (algo, language)


def test_the_independent_reader_catches_a_dropped_line(tmp_path):
    """Guard the guard: a source whose line starts with `*` is expected."""
    source = tmp_path / 'x.c'
    source.write_text('// lesson:helpers\nstatic void swap(int *a, int *b)\n{\n'
                      '    int t = *a;\n    *a = *b;\n    *b = t;\n}\n// lesson:end\n'
                      '// lesson:start\nvoid f(void) {\n    g();  // @hide\n}\n// lesson:end\n')
    listings, helpers = expected_lines(str(source))

    assert '*a = *b;' in helpers and '*b = t;' in helpers
    assert listings['default'] == ['void f(void) {', '}']


# ---------------------------------------------------------------------------
# A statement over several lines
# ---------------------------------------------------------------------------

@needs_node
@pytest.mark.parametrize('algo', ['bubble_sort', 'selection_sort'])
def test_javas_inline_swap_carries_its_id_on_all_three_lines(algo):
    for variant, lines in generated()[algo]['java']['listings'].items():
        swap = [(i, l['text']) for i, l in enumerate(lines) if l['id'] == 'swap']

        assert len(swap) == 3, (algo, variant, swap)
        assert [i for i, _ in swap] == list(range(swap[0][0], swap[0][0] + 3)), 'not contiguous'
        assert swap[0][1].startswith('int t = ')


@needs_node
def test_a_swap_that_is_one_call_stays_one_line_elsewhere():
    for language in ('c', 'cpp'):
        for algo in ('bubble_sort', 'selection_sort'):
            lines = generated()[algo][language]['listings']
            for variant, listing in lines.items():
                assert sum(1 for l in listing if l['id'] == 'swap') == 1, (algo, language, variant)


def test_the_extractor_accepts_one_id_on_consecutive_lines(tmp_path):
    source = tmp_path / 'x.c'
    source.write_text('// lesson:start\nvoid f(void) {\n    int t = a;   // @swap\n'
                      '    a = b;   // @swap\n    b = t;   // @swap\n}\n// lesson:end\n')
    _, listing = extract_code.parse(str(source))

    assert [l['id'] for l in listing['default']] == [None, 'swap', 'swap', 'swap', None]
