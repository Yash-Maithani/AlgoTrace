"""Links, the input fieldset and the growth chart look like this site, not like the browser.

  * no visible link anywhere uses the browser's default blue, purple or underline-only
    look, on any page, in either theme, at 375, 768 and 1440
  * a link has a clear hover state and a clear keyboard focus ring
  * the "One input for both" fieldset is the site's panel, not the default groove
  * the /big-o growth chart gives each of its five curves its own colour and its own
    line style, with a legend, and keeps its accessible description

Needs Playwright; see tests/test_browser_phase14.py and requirements-dev.txt.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_helpers import SKIP_REASON, available, page_for, returning_visitor

pytestmark = pytest.mark.skipif(not available(), reason=SKIP_REASON)

PAGES = (['/', '/learn', '/sorting', '/searching', '/compare', '/big-o', '/privacy', '/terms', '/nope']
         + ['/graph?algo=' + a for a in ('bfs', 'dfs', 'dijkstra', 'prim', 'kruskal', 'floyd_warshall',
                                         'bellman_ford', 'topological_sort', 'astar')])
SIZES = [(375, 'light'), (375, 'dark'), (768, 'light'), (768, 'dark'), (1440, 'light'), (1440, 'dark')]

# What Chromium paints a link when nothing styles it: link, visited, and the same two
# when the page says color-scheme: dark.
BROWSER_DEFAULTS = {'rgb(0, 0, 238)', 'rgb(85, 26, 139)', 'rgb(158, 158, 255)', 'rgb(208, 173, 240)'}

VISIBLE_LINKS = """() => {
    const luminance = (rgb) => {
        const [r, g, b] = rgb.map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
        return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    };
    const parse = (css) => { const m = css.match(/[\\d.]+/g).map(Number); return { rgb: m.slice(0, 3), a: m.length > 3 ? m[3] : 1 }; };
    const background = (node) => {
        for (let n = node; n; n = n.parentElement) {
            const c = parse(getComputedStyle(n).backgroundColor);
            if (c.a > 0.99) return c.rgb;
        }
        return [255, 255, 255];
    };
    const out = [];
    for (const a of document.querySelectorAll('a[href]')) {
        const r = a.getBoundingClientRect();
        const cs = getComputedStyle(a);
        if (!r.width || !r.height || cs.visibility === 'hidden' || cs.display === 'none') continue;
        const fg = parse(cs.color).rgb, bg = background(a);
        const hi = Math.max(luminance(fg), luminance(bg)), lo = Math.min(luminance(fg), luminance(bg));
        out.push({ text: a.textContent.trim().replace(/\\s+/g, ' ').slice(0, 40), href: a.getAttribute('href'),
                   color: cs.color, contrast: (hi + 0.05) / (lo + 0.05), cls: a.className });
    }
    return out;
}"""


def collect(context, base_url, path):
    page = context.new_page()
    try:
        page.goto(base_url + path, wait_until='load')
        if path == '/compare':                                  # the "Open in Sorting" links appear with a run
            page.click('#run-button')
            page.wait_for_selector('[data-role="open"]')
        return page.evaluate(VISIBLE_LINKS)
    finally:
        page.close()


@pytest.mark.parametrize('width,scheme', SIZES)
def test_no_visible_link_uses_the_browsers_default_colour_and_all_are_readable(browser, base_url, width, scheme):
    """On every page: not the browser's blue or purple, and 4.5:1 against what is behind it."""
    context = returning_visitor(browser.new_context(viewport={'width': width, 'height': 900}, color_scheme=scheme, bypass_csp=True))
    defaults, unreadable = [], []
    try:
        for path in PAGES:
            links = collect(context, base_url, path)
            assert links, path
            for link in links:
                if link['color'] in BROWSER_DEFAULTS:
                    defaults.append((path, link['text'], link['color']))
                if link['contrast'] < 4.5:
                    unreadable.append((path, link['text'], link['color'], round(link['contrast'], 2)))
    finally:
        context.close()
    assert not defaults, defaults[:10]
    assert not unreadable, unreadable[:10]


