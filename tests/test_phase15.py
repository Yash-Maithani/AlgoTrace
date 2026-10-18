"""Phase 15: the Home "One step, read three ways" player (data and markup).

The behaviour in a browser is tests/test_browser_phase15.py.
"""
import json
import os
import re

import pytest

from app import app, BAND_ARRAY, _sort_payload

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return f.read()


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def embedded(client):
    html = client.get('/').get_data(as_text=True)
    raw = re.search(r'<script type="application/json" id="player-data">(.*?)</script>', html, re.S).group(1)
    return html, json.loads(raw)


def test_the_player_plays_bubble_sort_on_the_five_values_the_plan_names():
    assert BAND_ARRAY == [17, 11, 32, 45, 9]


def test_the_steps_are_the_real_run_not_a_copy(client):
    """The page embeds what /run_sort sends for the same input."""
    _, data = embedded(client)
    real = client.post('/run_sort', json={'algorithm': 'Bubble Sort', 'values': '17, 11, 32, 45, 9'}).get_json()

    assert data['start'] == [17, 11, 32, 45, 9]
    assert len(data['steps']) == len(real['steps']) == 16
    for mine, theirs in zip(data['steps'], real['steps']):
        assert mine['array'] == theirs['array']
        assert mine['origins'] == theirs['origins']
        assert mine['action'] == theirs['action']
        assert mine['line'] == theirs['line']
        assert mine['indices'] == theirs['indices']
        assert mine['explain'] == theirs['explain']
        assert mine['comparisons'] == theirs['vars']['comparisons']
        assert mine['swaps'] == theirs['vars']['swaps']


def test_the_cost_card_counts_up_to_the_formula(client):
    _, data = embedded(client)
    counted = [s['comparisons'] for s in data['steps']]

    assert data['total'] == 10 == data['n'] * (data['n'] - 1) // 2
    assert counted == sorted(counted) and counted[0] == 1 and counted[-1] == 10
    assert data['steps'][-1]['action'] == 'done'
    # Each comparison step raises the count by exactly one.
    compares = [s['comparisons'] for s in data['steps'] if s['action'] == 'compare']
    assert compares == list(range(1, 11))


def test_origins_say_where_every_cell_now_stands(client):
    """What lets a swapped pair slide: the same ten starting cells, permuted."""
    _, data = embedded(client)
    for step in data['steps']:
        assert sorted(step['origins']) == [0, 1, 2, 3, 4]
        assert [data['start'][o] for o in step['origins']] == step['array']


def test_the_served_page_is_a_complete_still_picture_without_javascript(client):
    html, data = embedded(client)
    frozen = data['steps'][data['frozen']]

    assert frozen['action'] == 'compare' and data['frozen'] == 4
    assert frozen['explain']['beginner'] in html
    assert frozen['explain']['why'] in html
    assert 'id="player-count">%d</strong>' % frozen['comparisons'] in html
    assert 'of\n                            <strong>10</strong> comparisons' in html or '<strong>10</strong> comparisons' in html
    cells = re.findall(r'<span class="band-cell[^"]*"\s+style="--pos: (\d)">(\d+)</span>', html)
    assert [int(v) for _, v in cells] == frozen['array']
    track = html.split('id="player-track"', 1)[1].split('</div>', 1)[0]
    assert track.count('is-comparing') == 2
    # Nothing that needs scripting is visible until the scripts have run.
    assert re.search(r'id="player-controls"[^>]*\bhidden\b', html)


def test_the_explain_sentence_is_a_polite_live_region(client):
    html, _ = embedded(client)
    tag = re.search(r'<p class="band-lead" id="player-explain"[^>]*>', html).group(0)

    assert 'role="status"' in tag and 'aria-live="polite"' in tag


def test_the_old_hand_derived_band_is_gone():
    app_source = read('app.py')

    assert '_band_step' not in app_source
    # Its "5 of 10" counted the frame after a swap as a comparison; the
    # player's count is the one /run_sort reports.
    assert _sort_payload('Bubble Sort', list(BAND_ARRAY), None, None)['steps'][4]['vars']['comparisons'] == 4


def test_the_player_script_is_loaded_after_the_code_card(client):
    html = client.get('/').get_data(as_text=True)

    assert html.index('js/codeview.js') < html.index('js/home_code.js') < html.index('js/home_player.js')


def test_the_script_covers_every_behaviour_the_plan_asks_for():
    js = read('static', 'js', 'home_player.js')

    for needle in ('IntersectionObserver', 'visibilitychange', "'Play'", "'Pause'", "'Step'",
                   'prefers-reduced-motion: reduce', 'HomeCode.light', 'userPaused', "'--pos'"):
        assert needle in js, needle


def test_cells_move_by_transform_alone():
    css = read('static', 'styles.css')
    block = css.split('.band-stage.is-live .band-cell {', 1)[1].split('}', 1)[0]

    assert 'transform: translate(' in block
    assert 'transition: transform 320ms' in block
    for property_ in ('left', 'top', 'margin', 'width', 'height'):
        assert not re.search(r'transition:[^;]*\b%s\b' % property_, block), property_
    # Position is fixed in CSS; only --pos and --lift (inside transform) change.
    assert 'left: 0' in block and 'top: 14px' in block


def test_reduced_motion_turns_the_slide_off_in_css():
    css = read('static', 'styles.css')
    blocks = [b.split('}', 1)[0] for b in css.split('@media (prefers-reduced-motion: reduce) {')[1:]]

    assert any('.band-stage.is-live .band-cell' in b and 'transition: none' in b for b in blocks)


def test_no_banned_style_in_the_player_markup():
    css = read('static', 'styles.css')
    controls = css.split('.player-controls {', 1)[1].split('}', 1)[0]

    assert 'border-radius: 999' not in controls and '50%' not in controls


def test_the_reduced_motion_block_is_last_so_it_beats_every_transition_it_turns_off():
    """Media queries add no specificity, so a block placed before the rule it
    overrides loses to it. The browser test caught exactly that once."""
    css = read('static', 'styles.css')
    last = css.rindex('@media (prefers-reduced-motion: reduce) {')

    for selector in ('.lang-thumb', '.code-stage', '.band-stage.is-live .band-cell'):
        assert css.rindex(selector + ' {') < last or selector in css[last:], selector
    assert '.band-stage.is-live .band-cell' in css[last:]
    assert css.index('.band-stage.is-live .band-cell {') < last
