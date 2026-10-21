"""Phase 21: the C, C++ and Java A* programs take exactly the steps of
algotrace/algorithms/grid/astar.py.

Every step (action, line id, cells, g and h), the path, the cells expanded
and the number of heap comparisons must match, for A* and for Dijkstra
(h = 0), on random grids with every density of walls, mazes, grids with no
path, and long thin grids where ties are everywhere. Matching comparison
counts is what shows the heap and the tie-break are the same.

Marked slow, like the other compile tests.
"""
import random
import subprocess

import pytest

from algotrace.algorithms.grid.astar import astar
from test_reference_code import compile_program  # noqa: E402

pytestmark = pytest.mark.slow


def grids():
    rng = random.Random(2101)
    out = []
    for k in range(60):
        rows, cols = rng.randint(3, 14), rng.randint(3, 20)
        density = rng.choice([0.0, 0.1, 0.25, 0.4])
        walls = {(r, c) for r in range(rows) for c in range(cols) if rng.random() < density}
        cells = [(r, c) for r in range(rows) for c in range(cols) if (r, c) not in walls]
        if len(cells) < 2:
            continue
        start, goal = rng.sample(cells, 2)
        out.append((rows, cols, walls, start, goal))
    # The goal boxed in: no path.
    out.append((6, 8, {(2, 5), (4, 5), (3, 4), (3, 6)}, (0, 0), (3, 5)))
    # A serpentine maze.
    maze = set()
    for r in range(1, 9, 2):
        maze |= {(r, c) for c in range(12) if c != (11 if r % 4 == 1 else 0)}
    out.append((10, 12, maze, (0, 0), (9, 11)))
    # One row: every tie broken by order.
    out.append((3, 20, set(), (1, 0), (1, 19)))
    return out


def python_lines(rows, cols, walls, start, goal, heuristic):
    lines = []

    def draw(meta):
        lines.append(' '.join(['step', meta['action'], meta['line']] + meta['indices'] + ['|'] +
                              [str(v) for v in meta['values']]))
    stats = {}
    path = astar(rows, cols, walls, start, goal, draw, heuristic, stats)
    lines.append(' '.join(['path'] + ['%d,%d' % c for c in (path or [])]))
    lines.append('expanded %d' % stats['expanded'])
    lines.append('comparisons %d' % stats['comparisons'])
    lines.append('end')
    return lines


def to_input(rows, cols, walls, start, goal, heuristic):
    out = ['%s %d %d' % (heuristic, rows, cols), '%d %d %d %d' % (start + goal)]
    for r in range(rows):
        out.append(''.join('#' if (r, c) in walls else '.' for c in range(cols)))
    return out


@pytest.fixture(scope='module')
def build_dir(tmp_path_factory):
    return tmp_path_factory.mktemp('reference_grid')


@pytest.mark.parametrize('language', ['c', 'cpp', 'java'])
def test_astar_program_matches_python(language, build_dir):
    run = compile_program(language, 'astar', build_dir)
    cases = [(g, h) for g in grids() for h in ('manhattan', 'zero')]
    text = '\n'.join([str(len(cases))] + [line for g, h in cases for line in to_input(*g, h)]) + '\n'
    result = subprocess.run(run, input=text, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout[-2000:] + result.stderr
    got = result.stdout.replace('\r\n', '\n').split('\n')
    if got and got[-1] == '':
        got.pop()
    position = 0
    for g, h in cases:
        expected = python_lines(*g, h)
        actual = got[position:position + len(expected)]
        if actual != expected:
            k = next((i for i, (a, e) in enumerate(zip(actual, expected)) if a != e),
                     min(len(actual), len(expected)))
            pytest.fail('%s differs on %s %s\nline %d: got %r\n        want %r'
                        % (language, h, g, k, actual[k] if k < len(actual) else None,
                           expected[k] if k < len(expected) else None))
        position += len(expected)
    assert position == len(got)


@pytest.mark.parametrize('language', ['c', 'cpp', 'java'])
def test_unknown_heuristic_is_an_error(language, build_dir):
    run = compile_program(language, 'astar', build_dir)
    result = subprocess.run(run, input='1\neuclid 3 3\n0 0 2 2\n...\n...\n...\n',
                            capture_output=True, text=True)
    assert result.returncode != 0 and 'unknown heuristic' in result.stdout + result.stderr


def test_the_cases_hit_stale_entries_and_no_path():
    """The set really contains an entry skipped as stale, and a grid with no path."""
    stale = nopath = False
    for g in grids():
        for h in ('manhattan', 'zero'):
            lines = python_lines(*g, h)
            stale = stale or any(' reject stale ' in l for l in lines)
            nopath = nopath or any(' no-path ' in l for l in lines)
    assert nopath
    assert stale, 'no stale heap entry in the generated grids'
