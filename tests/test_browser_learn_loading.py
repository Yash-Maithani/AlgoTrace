"""/learn fills its complexity figures in the browser. Until it has, the cards
must hold their space and show a placeholder, not flash empty or reflow.

The loading state is reproduced by refusing to load static/js/learnfigures.js,
which is the script that fills them: the page then stays exactly as it is in
the moment before the figures arrive.

Needs Playwright; see tests/test_browser_phase14.py and requirements-dev.txt.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_helpers import SKIP_REASON, available

pytestmark = pytest.mark.skipif(not available(), reason=SKIP_REASON)

GEOMETRY = """() => {
    const box = e => { const r = e.getBoundingClientRect(); return [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10]; };
    return {
        cards: [...document.querySelectorAll('.algo-card')].map(box),
        rows: [...document.querySelectorAll('.order-list li')].map(box),
        tags: [...document.querySelectorAll('.order-tag')].map(box),
        facts: [...document.querySelectorAll('.algo-facts')].map(box),
        pageHeight: document.documentElement.scrollHeight,
        overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    };
}"""


def open_learn(browser, base_url, width, scheme, loaded):
    ctx = browser.new_context(viewport={'width': width, 'height': 900}, color_scheme=scheme)
    page = ctx.new_page()
    if not loaded:
        page.route('**/learnfigures.js*', lambda route: route.abort())
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(base_url + '/learn')
    page.wait_for_load_state('load')
    page.errors = errors
    page.ctx = ctx
    return page


@pytest.mark.parametrize('scheme', ['light', 'dark'])
@pytest.mark.parametrize('width', [375, 768, 1440])
def test_a_card_is_the_same_size_before_and_after_its_figures_arrive(browser, base_url, width, scheme):
    waiting = open_learn(browser, base_url, width, scheme, loaded=False)
    before = waiting.evaluate(GEOMETRY)
    assert waiting.evaluate("[...document.querySelectorAll('[data-figure]')].every(n => n.textContent === '')")
    waiting.ctx.close()

    done = open_learn(browser, base_url, width, scheme, loaded=True)
    after = done.evaluate(GEOMETRY)
    assert done.evaluate("[...document.querySelectorAll('[data-figure]')].every(n => n.textContent.trim() !== '')")
    done.ctx.close()

    assert len(before['cards']) == len(after['cards']) == 21            # twenty algorithms and the complexity guide
    for i, (b, a) in enumerate(zip(before['cards'], after['cards'])):
        assert b[0] == a[0] and abs(b[1] - a[1]) <= 1, ('card', i, b, a)        # nothing grew or shrank
    for i, (b, a) in enumerate(zip(before['rows'], after['rows'])):
        assert abs(b[1] - a[1]) <= 1, ('row', i, b, a)
    for i, (b, a) in enumerate(zip(before['facts'], after['facts'])):
        assert abs(b[1] - a[1]) <= 1, ('facts', i, b, a)
    assert abs(before['pageHeight'] - after['pageHeight']) <= 4, (before['pageHeight'], after['pageHeight'])
    assert before['overflow'] <= 0 and after['overflow'] <= 0


@pytest.mark.parametrize('scheme', ['light', 'dark'])
def test_every_empty_slot_shows_a_placeholder_not_a_gap(browser, base_url, scheme):
    page = open_learn(browser, base_url, 1440, scheme, loaded=False)
    slots = page.evaluate("""() => [...document.querySelectorAll('[data-figure]')].map(n => {
        const before = getComputedStyle(n, '::before');
        return {kind: n.className || n.tagName, text: n.textContent, display: before.display,
                width: parseFloat(before.width), height: parseFloat(before.height), bg: before.backgroundColor,
                content: before.content};
    })""")
    assert len(slots) == 72                                                  # 52 card figures and 20 order tags
    for slot in slots:
        assert slot['text'] == '' and slot['content'] == '""', slot
        assert slot['display'] == 'inline-block' and slot['width'] >= 30 and slot['height'] >= 8, slot
        assert slot['bg'] not in ('rgba(0, 0, 0, 0)', 'transparent'), slot
    # A bordered tag is never an empty box: its placeholder gives it a width.
    tags = page.evaluate("[...document.querySelectorAll('.order-tag')].map(t => t.getBoundingClientRect().width)")
    assert all(w > 40 for w in tags), tags
    page.ctx.close()


def test_the_placeholder_says_nothing_to_a_screen_reader(browser, base_url):
    page = open_learn(browser, base_url, 1440, 'light', loaded=False)
    # A pseudo element with no text is not in the accessibility tree: the slot is empty text.
    assert page.evaluate("[...document.querySelectorAll('[data-figure]')].every(n => n.textContent === '' && !n.hasAttribute('aria-label'))")
    page.ctx.close()


def test_figures_replace_the_placeholder_and_keep_their_words_for_screen_readers(browser, base_url):
    page = open_learn(browser, base_url, 1440, 'light', loaded=True)
    got = page.evaluate("""() => {
        const n = document.querySelector('.algo-facts [data-lesson="bubble_sort"][data-figure="worst"]');
        return {text: n.textContent, seen: n.querySelector('[aria-hidden]').textContent, spoken: n.querySelector('.sr-only').textContent,
                bar: getComputedStyle(n, '::before').content};
    }""")
    assert got['seen'] == 'O(n²)' and got['spoken'] == 'Big O of n squared'
    assert got['bar'] in ('none', 'normal'), got                           # the bar goes once there is content
    page.ctx.close()


def test_the_placeholder_rule_and_the_noscript_rule_are_in_the_page():
    from app import app
    app.config['TESTING'] = True
    html = app.test_client().get('/learn').get_data(as_text=True)
    css = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'styles.css'),
               encoding='utf-8').read()

    assert '<noscript><style nonce="' in html
    assert '[data-figure]:empty::before { display: none; }</style></noscript>' in html
    assert '[data-figure]:empty::before' in css
