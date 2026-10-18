"""Phase 10: variant switches, stability tags, depth and range meta.

What these prove:
  - the default of every switch is the run the site always made, so the
    baselines in baseline_sorting.json still describe it;
  - every variant sorts, and its counts are the ones its lesson states:
    each claim in a lesson's complexity.claims is measured here, as is each
    worked example and each figure quoted in a note;
  - stability is what each lesson's `stable` flag says, and the tags the
    page draws come from real positions;
  - a random pivot run is fully described by its seed;
  - every Merge and Quick Sort step carries depth and range.
"""
import json
import math
from html import escape
import os
import random
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module
from app import app, SORT_VARIANTS, _sort_payload
from sorting_algorithms.bubble_sort import bubble_sort
from sorting_algorithms.merge_sort import merge_sort
from sorting_algorithms.quick_sort import quick_sort
from sorting_algorithms.seeded import mulberry32

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NODE = shutil.which('node')
needs_node = pytest.mark.skipif(NODE is None, reason='node is not installed, so the lesson files cannot be read')

with open(os.path.join(ROOT, 'tests', 'baseline_sorting.json'), encoding='utf-8') as fh:
    BASELINE = json.load(fh)

# Lesson id, display name, function, and how each option id calls it.
SWITCHES = {
    'bubble_sort': ('Bubble Sort', bubble_sort, {
        'off': {'early_exit': False}, 'on': {'early_exit': True}}),
    'merge_sort': ('Merge Sort', merge_sort, {
        'lt': {'stable': False}, 'le': {'stable': True}}),
    'quick_sort': ('Quick Sort', quick_sort, {
        'last': {'pivot_rule': 'last'}, 'middle': {'pivot_rule': 'middle'},
        'random': {'pivot_rule': 'random'}}),
}
VARIANTS = [(lesson, opt) for lesson in sorted(SWITCHES) for opt in SWITCHES[lesson][2]]


class Tagged(int):
    def __new__(cls, value, tag):
        item = int.__new__(cls, value)
        item.tag = tag
        return item


def run(lesson, option, values, seed=1):
    """Run one variant directly and return (output, steps, stats)."""
    _, func, options = SWITCHES[lesson]
    kwargs = dict(options[option])
    if kwargs.get('pivot_rule') == 'random':
        kwargs['seed'] = seed
    data = list(values)
    steps = []
    stats = {'swaps': 0, 'comparisons': 0}

    def draw(array_state, compared=None, meta=None):
        step = {'array': array_state[:], 'compared': list(compared) if compared else []}
        if meta:
            step.update(meta)
        steps.append(step)

    func(data, draw, lambda: None, stats, **kwargs)
    return data, steps, stats


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


_LESSONS = None


def lessons():
    global _LESSONS
    if _LESSONS is None:
        out = subprocess.run([NODE, os.path.join(ROOT, 'tests', 'dump_lessons.js')],
                             capture_output=True, text=True, check=True)
        _LESSONS = json.loads(out.stdout)
    return _LESSONS


# ---------------------------------------------------------------------------
# Defaults change nothing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('lesson', sorted(SWITCHES))
@pytest.mark.parametrize('case', sorted(BASELINE['cases']))
def test_default_option_reproduces_the_baseline(lesson, case):
    """Calling the default explicitly is the same run as not choosing one."""
    name, _, options = SWITCHES[lesson]
    default = SORT_VARIANTS[name]['options'][0][0]
    payload = BASELINE['cases'][case]
    expected = payload['results'][lesson]

    data, steps, stats = run(lesson, default, payload['input'])

    assert data == expected['sorted']
    assert stats['comparisons'] == expected['comparisons']
    assert stats['swaps'] == expected['swaps']
    assert len(steps) == expected['steps']


@pytest.mark.parametrize('lesson', sorted(SWITCHES))
def test_payload_without_a_variant_is_the_default_run(lesson):
    name = SWITCHES[lesson][0]
    default = SORT_VARIANTS[name]['options'][0][0]
    values = [5, 3, 8, 1, 9, 3, 7]

    plain = _sort_payload(name, values)
    explicit = _sort_payload(name, values, default)

    assert plain == explicit
    assert plain['variant'] == default
    assert plain['seed'] is None


