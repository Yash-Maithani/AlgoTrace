"""Phase 19: Jump Search, Counting Sort and Radix Sort.

Every claim the new lessons make is measured here against the real code:
the sorted output, the zero comparisons, the counts of writes and of work,
the worked examples, the Theta of every case, the input rules and their
messages, and the Predict questions built from the real steps. The strips
in a real browser are tests/browser/test_browser_jump_counting_radix.py; the C, C++ and Java
translations are checked step by step in tests/reference/test_reference_code.py.
"""
import json
import math
import os
import random
import re
import shutil
import subprocess
import tempfile

import pytest

from paths import ROOT, JS
from wsgi import app
from algotrace.algorithms.searching.binary_search import binary_search
from algotrace.algorithms.searching.jump_search import jump_search
from algotrace.algorithms.sorting.counting_sort import KEY_MAX
from algotrace.algorithms.sorting.counting_sort import counting_sort
from algotrace.algorithms.sorting.radix_sort import radix_sort
from algotrace.catalog import sorting_algo_dict, SEARCH_ALGORITHMS
from algotrace.routes.searching import SEARCH_ACTIONS
from algotrace.routes.sorting import sort_payload, SORT_ACTIONS, KEYED_SORTS, COMPARE_TRIES
from test_theta_measured import check_growth

NODE = shutil.which('node')
needs_node = pytest.mark.skipif(NODE is None, reason='node is not installed')


@pytest.fixture(scope='module')
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return f.read()


_LESSONS = None


def lessons():
    global _LESSONS
    if _LESSONS is None:
        out = subprocess.run([NODE, os.path.join(JS, 'dump_lessons.js')],
                             capture_output=True, text=True, encoding='utf-8', check=True)
        _LESSONS = json.loads(out.stdout)
    return _LESSONS


def lesson(key):
    return lessons()[key]['resolved']['']


# ---------------------------------------------------------------------------
# Inputs: random, sorted, reversed, all equal, duplicates and edge sizes
# ---------------------------------------------------------------------------

def keyed_inputs():
    rng = random.Random(1919)
    out = [[], [0], [KEY_MAX], [1, 0], [0, 1], [5, 5], [KEY_MAX, 0, KEY_MAX, 0],
           list(range(KEY_MAX + 1)), list(range(KEY_MAX, -1, -1))]
    for n in (2, 5, 13, 30, 64, 100):
        values = [rng.randint(0, KEY_MAX) for _ in range(n)]
        out += [values, sorted(values), sorted(values, reverse=True), [values[0]] * n,
                [rng.randint(0, 3) for _ in range(n)]]
    return out


def run_sort(func, values, **kwargs):
    stats = {'swaps': 0, 'comparisons': 0}
    data = list(values)
    frames = []
    func(data, lambda arr, compared=None, meta=None: frames.append(meta), lambda: None, stats, **kwargs)
    return data, stats, frames


@pytest.mark.parametrize('func', [counting_sort, radix_sort], ids=['counting', 'radix'])
def test_keyed_sorts_match_python_sorted(func):
    for values in keyed_inputs():
        data, stats, _ = run_sort(func, values)
        assert data == sorted(values), values
        assert stats['comparisons'] == 0


@pytest.mark.parametrize('name', sorted(KEYED_SORTS))
def test_the_endpoint_sorts_and_never_compares(client, name):
    for values in keyed_inputs():
        if not values:
            continue
        body = client.post('/run_sort', json={'algorithm': name, 'values': values}).get_json()
        assert body['sorted'] == sorted(values)
        assert body['result']['comparisons'] == 0
        assert all(step['vars']['comparisons'] == 0 for step in body['steps'])
        assert body['steps'][-1]['action'] == 'done'
        assert {s['action'] for s in body['steps']} <= SORT_ACTIONS


def test_jump_search_matches_python_index():
    rng = random.Random(1920)
    lists = [[], [7], [7, 7], [1, 2], list(range(0, 60, 3)), [5] * 30]
    for n in (2, 3, 4, 5, 9, 16, 17, 30, 100):
        lists.append(sorted(rng.randint(-5, 40) for _ in range(n)))
        lists.append(list(range(n)))
    for values in lists:
        for target in sorted(set(values) | {-100, 1000, 0, 2, 41}):
            stats = {'comparisons': 0}
            got = jump_search(values, target, lambda *a: None, None, stats)
            assert got == (values.index(target) if target in values else -1), (values, target)


