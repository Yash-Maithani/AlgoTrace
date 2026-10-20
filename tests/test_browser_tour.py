"""The first-visit tour of each workspace (static/js/tour.js), in a real browser.

Everything here runs with the Content-Security-Policy ON, as the site is served, and
as a first-time visitor: the context starts with empty localStorage and no pre-set
"tour seen" flag (tests/browser_helpers.py sets that for every other test).

Needs Playwright; see tests/test_browser_phase14.py and requirements-dev.txt.
"""
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_helpers import SKIP_REASON, available

pytestmark = pytest.mark.skipif(not available(), reason=SKIP_REASON)

KEY = 'pbl2.tourSeen'
WORKSPACES = [('sorting', '/sorting'), ('searching', '/searching'), ('graph', '/graph?algo=bfs'),
              ('astar', '/graph?algo=astar')]
SIZES = [(375, 'light'), (375, 'dark'), (768, 'light'), (768, 'dark'), (1440, 'light'), (1440, 'dark')]

WATCH = """
window.__violations = [];
document.addEventListener('securitypolicyviolation', e => window.__violations.push(e.violatedDirective + ' ' + e.blockedURI));
"""

INPUT_TARGET = {
    'sorting': "document.querySelector('.setup-grid > div:last-child')",
    'searching': "document.querySelector('.setup-grid > div:last-child')",
    'graph': "document.querySelectorAll('.workspace-setup > .panel')[1]",
    'astar': "document.querySelectorAll('.workspace-setup > .panel')[1]",
}


class Visit:
    """A first-time visitor on a workspace, CSP on, with the violation watcher."""

    def __init__(self, browser, base_url, path, width=1280, height=None, scheme='light', reduced='no-preference',
                 init_script=None, seen=None):
        height = height or (812 if width < 500 else 900)
        self.base_url = base_url
        self.ctx = browser.new_context(viewport={'width': width, 'height': height}, color_scheme=scheme,
                                       reduced_motion=reduced)
        self.ctx.add_init_script(WATCH)
        if init_script:
            self.ctx.add_init_script(init_script)
        if seen is not None:
            self.ctx.add_init_script("try { localStorage.setItem('%s', '%s'); } catch (e) {}" % (KEY, seen))
        self.page = self.ctx.new_page()
        self.errors, self.console = [], []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        self.page.on('console', lambda m: self.console.append(m.text) if m.type in ('error', 'warning') else None)
        self.page.goto(base_url + path)
        self.page.wait_for_load_state('load')

    def close(self):
        self.ctx.close()

    def wait_for_tour(self):
        self.page.wait_for_selector('.tour-card', timeout=6000)
        self.page.wait_for_timeout(250)

    def no_tour_after_a_while(self):
        self.page.wait_for_timeout(1100)            # the tour starts 300 ms after load
        return self.page.query_selector('.tour') is None

    def stored(self):
        return self.page.evaluate("localStorage.getItem('%s')" % KEY)

    def step_label(self):
        return self.page.inner_text('.tour-count')

    def title(self):
        return self.page.inner_text('.tour-title')

    def violations(self):
        return self.page.evaluate('window.__violations')


@pytest.fixture
def visit(browser, base_url):
    made = []

    def make(path, **kw):
        v = Visit(browser, base_url, path, **kw)
        made.append(v)
        return v

    yield make
    for v in made:
        v.close()


# ---------------------------------------------------------------------------
# First visit, once
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('name,path', WORKSPACES)
def test_a_first_visit_shows_the_tour_as_a_dialog(visit, name, path):
    v = visit(path)
    v.wait_for_tour()
    card = v.page.locator('.tour-card')
    assert card.get_attribute('role') == 'dialog'
    assert card.get_attribute('aria-modal') == 'true'
    assert v.page.evaluate("document.getElementById(document.querySelector('.tour-card').getAttribute('aria-labelledby')).textContent") == v.title()
    assert v.step_label() == 'Step 1 of 5'
    assert v.stored() == name                        # remembered as soon as it is shown


@pytest.mark.parametrize('name,path', WORKSPACES)
def test_it_is_shown_once_per_workspace_even_without_pressing_skip(visit, name, path):
    v = visit(path)
    v.wait_for_tour()
    v.page.reload()
    v.page.wait_for_load_state('load')
    assert v.no_tour_after_a_while()


