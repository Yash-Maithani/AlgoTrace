"""Phase 15 in a real browser: the Home player.

Needs Playwright; see tests/test_browser_phase14.py and requirements-dev.txt.
Reduced motion is emulated with the browser's own media emulation.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_helpers import SKIP_REASON, available, page_for

pytestmark = pytest.mark.skipif(not available(), reason=SKIP_REASON)

DATA = "JSON.parse(document.getElementById('player-data').textContent)"
STATUS = "document.querySelector('.player-status').textContent"


def bring_into_view(page):
    page.evaluate("document.getElementById('player').scrollIntoView({block: 'center'})")


def current_index(page):
    return int(page.evaluate(STATUS).split()[1]) - 1


def cells(page):
    return page.evaluate("[...document.querySelectorAll('#player-track .band-cell')]"
                         ".sort((a, b) => a.style.getPropertyValue('--pos') - b.style.getPropertyValue('--pos'))"
                         ".map(c => c.textContent)")


# ---------------------------------------------------------------------------
# Starts and stops with the viewport
# ---------------------------------------------------------------------------

def test_it_waits_off_screen_plays_in_view_and_pauses_when_scrolled_away(browser, base_url):
    # A short window, so the section starts well below the fold.
    page = page_for(browser, base_url, '/', height=560)
    page.evaluate("window.scrollTo(0, 0)")
    start = current_index(page)
    page.wait_for_timeout(1800)
    assert current_index(page) == start                       # not in view, not playing
    assert page.inner_text('.player-play') == 'Play'

    bring_into_view(page)
    page.wait_for_function("document.querySelector('.player-play').textContent === 'Pause'", timeout=3000)
    page.wait_for_timeout(3300)
    assert current_index(page) > start                        # it moved on its own

    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_function("document.querySelector('.player-play').textContent === 'Play'", timeout=3000)
    held = current_index(page)
    page.wait_for_timeout(2000)
    assert current_index(page) == held                         # and stopped
    page.ctx.close()


def test_the_visitors_pause_survives_scrolling_away_and_back(browser, base_url):
    page = page_for(browser, base_url, '/')
    bring_into_view(page)
    page.wait_for_function("document.querySelector('.player-play').textContent === 'Pause'", timeout=3000)
    page.click('.player-play')
    held = current_index(page)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(400)
    bring_into_view(page)
    page.wait_for_timeout(2200)
    assert page.inner_text('.player-play') == 'Play' and current_index(page) == held
    page.click('.player-play')                                # Play resumes it
    page.wait_for_function("document.querySelector('.player-play').textContent === 'Pause'")
    page.ctx.close()


# ---------------------------------------------------------------------------
# The four cards change together, on every step
# ---------------------------------------------------------------------------

def test_every_step_changes_stage_explain_code_and_cost_together(browser, base_url):
    page = page_for(browser, base_url, '/')
    bring_into_view(page)
    page.click('.player-step')                                  # takes control: no autoplay while we check
    data = page.evaluate(DATA)
    # Start from the first step.
    for _ in range(len(data['steps'])):
        if current_index(page) == 0:
            break
        page.click('.player-step')

    for i, step in enumerate(data['steps']):
        assert current_index(page) == i
        assert page.inner_text('#player-explain') == step['explain']['beginner']
        assert page.inner_text('#player-why') == step['explain']['why']
        assert page.inner_text('#player-cost').replace('\n', ' ') == '%d of %d comparisons' % (step['comparisons'], data['total'])
        assert page.inner_text('#player-swaps') == str(step['swaps'])
        assert cells(page) == [str(v) for v in step['array']]
        state = page.evaluate("[...document.querySelectorAll('#player-track .band-cell')].map(c => c.className)")
        if step['action'] == 'done':
            assert all('is-sorted' in c for c in state)
        marks = page.evaluate("document.querySelectorAll('.band-code mark').length")
        assert marks == (1 if step['line'] == 'compare' else 0 if step['line'] != 'swap' else 1)   # Python: one line each
        page.click('.player-step')
    assert current_index(page) == 0                              # Step wraps after the last one
    assert page.errors == []
    page.ctx.close()


def test_the_code_card_uses_the_saved_language_and_lights_all_lines_of_the_statement(browser, base_url):
    page = page_for(browser, base_url, '/')
    page.evaluate("CodeView.setLanguage('java')")
    page.wait_for_timeout(150)
    bring_into_view(page)
    page.click('.player-step')
    data = page.evaluate(DATA)
    swap_at = next(i for i, s in enumerate(data['steps']) if s['action'] == 'swap')
    while current_index(page) != swap_at:
        page.click('.player-step')
    lit = page.evaluate("[...document.querySelectorAll('.band-code mark')].map(m => m.textContent.trim())")
    assert len(lit) == 3 and lit[0].startswith('int t = '), lit

    compare_at = next(i for i, s in enumerate(data['steps']) if s['action'] == 'compare')
    while current_index(page) != compare_at:
        page.click('.player-step')
    assert page.evaluate("document.querySelectorAll('.band-code mark').length") == 1
    # The language is the one chosen elsewhere on the site, and it is remembered.
    assert page.evaluate("localStorage.getItem('pbl2.codeLanguage')") == 'java'
    page.evaluate("CodeView.setLanguage('python')")
    page.ctx.close()


# ---------------------------------------------------------------------------
# Motion
# ---------------------------------------------------------------------------

def test_a_swapped_pair_slides_by_transform_only(browser, base_url):
    page = page_for(browser, base_url, '/', reduced='no-preference')
    bring_into_view(page)
    page.click('.player-step')
    data = page.evaluate(DATA)
    # Go to the step just before the first swap, then take it.
    swap_at = next(i for i, s in enumerate(data['steps']) if s['action'] == 'swap')
    while current_index(page) != swap_at - 1:
        page.click('.player-step')
    page.wait_for_timeout(150)          # a wrap back to the start settles over two frames

    probe = page.evaluate("""() => new Promise(resolve => {
        const cells = [...document.querySelectorAll('#player-track .band-cell')];
        const left = c => getComputedStyle(c).left + '|' + getComputedStyle(c).top + '|' + getComputedStyle(c).width;
        const before = cells.map(left);
        const x = c => new DOMMatrixReadOnly(getComputedStyle(c).transform);
        const startX = cells.map(c => x(c).m41);
        document.querySelector('.player-step').click();
        const samples = [];
        const tick = () => {
            samples.push(cells.map(c => [x(c).m41, x(c).m42]));
            if (samples.length < 14) setTimeout(tick, 30); else finish();
        };
        const finish = () => { const endX = cells.map(c => x(c).m41); resolve({
            sameBox: JSON.stringify(before) === JSON.stringify(cells.map(left)),
            properties: getComputedStyle(cells[0]).transitionProperty,
            duration: getComputedStyle(cells[0]).transitionDuration,
            startX, endX,
            lifted: samples.some(s => s.some(([, y]) => Math.abs(y) > 2)),
            inBetween: samples.some(s => s.some(([px], i) => px > Math.min(startX[i], endX[i]) + 1 && px < Math.max(startX[i], endX[i]) - 1)),
        }); };
        tick();
    })""")
    assert probe['sameBox'], 'left, top and width must not change'
    assert probe['properties'].startswith('transform')
    assert probe['duration'].startswith('0.32s')
    assert probe['startX'] != probe['endX']
    assert probe['lifted'], 'the pair should pass over and under each other'
    assert probe['inBetween'], 'the cells should be seen between their two places'
    page.ctx.close()


def test_reduced_motion_freezes_the_step_and_step_still_works(browser, base_url):
    page = page_for(browser, base_url, '/', reduced='reduce')
    assert page.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches")
    data = page.evaluate(DATA)
    served = data['steps'][data['frozen']]

    # The frozen step it was served on, and nothing plays even in view.
    assert current_index(page) == data['frozen']
    bring_into_view(page)
    page.wait_for_timeout(3200)
    assert current_index(page) == data['frozen']
    assert page.inner_text('#player-explain') == served['explain']['beginner']
    assert page.is_hidden('.player-play')                      # there is no autoplay to start or stop
    assert page.evaluate("getComputedStyle(document.querySelector('#player-track .band-cell')).transitionDuration") == '0s'

    page.click('.player-step')
    assert current_index(page) == data['frozen'] + 1
    assert page.inner_text('#player-explain') == data['steps'][data['frozen'] + 1]['explain']['beginner']
    assert cells(page) == [str(v) for v in data['steps'][data['frozen'] + 1]['array']]
    # Nothing is mid-slide: the cell is already where the step says.
    moving = page.evaluate("""() => {
        const c = document.querySelector('#player-track .band-cell');
        return getComputedStyle(c).transitionDuration;
    }""")
    assert moving == '0s'
    for _ in range(len(data['steps'])):
        page.click('.player-step')
    assert page.errors == []
    page.ctx.close()


def test_turning_reduced_motion_on_while_playing_stops_it(browser, base_url):
    page = page_for(browser, base_url, '/', reduced='no-preference')
    bring_into_view(page)
    page.wait_for_function("document.querySelector('.player-play').textContent === 'Pause'", timeout=3000)
    page.emulate_media(reduced_motion='reduce')
    page.wait_for_timeout(300)
    data = page.evaluate(DATA)
    assert current_index(page) == data['frozen']
    page.wait_for_timeout(2000)
    assert current_index(page) == data['frozen']
    page.ctx.close()


# ---------------------------------------------------------------------------
# Keyboard and screen readers
# ---------------------------------------------------------------------------

def test_the_buttons_work_from_the_keyboard(browser, base_url):
    page = page_for(browser, base_url, '/')
    bring_into_view(page)
    page.wait_for_function("document.querySelector('.player-play').textContent === 'Pause'", timeout=3000)
    page.focus('.player-play')
    page.keyboard.press('Enter')                                # pause
    assert page.inner_text('.player-play') == 'Play'
    held = current_index(page)
    page.keyboard.press('Tab')
    assert page.evaluate("document.activeElement.className").find('player-step') != -1
    page.keyboard.press('Space')                                # step
    assert current_index(page) == (held + 1) % 16
    page.keyboard.press('Enter')
    assert current_index(page) == (held + 2) % 16
    assert page.get_attribute('.player-play', 'aria-label') in ('Play the bubble sort', 'Pause the bubble sort')
    assert page.get_attribute('#player-explain', 'aria-live') == 'polite'
    assert page.get_attribute('#player-stage', 'aria-hidden') == 'true'    # the sentence narrates it
    page.ctx.close()


# ---------------------------------------------------------------------------
# Width and theme
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('scheme', ['light', 'dark'])
@pytest.mark.parametrize('width,height', [(375, 812), (768, 1024), (1440, 900)])
def test_the_player_fits_at_every_width_in_both_themes(browser, base_url, width, height, scheme):
    page = page_for(browser, base_url, '/', width=width, height=height, scheme=scheme)
    bring_into_view(page)
    page.click('.player-step')
    page.wait_for_timeout(500)

    assert page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth") <= 0
    box = page.evaluate("""() => {
        const s = document.getElementById('player-stage').getBoundingClientRect();
        const cs = [...document.querySelectorAll('#player-track .band-cell')].map(c => c.getBoundingClientRect());
        return {left: s.left, right: s.right, cells: cs.map(r => [r.left, r.right, r.width, r.height]), w: innerWidth};
    }""")
    assert all(c[0] >= box['left'] and c[1] <= box['right'] for c in box['cells']), box
    assert all(c[2] >= 40 and c[3] >= 40 for c in box['cells'])        # still a touch-sized target
    # Controls are visible and big enough to press.
    for selector in ('.player-play', '.player-step'):
        r = page.evaluate("(() => { const r = document.querySelector('%s').getBoundingClientRect(); return [r.width, r.height]; })()" % selector)
        assert r[1] >= 32 and r[0] > 40, (selector, r)
    # The three cards are readable: none of the sentences is clipped.
    assert page.evaluate("document.getElementById('player-explain').scrollWidth <= document.getElementById('player-explain').clientWidth + 1")
    page.ctx.close()