def test_algorithms_without_a_switch_record_no_variant(client):
    body = client.post('/run_sort', json={'algorithm': 'Heap Sort', 'values': '3, 1, 2'}).get_json()
    assert body['variant'] is None and body['seed'] is None

    refused = client.post('/run_sort', json={'algorithm': 'Heap Sort', 'values': '3, 1, 2',
                                             'variant': 'on'})
    assert refused.status_code == 400
    assert 'no variants' in refused.get_json()['error']


# ---------------------------------------------------------------------------
# Every variant sorts
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('lesson,option', VARIANTS)
def test_every_variant_sorts(lesson, option):
    rng = random.Random(7)
    inputs = [payload['input'] for payload in BASELINE['cases'].values()]
    inputs += [[rng.randint(1, 9) for _ in range(rng.randint(1, 40))] for _ in range(60)]
    for values in inputs:
        for seed in (1, 2, 99999):
            data, steps, stats = run(lesson, option, values, seed)
            assert data == sorted(values), (lesson, option, values, seed)
            assert steps[-1]['action'] == 'done'
            assert steps[-1]['array'] == sorted(values)
            assert stats['comparisons'] == sum(1 for s in steps if s['action'] == 'compare')
            if SWITCHES[lesson][2][option].get('pivot_rule') != 'random':
                break


@pytest.mark.parametrize('lesson,option', VARIANTS)
def test_every_variant_answers_over_http(client, lesson, option):
    name = SWITCHES[lesson][0]
    body = client.post('/run_sort', json={'algorithm': name, 'values': '4, 2, 4, 1, 3',
                                          'variant': option, 'seed': 5}).get_json()

    assert body['sorted'] == [1, 2, 3, 4, 4]
    assert body['variant'] == option
    assert body['seed'] == (5 if option == 'random' else None)


# ---------------------------------------------------------------------------
# The figures the lessons state
# ---------------------------------------------------------------------------

def _shape(kind, n):
    """The inputs a claim is measured on. Distinct values except `equal`."""
    if kind == 'sorted':
        return list(range(1, n + 1))
    if kind == 'reversed':
        return list(range(n, 0, -1))
    if kind == 'equal':
        return [7] * n
    if kind == 'random':
        values = list(range(1, n + 1))
        random.Random(n).shuffle(values)
        return values
    if kind == 'nearly':
        values = list(range(1, n + 1))
        # Every tenth neighbouring pair swapped, never two pairs touching.
        for i in range(0, n - 1, 10):
            values[i], values[i + 1] = values[i + 1], values[i]
        return values
    raise AssertionError(kind)


def _formula(text, n):
    harmonic = sum(1.0 / k for k in range(1, n + 1))
    scope = {'n': n, 'log2': math.log2, 'ceil': math.ceil, 'floor': math.floor,
             'H': lambda m: sum(1.0 / k for k in range(1, m + 1)), '__builtins__': {}}
    assert harmonic >= 0
    return eval(text, scope)


def _claims():
    out = []
    for lesson in sorted(SWITCHES):
        for option in SWITCHES[lesson][2]:
            out.append((lesson, option))
    return out