def test_a_browser_default_link_is_what_the_check_looks_for(browser):
    """Guard the guard: an unstyled link in this browser really is one of those colours."""
    for scheme in ('light', 'dark'):
        ctx = browser.new_context(color_scheme=scheme)
        page = ctx.new_page()
        page.set_content('<style>:root{color-scheme:%s}</style><a href="#x">plain</a>' % scheme)
        assert page.evaluate("getComputedStyle(document.querySelector('a')).color") in BROWSER_DEFAULTS
        ctx.close()


@pytest.mark.parametrize('scheme', ['light', 'dark'])
def test_a_link_has_a_hover_state_and_a_focus_ring(browser, base_url, scheme):
    page = page_for(browser, base_url, '/big-o', scheme=scheme)
    try:
        link = page.locator('.page-toc a').first
        rest = page.evaluate("""(el) => { const c = getComputedStyle(el); return { color: c.color, thickness: c.textDecorationThickness, line: c.textDecorationLine }; }""",
                             link.element_handle())
        assert 'underline' in rest['line']                                  # not told apart by colour alone
        link.hover()
        page.wait_for_timeout(150)
        hovered = page.evaluate("""(el) => { const c = getComputedStyle(el); return { color: c.color, thickness: c.textDecorationThickness }; }""",
                                link.element_handle())
        assert hovered['color'] != rest['color'], 'hover changes the colour'
        assert hovered['thickness'] != rest['thickness'], 'hover thickens the underline'
        page.mouse.move(0, 0)

        page.evaluate("document.querySelector('.page-toc a').focus()")
        page.keyboard.press('Tab')
        page.keyboard.press('Shift+Tab')                                    # focus-visible only shows for the keyboard
        ring = page.evaluate("""() => { const c = getComputedStyle(document.activeElement);
                                        return { style: c.outlineStyle, width: c.outlineWidth, color: c.outlineColor, tag: document.activeElement.tagName }; }""")
        assert ring['tag'] == 'A'
        assert ring['style'] == 'solid' and float(ring['width'].replace('px', '')) >= 2, ring
        assert ring['color'] != 'rgb(255, 255, 255)'
    finally:
        page.ctx.close()


@pytest.mark.parametrize('width,scheme', SIZES)
def test_the_input_fieldset_is_the_sites_panel(browser, base_url, width, scheme):
    page = page_for(browser, base_url, '/compare', width=width, scheme=scheme)
    try:
        info = page.evaluate("""() => {
            const pick = (sel) => { const c = getComputedStyle(document.querySelector(sel));
                return { style: c.borderTopStyle, width: c.borderTopWidth, color: c.borderTopColor, radius: c.borderTopLeftRadius }; };
            const box = document.querySelector('.input-method').getBoundingClientRect();
            return { input: pick('.input-method'), panel: pick('.compare-pick'),
                     legend: getComputedStyle(document.querySelector('.input-method > legend')).fontWeight,
                     overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
                     right: box.right, viewport: window.innerWidth };
        }""")
        assert info['input'] == info['panel'], 'same border, colour and radius as the algorithm pickers'
        assert info['input']['style'] == 'solid' and info['input']['width'] == '1px'
        assert info['input']['radius'] != '0px'
        assert int(info['legend']) >= 600
        assert info['overflow'] <= 0 and info['right'] <= info['viewport']
    finally:
        page.ctx.close()


def test_the_sorting_page_input_fieldset_matches(browser, base_url):
    page = page_for(browser, base_url, '/sorting', width=1440)
    try:
        style = page.evaluate("""() => { const c = getComputedStyle(document.querySelector('.input-method'));
                                          return [c.borderTopStyle, c.borderTopWidth, c.borderTopLeftRadius]; }""")
        assert style == ['solid', '1px', '8px'] or style[:2] == ['solid', '1px']
    finally:
        page.ctx.close()