def test_a_workspace_that_was_not_toured_still_shows_its_own_tour(visit):
    v = visit('/sorting', seen='searching,graph,astar')
    v.wait_for_tour()
    assert v.title() == 'Pick a sort'
    v.page.goto(v.base_url + '/searching')
    assert v.no_tour_after_a_while()


def test_every_graph_algorithm_page_shares_one_tour(visit):
    v = visit('/graph?algo=bfs')
    v.wait_for_tour()
    v.page.click('.tour-skip')
    for algo in ('dijkstra', 'kruskal', 'topological_sort'):
        v.page.goto('%s/graph?algo=%s' % (v.base_url, algo))
        assert v.no_tour_after_a_while(), algo
    v.page.goto(v.base_url + '/graph?algo=astar')       # A* is a workspace of its own
    v.wait_for_tour()
    assert v.stored() == 'graph,astar'


@pytest.mark.parametrize('path', ['/', '/learn', '/compare', '/big-o', '/privacy', '/terms'])
def test_pages_that_are_not_workspaces_have_no_tour(visit, path):
    v = visit(path)
    assert v.no_tour_after_a_while()
    assert v.page.query_selector('.tour-replay') is None


# ---------------------------------------------------------------------------
# The steps
# ---------------------------------------------------------------------------

def read_steps(v):
    steps = []
    for i in range(5):
        steps.append({'count': v.step_label(), 'title': v.title(), 'body': v.page.inner_text('.tour-body'),
                      'next': v.page.inner_text('.tour-next')})
        if i < 4:
            v.page.click('.tour-next')
    return steps


@pytest.mark.parametrize('name,path', WORKSPACES)
def test_five_steps_in_plain_words_with_no_dashes(visit, name, path):
    v = visit(path)
    v.wait_for_tour()
    steps = read_steps(v)
    assert [s['count'] for s in steps] == ['Step %d of 5' % n for n in range(1, 6)]
    assert [s['next'] for s in steps] == ['Next'] * 4 + ['Done']
    for s in steps:
        text = s['title'] + ' ' + s['body']
        assert chr(8212) not in text and chr(8211) not in text, text
        assert len(s['body']) < 420, 'short steps: %s' % s['title']
        assert len(s['body'].split()) < 80
    first, second, third, fourth, fifth = (s['body'] for s in steps)
    assert 'Space' in third and 'arrow' in third and 'R' in third           # the keyboard shortcuts
    for word in ('Explain', 'Code', 'Complexity', 'Python', 'C++', 'Java'):
        assert word in fourth, word
    assert 'Predict' in fifth and 'Take the tour' in fifth
    assert 'Run' in second


def test_the_words_are_specific_to_each_workspace(visit):
    texts = {}
    for name, path in WORKSPACES:
        v = visit(path)
        v.wait_for_tour()
        texts[name] = [s['title'] + '|' + s['body'] for s in read_steps(v)]
    assert 'quick sort' in texts['sorting'][0] and 'bubble' in texts['sorting'][0]
    assert 'binary' in texts['searching'][0] and 'Sort it' in texts['searching'][1]
    assert 'Dijkstra' in texts['graph'][0] and 'format guide' in texts['graph'][1]
    assert 'walls' in texts['astar'][1] and 'Run A*' in texts['astar'][1]
    for i in (0, 1, 2, 4):
        assert len({texts[n][i] for n in texts}) == 4, 'step %d reads the same on two workspaces' % (i + 1)


# ---------------------------------------------------------------------------
# What it lights, and where the card sits (3 widths, 2 themes)
# ---------------------------------------------------------------------------

# One function per step, written out so no string is evaluated by the page.
def _geometry(find):
    return """() => {
        const rect = (e) => { const b = e.getBoundingClientRect(); return { l: b.left, t: b.top, r: b.right, b: b.bottom }; };
        const target = %s;
        const spot = document.querySelector('.tour-spot');
        const card = document.querySelector('.tour-card');
        return { target: rect(target), spot: spot.hidden ? null : rect(spot), card: rect(card),
                 vw: window.innerWidth, vh: window.innerHeight,
                 overflow: document.documentElement.scrollWidth - window.innerWidth,
                 edge: card.getAttribute('data-edge') };
    }""" % find