@pytest.mark.slow
@needs_node
@pytest.mark.parametrize('lesson,option', _claims())
def test_complexity_claims_match_measured_counts(lesson, option):
    """complexity.claims is the machine readable form of the sentences the
    lesson shows. Each one is measured on this variant's real code."""
    resolved = lessons()[lesson]['resolved'][option]
    claims = resolved['complexity'].get('claims')
    assert claims, '%s %s states no measurable claims' % (lesson, option)
    random_pivot = SWITCHES[lesson][2][option].get('pivot_rule') == 'random'

    for claim in claims:
        if claim.get('bound') == 'mean':
            for n in (10, 20, 30):
                seeds = range(1, 301)
                mean = sum(run(lesson, option, _shape(claim['input'], n), s)[2]['comparisons']
                           for s in seeds) / len(seeds)
                want = _formula(claim['comparisons'], n)
                assert abs(mean - want) <= 0.06 * want, (
                    '%s %s says %s on %s averages %s = %.1f at n = %d, measured %.1f'
                    % (lesson, option, claim['where'], claim['input'],
                       claim['comparisons'], want, n, mean))
            continue

        for n in range(2, 41):
            for seed in (range(1, 21) if random_pivot else [1]):
                got = run(lesson, option, _shape(claim['input'], n), seed)[2]['comparisons']
                if 'sameAs' in claim:
                    want = run(lesson, option, _shape(claim['sameAs'], n), seed)[2]['comparisons']
                    assert got == want, (lesson, option, claim, n, got, want)
                    continue
                want = _formula(claim['comparisons'], n)
                if claim['bound'] == 'exact':
                    assert got == want, (
                        '%s %s: %s says %s comparisons on %s input, n = %d gives %s, code made %d'
                        % (lesson, option, claim['where'], claim['comparisons'],
                           claim['input'], n, want, got))
                else:
                    assert got <= want + 1e-9, (
                        '%s %s: %s says at most %s on %s input, n = %d allows %.1f, code made %d'
                        % (lesson, option, claim['where'], claim['comparisons'],
                           claim['input'], n, want, got))


@needs_node
@pytest.mark.parametrize('lesson,option', _claims())
def test_worked_example_of_every_variant(lesson, option):
    worked = lessons()[lesson]['resolved'][option]['complexity']['worked']
    values = json.loads(worked['input'])
    _, _, stats = run(lesson, option, values, worked.get('seed', 1))

    assert stats['comparisons'] == worked['comparisons'], (
        '%s %s quotes %d comparisons for %s, the code makes %d'
        % (lesson, option, worked['comparisons'], worked['input'], stats['comparisons']))


@pytest.mark.parametrize('lesson,option,values,seed,comparisons,swaps', [
    # bubble_sort.js on: "The sorted list [1, 3, 5, 8, 9] costs 4"
    ('bubble_sort', 'on', [1, 3, 5, 8, 9], None, 4, 0),
    # bubble_sort.js on: "each of the first three passes swaps"
    ('bubble_sort', 'on', [5, 3, 8, 1, 9], None, 10, 4),
    # merge_sort.js le: "<= makes 5 comparisons ... while < makes 7. Both write 12 times."
    ('merge_sort', 'le', [2, 2, 2, 2, 2], None, 5, 12),
    ('merge_sort', 'lt', [2, 2, 2, 2, 2], None, 7, 12),
    ('merge_sort', 'le', [1, 3, 5, 8, 9], None, 5, 12),
    # quick_sort.js middle: "[1, 3, 5, 8, 9] also costs 6 ... [7, 7, 7, 7, 7] still costs 10"
    ('quick_sort', 'middle', [1, 3, 5, 8, 9], None, 6, None),
    ('quick_sort', 'middle', [7, 7, 7, 7, 7], None, 10, None),
    # quick_sort.js random: "seed 1 costs 10 ... [1, 3, 5, 8, 9] costs 6 with seed 42"
    ('quick_sort', 'random', [5, 3, 8, 1, 9], 1, 10, None),
    ('quick_sort', 'random', [1, 3, 5, 8, 9], 42, 6, None),
])
def test_figures_quoted_in_variant_notes(lesson, option, values, seed, comparisons, swaps):
    _, _, stats = run(lesson, option, values, seed or 1)

    assert stats['comparisons'] == comparisons
    if swaps is not None:
        assert stats['swaps'] == swaps


def test_early_exit_on_sorted_input_makes_n_minus_one_comparisons():
    """The headline of the switch: best case drops from n(n-1)/2 to n-1."""
    for n in range(2, 60):
        values = list(range(n))
        assert run('bubble_sort', 'on', values)[2]['comparisons'] == n - 1
        assert run('bubble_sort', 'off', values)[2]['comparisons'] == n * (n - 1) // 2


def test_early_exit_never_costs_more_than_without_it():
    rng = random.Random(3)
    for _ in range(200):
        values = [rng.randint(1, 20) for _ in range(rng.randint(1, 30))]
        on = run('bubble_sort', 'on', values)[2]
        off = run('bubble_sort', 'off', values)[2]
        assert on['comparisons'] <= off['comparisons']
        assert on['swaps'] == off['swaps'], 'the flag skips passes, never swaps'