def test_jump_search_endpoint_refuses_an_unsorted_list(client):
    body = client.post('/run_search', json={'algorithm': 'jump_search',
                                            'array': '9, 2, 5', 'target': 5})
    assert body.status_code == 400
    data = body.get_json()
    assert data['unsorted'] is True and data['sorted_array'] == [2, 5, 9]
    assert data['error'].startswith('Jump search only works on a sorted list')


# ---------------------------------------------------------------------------
# Input rules: whole numbers from 0 to KEY_MAX, said in plain words
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('name', sorted(KEYED_SORTS))
@pytest.mark.parametrize('values,word', [('3, -1, 4', 'negative'), ('3, 100, 4', 'too big'),
                                         ('-7', 'negative'), ('250', 'too big')])
def test_out_of_range_values_are_refused_with_the_range(client, name, values, word):
    response = client.post('/run_sort', json={'algorithm': name, 'values': values})
    assert response.status_code == 400
    error = response.get_json()['error']
    assert 'from 0 to %d' % KEY_MAX in error
    assert word in error


def test_the_form_post_refuses_them_too(client):
    html = client.post('/sorting', data={'algorithm': 'Counting Sort', 'input_method': 'manual',
                                         'manual_input': '4, 120'}).get_data(as_text=True)
    assert 'from 0 to 99 only' in html
    assert 'var initialRun = null' in html


def test_the_other_sorts_still_take_any_whole_number(client):
    body = client.post('/run_sort', json={'algorithm': 'Bubble Sort', 'values': '3, -1, 400'}).get_json()
    assert body['sorted'] == [-1, 3, 400]


@pytest.mark.parametrize('name', sorted(KEYED_SORTS))
def test_a_random_array_stays_in_range(client, name):
    for _ in range(20):
        body = client.post('/run_sort', json={'algorithm': name, 'size': 100}).get_json()
        assert all(0 <= v <= KEY_MAX for v in body['array'])


def test_the_setup_column_states_the_range(client):
    html = client.get('/sorting?algorithm=Counting+Sort').get_data(as_text=True)
    assert 'take whole numbers from 0 to 99 only' in html
    assert 'id="key-range-hint"' in html


@needs_node
def test_every_preset_fits_the_range():
    """The presets draw 1 to 99, so none of them is ever refused."""
    script = ("const P=require('./algotrace/static/js/presets.js');"
              "const out=[];for(const k of P.ORDER)for(let s=1;s<=30;s++)out.push(...P.generate(k,100,s));"
              "console.log(JSON.stringify([Math.min(...out),Math.max(...out)]))")
    lo, hi = json.loads(subprocess.run([NODE, '-e', script], capture_output=True, text=True,
                                       cwd=ROOT, check=True).stdout)
    assert 0 <= lo and hi <= KEY_MAX


@needs_node
def test_presets_offered():
    assert lesson('jump_search')['presets'] == ['sorted', 'equal']
    for key in ('counting_sort', 'radix_sort'):
        assert 'presets' not in lesson(key)          # all five fit the range


# ---------------------------------------------------------------------------
# The step contract
# ---------------------------------------------------------------------------

def test_counting_steps_carry_the_count_list():
    values = [5, 3, 8, 1, 9, 3, 0, 99]
    _, _, frames = run_sort(counting_sort, values)
    tallied = [0] * (KEY_MAX + 1)
    for meta in frames:
        assert len(meta['counts']) == KEY_MAX + 1
        if meta['action'] == 'count':
            v = meta['values'][0]
            tallied[v] += 1
            assert meta['cells'] == [v, v] and meta['counts'] == tallied
            assert meta['line'] == 'tally'
    assert tallied == frames[-1]['counts']
    # The scan frames cover every slot exactly once, in order.
    covered = []
    for meta in frames:
        if meta['line'] == 'scan':
            lo, hi = meta['cells']
            covered += list(range(lo, hi + 1))
            if lo != hi:
                assert all(tallied[v] == 0 for v in range(lo, hi + 1))
    assert covered == list(range(KEY_MAX + 1))


