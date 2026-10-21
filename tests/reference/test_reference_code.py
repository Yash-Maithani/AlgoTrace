"""Phase 12: the C, C++ and Java reference programs behave exactly like the
Python, step by step.

Every program in reference_code/ is compiled (C11, C++17, Java 17) and fed
one batch of cases: random, sorted, reversed, all equal, with duplicates,
and the tiny lists, for every variant, and for the random pivot every seed
below. Its output must equal, line for line, what the Python functions in
algotrace/algorithms/sorting/ and algotrace/algorithms/searching/ produce for the same input:
every step's action, line id, indices and values (and depth and range for
merge and quick sort), then the answer and the counts.

A missing compiler skips that language's tests with the name of what to
install. These are marked slow: `pytest -m "not slow"` leaves them out.
"""
import os
import random
import shutil
import subprocess
import sys

import pytest

from paths import ROOT
from algotrace.algorithms.searching.binary_search import binary_search
from algotrace.algorithms.searching.jump_search import jump_search
from algotrace.algorithms.searching.linear_search import linear_search
from algotrace.algorithms.sorting.bubble_sort import bubble_sort
from algotrace.algorithms.sorting.counting_sort import counting_sort, KEY_MAX
from algotrace.algorithms.sorting.heap_sort import heap_sort
from algotrace.algorithms.sorting.insertion_sort import insertion_sort
from algotrace.algorithms.sorting.merge_sort import merge_sort
from algotrace.algorithms.sorting.quick_sort import quick_sort
from algotrace.algorithms.sorting.radix_sort import radix_sort
from algotrace.algorithms.sorting.selection_sort import selection_sort

pytestmark = pytest.mark.slow

REF = os.path.join(ROOT, 'reference_code')
EXE = '.exe' if os.name == 'nt' else ''

# Lesson id -> (Python function, Java class, {variant: keyword arguments})
SORTS = {
    'bubble_sort': (bubble_sort, 'BubbleSort', {'off': {'early_exit': False},
                                                'on': {'early_exit': True}}),
    'selection_sort': (selection_sort, 'SelectionSort', {'-': {}}),
    'insertion_sort': (insertion_sort, 'InsertionSort', {'-': {}}),
    'merge_sort': (merge_sort, 'MergeSort', {'lt': {'stable': False},
                                             'le': {'stable': True}}),
    'quick_sort': (quick_sort, 'QuickSort', {'last': {'pivot_rule': 'last'},
                                             'middle': {'pivot_rule': 'middle'},
                                             'random': {'pivot_rule': 'random'}}),
    'heap_sort': (heap_sort, 'HeapSort', {'-': {}}),
    'counting_sort': (counting_sort, 'CountingSort', {'-': {}}),
    'radix_sort': (radix_sort, 'RadixSort', {'-': {}}),
}
# The sorts that take whole numbers from 0 to KEY_MAX only.
KEYED = {'counting_sort', 'radix_sort'}
SEARCHES = {
    'linear_search': (linear_search, 'LinearSearch'),
    'binary_search': (binary_search, 'BinarySearch'),
    'jump_search': (jump_search, 'JumpSearch'),
}
ALGORITHMS = sorted(SORTS) + sorted(SEARCHES)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from extract_code import ALGORITHMS as JAVA_CLASS  # noqa: E402  lesson id -> Java class
SEEDS = [0, 1, 42, 4821, 99999, 2 ** 31 - 1]

TOOLS = {
    'c': ('gcc', 'gcc (for example MinGW-w64 on Windows, build-essential on Linux)'),
    'cpp': ('g++', 'g++ (for example MinGW-w64 on Windows, build-essential on Linux)'),
    'java': ('javac', 'a JDK 17 or newer, for javac and java (for example Eclipse Temurin)'),
}


# ---------------------------------------------------------------------------
# What the Python does
# ---------------------------------------------------------------------------