# ---------------------------------------------------------------------------
# Stability, and the tags the page draws
# ---------------------------------------------------------------------------

def _keeps_order(lesson, option, values, seed=1):
    tagged = [Tagged(v, i) for i, v in enumerate(values)]
    data, _, _ = run(lesson, option, tagged, seed)
    groups = {}
    for item in data:
        groups.setdefault(int(item), []).append(item.tag)
    return all(tags == sorted(tags) for tags in groups.values())


@needs_node
@pytest.mark.parametrize('lesson,option', VARIANTS)
def test_stable_flag_matches_behaviour(lesson, option):
    """A lesson that says stable keeps every tie in order on 300 inputs full
    of ties; one that says not stable is shown breaking one."""
    stable = lessons()[lesson]['resolved'][option]['stable']
    rng = random.Random(11)
    inputs = [[rng.randint(1, 4) for _ in range(rng.randint(2, 25))] for _ in range(300)]
    outcomes = [_keeps_order(lesson, option, values, seed)
                for seed, values in enumerate(inputs, 1)]

    if stable:
        assert all(outcomes), '%s %s claims stable but broke a tie' % (lesson, option)
    else:
        assert not all(outcomes), '%s %s claims unstable but never broke a tie' % (lesson, option)


def test_merge_comparison_decides_stability():
    assert not _keeps_order('merge_sort', 'lt', [2, 2, 1])
    assert _keeps_order('merge_sort', 'le', [2, 2, 1])


@pytest.mark.parametrize('lesson,option', VARIANTS)
def test_origins_track_every_value(lesson, option):
    """`origins[k]` is where the value now at k started, on every frame."""
    name = SWITCHES[lesson][0]
    values = [5, 3, 5, 1, 3, 5, 2]
    payload = _sort_payload(name, values, option, 9 if option == 'random' else None)

    for step in payload['steps']:
        assert [values[o] for o in step['origins']] == step['array']
        # Halfway through a merge's copy back a value can sit in two places
        # at once, its new one and its old one. Every other frame holds each
        # starting value exactly once.
        if step['action'] != 'overwrite':
            assert sorted(step['origins']) == list(range(len(values)))


def test_kept_equal_order_reports_the_run():
    assert _sort_payload('Merge Sort', [2, 2, 1], 'lt')['result']['kept_equal_order'] is False
    assert _sort_payload('Merge Sort', [2, 2, 1], 'le')['result']['kept_equal_order'] is True
    assert _sort_payload('Merge Sort', [3, 2, 1], 'lt')['result']['kept_equal_order'] is None


def test_tracked_values_reach_the_page_as_plain_numbers(client):
    body = client.post('/run_sort', json={'algorithm': 'Quick Sort', 'values': '3, 1, 2',
                                          'variant': 'random', 'seed': 4}).get_data(as_text=True)
    data = json.loads(body)
    for step in data['steps']:
        for v in step['array'] + step['values']:
            assert type(v) is int


# ---------------------------------------------------------------------------
# Seeds
# ---------------------------------------------------------------------------

def test_python_generator_matches_the_presets_generator():
    if NODE is None:
        pytest.skip('node is not installed')
    script = ("const P=require('./static/js/presets.js');const r=P.rng(%d);"
              "console.log(JSON.stringify(Array.from({length:50},()=>r())))")
    for seed in (0, 1, 42, 99999, 2 ** 31 - 1):
        out = subprocess.run([NODE, '-e', script % seed], capture_output=True,
                             text=True, check=True, cwd=ROOT)
        rand = mulberry32(seed)
        assert json.loads(out.stdout) == [rand() for _ in range(50)]


def test_same_seed_replays_the_same_run():
    values = [9, 4, 7, 1, 8, 2, 6, 3, 5, 4, 7]
    first = _sort_payload('Quick Sort', values, 'random', 1234)
    again = _sort_payload('Quick Sort', values, 'random', 1234)

    assert first == again
    assert first['seed'] == 1234


