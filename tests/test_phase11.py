"""Phase 11: Theta per case, overall O, Omega and Theta, measured.

Every lesson states a tight bound (theta) for its best, average and worst
case. These tests build an input of each case at several sizes, run the
real code, count its work and check that the count grows like the stated
bound and like neither of its neighbours: the bound times log n, or the
bound over log n. A bound that was too loose or too tight by even a log
factor fails.

What is counted:
  sorts      comparisons, from the stats every sort keeps
  searches   comparisons, the same way
  graphs     the endpoint's own look-ups and comparisons, read through
             counting node names and weights (tests/graph_cost.py). For
             Kruskal only the weight comparisons, which is the sort; its
             other work is one look-up per edge and cannot change the
             shape. Floyd-Warshall and Bellman-Ford log one step per pair
             or edge examined, so for them the steps are the count.

Also here: the Step 0 fix, switching algorithm clears the loaded run.
"""
import json
import math
import os
import random
import shutil
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from sorting_algorithms.bubble_sort import bubble_sort
from sorting_algorithms.selection_sort import selection_sort
from sorting_algorithms.insertion_sort import insertion_sort
from sorting_algorithms.merge_sort import merge_sort
from sorting_algorithms.quick_sort import quick_sort
from sorting_algorithms.heap_sort import heap_sort
from searching_algorithms.linear_search import linear_search
from searching_algorithms.binary_search import binary_search
import graph_cost
from graph_cost import measure, names, COUNT, Weight

NODE = shutil.which('node')
needs_node = pytest.mark.skipif(NODE is None, reason='node is not installed, so the lesson files cannot be read')

_LESSONS = None


def lessons():
    global _LESSONS
    if _LESSONS is None:
        out = subprocess.run([NODE, os.path.join(HERE, 'dump_lessons.js')],
                             capture_output=True, text=True, check=True)
        _LESSONS = json.loads(out.stdout)
    return _LESSONS


# ---------------------------------------------------------------------------
# Step 0: a new algorithm drops the loaded run
# ---------------------------------------------------------------------------

@pytest.mark.skipif(NODE is None, reason='node is not installed')
def test_switching_algorithm_clears_the_loaded_run():
    """Runs the real workspace.js against a stand-in DOM: after a switch the
    steps, stage, banner, step counter and Learn panel are all cleared, and
    a reply still in flight for the old algorithm is dropped."""
    result = subprocess.run([NODE, os.path.join(HERE, 'workspace_switch_check.js')],
                            capture_output=True, text=True)
    assert result.returncode == 0 and 'ok' in result.stdout, result.stdout + result.stderr


def test_both_pickers_use_the_shared_switch():
    """Sorting and searching both switch through Workspace.selectAlgorithm,
    so the one fix covers both pages."""
    for page in ('sorting.html', 'searching.html'):
        html = open(os.path.join(ROOT, 'templates', page), encoding='utf-8').read()
        assert 'id="algo-picker"' in html and 'data-algorithm=' in html
        assert 'Workspace.start' in html


# ---------------------------------------------------------------------------
# Inputs for each case
# ---------------------------------------------------------------------------

def ascending(n):
    return list(range(1, n + 1))


def descending(n):
    return list(range(n, 0, -1))


def shuffled(n, seed=0):
    values = ascending(n)
    random.Random(n * 1000 + seed).shuffle(values)
    return values


def merge_worst(n):
    """The arrangement that makes every merge compare until both halves are
    nearly empty: deal a sorted run out alternately to the two halves, with
    the left half the size merge_sort gives it, and recurse."""
    def build(values):
        if len(values) <= 1:
            return values
        left_size = len(values) // 2
        left, right = [], []
        for i, v in enumerate(values):
            # Alternate, then give whichever side is short the rest.
            if (i % 2 == 0 and len(right) < len(values) - left_size) or len(left) == left_size:
                right.append(v)
            else:
                left.append(v)
        return build(left) + build(right)
    return build(ascending(n))