def _frame(meta):
    text = 'step %s %s' % (meta['action'], meta['line'] or '-')
    text += ''.join(' %d:%d' % (i, v) for i, v in zip(meta['indices'], meta['values']))
    if 'depth' in meta:
        text += ' depth=%d range=%d:%d' % (meta['depth'], meta['range'][0], meta['range'][1])
    # Counting sort: the slots of the count list the step is about, and the
    # count in the first of them. Radix sort: the bucket, how many values it
    # holds as drawn, and the digit place.
    if meta.get('cells'):
        lo, hi = meta['cells']
        text += ' cells=%d:%d count=%d' % (lo, hi, meta['counts'][lo])
    if meta.get('bucket') is not None:
        text += ' bucket=%d size=%d place=%d' % (
            meta['bucket'], len(meta['buckets'][meta['bucket']]), meta['place'])
    return text


def python_sort(algo, variant, seed, values):
    func, _, variants = SORTS[algo]
    kwargs = dict(variants[variant])
    if kwargs.get('pivot_rule') == 'random':
        kwargs['seed'] = seed
    lines = []
    stats = {'swaps': 0, 'comparisons': 0}
    data = list(values)
    func(data, lambda arr, compared=None, meta=None: lines.append(_frame(meta)),
         lambda: None, stats, **kwargs)
    lines.append('sorted' + ''.join(' %d' % v for v in data))
    lines.append('comparisons %d' % stats['comparisons'])
    lines.append('swaps %d' % stats['swaps'])
    lines.append('end')
    return lines


def python_search(algo, values, target):
    func, _ = SEARCHES[algo]
    lines = []
    stats = {'comparisons': 0}
    index = func(values, target, lambda indices, meta: lines.append(_frame(meta)), None, stats)
    lines.append('index %d' % index)
    lines.append('comparisons %d' % stats['comparisons'])
    lines.append('end')
    return lines


# ---------------------------------------------------------------------------
# The inputs
# ---------------------------------------------------------------------------

def shapes():
    rng = random.Random(12)
    out = [[], [5], [2, 1], [1, 2], [3, 3]]
    for n in (5, 8, 13, 21, 30):
        out.append([rng.randint(1, 99) for _ in range(n)])            # random
        out.append(sorted(rng.randint(1, 99) for _ in range(n)))      # sorted
        out.append(sorted((rng.randint(1, 99) for _ in range(n)), reverse=True))
        out.append([7] * n)                                           # all equal
        out.append([rng.randint(-3, 3) for _ in range(n)])            # duplicates
    out.append(list(range(1, 31)))
    out.append(list(range(30, 0, -1)))
    return out


def keyed_shapes():
    """The same kinds of input inside 0 to KEY_MAX, the only values counting
    and radix sort accept, with both ends of the range."""
    rng = random.Random(19)
    out = [[], [0], [KEY_MAX], [2, 1], [1, 2], [3, 3], [KEY_MAX, 0], [0, KEY_MAX, 0]]
    for n in (5, 8, 13, 21, 30, 100):
        out.append([rng.randint(0, KEY_MAX) for _ in range(n)])
        out.append(sorted(rng.randint(0, KEY_MAX) for _ in range(n)))
        out.append(sorted((rng.randint(0, KEY_MAX) for _ in range(n)), reverse=True))
        out.append([7] * n)
        out.append([rng.randint(0, 3) for _ in range(n)])
    out.append(list(range(KEY_MAX + 1)))
    return out


def cases_for(algo):
    """[(variant, seed, target, values, expected lines)]"""
    out = []
    if algo in SORTS:
        for variant in SORTS[algo][2]:
            seeds = SEEDS if variant == 'random' else [0]
            for seed in seeds:
                for values in (keyed_shapes() if algo in KEYED else shapes()):
                    out.append((variant, seed, 0, values,
                                python_sort(algo, variant, seed, values)))
        return out
    rng = random.Random(5)
    for values in shapes():
        if algo in ('binary_search', 'jump_search'):
            values = sorted(values)
        targets = set(values[:3] + values[-2:]) | {-50, 1000}
        if values:
            targets.add(rng.choice(values))
        for target in sorted(targets):
            out.append(('-', 0, target, values, python_search(algo, values, target)))
    return out


def batch(cases):
    parts = ['%d' % len(cases)]
    for variant, seed, target, values, _ in cases:
        parts.append('%s %d %d' % (variant, seed, target))
        parts.append('%d' % len(values))
        parts.append(' '.join('%d' % v for v in values))
    return '\n'.join(parts) + '\n'


# ---------------------------------------------------------------------------
# Building and running the programs
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def build_dir(tmp_path_factory):
    return tmp_path_factory.mktemp('reference_build')