def test_different_seeds_make_different_runs():
    values = list(range(1, 31))
    runs = {json.dumps(_sort_payload('Quick Sort', values, 'random', s)['steps']) for s in range(1, 11)}
    assert len(runs) > 1


def test_server_picks_a_seed_and_the_seed_replays_it(client):
    body = client.post('/run_sort', json={'algorithm': 'Quick Sort', 'values': '5, 2, 8, 1, 9, 3',
                                          'variant': 'random'}).get_json()
    seed = body['seed']
    assert isinstance(seed, int) and seed >= 0

    replay = client.post('/run_sort', json={'algorithm': 'Quick Sort', 'values': '5, 2, 8, 1, 9, 3',
                                            'variant': 'random', 'seed': seed}).get_json()
    assert replay['steps'] == body['steps']
    assert replay['result'] == body['result']


@pytest.mark.parametrize('seed', [-1, 2 ** 31, 'abc', '1.5', True])
def test_bad_seeds_are_refused(client, seed):
    response = client.post('/run_sort', json={'algorithm': 'Quick Sort', 'values': '3, 1, 2',
                                              'variant': 'random', 'seed': seed})
    assert response.status_code == 400
    assert 'seed' in response.get_json()['error']


def test_unknown_variant_is_refused(client):
    response = client.post('/run_sort', json={'algorithm': 'Quick Sort', 'values': '3, 1, 2',
                                              'variant': 'median'})
    assert response.status_code == 400
    assert 'last, middle, random' in response.get_json()['error']


def test_a_seed_is_ignored_unless_the_pivot_is_random(client):
    body = client.post('/run_sort', json={'algorithm': 'Quick Sort', 'values': '3, 1, 2',
                                          'variant': 'middle', 'seed': 7}).get_json()
    assert body['seed'] is None


def test_quick_sort_refuses_a_random_pivot_without_a_seed():
    with pytest.raises(ValueError):
        quick_sort([3, 1, 2], lambda *a: None, lambda: None, None, 'random')


def test_form_post_carries_the_variant(client):
    html = client.post('/sorting', data={'algorithm': 'Bubble Sort', 'input_method': 'manual',
                                         'manual_input': '1, 2, 3, 4, 5',
                                         'variant': 'on'}).get_data(as_text=True)
    assert '"variant": "on"' in html
    assert '"comparisons": 4' in html


# ---------------------------------------------------------------------------
# depth and range
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('lesson,option', [v for v in VARIANTS if v[0] != 'bubble_sort'])
@pytest.mark.parametrize('case', sorted(BASELINE['cases']))
def test_depth_and_range_on_every_step(lesson, option, case):
    values = BASELINE['cases'][case]['input']
    n = len(values)
    _, steps, _ = run(lesson, option, values, 3)

    for k, step in enumerate(steps):
        where = '%s %s %s step %d' % (lesson, option, case, k)
        assert isinstance(step.get('depth'), int) and step['depth'] >= 0, where
        lo, hi = step['range']
        if n == 0:
            # An empty list's one frame owns the empty range.
            assert [lo, hi] == [0, -1], where
            continue
        assert 0 <= lo <= hi <= n - 1, where
        for index in step['indices']:
            assert lo <= index <= hi, '%s acts outside its range' % where
        if step['action'] == 'done':
            assert step['depth'] == 0 and step['range'] == [0, n - 1]

    if lesson == 'merge_sort' and n > 1:
        assert max(s['depth'] for s in steps) <= math.ceil(math.log2(n))


def test_depth_follows_the_recursion():
    """Sorted input with the last pivot nests one level per value."""
    _, steps, _ = run('quick_sort', 'last', list(range(1, 9)))
    depths = [s['depth'] for s in steps if s['action'] == 'place']
    assert depths == list(range(7))
    ranges = [s['range'] for s in steps if s['action'] == 'place']
    assert ranges == [[0, 7 - d] for d in range(7)]


def test_bubble_steps_carry_no_recursion_meta():
    _, steps, _ = run('bubble_sort', 'off', [3, 1, 2])
    assert all('depth' not in s for s in steps)


# ---------------------------------------------------------------------------
# Lessons and the switch agree
# ---------------------------------------------------------------------------