def quick_last_best(n):
    """An arrangement on which the last element pivot is always the median
    of its range, so every partition splits evenly. The values smaller than
    the pivot keep their order through a partition, and the larger ones come
    out rotated by one, so the larger half is laid down pre-rotated."""
    def build(values):
        if len(values) <= 1:
            return list(values)
        k = (len(values) - 1) // 2
        left = build(values[:k])
        right = build(values[k + 1:])
        if right:
            right = [right[-1]] + right[:-1]
        return left + right + [values[k]]
    return build(ascending(n))


SORTS = {
    'bubble_sort': (bubble_sort, {'': {}, 'off': {'early_exit': False}, 'on': {'early_exit': True}}),
    'selection_sort': (selection_sort, {'': {}}),
    'insertion_sort': (insertion_sort, {'': {}}),
    'merge_sort': (merge_sort, {'lt': {'stable': False}, 'le': {'stable': True}}),
    'heap_sort': (heap_sort, {'': {}}),
    'quick_sort': (quick_sort, {'last': {'pivot_rule': 'last'},
                                'middle': {'pivot_rule': 'middle'},
                                'random': {'pivot_rule': 'random', 'seed': 42}}),
}

# (lesson, variant) -> case -> input of size n
SORT_CASES = {
    ('bubble_sort', 'off'): {'best': ascending, 'average': shuffled, 'worst': descending},
    ('bubble_sort', 'on'): {'best': ascending, 'average': shuffled, 'worst': descending},
    ('selection_sort', ''): {'best': ascending, 'average': shuffled, 'worst': descending},
    ('insertion_sort', ''): {'best': ascending, 'average': shuffled, 'worst': descending},
    ('merge_sort', 'lt'): {'best': ascending, 'average': shuffled, 'worst': merge_worst},
    ('merge_sort', 'le'): {'best': ascending, 'average': shuffled, 'worst': merge_worst},
    ('heap_sort', ''): {'best': lambda n: [7] * n, 'average': shuffled, 'worst': ascending},
    ('quick_sort', 'last'): {'best': quick_last_best, 'average': shuffled, 'worst': ascending},
    ('quick_sort', 'middle'): {'best': ascending, 'average': shuffled, 'worst': lambda n: [7] * n},
    ('quick_sort', 'random'): {'best': ascending, 'average': shuffled, 'worst': lambda n: [7] * n},
}

# Quadratic cases stay small enough to run quickly and to keep quick sort's
# n deep recursion under Python's limit. The others start larger, because a
# term like -2.85n in quick sort's average still shows at n = 16.
SORT_SIZES = {'n squared': [32, 64, 128, 256, 512]}
SORT_SIZES_OTHER = [64, 128, 256, 512, 1024, 2048]


def sort_count(lesson, variant, values, seeds=20):
    func, options = SORTS[lesson]
    kwargs = dict(options[variant])
    if 'seed' in kwargs:
        # A random pivot's cost on an input is an expectation over seeds.
        total = 0
        for seed in range(1, seeds + 1):
            kwargs['seed'] = seed
            stats = {'swaps': 0, 'comparisons': 0}
            data = list(values)
            func(data, lambda *a: None, lambda: None, stats, **kwargs)
            assert data == sorted(values)
            total += stats['comparisons']
        return total / seeds
    stats = {'swaps': 0, 'comparisons': 0}
    data = list(values)
    func(data, lambda *a: None, lambda: None, stats, **kwargs)
    assert data == sorted(values)
    return stats['comparisons']


def search_count(func, values, target):
    stats = {'comparisons': 0}
    func(values, target, lambda *a: None, None, stats)
    return stats['comparisons']


def first_mid(n):
    """The position binary search looks at first."""
    return (n - 1) // 2


