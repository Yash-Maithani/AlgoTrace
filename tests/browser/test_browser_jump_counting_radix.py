"""Phase 19 in a real browser: the count list and bucket strips under the bars,
Jump Search on the searching stage, Predict on the new questions, and Compare
with a side that makes no comparisons.

Needs Playwright (requirements-dev.txt); skips with a warning without it.
Marked slow through tests/conftest.py, like every browser test.
"""

import pytest

from browser_helpers import SKIP_REASON, available, page_for
from wsgi import app

pytestmark = pytest.mark.skipif(not available(), reason=SKIP_REASON)

COUNTING_VALUES = '5, 3, 8, 1, 9, 3, 12, 0, 47, 99, 47'
RADIX_VALUES = '21, 12, 5, 40, 12, 99, 0, 35, 71, 18, 64, 23'


def run_sort(page, algorithm, values):
    page.goto(page.url.split('/sorting')[0] + '/sorting?algorithm=' + algorithm.replace(' ', '+'))
    page.check('#manual-input-choice')
    page.fill('#manual-input', values)
    page.click('#run-button')
    page.wait_for_function('Workspace.current.steps.length > 0')


def geometry(page):
    """Where the stage, the strip, the bars and the control bar sit."""
    return page.evaluate("""() => {
        const box = el => el.getBoundingClientRect();
        const stage = document.getElementById('stage');
        const strip = document.getElementById('sort-strip');
        const bars = [...document.querySelectorAll('#array-container .bar')];
        return {
            scroll: document.documentElement.scrollWidth - document.documentElement.clientWidth,
            stage: box(stage).toJSON(),
            strip: strip.hidden ? null : box(strip).toJSON(),
            barsTop: Math.min(...bars.map(b => box(b).top)),
            barsBottom: Math.max(...bars.map(b => box(b).bottom)),
            container: box(document.getElementById('array-container')).toJSON(),
            controlTop: box(document.querySelector('.control-bar')).top,
            nextToStage: stage.nextElementSibling.classList.contains('control-bar')
        };
    }""")


# ---------------------------------------------------------------------------
# The strips, at every width and in both themes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('width', [375, 768, 1440])
@pytest.mark.parametrize('scheme', ['light', 'dark'])
@pytest.mark.parametrize('algorithm,values,at', [('Counting Sort', COUNTING_VALUES, 9),
                                                 ('Radix Sort', RADIX_VALUES, 10)])
def test_strip_layout(browser, base_url, width, scheme, algorithm, values, at):
    page = page_for(browser, base_url, '/sorting', width=width, scheme=scheme)
    run_sort(page, algorithm, values)
    page.evaluate('n => Workspace.current.go(n)', at)
    g = geometry(page)
    assert g['scroll'] <= 0, 'the page scrolls sideways at %d' % width
    assert g['strip'], 'the strip is hidden'
    # Under the bars, inside the stage, and the control bar still right below it.
    assert g['strip']['top'] >= g['barsBottom']
    assert g['stage']['top'] <= g['strip']['top'] and g['strip']['bottom'] <= g['stage']['bottom'] + 1
    assert g['nextToStage'] and g['controlTop'] >= g['stage']['bottom'] - 1
    # No bar is clipped: the tallest (99, 297px) fits inside its container.
    assert g['barsTop'] >= g['container']['top'] - 0.5
    assert page.errors == []
    page.ctx.close()


def test_count_list_follows_the_steps(browser, base_url):
    page = page_for(browser, base_url, '/sorting', width=1440)
    run_sort(page, 'Counting Sort', COUNTING_VALUES)
    page.evaluate('Workspace.current.go(9)')        # the tenth tally: 99
    state = page.evaluate("""() => {
        const cells = [...document.querySelectorAll('#sort-strip .count-cell')];
        return {n: cells.length,
                active: cells.map((c, v) => c.dataset.state === 'active' ? v : -1).filter(v => v >= 0),
                three: cells[3].querySelector('.count-value').textContent,
                title: document.querySelector('#sort-strip [data-part="strip-title"]').textContent,
                visible: (() => { const s = document.getElementById('sort-strip').getBoundingClientRect();
                                  const c = cells[99].getBoundingClientRect();
                                  return c.top >= s.top && c.bottom <= s.bottom; })()};
    }""")
    assert state == {'n': 100, 'active': [99], 'three': '2', 'title': 'Count list', 'visible': True}
    # Step back: the count goes back down.
    page.click('#step-back')
    assert page.evaluate("document.querySelectorAll('#sort-strip .count-cell')[99]"
                         ".querySelector('.count-value').textContent") == '0'
    page.ctx.close()