GEOMETRY_FN = [_geometry("document.querySelector('#algo-picker')"), None,
               _geometry("document.querySelector('.control-bar')"),
               _geometry("document.querySelector('#learn-panel .learn-tabs')"),
               _geometry("document.querySelector('.predict-control')")]
GEOMETRY_INPUT = {name: _geometry(code) for name, code in INPUT_TARGET.items()}


def area(a):
    return max(0, a['r'] - a['l']) * max(0, a['b'] - a['t'])


def meet(a, b):
    return {'l': max(a['l'], b['l']), 't': max(a['t'], b['t']), 'r': min(a['r'], b['r']), 'b': min(a['b'], b['b'])}


@pytest.mark.parametrize('width,scheme', SIZES)
@pytest.mark.parametrize('name,path', WORKSPACES)
def test_each_step_lights_its_control_and_the_card_stays_on_screen(visit, name, path, width, scheme):
    v = visit(path, width=width, scheme=scheme)
    v.wait_for_tour()
    for step in range(1, 6):
        info = v.page.evaluate(GEOMETRY_FN[step - 1] if step != 2 else GEOMETRY_INPUT[name])
        view = {'l': 0, 't': 0, 'r': info['vw'], 'b': info['vh']}
        seen_target = meet(info['target'], view)

        assert info['spot'] is not None, 'step %d lights nothing' % step
        shared = area(meet(info['spot'], seen_target))
        assert shared >= 0.9 * min(area(info['spot']), area(seen_target)), (step, info)
        assert area(seen_target) >= 0.3 * area(info['target']) or (seen_target['b'] - seen_target['t']) > 200, \
            'step %d: the lit control is mostly off screen' % step

        card = info['card']
        assert card['l'] >= -0.5 and card['t'] >= -0.5 and card['r'] <= info['vw'] + 0.5 and card['b'] <= info['vh'] + 0.5, \
            ('the card leaves the screen', step, card)
        assert info['overflow'] <= 0
        small = (info['target']['b'] - info['target']['t']) < 220
        if small:
            assert area(meet(card, seen_target)) == 0, ('the card covers the control it explains', step, info)
        if width < 1024:
            assert info['edge'] in ('top', 'bottom'), 'a sheet below 1024px'
        else:
            assert info['edge'] is None
        if step < 5:
            v.page.click('.tour-next')
    assert v.violations() == []
    assert v.errors == []




# ---------------------------------------------------------------------------
# Skip, back, next, replay
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('name,path', WORKSPACES)
def test_skip_closes_it_and_the_choice_is_remembered(visit, name, path):
    v = visit(path)
    v.wait_for_tour()
    v.page.click('.tour-next')
    v.page.click('.tour-skip')
    assert v.page.query_selector('.tour') is None
    assert v.stored() == name
    v.page.reload()
    assert v.no_tour_after_a_while()


def test_skip_is_on_every_step_and_back_and_next_walk_the_steps(visit):
    v = visit('/sorting')
    v.wait_for_tour()
    assert v.page.locator('.tour-back').is_disabled()                 # nothing before the first step
    titles = [v.title()]
    for _ in range(4):
        assert v.page.locator('.tour-skip').is_visible()
        v.page.click('.tour-next')
        titles.append(v.title())
    assert v.step_label() == 'Step 5 of 5' and v.page.inner_text('.tour-next') == 'Done'
    assert v.page.locator('.tour-skip').is_visible()
    assert len(set(titles)) == 5
    v.page.click('.tour-back')
    assert v.step_label() == 'Step 4 of 5' and v.title() == titles[3]
    for expected in (3, 2, 1):
        v.page.click('.tour-back')
        assert v.step_label() == 'Step %d of 5' % expected
    assert v.page.locator('.tour-back').is_disabled()
    for _ in range(4):
        v.page.click('.tour-next')
    v.page.click('.tour-next')                                         # Done
    assert v.page.query_selector('.tour') is None


@pytest.mark.parametrize('name,path', WORKSPACES)
def test_take_the_tour_replays_it_from_the_start(visit, name, path):
    v = visit(path, seen='sorting,searching,graph,astar')
    assert v.no_tour_after_a_while()
    button = v.page.locator('.control-bar .tour-replay')
    assert button.inner_text() == 'Take the tour'
    assert v.page.locator('.control-bar-foot .shortcuts').count() == 1          # beside the keyboard shortcuts
    button.click()
    v.wait_for_tour()
    assert v.step_label() == 'Step 1 of 5'
    v.page.click('.tour-next')
    v.page.click('.tour-skip')
    button.click()
    v.wait_for_tour()
    assert v.step_label() == 'Step 1 of 5'                              # a replay always starts at the start
    assert v.stored() == 'sorting,searching,graph,astar'                 # and adds nothing to what is stored


