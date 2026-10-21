"""Launch preparation: the name, the meta tags, self-hosted D3, the production
files, robots and sitemap, error pages, cache and security headers, the licence.

The pages in a browser, with the Content-Security-Policy on and the network off,
are tests/browser/test_browser_launch.py.
"""
import hashlib
import os
from html import unescape
import re
import xml.etree.ElementTree as ET

import pytest

from paths import PACKAGE, ROOT, package_source
from wsgi import app
from algotrace.catalog import GRAPH_PICKER, SEARCH_PICKER, sorting_algo_dict
from algotrace.core import siteconfig

PAGES = ['/', '/learn', '/sorting', '/searching', '/compare', '/big-o', '/privacy', '/terms'] + \
    ['/graph?algo=%s' % key for key, _, _ in GRAPH_PICKER]


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return f.read()


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv('SITE_URL', raising=False)
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def meta(html, attr, name):
    m = re.search(r'<meta %s="%s" content="([^"]*)"' % (attr, re.escape(name)), html)
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# 1. The name
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('url', PAGES)
def test_the_site_is_called_algotrace_in_the_header_and_the_title(client, url):
    html = client.get(url).get_data(as_text=True)
    title = re.search(r'<title>(.*?)</title>', html, re.S).group(1).strip()
    logo = re.search(r'<a href="/" class="logo">(.*?)</a>', html, re.S).group(1)

    assert 'AlgoTrace' in title and 'Algorithm Visualizer' not in title, title
    assert 'AlgoTrace' in re.sub(r'<[^>]+>', '', logo)


def test_the_old_name_is_gone_from_the_pages_and_the_readme():
    for name in os.listdir(os.path.join(ROOT, 'algotrace', 'templates')):
        text = read('algotrace', 'templates', name)
        assert 'Algorithm Visualizer' not in text, name
    readme = read('README.md')
    assert readme.startswith('# AlgoTrace') and 'Algorithm Visualizer' not in readme


def test_the_footer_credit_is_untouched(client):
    for url in ('/', '/privacy', '/nope'):
        html = client.get(url).get_data(as_text=True)
        assert '<span>Yash Maithani</span>' in html, url


# ---------------------------------------------------------------------------
# 4. Meta tags on every page
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('url', PAGES)
def test_every_page_has_a_description_and_social_tags(client, url):
    html = client.get(url).get_data(as_text=True)
    title = unescape(re.search(r'<title>(.*?)</title>', html, re.S).group(1).strip())
    description = meta(html, 'name', 'description')

    assert description and 40 <= len(description) <= 200, (url, description)
    assert unescape(meta(html, 'property', 'og:title')) == title
    assert meta(html, 'property', 'og:description') == description
    assert meta(html, 'property', 'og:type') == 'website'
    assert meta(html, 'property', 'og:site_name') == 'AlgoTrace'
    assert meta(html, 'property', 'og:image').split('?')[0].endswith('/static/og-image.png')
    assert meta(html, 'property', 'og:image:width') == '1200' and meta(html, 'property', 'og:image:height') == '630'
    assert meta(html, 'name', 'twitter:card') == 'summary_large_image'
    assert unescape(meta(html, 'name', 'twitter:title')) == title
    assert meta(html, 'name', 'twitter:description') == description
    assert meta(html, 'name', 'twitter:image') == meta(html, 'property', 'og:image')


def test_descriptions_differ_page_to_page(client):
    seen = {}
    for url in ('/', '/learn', '/sorting', '/searching', '/compare', '/big-o', '/privacy', '/terms', '/graph'):
        seen[url] = meta(client.get(url).get_data(as_text=True), 'name', 'description')
    assert len(set(seen.values())) == len(seen), seen


def test_the_open_graph_image_is_1200_by_630_and_has_its_svg_source():
    png = open(os.path.join(ROOT, 'algotrace', 'static', 'og-image.png'), 'rb').read()
    svg = read('algotrace', 'static', 'og-image.svg')

    assert png[:8] == b'\x89PNG\r\n\x1a\n'
    assert (int.from_bytes(png[16:20], 'big'), int.from_bytes(png[20:24], 'big')) == (1200, 630)
    assert 'viewBox="0 0 1200 630"' in svg and 'AlgoTrace' in svg and '<rect' in svg


# ---------------------------------------------------------------------------
# SITE_URL
# ---------------------------------------------------------------------------

