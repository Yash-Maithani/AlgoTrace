"""Phase 8B: the accessibility pass.

Each test here pins one thing the audit found, so a later phase that undoes it
fails rather than quietly shipping. The contrast tests do the arithmetic from
the tokens in styles.css, so they follow the palette if it is ever retuned.
"""
import os
import re

import pytest

from paths import ROOT
from wsgi import app

TEMPLATES = os.path.join(ROOT, 'algotrace', 'templates')
STATIC = os.path.join(ROOT, 'algotrace', 'static')

WORKSPACES = ['sorting', 'searching', 'graph_base']
GRAPH_ALGOS = ['bfs', 'dfs', 'dijkstra', 'prim', 'kruskal',
               'floyd_warshall', 'bellman_ford']
PAGES = ['/', '/learn', '/big-o', '/sorting', '/searching', '/privacy',
         '/terms', '/graph?algo=bfs']


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def template(name):
    with open(os.path.join(TEMPLATES, '%s.html' % name), encoding='utf-8') as fh:
        return fh.read()


def stylesheet():
    with open(os.path.join(STATIC, 'styles.css'), encoding='utf-8') as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# Contrast, computed from the tokens rather than asserted as a magic number
# ---------------------------------------------------------------------------

def tokens(theme):
    """The custom properties for one theme, read out of styles.css."""
    css = stylesheet()
    if theme == 'light':
        block = css.split(':root {', 1)[1].split(chr(10) + '}', 1)[0]
    else:
        block = css.split(':root[data-theme="dark"] {', 1)[1].split(chr(10) + '}', 1)[0]
    found = dict(re.findall(r'(--[a-z0-9-]+):\s*([^;]+);', block))
    # Resolve one level of var() indirection, which is all the palette uses.
    for key, value in list(found.items()):
        match = re.fullmatch(r'var\((--[a-z0-9-]+)\)', value.strip())
        if match:
            found[key] = found[match.group(1)]
    return {k: v.strip() for k, v in found.items()}


def luminance(hex_colour):
    value = hex_colour.lstrip('#')
    parts = [int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    parts = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
             for c in parts]
    return 0.2126 * parts[0] + 0.7152 * parts[1] + 0.0722 * parts[2]


def contrast(fg, bg):
    a, b = luminance(fg), luminance(bg)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


# Every pair where text sits on a saturated fill. The audit found three of
# these below 4.5 because they used the fill tier, which is sized for a bar.
TEXT_ON_FILL = [
    ('--on-state', '--active-solid', 'the comparing cell, on Home and in search'),
    ('--on-state', '--done-solid', 'the found cell'),
    ('--on-state', '--visited-color', 'a visited graph node letter'),
    ('--on-state', '--frontier-color', 'a queued graph node letter'),
    ('--on-accent', '--accent', 'a primary button label'),
]


@pytest.mark.parametrize('theme', ['light', 'dark'])
@pytest.mark.parametrize('fg,bg,what', TEXT_ON_FILL)
def test_text_on_a_fill_clears_4_5(theme, fg, bg, what):
    palette = tokens(theme)
    ratio = contrast(palette[fg], palette[bg])

    assert ratio >= 4.5, (
        '%s in %s mode is %.2f:1 (%s on %s)'
        % (what, theme, ratio, palette[fg], palette[bg]))


@pytest.mark.parametrize('theme', ['light', 'dark'])
def test_body_and_muted_text_clear_4_5(theme):
    palette = tokens(theme)

    for text in ('--text', '--text-muted'):
        for ground in ('--bg', '--surface', '--sunken'):
            ratio = contrast(palette[text], palette[ground])
            assert ratio >= 4.5, (
                '%s on %s in %s mode is %.2f:1' % (text, ground, theme, ratio))


def test_the_two_dark_token_blocks_stay_identical():
    """One is the no-JavaScript fallback, the other is what the toggle drives."""
    media = tokens('dark')
    css = stylesheet()
    block = css.split(':root:not([data-theme="light"]) {', 1)[1].split(chr(10) + '    }', 1)[0]
    fallback = dict(re.findall(r'(--[a-z0-9-]+):\s*([^;]+);', block))

    for key, value in fallback.items():
        resolved = value.strip()
        match = re.fullmatch(r'var\((--[a-z0-9-]+)\)', resolved)
        if match:
            resolved = fallback[match.group(1)].strip()
        assert media[key] == resolved, 'the two dark blocks disagree on %s' % key