def test_a_replay_leaves_the_workspace_as_it_found_it(visit):
    v = visit('/sorting', seen='sorting')
    v.page.click('#run-button')
    v.page.wait_for_selector('#step-forward:not([disabled])')
    v.page.click('#step-forward')
    v.page.click('#step-forward')
    before = v.page.inner_text('#step-counter')
    assert not before.startswith('Step 0')
    v.page.click('.tour-replay')
    v.wait_for_tour()
    for key in ('ArrowRight', 'ArrowRight', 'ArrowLeft', 'Space', 'r'):
        v.page.keyboard.press(key)                                       # the tour's keys, not the workspace's
    v.page.click('.tour-skip')
    assert v.page.inner_text('#step-counter') == before


# ---------------------------------------------------------------------------
# Keyboard and focus
# ---------------------------------------------------------------------------

def active(v):
    return v.page.evaluate("""() => { const a = document.activeElement;
        return { cls: a.className, inside: !!a.closest('.tour'), tag: a.tagName, text: a.textContent.trim().slice(0, 20) }; }""")


def test_focus_moves_into_the_tour_and_tab_stays_inside_it(visit):
    v = visit('/sorting')
    v.wait_for_tour()
    assert active(v)['inside'] and 'tour-card' in active(v)['cls']
    seen = []
    for _ in range(8):
        v.page.keyboard.press('Tab')
        state = active(v)
        assert state['inside'], state
        seen.append(state['text'])
    assert set(seen) == {'Skip tour', 'Next'}                              # Back is disabled on step 1
    v.page.keyboard.press('Shift+Tab')
    first = active(v)['text']
    v.page.keyboard.press('Shift+Tab')
    assert {first, active(v)['text']} == {'Skip tour', 'Next'}             # wraps round the two stops


def test_a_click_on_the_dimmed_page_does_not_let_focus_out(visit):
    v = visit('/sorting')
    v.wait_for_tour()
    v.page.mouse.click(5, 300)
    v.page.keyboard.press('Tab')
    assert active(v)['inside']


def test_the_tour_can_be_walked_by_keyboard_alone(visit):
    v = visit('/searching')
    v.wait_for_tour()
    v.page.keyboard.press('Tab')                                           # Skip tour
    v.page.keyboard.press('Tab')                                           # Next
    assert active(v)['text'] == 'Next'
    v.page.keyboard.press('Enter')
    assert v.step_label() == 'Step 2 of 5'
    assert active(v)['text'] == 'Next'                                     # focus stays put on the button
    v.page.keyboard.press('Space')
    assert v.step_label() == 'Step 3 of 5'
    v.page.keyboard.press('ArrowRight')
    assert v.step_label() == 'Step 4 of 5'
    v.page.keyboard.press('ArrowLeft')
    assert v.step_label() == 'Step 3 of 5'
    v.page.keyboard.press('Shift+Tab')                                     # Back
    assert active(v)['text'] == 'Back'
    v.page.keyboard.press('Enter')
    assert v.step_label() == 'Step 2 of 5'
    for _ in range(3):
        v.page.keyboard.press('ArrowRight')
    assert v.step_label() == 'Step 5 of 5'
    v.page.keyboard.press('ArrowRight')                                    # past the last step: done
    assert v.page.query_selector('.tour') is None


def test_back_at_the_first_step_does_not_strand_the_focus(visit):
    v = visit('/sorting')
    v.wait_for_tour()
    v.page.keyboard.press('Tab')
    v.page.keyboard.press('Tab')
    v.page.keyboard.press('Enter')                                         # step 2
    v.page.keyboard.press('Shift+Tab')                                     # Back
    v.page.keyboard.press('Enter')                                         # step 1, Back now disabled
    assert v.step_label() == 'Step 1 of 5'
    assert active(v)['inside'] and active(v)['text'] == 'Next'