def _require(language):
    tool, install = TOOLS[language]
    if shutil.which(tool) is None or (language == 'java' and shutil.which('java') is None):
        pytest.skip('%s is not installed, so the %s reference code cannot be checked. '
                    'Install %s.' % (tool, language, install))


def compile_program(language, algo, out_dir):
    """Compile one program with warnings as errors and return the command
    that runs it."""
    _require(language)
    if language == 'c':
        src = os.path.join(REF, 'c', algo + '.c')
        exe = os.path.join(str(out_dir), algo + '_c' + EXE)
        cmd = ['gcc', '-std=c11', '-O2', '-Wall', '-Wextra', '-pedantic', '-Werror', src, '-o', exe]
        run = [exe]
    elif language == 'cpp':
        src = os.path.join(REF, 'cpp', algo + '.cpp')
        exe = os.path.join(str(out_dir), algo + '_cpp' + EXE)
        cmd = ['g++', '-std=c++17', '-O2', '-Wall', '-Wextra', '-pedantic', '-Werror', src, '-o', exe]
        run = [exe]
    else:
        cls = JAVA_CLASS[algo]
        src = os.path.join(REF, 'java', cls + '.java')
        classes = os.path.join(str(out_dir), 'java_' + algo)
        os.makedirs(classes, exist_ok=True)
        cmd = ['javac', '--release', '17', '-Xlint:all', '-Werror', '-d', classes, src]
        run = ['java', '-cp', classes, cls]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, '%s did not compile:\n%s%s' % (src, result.stdout, result.stderr)
    return run


@pytest.mark.parametrize('language', ['c', 'cpp', 'java'])
@pytest.mark.parametrize('algo', ALGORITHMS)
def test_program_matches_python_step_by_step(language, algo, build_dir):
    run = compile_program(language, algo, build_dir)
    cases = cases_for(algo)
    result = subprocess.run(run, input=batch(cases), capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout[-2000:] + result.stderr

    got = result.stdout.replace('\r\n', '\n').split('\n')
    if got and got[-1] == '':
        got.pop()
    want = [line for case in cases for line in case[4]]

    # Report the first case that differs, with its input, not a wall of text.
    position = 0
    for variant, seed, target, values, expected in cases:
        actual = got[position:position + len(expected)]
        if actual != expected:
            for k, (a, e) in enumerate(zip(actual, expected)):
                if a != e:
                    break
            else:
                k = min(len(actual), len(expected))
            pytest.fail('%s %s differs from Python on variant=%s seed=%d target=%d values=%s\n'
                        'line %d: got %r\n        want %r'
                        % (language, algo, variant, seed, target, values, k,
                           actual[k] if k < len(actual) else None,
                           expected[k] if k < len(expected) else None))
        position += len(expected)
    assert got == want


@pytest.mark.parametrize('language', ['c', 'cpp', 'java'])
def test_unknown_variant_is_an_error(language, build_dir):
    run = compile_program(language, 'quick_sort', build_dir)
    result = subprocess.run(run, input='1\nmedian 0 0\n3\n3 1 2\n', capture_output=True, text=True)
    assert result.returncode != 0
    assert 'unknown variant' in result.stdout + result.stderr


def test_every_algorithm_has_all_three_files():
    for algo in ALGORITHMS:
        cls = (SORTS.get(algo) or SEARCHES.get(algo))[1]
        for path in (os.path.join(REF, 'c', algo + '.c'),
                     os.path.join(REF, 'cpp', algo + '.cpp'),
                     os.path.join(REF, 'java', cls + '.java')):
            assert os.path.isfile(path), path


@pytest.mark.parametrize('language', ['c', 'cpp', 'java'])
@pytest.mark.parametrize('algo', sorted(KEYED))
@pytest.mark.parametrize('value', [-1, KEY_MAX + 1])
def test_keyed_sorts_refuse_values_outside_the_range(language, algo, value, build_dir):
    """Counting and radix sort take 0 to KEY_MAX only, as /run_sort does."""
    run = compile_program(language, algo, build_dir)
    result = subprocess.run(run, input='1\n- 0 0\n3\n4 %d 2\n' % value, capture_output=True, text=True)
    assert result.returncode != 0
    assert 'outside 0 to %d' % KEY_MAX in result.stdout + result.stderr