def test_dimmed_text_is_still_readable():
    """A discarded search cell is dimmed, not hidden."""
    css = stylesheet()
    rule = css.split('.cell[data-state="discarded"] .cell-box {', 1)[1].split('}', 1)[0]
    opacity = float(re.search(r'opacity:\s*([0-9.]+)', rule).group(1))

    assert opacity >= 0.6, 'the value inside a discarded cell drops under 4.5:1'


def test_the_reference_curves_are_visible():
    css = stylesheet()
    rule = css.split('.growth-ref {', 1)[1].split('}', 1)[0]
    opacity = float(re.search(r'opacity:\s*([0-9.]+)', rule).group(1))

    assert opacity >= 0.7, 'the curves the highlighted one is compared against fade out'


# ---------------------------------------------------------------------------
# Headings
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('url', PAGES)
def test_every_page_has_exactly_one_h1(client, url):
    body = client.get(url).get_data(as_text=True)

    assert len(re.findall(r'<h1[\s>]', body)) == 1, url


@pytest.mark.parametrize('url', PAGES)
def test_no_heading_level_is_skipped(client, url):
    body = client.get(url).get_data(as_text=True)
    levels = [int(m) for m in re.findall(r'<h([1-6])[\s>]', body)]

    assert levels[0] == 1, '%s does not open with its h1' % url
    for before, after in zip(levels, levels[1:]):
        assert after <= before + 1, (
            '%s jumps from h%d to h%d' % (url, before, after))


@pytest.mark.parametrize('name', WORKSPACES)
def test_the_workspace_heading_is_in_the_grid(name):
    assert 'class="workspace-title"' in template(name)


# ---------------------------------------------------------------------------
# Keyboard and semantics
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('name', ['sorting', 'searching'])
def test_the_picker_is_buttons_not_links_to_nowhere(name):
    """These change the page you are on, so they are not links."""
    source = template(name)

    assert 'href="#"' not in source, '%s still has a link to nowhere' % name
    picker = source.split('class="algo-picker"', 1)[1].split('</ul>', 1)[0]
    assert '<button type="button" data-algorithm=' in picker


def test_the_graph_picker_stays_links():
    """Each graph algorithm is its own URL, so these really are navigation."""
    # The list lives in one partial, included by the graph page and the A* grid.
    assert '{% include "_graph_picker.html" %}' in template('graph_base')
    assert '{% include "_graph_picker.html" %}' in template('astar')
    picker = template('_graph_picker').split('class="algo-picker"', 1)[1].split('</ul>', 1)[0]

    assert 'url_for(' in picker
    assert 'aria-current="page"' in picker


@pytest.mark.parametrize('name', WORKSPACES + ['landing', 'learn', 'big_o',
                                               'privacy', 'terms', 'layout'])
def test_nothing_is_clicked_that_cannot_be_focused(name):
    """onclick belongs on a button or a link, never on a span or a div."""
    for line in template(name).split(chr(10)):
        if 'onclick' not in line:
            continue
        assert '<button' in line or '<a ' in line, (
            '%s has an onclick on something no keyboard can reach: %s'
            % (name, line.strip()[:80]))


@pytest.mark.parametrize('name', WORKSPACES + GRAPH_ALGOS +
                         ['landing', 'learn', 'big_o', 'layout'])
def test_every_button_declares_its_type(name):
    """A button with no type submits the form it is standing in."""
    for match in re.finditer(r'<button\b[^>]*>', template(name)):
        assert 'type=' in match.group(0), '%s: %s' % (name, match.group(0)[:70])


def test_the_format_guide_toggle_is_a_button():
    source = template('graph_base')

    assert '<button type="button" class="format-toggle"' in source
    assert 'aria-expanded="false"' in source
    assert 'aria-controls="format-content"' in source


def test_the_format_guide_opens_on_the_first_press():
    """It used to read style.display, which is empty before the first toggle."""
    source = template('graph_base')
    body = source.split('function toggleFormatGuide()', 1)[1].split(chr(10) + '        }', 1)[0]

    assert "getAttribute('aria-expanded')" in body
    assert 'const currentDisplay' not in body


@pytest.mark.parametrize('name', WORKSPACES)
def test_the_stage_is_a_named_focus_stop(name):
    """It scrolls, and a scroll box no keyboard can reach hides its content."""
    source = template(name)
    stage = source.split('class="stage" id="stage"', 1)[1].split('>', 1)[0]

    assert 'tabindex="0"' in stage, '%s stage cannot be reached' % name
    assert 'aria-labelledby="stage-heading"' in stage