@needs_node
@pytest.mark.parametrize('lesson', sorted(SWITCHES))
def test_lesson_variants_match_the_server(lesson):
    name = SWITCHES[lesson][0]
    info = lessons()[lesson]
    server = [opt[0] for opt in SORT_VARIANTS[name]['options']]

    assert list(info['resolved']) == server
    assert info['default'] == server[0]
    assert info['variantKey'] == SORT_VARIANTS[name]['key']


@needs_node
@pytest.mark.parametrize('lesson,option', VARIANTS)
def test_line_ids_exist_in_the_variant_listing(lesson, option):
    code = lessons()[lesson]['resolved'][option]['code']
    _, steps, _ = run(lesson, option, [5, 3, 8, 1, 9, 2, 7, 5], 2)
    emitted = {s['line'] for s in steps if s['line']}

    for view in ('pseudocode', 'python'):
        declared = {line['id'] for line in code[view] if line['id']}
        assert emitted <= declared, (lesson, option, view, emitted - declared)


@needs_node
@pytest.mark.parametrize('mutation,expected', [
    ("variants: {", "variants: { bogus: 1, "),
    ("note: 'Every pass runs to the end, even after the list is sorted.'",
     "note: ''"),
    ("                    divergence: null,\n                    claims: [\n                        { input: 'sorted', comparisons: 'n-1'",
     "                    divergence: null,\n                    claimz: [\n                        { input: 'sorted', comparisons: 'n-1'"),
    ("label: 'Off',", "label: 'Off', stable: false,"),
    ("comparisons: 'n-1', bound: 'exact', where: 'time.best'",
     "comparisons: 'process.exit()', bound: 'exact', where: 'time.best'"),
    ("comparisons: 'n-1', bound: 'exact', where: 'time.best'",
     "comparisons: 'n-1', bound: 'exact', where: 'time.nowhere'"),
])
def test_validator_rejects_a_broken_variants_block(tmp_path, mutation, expected):
    source_dir = os.path.join(ROOT, 'static', 'js', 'lessons')
    for name in os.listdir(source_dir):
        if name.endswith('.js'):
            shutil.copy(os.path.join(source_dir, name), tmp_path / name)
    target = tmp_path / 'bubble_sort.js'
    text = target.read_text(encoding='utf-8')
    assert mutation in text, 'the mutation no longer matches bubble_sort.js'
    target.write_text(text.replace(mutation, expected, 1), encoding='utf-8')

    result = subprocess.run([NODE, os.path.join(ROOT, 'tests', 'validate_lessons.js')],
                            capture_output=True, text=True,
                            env=dict(os.environ, LESSON_DIR=str(tmp_path)))
    assert result.returncode != 0, result.stdout


# ---------------------------------------------------------------------------
# The page
# ---------------------------------------------------------------------------

def test_search_cells_redraw_their_values_every_step():
    """Found in the Phase 9 check: a run the same length as the last one
    kept the old values in the cells, because they were only rebuilt when
    the length changed."""
    html = open(os.path.join(ROOT, 'templates', 'searching.html'), encoding='utf-8').read()
    loop = html[html.index('Array.prototype.forEach.call(row.children'):]
    assert "querySelector('.cell-box').textContent = values[index]" in loop[:1500]


def test_picker_takes_its_own_row_between_768_and_1279():
    """Found in the Phase 9 check: six picks squeezed into one 240px track
    overflowed into the input fields beside them."""
    css = open(os.path.join(ROOT, 'static', 'styles.css'), encoding='utf-8').read()
    block = css[css.index('@media (min-width: 768px) and (max-width: 1279px)'):]
    block = block[:block.index('/* --- Stage')]
    assert '.setup-grid > :first-child { grid-column: 1 / -1; }' in block
    assert 'grid-auto-flow: column' not in block


def test_sorting_page_has_the_switch_and_its_script(client):
    html = client.get('/sorting').get_data(as_text=True)

    assert 'id="variant-host"' in html
    assert 'js/variants.js' in html
    assert html.index('js/variants.js') < html.index('js/teacher.js')
    for spec in SORT_VARIANTS.values():
        for option in spec['options']:
            assert escape(option[1]) in html