@pytest.mark.parametrize('name,path', WORKSPACES)
def test_escape_closes_it_and_gives_focus_back(visit, name, path):
    v = visit(path, seen='sorting,searching,graph,astar')
    v.page.focus('.tour-replay')
    v.page.keyboard.press('Enter')
    v.wait_for_tour()
    assert active(v)['inside']
    v.page.keyboard.press('Escape')
    assert v.page.query_selector('.tour') is None
    assert active(v)['cls'].split()[-1] == 'tour-replay'                  # back where it was


def test_escape_on_a_first_visit_counts_as_seen(visit):
    v = visit('/graph?algo=dfs')
    v.wait_for_tour()
    v.page.keyboard.press('Escape')
    assert v.page.query_selector('.tour') is None
    v.page.reload()
    assert v.no_tour_after_a_while()
    assert v.stored() == 'graph'


def test_focus_returns_to_the_control_that_opened_the_tour(visit):
    v = visit('/sorting', seen='sorting')
    v.page.focus('.tour-replay')
    v.page.keyboard.press('Space')
    v.wait_for_tour()
    v.page.click('.tour-skip')
    assert active(v)['cls'].split()[-1] == 'tour-replay'


def test_each_step_is_announced_through_a_polite_live_region(visit):
    v = visit('/sorting')
    v.wait_for_tour()
    region = v.page.locator('.tour-content')
    assert region.get_attribute('aria-live') == 'polite'
    assert region.get_attribute('aria-atomic') == 'true'
    first = region.inner_text()
    v.page.click('.tour-next')
    second = region.inner_text()
    assert first != second and second.startswith('Step 2 of 5')
    assert v.page.locator('.tour-card').get_attribute('aria-describedby') == 'tour-body'


def test_the_tour_keys_are_the_tours_own(visit):
    v = visit('/sorting')
    v.wait_for_tour()
    assert v.page.locator('.tour').get_attribute('data-keys') == 'own'     # workspace.js leaves its keys alone


# ---------------------------------------------------------------------------
# Motion, themes, contrast
# ---------------------------------------------------------------------------

def test_nothing_animates_under_reduced_motion(visit):
    v = visit('/sorting', reduced='reduce')
    v.wait_for_tour()
    style = v.page.evaluate("""() => { const c = getComputedStyle(document.querySelector('.tour-card'));
        const s = getComputedStyle(document.querySelector('.tour-spot'));
        return { opacity: c.opacity, duration: c.transitionDuration, anim: c.animationName,
                 spotDuration: s.transitionDuration, spotAnim: s.animationName }; }""")
    assert style['opacity'] == '1'
    assert style['duration'] == '0s' and style['anim'] == 'none'
    assert style['spotDuration'] == '0s' and style['spotAnim'] == 'none'


def test_with_motion_allowed_the_card_only_fades_in(visit):
    v = visit('/sorting')
    v.wait_for_tour()
    style = v.page.evaluate("""() => { const c = getComputedStyle(document.querySelector('.tour-card'));
        return { property: c.transitionProperty, duration: c.transitionDuration }; }""")
    assert style['property'] == 'opacity' and style['duration'] == '0.15s'


@pytest.mark.parametrize('scheme', ['light', 'dark'])
def test_the_card_text_and_buttons_are_readable_and_big_enough(visit, scheme):
    v = visit('/sorting', scheme=scheme, width=375)
    v.wait_for_tour()
    info = v.page.evaluate("""() => {
        const lum = (rgb) => { const [r, g, b] = rgb.map(x => { x /= 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); }); return 0.2126*r + 0.7152*g + 0.0722*b; };
        const nums = (css) => css.match(/[\\d.]+/g).map(Number).slice(0, 3);
        const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
        const bg = nums(getComputedStyle(document.querySelector('.tour-card')).backgroundColor);
        const out = { text: {}, buttons: {} };
        for (const sel of ['.tour-count', '.tour-title', '.tour-body']) out.text[sel] = ratio(nums(getComputedStyle(document.querySelector(sel)).color), bg);
        for (const sel of ['.tour-skip', '.tour-back', '.tour-next']) {
            const e = document.querySelector(sel); const c = getComputedStyle(e);
            out.buttons[sel] = { height: e.getBoundingClientRect().height, ratio: ratio(nums(c.color), nums(c.backgroundColor)) };
        }
        out.ring = getComputedStyle(document.querySelector('.tour-spot')).outlineStyle;
        return out;
    }""")
    for selector, value in info['text'].items():
        assert value >= 4.5, (selector, value)
    for selector, button in info['buttons'].items():
        assert button['height'] >= 44, (selector, button)
        if selector != '.tour-back':                                         # Back is disabled on step 1
            assert button['ratio'] >= 4.5, (selector, button)
    assert info['ring'] == 'solid'