def test_the_code_listing_never_scrolls_sideways():
    """It wraps instead (Phase 14), so there is no hidden half to reach. The
    listing is named, and the Expand dialog's body, which scrolls down, is a
    focus stop."""
    with open(os.path.join(STATIC, 'js', 'codeview.js'), encoding='utf-8') as fh:
        source = fh.read()
    with open(os.path.join(STATIC, 'styles.css'), encoding='utf-8') as fh:
        css = fh.read()
    listing_rules = css.split('.code-listing {', 1)[1].split('}', 1)[0]
    line_rules = css.split('.code-line code {', 1)[1].split('}', 1)[0]

    assert 'overflow-x' not in listing_rules
    assert 'pre-wrap' in line_rules
    assert "this.list.setAttribute('aria-label'" in source
    assert 'this.body.root.tabIndex = 0;' in source


# ---------------------------------------------------------------------------
# Forms
# ---------------------------------------------------------------------------

def test_the_graph_textarea_has_a_label():
    source = template('graph_base')

    assert '<label for="graph-input">' in source
    assert 'aria-describedby="graph-input-hint graph-input-error"' in source


def test_every_control_that_takes_input_is_labelled(client):
    """A placeholder is not a label: it leaves as soon as anything is typed.

    Either form counts, a label with a for= or a label the control sits
    inside, which is how the radio groups are written.
    """
    for url in PAGES:
        body = client.get(url).get_data(as_text=True)
        labelled = set(re.findall(r'<label[^>]+for="([^"]+)"', body))
        wrapped = set()
        for block in re.findall(r'<label\b(?![^>]*\bfor=)[^>]*>(.*?)</label>', body, re.S):
            wrapped.update(re.findall(r'id="([^"]+)"', block))

        for match in re.finditer(r'<(?:input|textarea|select)\b[^>]*>', body):
            tag = match.group(0)
            if re.search(r'type="(hidden|submit|button)"', tag):
                continue
            if 'aria-label' in tag:
                continue
            ident = re.search(r'id="([^"]+)"', tag)
            assert ident, '%s: a control with no id and no label: %s' % (url, tag[:70])
            assert ident.group(1) in labelled or ident.group(1) in wrapped, (
                '%s: %s has no label' % (url, ident.group(1)))


@pytest.mark.parametrize('name', WORKSPACES)
def test_every_speed_slider_is_a_full_size_target(name):
    """Without the class it keeps the native 16px track and no focus ring."""
    tag = re.search(r'<input[^>]*id="speed"[^>]*>', template(name), re.S)

    assert tag, '%s has no speed slider' % name
    assert 'speed-slider' in tag.group(0), (
        '%s keeps the native slider, which is 16px tall: %s'
        % (name, ' '.join(tag.group(0).split())))


# ---------------------------------------------------------------------------
# Titles, and the dead markup Phase 0 missed
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('url', PAGES + ['/graph?algo=%s' % a for a in GRAPH_ALGOS])
def test_every_title_names_the_site(client, url):
    body = client.get(url).get_data(as_text=True)
    title = re.search(r'<title>(.*?)</title>', body, re.S).group(1).strip()

    assert 'AlgoTrace' in title, '%s: %r' % (url, title)
    assert title != 'AlgoTrace' or url == '/', (
        '%s fell back to the layout default' % url)


@pytest.mark.parametrize('name', GRAPH_ALGOS)
def test_no_child_template_carries_a_second_document(name):
    """A child that extends another renders only its blocks, so a trailing
    document never reaches a browser and only confuses whoever reads it."""
    source = template(name)
    tail = source.rsplit('{% endblock %}', 1)[1]

    assert '<html' not in tail.lower(), '%s has a stray document after its block' % name
    assert '<!doctype' not in tail.lower(), '%s has a stray document after its block' % name


# ---------------------------------------------------------------------------
# Motion
# ---------------------------------------------------------------------------

def test_every_keyframe_animation_has_a_reduced_motion_fallback():
    css = stylesheet()
    reduced = css.split('@media (prefers-reduced-motion: reduce) {', 1)[1]

    for name in re.findall(r'@keyframes\s+([A-Za-z]\w*)', css):
        users = re.findall(r'([^{}]+)\{[^{}]*animation:\s*%s\b' % name, css)
        assert users, 'nothing uses @keyframes %s' % name
        selectors = re.split(r',', users[0])
        assert any(s.strip().split(' ')[-1].lstrip('.').split(':')[0] in reduced
                   or s.strip() in reduced for s in selectors), (
            '%s keeps moving under reduced motion' % name)


def test_the_graph_page_checks_reduced_motion_at_call_time():
    """The D3 durations are not CSS, so they are checked in JavaScript."""
    source = template('graph_base')

    assert 'const prefersReducedMotion = () =>' in source
    assert 'const dur = (ms) => prefersReducedMotion() ? 0 : ms;' in source