def test_the_canonical_url_comes_from_site_url(monkeypatch):
    monkeypatch.setenv('SITE_URL', 'https://algotrace.example/')
    app.config['TESTING'] = True
    with app.test_client() as c:
        html = c.get('/learn').get_data(as_text=True)
        assert '<link rel="canonical" href="https://algotrace.example/learn">' in html
        assert meta(html, 'property', 'og:url') == 'https://algotrace.example/learn'
        assert meta(html, 'property', 'og:image').startswith('https://algotrace.example/static/og-image.png')
        assert 'Sitemap: https://algotrace.example/sitemap.xml' in c.get('/robots.txt').get_data(as_text=True)
        locs = [e.text for e in ET.fromstring(c.get('/sitemap.xml').data).iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
        assert locs and all(loc.startswith('https://algotrace.example/') for loc in locs)


def test_without_site_url_links_follow_the_request(client):
    html = client.get('/learn').get_data(as_text=True)
    assert '<link rel="canonical" href="http://localhost/learn">' in html


def test_a_page_that_opens_on_one_algorithm_keeps_it_in_its_canonical_address(client):
    html = client.get('/graph?algo=dijkstra').get_data(as_text=True)
    assert '<link rel="canonical" href="http://localhost/graph?algo=dijkstra">' in html
    html = client.get('/sorting?algorithm=Merge+Sort').get_data(as_text=True)
    assert 'href="http://localhost/sorting?algorithm=Merge+Sort"' in html
    # Anything else in the query string is not part of the address.
    html = client.get('/learn?utm_source=x').get_data(as_text=True)
    assert '<link rel="canonical" href="http://localhost/learn">' in html


# ---------------------------------------------------------------------------
# 5. robots, sitemap, error pages, cache
# ---------------------------------------------------------------------------

def test_robots_txt(client):
    reply = client.get('/robots.txt')
    body = reply.get_data(as_text=True)

    assert reply.status_code == 200 and reply.mimetype == 'text/plain'
    assert 'User-agent: *' in body and 'Allow: /' in body and 'Disallow: /run_' in body
    assert body.strip().splitlines()[-1] == 'Sitemap: http://localhost/sitemap.xml'


def test_sitemap_is_generated_from_the_routes(client):
    reply = client.get('/sitemap.xml')
    root = ET.fromstring(reply.data)
    ns = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
    locs = [e.text for e in root.iter(ns + 'loc')]
    paths = [loc.replace('http://localhost', '') for loc in locs]

    assert reply.mimetype == 'application/xml' and root.tag == ns + 'urlset'
    for page in ('/', '/learn', '/sorting', '/searching', '/compare', '/graph', '/big-o', '/privacy', '/terms'):
        assert page in paths, page
    for key, _, _ in GRAPH_PICKER:
        assert '/graph?algo=%s' % key in paths
    for key, _, _ in SEARCH_PICKER:
        assert '/searching?algorithm=%s' % key in paths
    for name in sorting_algo_dict:
        assert '/sorting?algorithm=%s' % name.replace(' ', '+') in paths
    assert len(paths) == len(set(paths))
    # No endpoint that only answers POST, no static file, no error page.
    assert not any(p.startswith(('/run_', '/static', '/generate')) for p in paths)
    # Every address in it is a page that answers 200.
    for path in paths:
        assert client.get(path.replace('&amp;', '&')).status_code == 200, path


def test_a_missing_page_is_the_sites_own_404(client):
    reply = client.get('/no-such-page')
    html = reply.get_data(as_text=True)

    assert reply.status_code == 404 and reply.mimetype == 'text/html'
    assert 'That page is not here' in html and 'class="logo"' in html and 'Yash Maithani' in html
    assert '<meta name="robots" content="noindex">' in html
    assert '<title>Page not found | AlgoTrace</title>' in html
    assert 'href="/learn"' in html


def test_an_endpoint_that_returns_json_gets_json_errors(client):
    reply = client.post('/run_nothing', json={})
    assert reply.status_code == 404 and reply.get_json() == {'error': 'Not found.'}

    big = client.post('/run_sort', data=b'x' * (siteconfig.MAX_REQUEST_BYTES + 10), content_type='application/json')
    assert big.status_code == 413 and 'too large' in big.get_json()['error']


def test_an_unhandled_error_is_the_sites_own_500(monkeypatch):
    def boom():
        raise RuntimeError('boom')

    monkeypatch.setitem(app.view_functions, 'privacy', boom)
    monkeypatch.setitem(app.config, 'PROPAGATE_EXCEPTIONS', False)
    monkeypatch.setitem(app.config, 'TESTING', False)
    with app.test_client() as c:
        reply = c.get('/privacy')
    html = reply.get_data(as_text=True)

    assert reply.status_code == 500 and 'Something went wrong on our side' in html
    assert 'class="logo"' in html and '<meta name="robots" content="noindex">' in html
    assert 'RuntimeError' not in html and 'boom' not in html        # nothing about the failure leaks


def test_static_files_are_cache_busted_and_cached_for_a_year(client):
    html = client.get('/').get_data(as_text=True)
    css = re.search(r'href="(/static/styles\.css\?v=[0-9a-f]{12})"', html)
    assert css, 'the stylesheet link carries a version'

    versioned = client.get(css.group(1))
    assert versioned.headers['Cache-Control'] == 'public, max-age=31536000, immutable'
    assert client.get('/static/styles.css').headers['Cache-Control'] == 'public, max-age=86400'
    # Every static link on every page is versioned.
    for url in PAGES:
        page = client.get(url).get_data(as_text=True)
        for link in re.findall(r'(?:src|href)="(/static/[^"]+)"', page):
            assert '?v=' in link, (url, link)


def test_the_version_follows_the_files_contents(tmp_path):
    folder = str(tmp_path)
    (tmp_path / 'a.js').write_text('one')
    first = siteconfig._file_hash('a.js', folder)
    assert siteconfig._file_hash('a.js', folder) == first
    (tmp_path / 'a.js').write_text('two')
    os.utime(tmp_path / 'a.js', (1, 2))                     # a new modification time, as a deploy brings
    assert siteconfig._file_hash('a.js', folder) != first
    assert siteconfig._file_hash('missing.js', folder) is None


def test_pages_are_revalidated_not_cached(client):
    assert client.get('/learn').headers['Cache-Control'] == 'no-cache'


# ---------------------------------------------------------------------------
# 6. Security headers and the CSP
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('url', PAGES + ['/no-such-page'])
def test_every_page_sends_the_security_headers(client, url):
    headers = client.get(url).headers

    assert headers['X-Content-Type-Options'] == 'nosniff'
    assert headers['Referrer-Policy'] == 'strict-origin-when-cross-origin'
    assert headers['X-Frame-Options'] == 'DENY'
    assert 'Content-Security-Policy' in headers


def test_the_headers_are_on_json_too(client):
    reply = client.post('/run_sort', json={'algorithm': 'Bubble Sort', 'values': '3, 1, 2'})
    assert reply.headers['X-Content-Type-Options'] == 'nosniff'
    assert reply.headers['Referrer-Policy'] == 'strict-origin-when-cross-origin'


def directives(policy):
    return {d.split()[0]: d.split()[1:] for d in policy.split('; ')}


def test_the_policy_allows_this_site_and_the_google_fonts_it_uses_and_nothing_else(client):
    policy = client.get('/').headers['Content-Security-Policy']
    d = directives(policy)

    assert d['default-src'] == ["'self'"]
    assert d['script-src'][0] == "'self'" and len(d['script-src']) == 2 and d['script-src'][1].startswith("'nonce-")
    assert "'unsafe-inline'" not in d['script-src'] and "'unsafe-eval'" not in policy
    assert d['style-src'][0] == "'self'" and 'https://fonts.googleapis.com' in d['style-src']
    assert d['font-src'] == ["'self'", 'https://fonts.gstatic.com']
    assert d['style-src-attr'] == ["'unsafe-inline'"]                 # style="..." only; cannot run code
    assert d['object-src'] == ["'none'"] and d['frame-ancestors'] == ["'none'"]
    assert d['connect-src'] == ["'self'"] and d['base-uri'] == ["'self'"] and d['form-action'] == ["'self'"]
    hosts = set(re.findall(r'https?://[^\s;]+', policy))
    assert hosts == {'https://fonts.googleapis.com', 'https://fonts.gstatic.com'}


@pytest.mark.parametrize('url', PAGES + ['/no-such-page'])
def test_every_inline_script_and_style_carries_this_requests_nonce(client, url):
    reply = client.get(url)
    html = reply.get_data(as_text=True)
    nonce = re.search(r"'nonce-([^']+)'", reply.headers['Content-Security-Policy']).group(1)

    for tag in re.findall(r'<(script|style)\b([^>]*)>', html):
        name, attrs = tag
        if name == 'script' and 'src=' in attrs or 'application/json' in attrs:
            continue
        assert 'nonce="%s"' % nonce in attrs, (url, name, attrs)


def test_the_nonce_is_new_for_every_request(client):
    nonces = {re.search(r"'nonce-([^']+)'", client.get('/').headers['Content-Security-Policy']).group(1) for _ in range(5)}
    assert len(nonces) == 5


@pytest.mark.parametrize('url', PAGES)
def test_no_page_has_an_inline_event_handler_or_a_javascript_url(client, url):
    html = client.get(url).get_data(as_text=True)

    markup = re.sub(r'<(script|style)\b.*?</\1>', '', html, flags=re.S)     # tags only, not the code inside them
    assert not re.search(r'<[^>]+\son[a-z]+\s*=', markup), url
    assert 'javascript:' not in html


def test_no_script_in_the_source_builds_an_inline_handler_or_uses_eval():
    for folder in ('static/js', 'templates'):
        for name in os.listdir(os.path.join(PACKAGE, folder)):
            path = os.path.join(PACKAGE, folder, name)
            if not os.path.isfile(path):
                continue
            text = open(path, encoding='utf-8').read()
            assert 'eval(' not in text and 'new Function' not in text, path
            assert not re.search(r"setAttribute\(\s*['\"]on[a-z]+['\"]", text), path
            assert not re.search(r"setAttribute\(\s*['\"]style['\"]", text), path


# ---------------------------------------------------------------------------
# 2. D3, self-hosted
# ---------------------------------------------------------------------------

def test_d3_is_served_from_this_site_with_its_licence_and_a_known_hash():
    path = os.path.join(ROOT, 'algotrace', 'static', 'vendor', 'd3.v7.min.js')
    data = open(path, 'rb').read()
    readme = read('algotrace', 'static', 'vendor', 'README.md')

    assert data.startswith(b'// https://d3js.org v7.9.0')
    assert hashlib.sha256(data).hexdigest() in readme
    assert '7.9.0' in readme
    licence = read('algotrace', 'static', 'vendor', 'd3-LICENSE.txt')
    assert 'Copyright 2010-2023 Mike Bostock' in licence and 'Permission to use, copy, modify' in licence


def test_no_page_or_test_loads_d3_or_anything_else_from_a_cdn(client):
    for url in PAGES:
        html = client.get(url).get_data(as_text=True)
        assert 'd3js.org' not in html and 'cdn.' not in html and 'unpkg' not in html and 'jsdelivr' not in html, url
        # what the page loads: scripts, images and <link> tags
        loaded = set(re.findall(r'\ssrc="(https?://[^"]+)"', html)) | set(re.findall(r'<link[^>]*\shref="(https?://[^"]+)"', html))
        loaded = {u for u in loaded if 'localhost' not in u}
        assert loaded <= {'https://fonts.googleapis.com', 'https://fonts.gstatic.com'}, (url, loaded)
        # where it links to: only the project's issues page, and only for the reader to click
        linked = {u for u in re.findall(r'<a[^>]*\shref="(https?://[^"]+)"', html) if 'localhost' not in u}
        assert linked <= {'https://github.com/Yash-Maithani/AlgoTrace/issues'}, (url, linked)
    graph = client.get('/graph?algo=bfs').get_data(as_text=True)
    assert 'src="/static/vendor/d3.v7.min.js?v=' in graph
    for dirpath, _, filenames in os.walk(os.path.join(ROOT, 'tests')):
        for name in filenames:
            if name.endswith('.py'):
                needle = 'd3js.org' + '/d3'                  # built in two parts so this file does not contain it
                with open(os.path.join(dirpath, name), encoding='utf-8') as handle:
                    assert needle not in handle.read(), name   # no test loads it from the CDN either


# ---------------------------------------------------------------------------
# 3. Production
# ---------------------------------------------------------------------------

def test_debug_is_off_unless_the_environment_turns_it_on():
    source = package_source() + read('wsgi.py')

    # Nothing starts a server from code: development is `flask --app algotrace run`,
    # which turns debug mode on only when FLASK_DEBUG=1 is set.
    assert 'debug=True' not in source and 'app.run(' not in source
    assert 'flask --app algotrace run --port 5002' in read('README.md')
    assert app.debug is False


def test_the_secret_key_comes_from_the_environment_only(monkeypatch):
    source = package_source()
    assert 'SECRET_KEY' in source and "os.environ.get(\"SECRET_KEY\")" in source
    assert not re.search(r"SECRET_KEY['\"]\]\s*=\s*['\"]", source)       # never a literal


def test_wsgi_exposes_the_app_without_starting_anything():
    import wsgi
    assert wsgi.app is app
    assert 'app.run' not in read('wsgi.py')


def test_requirements_list_both_servers_per_platform_and_no_test_tools():
    text = read('requirements.txt')

    assert re.search(r'^gunicorn>=[\d.]+; sys_platform != "win32"$', text, re.M)
    assert re.search(r'^waitress>=[\d.]+; sys_platform == "win32"$', text, re.M)
    assert re.search(r'^Flask>=3', text, re.M) and 'pytest' not in text and 'playwright' not in text
    assert '-r requirements.txt' in read('requirements-dev.txt')


def test_procfile_and_render_blueprint():
    procfile = read('Procfile').strip()
    render = read('render.yaml')

    assert procfile.startswith('web: gunicorn wsgi:app') and '--bind 0.0.0.0:$PORT' in procfile
    assert 'startCommand: gunicorn wsgi:app' in render and '$PORT' in render
    assert 'buildCommand: pip install -r requirements.txt' in render
    assert 'branch: main' in render and 'https://github.com/Yash-Maithani/AlgoTrace' in render
    assert re.search(r'key: PYTHON_VERSION\s+value: 3\.11\.\d+', render)
    assert re.search(r'key: SITE_URL\s+sync: false', render)               # set in the dashboard, not committed
    assert re.search(r'key: SECRET_KEY\s+generateValue: true', render)
    assert 'runtime: python' in render and 'healthCheckPath' in render
    assert read('.python-version').strip().startswith('3.11.')


def test_the_readme_documents_the_local_production_command_for_windows():
    readme = read('README.md')

    assert 'waitress-serve' in readme and 'wsgi:app' in readme
    assert '$env:SITE_URL' in readme and 'SITE_URL' in readme and 'SECRET_KEY' in readme and 'FLASK_DEBUG' in readme


# ---------------------------------------------------------------------------
# 7 and 9. Licence, and what stays out of git
# ---------------------------------------------------------------------------

def test_the_licence_is_mit_in_yash_maithanis_name_and_the_readme_says_so():
    licence = read('LICENSE')

    assert licence.startswith('MIT License') and 'Copyright (c) 2026 Yash Maithani' in licence
    assert 'THE SOFTWARE IS PROVIDED "AS IS"' in licence
    readme = read('README.md')
    assert 'MIT' in readme.split('## Licence', 1)[1] and 'LICENSE' in readme


def test_tool_folders_stay_out_of_git():
    ignore = read('.gitignore').splitlines()
    assert '.claude/' in ignore and '.agents/' in ignore
    import subprocess
    tracked = subprocess.run(['git', 'ls-files'], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
    assert not [f for f in tracked if f.startswith(('.claude/', '.agents/'))]


# ---------------------------------------------------------------------------
# 8 and 9. The documentation, and the checklist
# ---------------------------------------------------------------------------

def test_the_project_documentation_is_current_and_describes_this_site():
    import shutil
    import subprocess
    import sys
    if shutil.which('node') is None:
        pytest.skip('node is needed to read the lesson files')
    result = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'generate_docs.py'), '--check'],
                            capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 0, result.stdout + result.stderr

    folder = os.path.join(ROOT, 'docs', 'project_documentation')
    text = ''.join(read('docs', 'project_documentation', name) for name in os.listdir(folder)
                   if name.endswith(('.md', '.txt', '.html')))
    assert 'AlgoTrace' in text and '20 algorithms' in text and 'Twenty algorithms' in text
    for stale in ('Algorithm Visualizer', 'v2.1', '10+ Algorithms', '6 Sorting + 4 Graph', '3000+ Lines'):
        assert stale not in text, stale
    assert not [n for n in os.listdir(folder) if os.path.getsize(os.path.join(folder, n)) == 0]


def test_the_checklist_matches_the_repository():
    checklist = read('docs', 'development', 'LAUNCH_CHECKLIST.md')

    assert 'Twenty of them' in checklist and 'Fifteen' not in checklist
    assert 'python tools/extract_code.py --check' in checklist
    assert 'python -m playwright install chromium' in checklist
    assert '- [x] **`app.run` is guarded**' in checklist
    assert '- [x] **D3 is self-hosted.**' in checklist
    for need in ('SITE_URL', 'SECRET_KEY', 'TRUST_PROXY', 'Custom Domains', 'CNAME', 'Render'):
        assert need in checklist, need
    assert len(os.listdir(os.path.join(ROOT, 'algotrace', 'static', 'js', 'lessons'))) >= 20