def test_radix_steps_carry_the_buckets():
    values = [21, 12, 5, 40, 12, 99, 0]
    _, _, frames = run_sort(radix_sort, values)
    for meta in frames[:-1]:
        assert len(meta['buckets']) == 10 and meta['place'] in (1, 10)
        if meta['action'] == 'bucket':
            v = meta['values'][0]
            assert meta['bucket'] == v // meta['place'] % 10
            assert meta['buckets'][meta['bucket']][-1] == v
    assert frames[-1]['bucket'] is None


def test_radix_keeps_equal_values_in_order_and_counting_has_no_order_to_keep():
    values = [12, 5, 12, 5, 99, 12]
    radix = sort_payload('Radix Sort', values)
    counting = sort_payload('Counting Sort', values)
    assert radix['result']['kept_equal_order'] is True
    assert counting['result']['kept_equal_order'] is None
    # Radix moves the values themselves, so every frame says where each began.
    for step in radix['steps']:
        assert [values[o] for o in step['origins']] == step['array']
    # Counting rebuilds them: a written cell has no starting position.
    assert counting['steps'][-1]['origins'] == [None] * len(values)


def test_jump_steps_name_the_live_range():
    values = list(range(0, 100, 5))
    frames = []
    jump_search(values, 72, lambda idx, meta: frames.append(meta))
    for meta in frames:
        assert meta['action'] in SEARCH_ACTIONS
        v = meta['vars']
        assert v['block'] == math.isqrt(len(values))
        if meta['line'] == 'scan':
            assert v['high'] == v['end'] and v['low'] <= v['i'] <= v['end']
        elif meta['line'] in ('jump-check', 'jump'):
            assert v['high'] == len(values) - 1


@needs_node
@pytest.mark.parametrize('key,make', [
    ('counting_sort', lambda: [m for m in run_sort(counting_sort, [4, 1, 4, 0])[2]]),
    ('radix_sort', lambda: [m for m in run_sort(radix_sort, [41, 14, 7])[2]]),
])
def test_every_step_line_is_in_the_listing(key, make):
    ids = {line['id'] for line in lesson(key)['code']['python'] if line['id']}
    for meta in make():
        assert meta['line'] is None or meta['line'] in ids


@needs_node
def test_jump_step_lines_are_in_the_listing():
    ids = {line['id'] for line in lesson('jump_search')['code']['python'] if line['id']}
    for target in (0, 30, 31, 95, 200, -3):
        frames = []
        jump_search(list(range(0, 100, 5)), target, lambda idx, meta: frames.append(meta))
        assert all(m['line'] in ids for m in frames)


# ---------------------------------------------------------------------------
# The figures the lessons state
# ---------------------------------------------------------------------------

def ops(func, values, key_max=KEY_MAX):
    stats = {'swaps': 0, 'comparisons': 0}
    func(list(values), lambda *a, **k: None, lambda: None, stats, key_max=key_max)
    return stats


def test_counting_does_2n_plus_k_plus_1_steps_on_every_input():
    for values in keyed_inputs():
        stats = ops(counting_sort, values)
        n = len(values)
        assert stats['operations'] == 2 * n + KEY_MAX + 1
        assert stats['swaps'] == n


def test_radix_does_d_times_2n_plus_10_steps_on_every_input():
    d = len(str(KEY_MAX))
    for values in keyed_inputs():
        stats = ops(radix_sort, values)
        n = len(values)
        assert stats['operations'] == d * (2 * n + 10)
        assert stats['swaps'] == d * n


@needs_node
def test_worked_examples():
    w = lesson('counting_sort')['complexity']['worked']
    values = json.loads(w['input'])
    stats = ops(counting_sort, values)
    assert w['comparisons'] == stats['comparisons'] == 0
    assert '110 steps' in w['note'] and stats['operations'] == 110

    w = lesson('radix_sort')['complexity']['worked']
    stats = ops(radix_sort, json.loads(w['input']))
    assert w['comparisons'] == stats['comparisons'] == 0
    assert '40 in all, 10 writes' in w['note'] and stats['operations'] == 40 and stats['swaps'] == 10

    w = lesson('jump_search')['complexity']['worked']
    values = [4, 8, 15, 16, 23]
    assert w['input'] == '[4, 8, 15, 16, 23], target 23'
    assert search(jump_search, values, 23) == w['comparisons'] == 4
    assert search(jump_search, values, 4) == 2 and 'Target 4 takes 2' in w['note']
    big = list(range(1024))
    assert max(search(jump_search, big, t) for t in range(-1, 1025)) == 64
    assert max(search(binary_search, big, t) for t in range(-1, 1025)) == 11
    assert '64 comparisons, against 1024 for linear search and 11 for binary search' in w['note']