def test_buckets_follow_the_steps(browser, base_url):
    page = page_for(browser, base_url, '/sorting', width=1440)
    run_sort(page, 'Radix Sort', RADIX_VALUES)
    page.evaluate('Workspace.current.go(3)')        # 40 dealt by its ones digit
    state = page.evaluate("""() => {
        const cols = [...document.querySelectorAll('#sort-strip .bucket')];
        return {n: cols.length,
                active: cols.map((c, d) => c.dataset.state === 'active' ? d : -1).filter(d => d >= 0),
                zero: [...cols[0].querySelectorAll('.bucket-chip')].map(c => c.textContent),
                two: [...cols[2].querySelectorAll('.bucket-chip')].map(c => c.textContent),
                title: document.querySelector('#sort-strip [data-part="strip-title"]').textContent};
    }""")
    assert state == {'n': 10, 'active': [0], 'zero': ['40'], 'two': ['12'],
                     'title': 'Buckets, by the ones digit'}
    page.evaluate('Workspace.current.go(Workspace.current.steps.length - 2)')
    assert page.evaluate("document.querySelector('#sort-strip [data-part=\"strip-title\"]').textContent") \
        == 'Buckets, by the tens digit'
    page.ctx.close()


def test_strip_hides_for_the_other_sorts_and_on_switch(browser, base_url):
    page = page_for(browser, base_url, '/sorting', width=1440)
    run_sort(page, 'Counting Sort', COUNTING_VALUES)
    page.evaluate('Workspace.current.go(3)')
    assert page.is_visible('#sort-strip')
    page.click('[data-algorithm="Bubble Sort"]')
    assert not page.is_visible('#sort-strip')
    assert not page.evaluate("document.getElementById('stage').classList.contains('has-strip')")
    run_sort(page, 'Bubble Sort', '5, 3, 8')
    page.evaluate('Workspace.current.go(1)')
    assert not page.is_visible('#sort-strip')
    assert not page.is_visible('#key-range-hint')
    page.ctx.close()


def test_out_of_range_input_is_refused_on_the_page(browser, base_url):
    page = page_for(browser, base_url, '/sorting?algorithm=Radix+Sort', width=768)
    assert page.is_visible('#key-range-hint')
    page.check('#manual-input-choice')
    page.fill('#manual-input', '4, 120, 7')
    page.click('#run-button')
    page.wait_for_function("document.getElementById('setup-error').textContent.length > 0")
    error = page.text_content('#setup-error')
    assert 'from 0 to 99 only' in error and '120 is too big' in error
    assert page.evaluate("Workspace.current.steps.length") == 0
    page.ctx.close()


def test_reduced_motion_keeps_the_strip_still_but_coloured(browser, base_url):
    page = page_for(browser, base_url, '/sorting', width=1440, reduced='reduce')
    run_sort(page, 'Counting Sort', COUNTING_VALUES)
    page.evaluate('Workspace.current.go(9)')
    style = page.evaluate("""() => {
        const cell = document.querySelectorAll('#sort-strip .count-cell')[99];
        const cs = getComputedStyle(cell);
        return {transition: cs.transitionDuration, border: cs.borderTopColor, state: cell.dataset.state};
    }""")
    assert all(float(t.rstrip('s')) == 0 for t in style['transition'].split(','))
    assert style['state'] == 'active' and style['border'] != 'rgba(0, 0, 0, 0)'
    moving = page_for(browser, base_url, '/sorting', width=1440)
    run_sort(moving, 'Counting Sort', COUNTING_VALUES)
    moving.evaluate('Workspace.current.go(2)')
    assert moving.evaluate("getComputedStyle(document.querySelector('#sort-strip .count-cell'))"
                           ".transitionDuration") != '0s'
    page.ctx.close()
    moving.ctx.close()


# ---------------------------------------------------------------------------
# Jump Search
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('width', [375, 768, 1440])
@pytest.mark.parametrize('scheme', ['light', 'dark'])
def test_jump_search_stage(browser, base_url, width, scheme):
    page = page_for(browser, base_url, '/searching?algorithm=jump_search', width=width, scheme=scheme)
    page.fill('#array-input', '2, 5, 8, 12, 16, 23, 38, 42, 56, 72, 81, 90, 95, 99')
    page.fill('#target-input', '81')
    page.click('#run-button')
    page.wait_for_function('Workspace.current.steps.length > 0')
    page.evaluate('Workspace.current.go(4)')        # the third block end, position 8
    state = page.evaluate("""() => {
        const cells = [...document.querySelectorAll('#cell-row .cell')];
        return {scroll: document.documentElement.scrollWidth - document.documentElement.clientWidth,
                states: cells.map(c => c.dataset.state),
                pointers: cells.map(c => c.querySelector('.cell-pointers').textContent)};
    }""")
    assert state['scroll'] <= 0
    assert state['states'][:6] == ['discarded'] * 6
    assert state['pointers'][6] == 'low' and state['pointers'][8] == 'end' and state['pointers'][13] == 'high'
    page.evaluate('Workspace.current.go(Workspace.current.steps.length - 1)')
    with app.test_client() as c:
        result = c.post('/run_search', json={'algorithm': 'jump_search', 'target': 81,
                                             'array': '2, 5, 8, 12, 16, 23, 38, 42, 56, 72, 81, 90, 95, 99'}
                        ).get_json()['result']
    assert result == {'found': True, 'index': 10, 'comparisons': 6}
    assert page.text_content('#run-banner') == 'Found 81 at index 10 after 6 comparisons.'
    assert page.errors == []
    page.ctx.close()