# ---------------------------------------------------------------------------
# The Learn panel below the stage on a phone, and a short screen
# ---------------------------------------------------------------------------

def test_on_a_phone_the_learn_tabs_are_in_view_and_not_under_the_card(visit):
    v = visit('/sorting', width=375)
    v.wait_for_tour()
    for _ in range(3):
        v.page.click('.tour-next')
    assert v.title() == 'Read the Learn panel'
    info = v.page.evaluate(GEOMETRY_FN[3])
    seen = meet(info['target'], {'l': 0, 't': 0, 'r': info['vw'], 'b': info['vh']})
    assert area(seen) == area(info['target']), 'the tab strip is fully on screen'
    assert area(meet(info['card'], info['target'])) == 0
    assert info['target']['t'] > 56                                         # not under the sticky header


def test_a_short_phone_screen_still_fits_the_card(visit):
    v = visit('/graph?algo=dijkstra', width=375, height=568)
    v.wait_for_tour()
    for step in range(5):
        info = v.page.evaluate(_geometry("document.querySelector('.tour-card')"))
        assert info['card']['t'] >= 0 and info['card']['b'] <= info['vh'] + 0.5
        assert v.page.locator('.tour-next').is_visible()
        if step < 4:
            v.page.click('.tour-next')


def test_resizing_while_it_is_open_keeps_it_in_place(visit):
    v = visit('/sorting', width=1440)
    v.wait_for_tour()
    v.page.click('.tour-next')
    v.page.set_viewport_size({'width': 375, 'height': 812})
    v.page.wait_for_timeout(300)
    info = v.page.evaluate(GEOMETRY_INPUT['sorting'])
    assert info['edge'] in ('top', 'bottom')
    assert info['card']['l'] >= 0 and info['card']['r'] <= info['vw'] + 0.5
    assert area(meet(info['spot'], info['target'])) > 0


# ---------------------------------------------------------------------------
# Storage and the policy
# ---------------------------------------------------------------------------

BLOCKED = """
Object.defineProperty(window, 'localStorage', { get() { throw new DOMException('blocked', 'SecurityError'); } });
"""


@pytest.mark.parametrize('path', [p for _, p in WORKSPACES])
def test_with_storage_blocked_nothing_breaks_and_the_button_still_works(visit, path):
    v = visit(path, init_script=BLOCKED)
    assert v.no_tour_after_a_while()                                         # never starts by itself
    v.page.click('.tour-replay')
    v.wait_for_tour()
    assert v.step_label() == 'Step 1 of 5'
    v.page.click('.tour-skip')
    assert v.page.query_selector('.tour') is None
    assert v.errors == []


@pytest.mark.parametrize('name,path', WORKSPACES)
def test_the_whole_tour_runs_with_the_policy_on_and_no_console_violations(visit, name, path):
    v = visit(path)
    v.wait_for_tour()
    policy = v.page.evaluate("fetch(location.href).then(r => r.headers.get('content-security-policy'))")
    scripts = policy.split('script-src')[1].split(';')[0]
    assert "'self' 'nonce-" in scripts and 'unsafe-eval' not in policy and "'unsafe-inline'" not in scripts
    for _ in range(4):
        v.page.click('.tour-next')
    v.page.click('.tour-next')
    v.page.click('.tour-replay')
    v.wait_for_tour()
    v.page.keyboard.press('Escape')
    assert v.violations() == []
    assert v.errors == []
    assert [m for m in v.console if 'Content Security Policy' in m or 'Refused to' in m] == []


def test_the_overlay_is_removed_completely_when_closed(visit):
    v = visit('/sorting')
    v.wait_for_tour()
    v.page.keyboard.press('Escape')
    assert v.page.evaluate("document.querySelectorAll('.tour, .tour-card, .tour-spot').length") == 0
    v.page.click('#run-button')                                              # the page is usable again
    v.page.wait_for_selector('#step-forward:not([disabled])')