def search(func, values, target):
    stats = {'comparisons': 0}
    func(values, target, lambda *a: None, None, stats)
    return stats['comparisons']


@needs_node
def test_jump_preset_notes_hold():
    for n in range(5, 31):
        equal = [42] * n
        assert search(jump_search, equal, 42) == 2              # presetNotes.equal
        values = list(range(n))
        worst = max(search(jump_search, values, t) for t in range(-1, n + 1))
        assert worst <= 2 * math.isqrt(n) + n // math.isqrt(n)  # about 2 root n
    assert 'found after 2 comparisons' in lesson('jump_search')['presetNotes']['equal']


@needs_node
def test_the_no_comparisons_note_is_there():
    for key in ('counting_sort', 'radix_sort'):
        c = lesson(key)['complexity']
        assert 'stays at 0' in c['countsNote'] and 'n log n' in c['countsNote']
        assert lesson(key)['countLabel'] == 'writes'
        assert c['space']['what']


@needs_node
def test_bounds_per_case():
    j = lesson('jump_search')['complexity']
    assert [j['time'][c]['theta'] for c in ('best', 'average', 'worst')] == \
        ['1', 'square root of n', 'square root of n']
    assert j['overall'] == {'O': 'square root of n', 'Omega': '1', 'Theta': None}
    for key, theta in (('counting_sort', 'n plus k'), ('radix_sort', 'd times (n plus b)')):
        c = lesson(key)['complexity']
        assert all(c['time'][case]['theta'] == theta for case in ('best', 'average', 'worst'))
        assert c['overall'] == {'O': theta, 'Omega': theta, 'Theta': theta}
        assert c['growth'] is None and c['growthNote']


# ---------------------------------------------------------------------------
# Theta, measured
# ---------------------------------------------------------------------------

def keyed_count(func, n, key_max, seed=0):
    rng = random.Random(n * 7 + key_max + seed)
    values = [rng.randint(0, key_max) for _ in range(n)]
    stats = ops(func, values, key_max)
    data = list(values)
    func(data, lambda *a, **k: None, lambda: None, {'swaps': 0, 'comparisons': 0}, key_max=key_max)
    assert data == sorted(values)
    return stats['operations']


@pytest.mark.slow
@pytest.mark.parametrize('case', ['best', 'average', 'worst'])
def test_counting_grows_as_n_plus_k(case):
    """Theta(n + k) in two variables: over a whole grid of n and k the work
    stays between 1 and 2 times n + k, so it is bounded above and below by
    n + k. Then, with both growing together, it tracks n + k more closely
    than a log factor either way. The order of the input does not matter,
    so every case is the same."""
    sizes = [16, 64, 256, 1024, 4096]
    for n in sizes:
        for k in sizes:
            count = keyed_count(counting_sort, n, k, seed=len(case))
            assert n + k <= count <= 2 * (n + k) + 1, (case, n, k, count)
    samples = []
    for n in [64, 128, 256, 512, 1024, 2048]:
        samples.append((keyed_count(counting_sort, n, n), n, 2 * n))
    check_growth('counting %s, n and k grow together' % case, 'n plus k', samples)


@pytest.mark.slow
@pytest.mark.parametrize('case', ['best', 'average', 'worst'])
def test_radix_grows_as_d_times_n_plus_b(case):
    """Theta(d(n + b)): grow n with d fixed, then d (the digits of the key
    range) with n fixed."""
    samples = []
    for n in [64, 128, 256, 512, 1024, 2048]:
        samples.append((keyed_count(radix_sort, n, 99), n, 2 * (n + 10)))
    check_growth('radix %s n grows' % case, 'd times (n plus b)', samples)
    samples = []
    for d in range(2, 8):
        key_max = 10 ** d - 1
        samples.append((keyed_count(radix_sort, 200, key_max), 2 ** d, d * (200 + 10)))
    check_growth('radix %s d grows' % case, 'd times (n plus b)', samples)