CURVE_JS = """() => {
    const out = {};
    for (const p of document.querySelectorAll('#growth-host svg.growth-chart path')) {
        const c = getComputedStyle(p);
        out[p.getAttribute('data-curve')] = { stroke: c.stroke, dash: c.strokeDasharray, width: c.strokeWidth, cls: p.getAttribute('class') };
    }
    const legend = [...document.querySelectorAll('#growth-host .growth-legend-item')].map(li => {
        const line = li.querySelector('line'); const c = getComputedStyle(line);
        return { text: li.textContent.trim(), stroke: c.stroke, dash: c.strokeDasharray, hidden: li.querySelector('svg').getAttribute('aria-hidden') };
    });
    const svg = document.querySelector('#growth-host svg.growth-chart');
    return { curves: out, legend, label: svg.getAttribute('aria-label'), role: svg.getAttribute('role'),
             caption: document.querySelector('#growth-host .growth-caption').textContent,
             table: document.querySelectorAll('#growth-host .growth-data tr').length };
}"""


@pytest.mark.parametrize('width,scheme', SIZES)
@pytest.mark.parametrize('log', [False, True])
def test_the_growth_chart_has_five_distinct_curves_and_a_legend(browser, base_url, width, scheme, log):
    page = page_for(browser, base_url, '/big-o', width=width, scheme=scheme)
    try:
        if log:
            page.check('#growth-log')
        page.wait_for_selector('#growth-host svg.growth-chart')
        data = page.evaluate(CURVE_JS)
        keys = ['1', 'logn', 'n', 'nlogn', 'n2']
        assert list(data['curves']) == keys
        strokes = [data['curves'][k]['stroke'] for k in keys]
        dashes = [data['curves'][k]['dash'] for k in keys]
        assert len(set(strokes)) == 5, 'each curve has its own colour'
        assert len(set(dashes)) == 5, 'and its own line style, so colour is not the only difference'
        assert all(d != 'none' for d in dashes[:4]) and dashes[4] == 'none'
        # the legend names them, with the same colour and line style as the curves
        assert [item['text'] for item in data['legend']] == ['O(1)', 'O(log n)', 'O(n)', 'O(n log n)', 'O(n squared)']
        assert [item['stroke'] for item in data['legend']] == strokes
        assert [item['dash'] for item in data['legend']] == dashes
        assert all(item['hidden'] == 'true' for item in data['legend'])
        # the accessible description is the one it always had
        assert data['role'] == 'img'
        assert data['label'].startswith('The five common growth curves, for n up to 20.')
        assert data['caption'].startswith('The five common growth curves')
        assert data['table'] == 6
        assert ('vertical axis is logarithmic' in data['label']) == log
    finally:
        page.ctx.close()


@pytest.mark.parametrize('scheme', ['light', 'dark'])
def test_every_growth_curve_clears_3_to_1_on_its_panel(browser, base_url, scheme):
    page = page_for(browser, base_url, '/big-o', scheme=scheme)
    try:
        page.wait_for_selector('#growth-host svg.growth-chart')
        ratios = page.evaluate("""() => {
            const lum = (rgb) => { const [r, g, b] = rgb.map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }); return 0.2126*r + 0.7152*g + 0.0722*b; };
            const nums = (css) => css.match(/[\\d.]+/g).map(Number).slice(0, 3);
            const bg = nums(getComputedStyle(document.querySelector('.growth-explorer')).backgroundColor);
            const out = {};
            for (const p of document.querySelectorAll('#growth-host svg.growth-chart path')) {
                const a = lum(nums(getComputedStyle(p).stroke)), b = lum(bg);
                out[p.getAttribute('data-curve')] = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
            }
            return out;
        }""")
        assert all(r >= 3 for r in ratios.values()), ratios
    finally:
        page.ctx.close()


def test_a_workspace_complexity_chart_is_unchanged(browser, base_url):
    """Beside an algorithm's own figures the chart is still faint references and one accent curve."""
    page = page_for(browser, base_url, '/sorting')
    try:
        page.click('#run-button')
        page.wait_for_selector('#step-forward:not([disabled])')
        page.click('#learn-tab-complexity')
        page.wait_for_selector('.growth-chart')
        classes = page.evaluate("[...document.querySelectorAll('.learn-panel .growth-chart path')].map(p => p.getAttribute('class'))")
        assert classes.count('growth-mine') == 1 and 'growth-curve' not in classes
        assert page.evaluate("document.querySelectorAll('.learn-panel .growth-legend').length") == 0
    finally:
        page.ctx.close()