SEARCH_CASES = {
    'linear_search': {
        'best': lambda vals: [search_count(linear_search, vals, vals[0])],
        'average': lambda vals: [search_count(linear_search, vals, v) for v in vals[::max(1, len(vals) // 64)]],
        'worst': lambda vals: [search_count(linear_search, vals, 10 ** 9)],
    },
    'binary_search': {
        'best': lambda vals: [search_count(binary_search, vals, vals[first_mid(len(vals))])],
        'average': lambda vals: [search_count(binary_search, vals, v) for v in vals],
        'worst': lambda vals: [search_count(binary_search, vals, 10 ** 9)],
    },
}

SEARCH_SIZES = [16, 64, 256, 1024, 4096]


# Graph families: n -> (nodes, undirected edges, start)
def g_path(n):
    nodes = names(n)
    return nodes, [(nodes[i], nodes[i + 1], i + 1) for i in range(n - 1)], nodes[0]


def g_complete(n, sorted_weights=False, seed=1):
    nodes = names(n)
    pairs = [(nodes[i], nodes[j]) for i in range(n) for j in range(i + 1, n)]
    weights = list(range(1, len(pairs) + 1))
    if not sorted_weights:
        random.Random(seed).shuffle(weights)
    return nodes, [(u, v, w) for (u, v), w in zip(pairs, weights)], nodes[0]


def g_random(n, seed=1):
    """Built the way /generate_random_graph builds one: a random spanning
    tree, then random extra edges, here up to about V squared over 8."""
    rng = random.Random(seed)
    nodes = names(n)
    used, rest, edges, seen = [nodes[0]], nodes[1:], [], set()
    while rest:
        u = rng.choice(used)
        v = rest.pop(rng.randrange(len(rest)))
        edges.append((u, v))
        seen.add(frozenset((u, v)))
        used.append(v)
    while len(edges) < max(n - 1, n * n // 8):
        u, v = rng.sample(nodes, 2)
        if frozenset((u, v)) not in seen:
            seen.add(frozenset((u, v)))
            edges.append((u, v))
    weights = list(range(1, len(edges) + 1))
    rng.shuffle(weights)
    return nodes, [(u, v, w) for (u, v), w in zip(edges, weights)], nodes[0]


def g_bf_worst(n):
    """A path whose start is listed last, inside an otherwise complete graph
    of heavy edges: the shortest paths follow the path, and each pass of the
    edge list settles only one more node."""
    nodes = names(n)
    edges = [(nodes[i], nodes[j], 1 if j == i + 1 else n * n)
             for i in range(n) for j in range(i + 1, n)]
    return nodes, edges, nodes[-1]


def g_star(n):
    nodes = names(n)
    return nodes, [(nodes[0], nodes[i], i) for i in range(1, n)], nodes[0]


GRAPH_CASES = {
    'bfs': {'best': [g_path], 'average': [g_random], 'worst': [g_complete, g_star]},
    'dfs': {'best': [g_path], 'average': [g_random], 'worst': [g_complete, g_star]},
    'dijkstra': {'best': [g_path], 'average': [g_random], 'worst': [g_complete]},
    'prim': {'best': [g_path], 'average': [g_random], 'worst': [g_complete]},
    'kruskal': {'best': [lambda n: g_complete(n, sorted_weights=True), g_path],
                'average': [g_random], 'worst': [g_complete]},
    'bellman_ford': {'best': [g_path, lambda n: g_complete(n, sorted_weights=True)],
                     'worst': [g_bf_worst]},
    'floyd_warshall': {'best': [g_path], 'average': [g_random], 'worst': [g_complete]},
}

GRAPH_SIZES = {
    'bfs': [32, 64, 128, 192], 'dfs': [32, 64, 128, 192],
    # Dijkstra spends about 32 look-ups per node outside its V squared scan,
    # so its sizes start where that term is small.
    'dijkstra': [128, 256, 512, 768], 'prim': [16, 32, 64, 96],
    'kruskal': [16, 32, 64, 128], 'bellman_ford': [8, 16, 24, 32, 48],
    'floyd_warshall': [8, 12, 16, 24],
    # A complete graph's relaxations already outweigh the linear term.
    ('dijkstra', 'worst'): [64, 128, 256, 384],
}


def graph_count(algo, family, n):
    nodes, edges, start = family(n)
    if algo == 'kruskal':
        # Only the comparisons between weights: the sort.
        graph_cost.WEIGHT_ONLY[0] = True
    try:
        work, _ = measure(algo, nodes, edges, start)
    finally:
        graph_cost.WEIGHT_ONLY[0] = False
    return work, len(nodes), len(edges)


# ---------------------------------------------------------------------------
# Growth
# ---------------------------------------------------------------------------

def bound(theta, n, V=None, E=None):
    lg = math.log2
    return {
        '1': lambda: 1.0,
        'log n': lambda: lg(n),
        'n': lambda: n,
        'n log n': lambda: n * lg(n),
        'n squared': lambda: n * n,
        'V': lambda: V,
        'E': lambda: E,
        'V squared': lambda: V * V,
        'V cubed': lambda: V ** 3,
        'V times E': lambda: V * E,
        'E log E': lambda: E * lg(E),
    }[theta]()


BAND = 1.6      # the count over the bound may wander by at most this much


def check_growth(label, theta, samples):
    """samples: list of (count, size for the log factor, bound value).

    Over the sizes tried, a log factor would change the count over the bound
    by L = log(largest) / log(smallest). The count over the stated bound must
    change by less than the square root of L either way: it tracks the stated
    bound more closely than the bound times log n or the bound over log n,
    so the stated bound is the tight one. It also may not wander by more than
    BAND in between."""
    ratios = [c / b for c, _, b in samples]
    first, last = samples[0][1], samples[-1][1]
    L = math.log2(last) / math.log2(first)
    drift = ratios[-1] / ratios[0]
    assert max(ratios) / min(ratios) <= BAND, (
        '%s: count over %s wanders from %.3f to %.3f across sizes %s, counts %s'
        % (label, theta, min(ratios), max(ratios),
           [s for _, s, _ in samples], [c for c, _, _ in samples]))
    assert drift < L ** 0.5, (
        '%s grows faster than %s: count over it rose by %.2f, nearer the %.2f of '
        'a log factor more. Counts %s' % (label, theta, drift, L, [c for c, _, _ in samples]))
    assert drift > L ** -0.5, (
        '%s grows slower than %s: count over it fell by %.2f, nearer the %.2f of '
        'a log factor less. Counts %s' % (label, theta, 1 / drift, L, [c for c, _, _ in samples]))


def _sort_params():
    return [(lesson, variant, case) for (lesson, variant) in sorted(SORT_CASES)
            for case in ('best', 'average', 'worst')]


@pytest.mark.slow
@needs_node
@pytest.mark.parametrize('lesson,variant,case', _sort_params())
def test_sorting_cases_grow_as_their_theta(lesson, variant, case):
    resolved = lessons()[lesson]['resolved']
    theta = resolved[variant if variant in resolved else '']['complexity']['time'][case]['theta']
    make = SORT_CASES[(lesson, variant)][case]
    samples = []
    for n in SORT_SIZES.get(theta, SORT_SIZES_OTHER):
        if case == 'average' and variant == 'random':
            # The seeds already average over pivots: one shuffled input will do.
            count = sort_count(lesson, variant, shuffled(n))
        elif case == 'average':
            count = sum(sort_count(lesson, variant, shuffled(n, s)) for s in range(5)) / 5
        elif case == 'worst' and variant in ('middle', 'random'):
            # All equal values: every seed and every pivot position costs the same.
            count = sort_count(lesson, variant, make(n), seeds=2)
        else:
            count = sort_count(lesson, variant, make(n))
        samples.append((count, n, bound(theta, n)))
    check_growth('%s %s %s' % (lesson, variant or '-', case), theta, samples)


@pytest.mark.slow
@needs_node
@pytest.mark.parametrize('lesson,case', [(l, c) for l in sorted(SEARCH_CASES)
                                         for c in ('best', 'average', 'worst')])
def test_searching_cases_grow_as_their_theta(lesson, case):
    theta = lessons()[lesson]['resolved']['']['complexity']['time'][case]['theta']
    samples = []
    for n in SEARCH_SIZES:
        values = list(range(0, 2 * n, 2))
        counts = SEARCH_CASES[lesson][case](values)
        samples.append((sum(counts) / len(counts), n, bound(theta, n)))
    check_growth('%s %s' % (lesson, case), theta, samples)


def _graph_params():
    out = []
    for algo in sorted(GRAPH_CASES):
        for case, families in sorted(GRAPH_CASES[algo].items()):
            for k in range(len(families)):
                out.append((algo, case, k))
    return out


@pytest.mark.slow
@needs_node
@pytest.mark.parametrize('algo,case,family', _graph_params())
def test_graph_cases_grow_as_their_theta(algo, case, family):
    theta = lessons()[algo]['resolved']['']['complexity']['time'][case]['theta']
    make = GRAPH_CASES[algo][case][family]
    samples = []
    for n in GRAPH_SIZES.get((algo, case), GRAPH_SIZES[algo]):
        if case == 'average':
            seeds = (1, 2) if algo == 'dijkstra' else (1, 2, 3)
            runs = [graph_count(algo, lambda m, s=s: g_random(m, s), n) for s in seeds]
            work = sum(r[0] for r in runs) / len(runs)
            V, E = runs[0][1], sum(r[2] for r in runs) / len(runs)
        else:
            work, V, E = graph_count(algo, make, n)
        samples.append((work, n, bound(theta, n, V, E)))
    check_growth('%s %s family %d' % (algo, case, family), theta, samples)


@pytest.mark.slow
@needs_node
def test_bellman_ford_average_is_k_passes_of_e_edges():
    """The average case is written Theta(k times E), k being the number of
    passes, because the pass count depends on the graph and the edge order.
    The count is exactly k sweeps of every edge in the edge list."""
    assert (lessons()['bellman_ford']['resolved']['']['complexity']['time']['average']['theta']
            == 'k times E')
    for n in (16, 32, 64):
        for seed in (1, 2, 3):
            nodes, edges, start = g_random(n, seed)
            work, payload = measure('bellman_ford', nodes, edges, start)
            listed = 2 * len(edges)      # each undirected edge, both ways
            assert work == payload['iterations'] * listed
            assert 1 <= payload['iterations'] <= n - 1


# ---------------------------------------------------------------------------
# Figures quoted in the new texts
# ---------------------------------------------------------------------------

def test_heap_sort_on_equal_values_makes_3n_minus_6_comparisons():
    """heap_sort.js: '3n - 6 comparisons for n of 3 or more'."""
    for n in range(3, 80):
        assert sort_count('heap_sort', '', [7] * n) == 3 * n - 6


def test_kruskal_sorts_presorted_edges_in_e_minus_one_comparisons():
    """kruskal.js: Timsort 'spots the sorted run in E-1 comparisons'."""
    for n in (8, 16, 32):
        work, _, E = graph_count('kruskal', lambda m: g_complete(m, sorted_weights=True), n)
        assert work == E - 1


def test_bellman_ford_best_case_is_two_sweeps():
    """bellman_ford.js: edges listed outward from the start settle in one
    pass, and a second, quiet pass ends the loop."""
    for n in (8, 16, 32):
        nodes, edges, start = g_path(n)
        work, payload = measure('bellman_ford', nodes, edges, start)
        assert payload['iterations'] == 2
        assert work == 2 * 2 * len(edges)


def test_bellman_ford_worst_case_runs_every_pass():
    for n in (8, 16, 24):
        nodes, edges, start = g_bf_worst(n)
        _, payload = measure('bellman_ford', nodes, edges, start)
        assert payload['iterations'] == n - 1


def test_dijkstra_stops_early_when_the_start_reaches_little():
    """dijkstra.js caseScope: a start that reaches fewer nodes does less
    work. With the start cut off, the scan is linear, not quadratic."""
    counts = []
    for n in (32, 64, 128):
        nodes = names(n)
        edges = [(nodes[i], nodes[i + 1], 1) for i in range(1, n - 1)]
        work, _ = measure('dijkstra', nodes, edges, nodes[0])
        counts.append(work / n)
    assert max(counts) / min(counts) < 1.3


def test_kruskal_checks_edge_ends_with_a_set():
    """The validation used to scan the node list for both ends of every
    edge, which alone made the endpoint O(V times E). It must stay linear
    in E on a path, where Kruskal itself is linear."""
    per_edge = []
    for n in (32, 64, 128, 256):
        nodes, edges, start = g_path(n)
        work, _ = measure('kruskal', nodes, edges, start)
        per_edge.append(work / len(edges))
    assert max(per_edge) / min(per_edge) < 1.3, per_edge


# ---------------------------------------------------------------------------
# The contract itself
# ---------------------------------------------------------------------------

@needs_node
def test_every_lesson_and_variant_states_its_bounds():
    for key, info in lessons().items():
        for variant, lesson in info['resolved'].items():
            c = lesson['complexity']
            where = '%s %s' % (key, variant)
            thetas = {case: c['time'][case]['theta'] for case in ('best', 'average', 'worst')}
            assert all(thetas.values()), where
            assert c['overall']['O'] == thetas['worst'], where
            assert c['overall']['Omega'] == thetas['best'], where
            assert c['overall']['Theta'] == (thetas['best'] if thetas['best'] == thetas['worst'] else None), where
            assert 'cases' in c['misconception'] and 'bounds' in c['misconception'], where


@needs_node
@pytest.mark.parametrize('lesson,mutation,replacement', [
    ('insertion_sort', "overall: { O: 'n squared', Omega: 'n', Theta: null }",
     "overall: { O: 'n', Omega: 'n', Theta: null }"),
    ('insertion_sort', "overall: { O: 'n squared', Omega: 'n', Theta: null }",
     "overall: { O: 'n squared', Omega: 'n', Theta: 'n squared' }"),
    ('selection_sort', "overall: { O: 'n squared', Omega: 'n squared', Theta: 'n squared' }",
     "overall: { O: 'n squared', Omega: 'n squared', Theta: null }"),
    ('heap_sort', "theta: 'n',", "theta: 'n log n',"),
    ('heap_sort', "theta: 'n',", "theta: 'linear',"),
    ('linear_search', "misconception: 'Best,", "misconception: 'The best,"),
    ('bfs', "caseScope: 'The cases", "notScope: 'The cases"),
    ('merge_sort', "        overall: {", "        overallx: {"),
])
def test_validator_rejects_inconsistent_bounds(tmp_path, lesson, mutation, replacement):
    source_dir = os.path.join(ROOT, 'static', 'js', 'lessons')
    for name in os.listdir(source_dir):
        if name.endswith('.js'):
            shutil.copy(os.path.join(source_dir, name), tmp_path / name)
    target = tmp_path / ('%s.js' % lesson)
    text = target.read_text(encoding='utf-8')
    assert mutation in text, 'the mutation no longer matches %s.js' % lesson
    target.write_text(text.replace(mutation, replacement, 1), encoding='utf-8')

    result = subprocess.run([NODE, os.path.join(HERE, 'validate_lessons.js')],
                            capture_output=True, text=True,
                            env=dict(os.environ, LESSON_DIR=str(tmp_path)))
    assert result.returncode != 0, result.stdout