def test_jump_search_offers_sort_it_for_me(browser, base_url):
    page = page_for(browser, base_url, '/searching?algorithm=jump_search', width=768)
    page.fill('#array-input', '9, 2, 5')
    page.fill('#target-input', '5')
    page.click('#run-button')
    page.wait_for_selector('#array-error button')
    page.click('#array-error button')
    page.wait_for_function('Workspace.current.steps.length > 0')
    assert page.input_value('#array-input') == '2, 5, 9'
    page.ctx.close()


# ---------------------------------------------------------------------------
# Predict and Compare
# ---------------------------------------------------------------------------

def test_predict_asks_which_count_goes_up(browser, base_url):
    page = page_for(browser, base_url, '/sorting', width=1440)
    run_sort(page, 'Counting Sort', '4, 7, 2')
    questions = page.evaluate("""() => Predict.questionsFor('sorting', Workspace.current.steps)""")
    assert [q['kind'] for q in questions] == ['counting-slot', 'counting-slot']
    assert questions[0]['prompt'] == 'Next the sort reads position 1, which holds 7. Which count goes up?'
    assert questions[0]['answer'] == '7'
    page.ctx.close()


def test_compare_counts_steps_when_a_side_never_compares(browser, base_url):
    page = page_for(browser, base_url, '/compare', width=1440)
    page.select_option('#left-algorithm', 'Counting Sort')
    page.select_option('#right-algorithm', 'Merge Sort')
    page.check('#manual-input-choice')
    page.fill('#manual-input', '42, 17, 93, 8, 61, 29, 75, 36, 17, 50, 3, 88')
    page.click('#run-button')
    page.wait_for_function('Compare.left.ws.steps.length > 0 && Compare.right.ws.steps.length > 0')
    page.evaluate('Compare.group.go(Compare.group.length() - 1)')
    text = page.text_content('#run-banner')
    with app.test_client() as c:
        a = c.post('/run_sort', json={'algorithm': 'Counting Sort', 'values': '42, 17, 93, 8, 61, 29, 75, 36, 17, 50, 3, 88'}).get_json()
        b = c.post('/run_sort', json={'algorithm': 'Merge Sort', 'values': '42, 17, 93, 8, 61, 29, 75, 36, 17, 50, 3, 88'}).get_json()
    few, many = sorted([len(a['steps']), len(b['steps'])])
    assert text.startswith('Counting Sort never compares two values, so comparisons cannot say which did less.')
    assert 'compares the total steps' in text
    assert '%d against %d' % (few, many) in text
    assert 'Merge Sort (Merge comparison: left < right) made %d comparisons' % b['result']['comparisons'] in text \
        or 'made %d comparisons' % b['result']['comparisons'] in text
    assert page.text_content('#compare-left [data-role="second-label"]') == 'Writes'
    assert page.text_content('#compare-left [data-role="comparisons"]') == '0'
    page.ctx.close()


def test_compare_with_two_ordinary_sorts_still_counts_comparisons(browser, base_url):
    page = page_for(browser, base_url, '/compare', width=1440)
    page.check('#manual-input-choice')
    page.fill('#manual-input', '5, 3, 8, 1, 9')
    page.click('#run-button')
    page.wait_for_function('Compare.left.ws.steps.length > 0 && Compare.right.ws.steps.length > 0')
    page.evaluate('Compare.group.go(Compare.group.length() - 1)')
    text = page.text_content('#run-banner')
    assert 'comparisons cannot say' not in text and 'fewer comparisons' in text
    page.ctx.close()


def test_compare_never_refuses_a_generated_or_preset_array(browser, base_url):
    """Phase 20 Step 0: Radix or Counting on either side, random arrays and
    every preset, nothing refused."""
    page = page_for(browser, base_url, '/compare', width=1440)
    for left, right in (('Radix Sort', 'Bubble Sort'), ('Quick Sort', 'Counting Sort'),
                        ('Counting Sort', 'Radix Sort')):
        page.select_option('#left-algorithm', left)
        page.select_option('#right-algorithm', right)
        for _ in range(3):
            page.check('#random-input')
            page.evaluate("document.getElementById('array-size').value = '100'")
            page.evaluate('Compare.run()')
            assert page.text_content('#setup-error').strip() == ''
            assert page.evaluate('Compare.left.ws.steps.length > 0 && Compare.right.ws.steps.length > 0')
        for preset in ('random', 'sorted', 'reversed', 'equal', 'nearly'):
            page.check('#random-input')
            page.evaluate("document.getElementById('array-size').value = '60'")
            page.click('#preset-host [data-preset="%s"]' % preset)
            page.evaluate('Compare.run()')
            assert page.text_content('#setup-error').strip() == '', (left, right, preset)
            assert page.evaluate('Compare.left.ws.steps.length > 0 && Compare.right.ws.steps.length > 0')
    assert page.errors == []
    page.ctx.close()