@pytest.mark.slow
@pytest.mark.parametrize('case', ['best', 'average', 'worst'])
def test_jump_search_cases_grow_as_their_theta(case):
    theta = {'best': '1', 'average': 'square root of n', 'worst': 'square root of n'}[case]
    samples = []
    for n in [16, 64, 256, 1024, 4096, 16384]:
        values = list(range(0, 2 * n, 2))
        if case == 'best':
            count = search(jump_search, values, values[0])
        elif case == 'average':
            # A stride of 7 shares no factor with the power-of-two block sizes,
            # so the picks land evenly across every position in a block.
            picks = values[::7]
            count = sum(search(jump_search, values, t) for t in picks) / len(picks)
        else:
            count = max(search(jump_search, values, t) for t in (values[-1], values[-2] + 1, 10 ** 9))
        samples.append((count, n, 1.0 if theta == '1' else math.sqrt(n)))
    check_growth('jump %s' % case, theta, samples)


# ---------------------------------------------------------------------------
# Predict: the three new questions, checked against the real steps
# ---------------------------------------------------------------------------

def predict(runs):
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(runs, f)
    try:
        out = subprocess.run([NODE, os.path.join(JS, 'predict_check.js'), f.name],
                             capture_output=True, text=True, encoding='utf-8', check=True)
    finally:
        os.unlink(f.name)
    return json.loads(out.stdout)


def sort_runs(name):
    rng = random.Random(1921)
    runs = []
    for k in range(25):
        values = [rng.randint(0, rng.choice([9, 30, 99])) for _ in range(rng.randint(2, 16))]
        runs.append({'id': '%s|%d' % (name, k), 'family': 'sorting',
                     'metas': sort_payload(name, values)['steps']})
    return runs


@needs_node
def test_counting_question_asks_which_count_goes_up():
    runs = sort_runs('Counting Sort')
    questions = predict(runs)
    seen = 0
    for run in runs:
        for q in questions[run['id']]:
            step = run['metas'][q['step']]
            assert q['kind'] == 'counting-slot'
            assert q['prompt'].endswith('Which count goes up?')
            assert step['action'] == 'count'
            assert q['answer'] == str(step['values'][0]) == str(step['cells'][0])
            ids = [o['id'] for o in q['options']]
            assert len(ids) >= 2 and q['answer'] in ids
            # Every option is a real slot: the value, the position it was read
            # from, or the slot the previous read sent up.
            prev = run['metas'][q['step'] - 1]
            allowed = {step['values'][0], step['indices'][0]}
            if prev['action'] == 'count':
                allowed.add(prev['cells'][0])
            assert {int(i) for i in ids} <= allowed
            assert all(o['label'] == 'count[%s]' % o['id'] for o in q['options'])
            seen += 1
    assert seen > 50


