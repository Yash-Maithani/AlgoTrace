"""Phase 16 in a real browser: Predict mode on all three workspaces.

Needs Playwright; see tests/test_browser_phase14.py and requirements-dev.txt.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_helpers import SKIP_REASON, available, page_for

pytestmark = pytest.mark.skipif(not available(), reason=SKIP_REASON)

VALUES = '17, 11, 32, 45, 9'
STEP = "Workspace.current.index"
CARD = '.predict-card'


def index(page):
    return page.evaluate(STEP)


def start_sort(page, algorithm='Bubble Sort', values=VALUES):
    page.click('#algo-picker [data-algorithm="%s"]' % algorithm)
    page.check('#manual-input-choice')
    page.fill('#manual-input', values)
    page.click('#run-button')
    page.wait_for_function('Workspace.current.steps.length > 0')


def predict_on(page):
    page.check('#predict-toggle')


def forward_to_question(page, limit=40):
    for _ in range(limit):
        if page.query_selector(CARD):
            return True
        if page.evaluate("Workspace.current.index >= Workspace.current.steps.length - 1"):
            return False
        page.click('#step-forward')
    return bool(page.query_selector(CARD))


def option_ids(page):
    return page.evaluate("[...document.querySelectorAll('.predict-option')].map(b => b.dataset.option)")


def wrong_option(page):
    q = page.evaluate("""() => {
        const m = Workspace.current.metaAt(Workspace.current.index + 1);
        const after = Workspace.current.metaAt(Workspace.current.index + 2);
        return after.action === 'swap' ? 'yes' : 'no';
    }""")
    return 'no' if q == 'yes' else 'yes'


def right_option(page):
    return 'no' if wrong_option(page) == 'yes' else 'yes'


# ---------------------------------------------------------------------------
# Off by default, on when asked
# ---------------------------------------------------------------------------

def test_predict_is_off_by_default_and_never_interrupts(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    start_sort(page)

    assert page.is_visible('#predict-toggle') and not page.is_checked('#predict-toggle')
    for _ in range(15):
        page.click('#step-forward')
        assert page.query_selector(CARD) is None
    assert index(page) == 15
    assert page.is_hidden('.predict-score')
    page.ctx.close()


def test_the_toggle_is_in_the_control_bar_and_is_labelled(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    assert page.evaluate("!!document.querySelector('.control-bar #predict-toggle')")
    assert page.evaluate("document.querySelector('label.predict-toggle').textContent.trim()") == 'Predict'
    assert page.evaluate("document.getElementById('predict-toggle').closest('label') !== null")
    page.ctx.close()


def test_a_question_holds_the_step_and_is_built_from_the_real_next_step(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    start_sort(page)
    predict_on(page)
    assert forward_to_question(page)
    asked_at = index(page)

    meta = page.evaluate("Workspace.current.metaAt(Workspace.current.index + 1)")
    prompt = page.inner_text('.predict-prompt')
    assert 'Will these two swap?' in prompt
    assert '%s and %s' % tuple(meta['values']) in prompt
    assert option_ids(page) == ['yes', 'no']
    assert page.evaluate("document.activeElement.classList.contains('predict-card')")     # focus is on the card, not an answer
    assert index(page) == asked_at                                                       # the step has not played
    assert page.get_attribute(CARD, 'role') == 'group'
    assert page.get_attribute(CARD, 'aria-labelledby')
    page.ctx.close()


def test_a_right_answer_says_so_shows_the_real_reason_then_plays_the_step(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    start_sort(page)
    predict_on(page)
    assert forward_to_question(page)
    asked_at = index(page)
    choice = right_option(page)
    expected = page.evaluate("Workspace.current.metaAt(Workspace.current.index + 2).explain.beginner")

    page.click('.predict-option[data-option="%s"]' % choice)

    assert index(page) == asked_at + 1
    assert page.query_selector(CARD) is None
    result = page.inner_text('.predict-result')
    assert result.startswith('Correct') and expected in result
    assert page.get_attribute('.predict-result', 'data-correct') == 'true'
    assert page.inner_text('.predict-score') == '1 of 1 correct'
    page.wait_for_function("document.querySelector('.predict-host').previousElementSibling.textContent.startsWith('Correct')")
    # Focus is left on the control that carries on.
    assert page.evaluate("document.activeElement.id") == 'step-forward'
    page.ctx.close()


def test_a_wrong_answer_says_so_and_names_the_right_one(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    start_sort(page)
    predict_on(page)
    assert forward_to_question(page)
    page.click('.predict-option[data-option="%s"]' % wrong_option(page))

    result = page.inner_text('.predict-result')
    assert result.startswith('Not quite') and 'The answer was' in result
    assert page.get_attribute('.predict-result', 'data-correct') == 'false'
    assert page.inner_text('.predict-score') == '0 of 1 correct'
    page.wait_for_function("document.querySelector('.predict-host').previousElementSibling.textContent.startsWith('Not quite')")
    page.ctx.close()


def test_skip_plays_the_step_without_scoring(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    start_sort(page)
    predict_on(page)
    assert forward_to_question(page)
    asked_at = index(page)
    page.click('.predict-skip')

    assert index(page) == asked_at + 1 and page.query_selector(CARD) is None
    assert page.inner_text('.predict-score') == '0 of 0 correct, 1 skipped'
    assert page.query_selector('.predict-result') is None
    page.ctx.close()


def test_the_score_counts_a_whole_run_and_resets_with_a_new_one(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    start_sort(page)
    predict_on(page)
    total = int(page.inner_text('.predict-note').split()[0])
    right = 0
    for n in range(total):
        assert forward_to_question(page)
        choose = right_option(page) if n % 3 else wrong_option(page)
        right += choose == right_option(page)
        page.click('.predict-option[data-option="%s"]' % choose)
    assert page.inner_text('.predict-score') == '%d of %d correct' % (right, total)

    page.click('#run-button')                                        # a new run
    page.wait_for_function('Workspace.current.index === 0')
    assert page.is_hidden('.predict-score')
    assert page.query_selector('.predict-result') is None
    assert forward_to_question(page)                                 # asked again: nothing is remembered
    page.ctx.close()


# ---------------------------------------------------------------------------
# Step back
# ---------------------------------------------------------------------------

def test_step_back_always_works_and_never_reasks_an_answered_question(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    start_sort(page)
    predict_on(page)
    assert forward_to_question(page)
    asked_at = index(page)
    page.click('.predict-option[data-option="%s"]' % right_option(page))
    assert index(page) == asked_at + 1
    page.click('#step-back')
    assert index(page) == asked_at and page.query_selector('.predict-result') is None
    page.click('#step-forward')                                      # over the answered step again
    assert page.query_selector(CARD) is None and index(page) == asked_at + 1
    assert page.inner_text('.predict-score') == '1 of 1 correct'     # and the score did not move
    page.ctx.close()


def test_step_back_with_a_question_open_closes_it_and_it_is_asked_again_on_the_way_forward(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    start_sort(page)
    predict_on(page)
    assert forward_to_question(page)
    asked_at = index(page)
    page.click('#step-back')

    assert page.query_selector(CARD) is None and index(page) == asked_at - 1
    page.click('#step-forward')
    page.click('#step-forward') if page.query_selector(CARD) is None else None
    assert forward_to_question(page) and index(page) == asked_at
    assert page.inner_text('.predict-score') == '' or page.is_hidden('.predict-score')     # unanswered, unscored
    page.ctx.close()


def test_turning_predict_off_closes_the_question(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    start_sort(page)
    predict_on(page)
    assert forward_to_question(page)
    page.uncheck('#predict-toggle')
    assert page.query_selector(CARD) is None
    held = index(page)
    page.click('#step-forward')
    assert index(page) == held + 1 and page.query_selector(CARD) is None
    page.ctx.close()


# ---------------------------------------------------------------------------
# Autoplay waits
# ---------------------------------------------------------------------------

def test_autoplay_waits_for_the_answer_then_carries_on(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    start_sort(page)
    page.evaluate("document.getElementById('speed').value = 190; document.getElementById('speed').dispatchEvent(new Event('input'))")
    predict_on(page)
    page.click('#play-pause')
    page.wait_for_selector(CARD, timeout=5000)
    asked_at = index(page)
    assert page.get_attribute('#play-pause', 'aria-label') == 'Play'          # it stopped
    page.wait_for_timeout(1500)
    assert index(page) == asked_at and page.query_selector(CARD)                # and is still waiting

    page.click('.predict-option[data-option="%s"]' % right_option(page))
    # It carries on by itself, with no further click, to the next question.
    page.wait_for_function("document.querySelector('.predict-kicker') && "
                           "document.querySelector('.predict-kicker').textContent.endsWith('question 2')", timeout=5000)
    assert index(page) > asked_at
    assert page.get_attribute('#play-pause', 'aria-label') == 'Play'          # and waited again
    page.ctx.close()


def test_play_does_not_answer_or_dismiss_a_question(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    start_sort(page)
    predict_on(page)
    assert forward_to_question(page)
    asked_at = index(page)
    page.click('#play-pause')
    page.click('#step-forward')

    assert page.query_selector(CARD) and index(page) == asked_at
    assert page.query_selector('.predict-result') is None
    page.ctx.close()


# ---------------------------------------------------------------------------
# Keyboard
# ---------------------------------------------------------------------------

def test_the_shortcuts_cannot_answer_a_question(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    start_sort(page)
    predict_on(page)
    assert forward_to_question(page)
    asked_at = index(page)

    page.keyboard.press('Space')                  # the play shortcut, with the card focused
    page.keyboard.press('ArrowRight')             # not an answer, not a step
    page.keyboard.press('Escape')
    assert page.query_selector(CARD) and index(page) == asked_at
    assert page.query_selector('.predict-result') is None
    assert page.inner_text('.predict-score') == '' or page.is_hidden('.predict-score')
    page.evaluate("document.activeElement.blur()")
    page.keyboard.press('Space')                  # with nothing focused at all
    assert page.query_selector(CARD) and index(page) == asked_at
    page.ctx.close()


def test_the_question_is_fully_operable_from_the_keyboard(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    start_sort(page)
    predict_on(page)
    page.focus('#step-forward')
    for _ in range(40):
        if page.query_selector(CARD):
            break
        page.keyboard.press('Enter')
    assert page.query_selector(CARD)
    assert page.evaluate("document.activeElement.classList.contains('predict-card')")
    page.keyboard.press('Tab')
    assert page.evaluate("document.activeElement.dataset.option") == 'yes'
    page.keyboard.press('ArrowRight')             # moves between answers, does not step
    assert page.evaluate("document.activeElement.dataset.option") == 'no'
    assert page.query_selector(CARD)
    page.keyboard.press('ArrowLeft')
    assert page.evaluate("document.activeElement.dataset.option") == 'yes'
    page.keyboard.press('Tab'); page.keyboard.press('Tab')
    assert page.evaluate("document.activeElement.className") == 'predict-skip'

    page.focus('.predict-option[data-option="%s"]' % right_option(page))
    page.keyboard.press('Enter')                  # a deliberate Enter on a focused answer
    assert page.query_selector(CARD) is None and page.query_selector('.predict-result')
    page.ctx.close()


def test_the_toggle_works_with_the_keyboard_and_space_on_it_is_not_a_shortcut(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    start_sort(page)
    page.focus('#predict-toggle')
    before = index(page)
    page.keyboard.press('Space')
    assert page.is_checked('#predict-toggle') and index(page) == before        # it toggled, it did not play
    assert page.get_attribute('#play-pause', 'aria-label') == 'Play'
    page.ctx.close()


# ---------------------------------------------------------------------------
# Searching and graphs
# ---------------------------------------------------------------------------

def run_search(page, algo, array, target):
    page.click('#algo-picker [data-algorithm="%s"]' % algo)
    page.fill('#array-input', array)
    page.fill('#target-input', target)
    page.click('#run-button')
    page.wait_for_function('Workspace.current.steps.length > 0')


def answer_truthfully(page):
    truth = page.evaluate("""() => {
        const after = Workspace.current.metaAt(Workspace.current.index + 2);
        return after.action === 'found' ? 'found' : after.action === 'discard'
            ? (after.line === 'go-left' ? 'left' : 'right') : 'onward';
    }""")
    page.click('.predict-option[data-option="%s"]' % truth)
    assert page.get_attribute('.predict-result', 'data-correct') == 'true'
    return truth


@pytest.mark.parametrize('target,expected', [('5', ['left', 'right']), ('42', ['found'])])
def test_binary_search_asks_found_left_or_right(browser, base_url, target, expected):
    page = page_for(browser, base_url, '/searching')
    run_search(page, 'binary_search', '4, 8, 15, 16, 23, 42, 50', target)
    predict_on(page)
    asked = []
    for _ in range(12):
        if not forward_to_question(page):
            break
        assert option_ids(page) == ['found', 'left', 'right']
        prompt = page.inner_text('.predict-prompt')
        assert 'Found it, go left, or go right?' in prompt and 'The target is %s' % target in prompt
        asked.append(answer_truthfully(page))
    assert asked == expected
    page.ctx.close()


def test_linear_search_asks_found_or_keep_looking(browser, base_url):
    page = page_for(browser, base_url, '/searching')
    run_search(page, 'linear_search', '4, 8, 15, 16, 23, 42, 50', '16')
    predict_on(page)
    assert forward_to_question(page)
    assert option_ids(page) == ['found', 'onward']
    page.click('.predict-option[data-option="onward"]')
    assert page.inner_text('.predict-result').startswith('Correct')
    page.ctx.close()


GRAPHS = {
    'unweighted': '5 5\nA B\nA C\nB D\nC E\nD E\nA',
    'weighted': '5 7\nA B 4\nA C 2\nB C 5\nB D 10\nC D 3\nC E 7\nD E 6\nA',
    'edges': '5 7\nA B 4\nA C 2\nB C 5\nB D 10\nC D 3\nC E 7\nD E 6',
}


def graph_run(page, algo):
    """A fixed graph, so the same questions come up on every run."""
    kind = {'bfs': 'unweighted', 'dfs': 'unweighted', 'kruskal': 'edges'}.get(algo, 'weighted')
    page.evaluate("text => { const t = document.getElementById('graph-input'); t.value = text; "
                  "t.dispatchEvent(new Event('input')); }", GRAPHS[kind])
    page.click('#run-button')
    page.wait_for_function('Workspace.current.steps.length > 0', timeout=8000)


@pytest.mark.parametrize('algo,frontier', [('bfs', 'queue'), ('dfs', 'stack'), ('dijkstra', 'unvisited')])
def test_graph_options_are_the_frontier_and_the_answer_is_the_next_visit(browser, base_url, algo, frontier):
    page = page_for(browser, base_url, '/graph?algo=' + algo)
    graph_run(page, algo)
    predict_on(page)
    assert forward_to_question(page, limit=60)
    at = index(page)
    live = page.evaluate("Workspace.current.metaAt(%d).vars['%s'].map(String)" % (at, frontier))
    options = option_ids(page)
    # Listed by name, so the order says nothing about the answer.
    assert options == sorted(list(dict.fromkeys(live)), key=lambda n: [int(t) if t.isdigit() else t for t in __import__('re').split(r'(\d+)', n)]) and len(options) >= 2
    assert 'Which node is visited next?' in page.inner_text('.predict-prompt')
    truth = page.evaluate("String(Workspace.current.metaAt(%d).indices[0])" % (at + 1))
    page.click('.predict-option[data-option="%s"]' % truth)
    assert page.get_attribute('.predict-result', 'data-correct') == 'true'
    assert page.evaluate("Workspace.current.index") == at + 1
    page.ctx.close()


def test_prim_asks_which_node_joins_the_tree(browser, base_url):
    page = page_for(browser, base_url, '/graph?algo=prim')
    graph_run(page, 'prim')
    predict_on(page)
    assert forward_to_question(page, limit=60)
    assert 'Which node joins the tree next?' in page.inner_text('.predict-prompt')
    at = index(page)
    truth = page.evaluate("String(Workspace.current.metaAt(%d).indices[1])" % (at + 1))
    assert truth in option_ids(page)
    page.ctx.close()


def truth(page, fact):
    """What the next step really does, read by the test from the run itself."""
    return page.evaluate(fact)


def test_selection_sort_asks_whether_this_is_the_new_smallest(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    start_sort(page, 'Selection Sort', '5, 3, 8, 1, 9, 2')
    predict_on(page)
    assert 'questions in this run' in page.inner_text('.predict-note')
    assert forward_to_question(page)
    prompt = page.inner_text('.predict-prompt')
    meta = page.evaluate("Workspace.current.metaAt(Workspace.current.index + 1)")
    smallest, candidate = meta['values']
    assert 'Is %s the new smallest value?' % candidate in prompt and 'smallest value so far, %s' % smallest in prompt
    assert option_ids(page) == ['yes', 'no']

    expected = 'yes' if candidate < smallest else 'no'
    page.click('.predict-option[data-option="%s"]' % expected)
    assert page.get_attribute('.predict-result', 'data-correct') == 'true'
    # The whole run can be played through, answering from the data.
    for _ in range(80):
        if forward_to_question(page, limit=40):
            m = page.evaluate("Workspace.current.metaAt(Workspace.current.index + 1)")
            page.click('.predict-option[data-option="%s"]' % ('yes' if m['values'][1] < m['values'][0] else 'no'))
        else:
            break
    total, correct = page.inner_text('.predict-score').split(' correct')[0].split(' of ')
    assert total == correct                                          # every answer taken from the data was right
    page.ctx.close()


def test_merge_sort_asks_which_half_is_written_next_and_names_the_values(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    start_sort(page, 'Merge Sort', '5, 3, 8, 3, 9, 1')
    predict_on(page)
    assert forward_to_question(page)
    meta = page.evaluate("Workspace.current.metaAt(Workspace.current.index + 1)")
    l, r = meta['values']
    assert option_ids(page) == ['left', 'right']
    labels = page.evaluate("[...document.querySelectorAll('.predict-option')].map(b => b.textContent)")
    assert str(l) in labels[0] and str(r) in labels[1]
    assert 'Which value is written next' in page.inner_text('.predict-prompt')
    page.click('.predict-option[data-option="%s"]' % meta['taken'])
    assert page.get_attribute('.predict-result', 'data-correct') == 'true'
    page.ctx.close()


def test_quick_sort_asks_about_the_pivot_the_variant_chose(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    page.click('#algo-picker [data-algorithm="Quick Sort"]')
    page.click('[data-variant-for="Quick Sort"] input[value="middle"]')
    page.check('#manual-input-choice')
    page.fill('#manual-input', '5, 3, 8, 1, 9, 2')
    page.click('#run-button')
    page.wait_for_function('Workspace.current.steps.length > 0')
    predict_on(page)
    assert forward_to_question(page)
    meta = page.evaluate("Workspace.current.metaAt(Workspace.current.index + 1)")
    assert 'with the pivot, %s' % meta['vars']['pivot'] in page.inner_text('.predict-prompt')
    assert meta['vars']['pivot'] == 8                                  # the middle value, not the last (2)
    page.ctx.close()


def test_kruskal_asks_whether_the_edge_is_added_or_makes_a_cycle(browser, base_url):
    page = page_for(browser, base_url, '/graph?algo=kruskal')
    graph_run(page, 'kruskal')
    predict_on(page)
    assert 'questions in this run' in page.inner_text('.predict-note')
    seen = set()
    for _ in range(40):
        if not forward_to_question(page, limit=40):
            break
        assert 'Will it be added, or would it make a cycle?' in page.inner_text('.predict-prompt')
        assert option_ids(page) == ['add', 'cycle']
        after = page.evaluate("Workspace.current.metaAt(Workspace.current.index + 2).action")
        answer = 'add' if after == 'include' else 'cycle'
        page.click('.predict-option[data-option="%s"]' % answer)
        assert page.get_attribute('.predict-result', 'data-correct') == 'true'
        seen.add(answer)
    assert seen == {'add', 'cycle'}
    page.ctx.close()


@pytest.mark.parametrize('algo', ['bellman_ford', 'floyd_warshall'])
def test_the_other_weighted_graph_algorithms_ask_too(browser, base_url, algo):
    page = page_for(browser, base_url, '/graph?algo=' + algo)
    graph_run(page, algo)
    predict_on(page)
    assert forward_to_question(page, limit=80)
    prompt = page.inner_text('.predict-prompt')
    assert ('shorten the distance' if algo == 'bellman_ford' else 'shorter?') in prompt
    after = page.evaluate("Workspace.current.metaAt(Workspace.current.index + 2).action")
    page.click('.predict-option[data-option="%s"]' % ('yes' if after == 'relax' else 'no'))
    assert page.get_attribute('.predict-result', 'data-correct') == 'true'
    page.ctx.close()


def test_the_fallback_note_appears_only_for_a_run_with_nothing_to_ask(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    start_sort(page, 'Bubble Sort', '7')                               # one value: nothing is compared
    predict_on(page)
    assert 'No step in this run can be predicted' in page.inner_text('.predict-note')
    assert 'nothing to predict' not in page.inner_text('body')
    page.ctx.close()


# ---------------------------------------------------------------------------
# Themes, widths, motion
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('scheme', ['light', 'dark'])
@pytest.mark.parametrize('width,height', [(375, 812), (768, 1024), (1440, 900)])
def test_the_question_fits_and_is_usable_at_every_width_in_both_themes(browser, base_url, width, height, scheme):
    page = page_for(browser, base_url, '/sorting', width=width, height=height, scheme=scheme)
    start_sort(page)
    predict_on(page)
    assert forward_to_question(page)
    page.wait_for_timeout(200)

    assert page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth") <= 0
    box = page.evaluate("""() => {
        const r = document.querySelector('.predict-card').getBoundingClientRect();
        const opts = [...document.querySelectorAll('.predict-option, .predict-skip')].map(b => {
            const q = b.getBoundingClientRect(); return [q.width, q.height, q.left, q.right]; });
        return {left: r.left, right: r.right, w: innerWidth, opts};
    }""")
    assert box['left'] >= 0 and box['right'] <= box['w'], box
    for w, h, left, right in box['opts']:
        assert h >= 43 and w >= 40 and left >= 0 and right <= box['w'], box           # touch sized, on screen
    # The card is the thing in view: its question is not scrolled out of sight.
    assert page.evaluate("""() => { const r = document.querySelector('.predict-card').getBoundingClientRect();
                                    return r.top < innerHeight && r.bottom > 0; }""")
    # Colours are not the only signal: answer, then read the verdict as a word.
    page.click('.predict-option[data-option="%s"]' % right_option(page))
    assert page.inner_text('.predict-verdict') == 'Correct'
    page.ctx.close()


def test_the_flow_works_with_reduced_motion(browser, base_url):
    page = page_for(browser, base_url, '/sorting', reduced='reduce')
    assert page.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches")
    start_sort(page)
    predict_on(page)
    assert forward_to_question(page)
    assert page.evaluate("getComputedStyle(document.querySelector('.predict-card')).transitionDuration") == '0s'
    page.click('.predict-option[data-option="%s"]' % right_option(page))
    assert page.query_selector('.predict-result')
    assert page.errors == []
    page.ctx.close()


def test_no_script_errors_across_a_whole_predicted_run(browser, base_url):
    page = page_for(browser, base_url, '/sorting')
    start_sort(page)
    predict_on(page)
    for _ in range(60):
        if page.query_selector(CARD):
            page.click('.predict-option >> nth=0')
        elif index(page) < page.evaluate('Workspace.current.steps.length - 1'):
            page.click('#step-forward')
        else:
            break
    assert index(page) == page.evaluate('Workspace.current.steps.length - 1')
    assert page.errors == []
    page.ctx.close()
