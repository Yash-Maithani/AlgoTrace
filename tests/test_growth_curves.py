"""The growth chart must agree with the lesson that owns the figure.

Before this, seven of the fifteen lessons named a reference curve they do not
have, and the Complexity tab printed that curve's label as the algorithm's
complexity. Floyd-Warshall is cubic and was described in words, in the This
Run box and in the chart's accessible name as quadratic. Quick sort's worst
case here is quadratic and was described as n log n, which is the one figure
this project exists to correct.

The lesson file is the single source of truth. These tests read the worst
case each lesson states and check the curve it asks to be drawn really has
that shape.
"""
import json
import math
import os
import re
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LESSONS = os.path.join(ROOT, 'static', 'js', 'lessons')
GROWTH = os.path.join(ROOT, 'static', 'js', 'growth.js')


def node_available():
    try:
        subprocess.run(['node', '--version'], capture_output=True, check=True)
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not node_available(), reason='node is needed to read the lesson files')


def load_lessons():
    """Run the lesson files the way a browser does and hand back the registry."""
    script = (
        "global.window = {};"
        "const fs = require('fs'), path = require('path');"
        "const dir = %s;"
        "fs.readdirSync(dir).filter(f => f.endsWith('.js')).sort()"
        "  .forEach(f => eval(fs.readFileSync(path.join(dir, f), 'utf8')));"
        "process.stdout.write(JSON.stringify(global.window.LESSONS));"
    ) % json.dumps(LESSONS)
    out = subprocess.run([sys.executable and 'node', '-e', script],
                         capture_output=True, check=True)
    return json.loads(out.stdout.decode('utf-8'))


LESSON_DATA = load_lessons() if node_available() else {}
NAMES = sorted(LESSON_DATA)


# The shape each reference curve has, as growth.js draws it. Kept here
# independently so a change to growth.js cannot quietly agree with itself.
CURVE_OF = {
    '1': lambda n: 1.0,
    'logn': lambda n: math.log2(n + 1),
    'sqrtn': lambda n: math.sqrt(n),
    'n': lambda n: float(n),
    'nlogn': lambda n: n * math.log2(n + 1),
    'n2': lambda n: float(n * n),
    'n3': lambda n: float(n * n * n),
}

# How a lesson's stated figure maps onto a curve, once the letter standing
# for the input size is set aside. O(V squared) and O(n squared) are the same
# shape; which letter is used is what growthBasis has to declare.
SHAPE = {
    'O(1)': '1',
    'O(log n)': 'logn',
    'O(square root of n)': 'sqrtn',
    'O(n)': 'n',
    'O(n log n)': 'nlogn',
    'O(n squared)': 'n2',
    'O(V squared)': 'n2',
    'O(n cubed)': 'n3',
    'O(V cubed)': 'n3',
    'O(E log E)': 'nlogn',
    'O(E log V)': 'nlogn',
    # Two variables at once. No single curve on an axis of one variable is
    # this figure, so a lesson stating it must draw none.
    'O(V times E)': None,
    'O(n plus k)': None,
    'O(d times (n plus b))': None,
}


def test_every_lesson_was_read():
    assert len(NAMES) == 18, 'expected 18 lessons, read %d' % len(NAMES)


@pytest.mark.parametrize('name', NAMES)
def test_the_curve_has_the_shape_the_lesson_states(name):
    lesson = LESSON_DATA[name]
    worst = lesson['complexity']['time']['worst']['value']

    assert worst in SHAPE, (
        '%s states a worst case this test does not know how to check: %r. '
        'Add it to SHAPE, with the curve it matches or None.' % (name, worst))

    assert lesson['complexity']['growth'] == SHAPE[worst], (
        '%s states %s but asks for the %r curve, which is %s'
        % (name, worst, lesson['complexity']['growth'],
           'a different shape' if SHAPE[worst] else 'not a single curve'))


@pytest.mark.parametrize('name', NAMES)
def test_a_figure_in_another_letter_says_which(name):
    """O(V squared) is drawn as O(n squared), so n has to be explained."""
    lesson = LESSON_DATA[name]
    c = lesson['complexity']
    worst = c['time']['worst']['value']
    if not c['growth']:
        return

    letters = set(re.findall(r'\b([VE])\b', worst))
    if letters:
        assert c['growthBasis'], (
            '%s is written in %s but never says what n stands for'
            % (name, ', '.join(sorted(letters))))
        assert c['growthBasis'].split(',')[0] in letters, (
            '%s says n stands for %r, which is not in %s'
            % (name, c['growthBasis'], worst))
    else:
        assert not c['growthBasis'], (
            '%s is written in n, so it needs no basis' % name)


@pytest.mark.parametrize('name', NAMES)
def test_a_lesson_with_no_curve_says_why(name):
    c = LESSON_DATA[name]['complexity']
    if c['growth']:
        assert not c['growthNote'], '%s has a curve and a note' % name
        return

    assert c['growthNote'], '%s draws no curve and does not say why' % name
    assert c['time']['worst']['value'] in c['growthNote'], (
        '%s does not name its own figure in the note' % name)


@pytest.mark.parametrize('name', NAMES)
def test_the_curve_is_one_growth_js_can_draw(name):
    with open(GROWTH, encoding='utf-8') as fh:
        source = fh.read()
    key = LESSON_DATA[name]['complexity']['growth']
    if key is None:
        return

    assert "'%s':" % key in source, (
        '%s asks for the %r curve, which growth.js does not define'
        % (name, key))


@pytest.mark.parametrize('name', NAMES)
def test_the_drawn_curve_outgrows_the_slower_ones(name):
    """A sanity check on the mapping itself, not just on the strings."""
    key = LESSON_DATA[name]['complexity']['growth']
    if key is None:
        return

    order = ['1', 'logn', 'sqrtn', 'n', 'nlogn', 'n2', 'n3']
    at = order.index(key)
    for slower in order[:at]:
        assert CURVE_OF[key](64) > CURVE_OF[slower](64), (
            '%s: %s should outgrow %s' % (name, key, slower))


def test_the_five_reference_curves_are_still_five():
    """/big-o teaches five. n3 is drawn only when an algorithm has it."""
    with open(GROWTH, encoding='utf-8') as fh:
        source = fh.read()

    order = re.search(r'var ORDER = \[(.*?)\];', source, re.S).group(1)
    keys = re.findall(r"'([^']+)'", order)

    assert keys == ['1', 'logn', 'n', 'nlogn', 'n2'], keys
    assert "'n3'" in source, 'the cubic curve is gone'
    assert "'n3'" not in order, (
        'n3 is in the reference set, so /big-o would draw six curves '
        'while its copy says five')


def test_the_panel_prints_the_lesson_figure_not_the_curve_label():
    """What the Complexity tab shows has to come from the lesson."""
    with open(os.path.join(ROOT, 'static', 'js', 'teacher.js'), encoding='utf-8') as fh:
        teacher = fh.read()

    assert 'label: c.time.worst.value' in teacher, (
        'the chart caption is not reading the lesson figure')
    assert "row(c.time.worst.value + ' at '" in teacher, (
        'the This Run row is not reading the lesson figure')
    assert 'curve.label' not in teacher, (
        'teacher.js still prints a curve label as the complexity')