@needs_node
def test_radix_question_asks_which_bucket():
    runs = sort_runs('Radix Sort')
    questions = predict(runs)
    seen = 0
    for run in runs:
        for q in questions[run['id']]:
            step = run['metas'][q['step']]
            assert q['kind'] == 'radix-bucket'
            assert q['prompt'].endswith('Which bucket does this value go into?')
            v, place = step['values'][0], step['place']
            assert q['answer'] == str(v // place % 10) == str(step['bucket'])
            assert ('ones digit' if place == 1 else 'tens digit') in q['prompt']
            assert q['answer'] in [o['id'] for o in q['options']]
            seen += 1
    assert seen > 50


@needs_node
def test_jump_questions_ask_jump_or_scan(client):
    rng = random.Random(1922)
    runs = []
    for k in range(40):
        values = sorted(rng.randint(0, 60) for _ in range(rng.randint(5, 30)))
        target = rng.choice(values + [rng.randint(-5, 70)])
        body = client.post('/run_search', json={'algorithm': 'jump_search', 'array': values,
                                                'target': target}).get_json()
        runs.append({'id': 'jump|%d' % k, 'family': 'searching', 'metas': body['steps']})
    questions = predict(runs)
    kinds = set()
    for run in runs:
        for q in questions[run['id']]:
            asked, after = run['metas'][q['step']], run['metas'][q['step'] + 1]
            kinds.add(q['kind'])
            ids = [o['id'] for o in q['options']]
            assert q['answer'] in ids
            if q['kind'] == 'jump-block':
                assert q['prompt'].endswith('Jump again or scan back?')
                assert asked['line'] == 'jump-check'
                smaller = asked['values'][0] < asked['vars']['target']
                last = asked['vars']['end'] == asked['vars']['n'] - 1
                want = 'scan' if not smaller else ('stop' if last else 'jump')
                assert q['answer'] == want
                assert ('stop' in ids) == last and ('jump' in ids) == (not last)
            else:
                assert q['kind'] == 'jump-scan' and asked['line'] == 'scan'
                v, t = asked['values'][0], asked['vars']['target']
                want = 'found' if v == t else ('onward' if v < t else 'stop')
                assert q['answer'] == want
                assert after['action'] == {'found': 'found', 'onward': 'compare', 'stop': 'missing'}[want]
    assert kinds == {'jump-block', 'jump-scan'}


# ---------------------------------------------------------------------------
# Compare, Learn, Home, Complexity
# ---------------------------------------------------------------------------

def test_compare_offers_both_new_sorts(client):
    html = client.get('/compare').get_data(as_text=True)
    for name in ('Counting Sort', 'Radix Sort'):
        assert html.count('<option value="%s"' % name) == 2
    assert 'js/lessons/counting_sort.js' in html and 'js/lessons/radix_sort.js' in html


def test_compare_banner_falls_back_to_steps():
    js = read('algotrace', 'static', 'js', 'compare.js')
    assert "if (x === 0 || y === 0)" in js
    assert 'steps.length' in js
    assert 'so comparisons cannot say which did less' in js
    assert any(t['left'] in KEYED_SORTS or t['right'] in KEYED_SORTS for t in COMPARE_TRIES)


def test_learn_lists_all_eighteen_in_order(client):
    html = client.get('/learn').get_data(as_text=True)
    order = re.findall(r'class="order-name"[^>]*>([^<]+)</a>', html)
    assert len(order) == 20          # 18 in Phase 19, then Topological Sort and A*
    assert order[:3] == ['Linear Search', 'Binary Search', 'Jump Search']
    assert order[order.index('Heap Sort') + 1:order.index('Heap Sort') + 3] == ['Counting Sort', 'Radix Sort']
    cards = re.findall(r'<h3>([^<]+)</h3>', html)
    for name in ('Jump Search', 'Counting Sort', 'Radix Sort'):
        assert name in cards


@needs_node
def test_learn_cards_quote_the_lessons(client):
    """The cards hold no figure of their own: each slot names its lesson and
    is filled from it (tests/unit/test_learn_and_home.py checks the values)."""
    html = client.get('/learn').get_data(as_text=True)
    for key, name in (('jump_search', 'Jump Search'), ('counting_sort', 'Counting Sort'),
                      ('radix_sort', 'Radix Sort')):
        card = html.split('<h3>%s</h3>' % name, 1)[1].split('</a>', 1)[0]
        for figure in ('best', 'worst', 'space'):
            assert 'data-lesson="%s" data-figure="%s"' % (key, figure) in card


def test_home_tiles_count_the_algorithms(client):
    html = client.get('/').get_data(as_text=True)
    assert '<span class="track-meta">%d algorithms</span>' % len(sorting_algo_dict) in html
    assert '<span class="track-meta">%d algorithms</span>' % len(SEARCH_ALGORITHMS) in html
    assert len(sorting_algo_dict) == 8 and len(SEARCH_ALGORITHMS) == 3


def test_complexity_page_names_the_new_examples(client):
    html = client.get('/big-o').get_data(as_text=True)
    assert '?algorithm=jump_search' in html
    assert '?algorithm=Counting+Sort' in html and '?algorithm=Radix+Sort' in html
    assert 'Counting and radix' in html


def test_searching_page_offers_jump_search(client):
    html = client.get('/searching?algorithm=jump_search').get_data(as_text=True)
    assert 'data-algorithm="jump_search"' in html
    assert re.search(r'data-algorithm="jump_search"\s+data-accent="3"\s+aria-current="true"', html)
    assert 'js/lessons/jump_search.js' in html and 'js/lessons/code/jump_search.js' in html


def test_sorting_page_has_the_strip_inside_the_stage(client):
    html = client.get('/sorting').get_data(as_text=True)
    stage = html.split('id="stage"', 1)[1].split('class="control-bar"', 1)[0]
    assert 'id="sort-strip"' in stage
    assert 'js/sortstrip.js' in html
