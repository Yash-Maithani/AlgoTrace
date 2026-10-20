"""What is actually on screen, not what an attribute says.

The first version of these checks read the `hidden` attribute. It was true
while every algorithm's variant switch and the seed row were visibly on the
page, because `display: flex` on those components overrode the attribute.
So everything here asks the browser whether the element is visible: it has a
box, is not display: none and is not collapsed.

Needs Playwright; see tests/test_browser_phase14.py and requirements-dev.txt.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import SORT_VARIANTS
from browser_helpers import SKIP_REASON, available, page_for

pytestmark = pytest.mark.skipif(not available(), reason=SKIP_REASON)

ALGORITHMS = ['Bubble Sort', 'Selection Sort', 'Insertion Sort', 'Merge Sort', 'Quick Sort', 'Heap Sort']
SWITCHED = sorted(SORT_VARIANTS)                          # the ones with a variant switch


def visible_switches(page, scope=''):
    """The data-variant-for names of every switch you can see, by asking the browser."""
    names = page.evaluate("(scope) => [...document.querySelectorAll(scope + ' [data-variant-for]')]"
                          ".map(e => e.dataset.variantFor)", scope)
    return [n for n in names if page.is_visible('%s [data-variant-for="%s"]' % (scope, n))]


# ---------------------------------------------------------------------------
# One rule for every component
# ---------------------------------------------------------------------------

def test_the_hidden_attribute_hides_whatever_display_the_element_has(browser, base_url):
    """The cause of the bug: a component that sets display beats the browser's own [hidden]."""
    page = page_for(browser, base_url, '/sorting')
    got = page.evaluate("""() => {
        const out = {};
        for (const display of ['flex', 'grid', 'inline-flex', 'block', 'table']) {
            const e = document.createElement('div');
            e.style.display = display;               // inline style: the strongest ordinary rule
            e.hidden = true;
            e.textContent = 'x';
            document.body.appendChild(e);
            out[display] = getComputedStyle(e).display;
            e.remove();
        }
        const f = document.createElement('div'); f.className = 'setup-grid'; f.hidden = true;
        document.body.appendChild(f); out.setupGrid = getComputedStyle(f).display; f.remove();
        return out;
    }""")
    assert all(v == 'none' for v in got.values()), got
    page.ctx.close()


def test_the_rule_is_global_and_the_old_per_component_fixes_are_not_needed():
    css = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'static', 'styles.css'), encoding='utf-8').read()

    assert '[hidden] {\n    display: none !important;\n}' in css.replace('\r\n', '\n')


# ---------------------------------------------------------------------------
# /sorting
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('algorithm', ALGORITHMS)
def test_sorting_shows_only_the_chosen_algorithms_switch(browser, base_url, algorithm):
    page = page_for(browser, base_url, '/sorting')
    page.click('#algo-picker [data-algorithm="%s"]' % algorithm)

    shown = visible_switches(page)
    assert shown == ([algorithm] if algorithm in SWITCHED else []), (algorithm, shown)
    assert page.is_visible('#variant-host') is (algorithm in SWITCHED)
    assert not page.is_visible('#seed-row')                    # the random pivot is not chosen
    page.ctx.close()


