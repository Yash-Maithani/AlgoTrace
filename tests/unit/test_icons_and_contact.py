"""PNG icons, the web app manifest, and the contact line on /terms."""
import json
import os
import re
import struct

import pytest

from paths import PACKAGE, ROOT
from wsgi import app

client = app.test_client()
ICON_FILES = {'favicon-32.png': 32, 'icon-192.png': 192, 'icon-512.png': 512, 'apple-touch-icon.png': 180}
PAGES = ['/', '/learn', '/sorting', '/searching', '/compare', '/big-o', '/privacy', '/terms', '/graph?algo=bfs',
         '/graph?algo=astar', '/nope']


def png_size(path):
    with open(path, 'rb') as handle:
        head = handle.read(24)
    assert head[:8] == b'\x89PNG\r\n\x1a\n', path
    return struct.unpack('>II', head[16:24])


@pytest.mark.parametrize('name,size', sorted(ICON_FILES.items()))
def test_each_icon_is_a_png_of_the_stated_size(name, size):
    assert png_size(os.path.join(ROOT, 'algotrace', 'static', name)) == (size, size)


def test_the_icons_are_drawn_from_the_svg_by_a_script_in_the_repo():
    assert os.path.exists(os.path.join(ROOT, 'tools', 'make_icons.py'))
    with open(os.path.join(ROOT, 'algotrace', 'static', 'favicon.svg'), encoding='utf-8') as handle:
        assert 'AlgoTrace' in handle.read()


@pytest.mark.parametrize('path', PAGES)
def test_every_page_links_the_icons_and_the_manifest(path):
    html = client.get(path).get_data(as_text=True)
    links = re.findall(r'<link\b[^>]*>', html)

    def link(rel, **match):
        for tag in links:
            if 'rel="%s"' % rel in tag and all(('%s="%s"' % (k, v)) in tag for k, v in match.items()):
                return re.search(r'href="([^"]+)"', tag).group(1)
        return None

    assert link('icon', type='image/svg+xml').startswith('/static/favicon.svg?v=')
    assert link('icon', sizes='32x32').startswith('/static/favicon-32.png?v=')
    assert link('icon', sizes='192x192').startswith('/static/icon-192.png?v=')
    assert link('apple-touch-icon', sizes='180x180').startswith('/static/apple-touch-icon.png?v=')
    assert link('manifest') == '/site.webmanifest'
    # every address the head names answers
    for rel in ('icon', 'apple-touch-icon', 'manifest'):
        for tag in links:
            if 'rel="%s"' % rel in tag:
                href = re.search(r'href="([^"]+)"', tag).group(1)
                assert client.get(href).status_code == 200, href


def test_the_manifest_names_the_site_and_points_at_real_icons():
    response = client.get('/site.webmanifest')
    assert response.status_code == 200
    assert response.mimetype == 'application/manifest+json'
    manifest = json.loads(response.get_data(as_text=True))
    assert manifest['name'] == manifest['short_name'] == 'AlgoTrace'
    assert manifest['start_url'] == '/' and manifest['scope'] == '/'
    assert manifest['display'] == 'standalone'
    sizes = set()
    for icon in manifest['icons']:
        assert icon['type'] == 'image/png'
        assert client.get(icon['src']).status_code == 200
        w, h = (int(n) for n in icon['sizes'].split('x'))
        assert png_size(os.path.join(PACKAGE, icon['src'].split('?')[0].lstrip('/'))) == (w, h)
        sizes.add(w)
    assert sizes == {192, 512}


def test_the_manifest_colours_are_the_sites_own():
    manifest = client.get('/site.webmanifest').get_json()
    with open(os.path.join(ROOT, 'algotrace', 'static', 'styles.css'), encoding='utf-8') as handle:
        css = handle.read()
    for key in ('theme_color', 'background_color'):
        assert re.fullmatch(r'#[0-9A-Fa-f]{6}', manifest[key])
        assert manifest[key].upper() in css.upper(), key
    layout = client.get('/').get_data(as_text=True)
    assert 'content="%s" media="(prefers-color-scheme: light)"' % manifest['theme_color'] in layout


def test_the_manifest_is_not_a_sitemap_entry_and_is_not_noindexed_by_robots():
    assert 'webmanifest' not in client.get('/sitemap.xml').get_data(as_text=True)
    assert 'webmanifest' not in client.get('/robots.txt').get_data(as_text=True)


def test_the_policy_allows_the_icons_and_the_manifest_and_nothing_wider():
    csp = client.get('/').headers['Content-Security-Policy']
    assert "manifest-src 'self'" in csp
    assert "img-src 'self' data:" in csp
    assert 'http' not in re.search(r"img-src[^;]*", csp).group(0)


def test_icons_are_cached_for_a_year_by_their_versioned_address():
    href = re.search(r'href="(/static/icon-192\.png\?v=[0-9a-f]+)"', client.get('/').get_data(as_text=True)).group(1)
    assert 'max-age=31536000' in client.get(href).headers['Cache-Control']


def test_terms_points_to_the_github_issues_page_and_gives_no_email_address():
    html = client.get('/terms').get_data(as_text=True)
    contact = html[html.index('<h2>Contact</h2>'):]
    assert 'href="https://github.com/Yash-Maithani/AlgoTrace/issues"' in contact
    assert 'rel="noopener noreferrer"' in contact
    assert not re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', html), 'an email address is on the terms page'
    assert 'mailto:' not in html