def test_sorting_shows_the_seed_only_for_quick_sort_with_the_random_pivot(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    page.click('#algo-picker [data-algorithm="Quick Sort"]')

    for option, expected in (('last', False), ('middle', False), ('random', True), ('last', False)):
        page.click('[data-variant-for="Quick Sort"] input[value="%s"]' % option)
        assert page.is_visible('#seed-row') is expected, option
        assert page.is_visible('#pivot-seed') is expected and page.is_visible('#new-seed') is expected

    # Choosing random, then another algorithm: the seed goes with the pivot.
    page.click('[data-variant-for="Quick Sort"] input[value="random"]')
    assert page.is_visible('#seed-row')
    for other in ALGORITHMS:
        page.click('#algo-picker [data-algorithm="%s"]' % other)
        assert page.is_visible('#seed-row') is (other == 'Quick Sort'), other
    page.ctx.close()


def test_sorting_hides_the_other_switches_after_a_run_and_a_change_of_algorithm(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    page.click('#algo-picker [data-algorithm="Merge Sort"]')
    page.check('#manual-input-choice')
    page.fill('#manual-input', '5, 3, 8, 1')
    page.click('#run-button')
    page.wait_for_function('Workspace.current.steps.length > 0')
    assert visible_switches(page) == ['Merge Sort']
    page.click('#algo-picker [data-algorithm="Heap Sort"]')
    assert visible_switches(page) == [] and not page.is_visible('#variant-host')
    page.ctx.close()


# ---------------------------------------------------------------------------
# /compare, both sides
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('side', ['left', 'right'])
@pytest.mark.parametrize('algorithm', ALGORITHMS)
def test_compare_shows_only_the_chosen_algorithms_switch_on_each_side(browser, base_url, side, algorithm):
    page = page_for(browser, base_url, '/compare')
    scope = '.compare-pick[data-side="%s"]' % side
    page.select_option('#%s-algorithm' % side, algorithm)

    assert visible_switches(page, scope) == ([algorithm] if algorithm in SWITCHED else []), (side, algorithm)
    assert not page.is_visible(scope + ' [data-role="seed-row"]')
    # The other side is not touched by this one's choice.
    other = '.compare-pick[data-side="%s"]' % ('right' if side == 'left' else 'left')
    assert len(visible_switches(page, other)) <= 1
    page.ctx.close()


@pytest.mark.parametrize('side', ['left', 'right'])
def test_compare_shows_the_seed_only_for_the_random_pivot_on_that_side(browser, base_url, side):
    page = page_for(browser, base_url, '/compare')
    scope = '.compare-pick[data-side="%s"]' % side
    other = '.compare-pick[data-side="%s"]' % ('right' if side == 'left' else 'left')
    page.select_option('#%s-algorithm' % side, 'Quick Sort')
    key = page.get_attribute(scope + ' [data-variant-for="Quick Sort"]', 'data-variant-key')

    for option, expected in (('last', False), ('middle', False), ('random', True), ('last', False)):
        page.check('#%s-variant-%s-%s' % (side, key, option))
        assert page.is_visible(scope + ' [data-role="seed-row"]') is expected, option
        assert not page.is_visible(other + ' [data-role="seed-row"]'), 'the seed appeared on the other side'
    page.check('#%s-variant-%s-random' % (side, key))
    page.select_option('#%s-algorithm' % side, 'Merge Sort')
    assert not page.is_visible(scope + ' [data-role="seed-row"]')
    page.ctx.close()


def test_compare_hides_the_seed_note_until_a_random_pivot_run_has_one(browser, base_url):
    page = page_for(browser, base_url, '/compare')
    for side in ('left', 'right'):
        assert not page.is_visible('#compare-%s [data-role="seed-shown"]' % side)
    page.ctx.close()


# ---------------------------------------------------------------------------
# Other things the rule changed, checked as a visitor would see them
# ---------------------------------------------------------------------------

def test_the_empty_message_and_the_stage_swap_places(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    assert page.is_visible('#stage-empty') and not page.is_visible('#array-container')
    page.check('#manual-input-choice')
    page.fill('#manual-input', '5, 3, 8, 1')
    page.click('#run-button')
    page.wait_for_function('Workspace.current.steps.length > 0')
    assert page.is_visible('#array-container') and not page.is_visible('#stage-empty')
    page.ctx.close()


def test_the_manual_and_random_input_fields_swap_places(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    assert page.is_visible('#size-field') and not page.is_visible('#values-field')
    page.check('#manual-input-choice')
    assert page.is_visible('#values-field') and not page.is_visible('#size-field')
    page.ctx.close()


def test_the_call_tree_panel_is_there_only_for_the_recursive_sorts(browser, base_url):
    page = page_for(browser, base_url, '/sorting', width=1440, height=900)
    for algorithm in ALGORITHMS:
        page.click('#algo-picker [data-algorithm="%s"]' % algorithm)
        assert page.is_visible('#call-tree') is (algorithm in ('Merge Sort', 'Quick Sort')), algorithm
    page.ctx.close()


def test_the_home_player_controls_appear_once_the_script_runs(browser, base_url):
    page = page_for(browser, base_url, '/')
    assert page.is_visible('#player-controls') and page.is_visible('.player-play')
    page.ctx.close()
