"""The GitHub showcase: the README's top, the screenshots and the GIF."""
import os
import re
import struct

import pytest

from paths import ROOT

SHOTS = os.path.join(ROOT, 'docs', 'screenshots')
PNGS = ['home.png', 'sorting-code.png', 'compare.png', 'graph-dijkstra.png', 'astar.png', 'complexity.png',
        'complexity-chart.png']
GIF = 'predict-demo.gif'


def readme():
    with open(os.path.join(ROOT, 'README.md'), encoding='utf-8') as handle:
        return handle.read()


def test_the_readme_leads_with_the_project_in_the_order_asked_for():
    text = readme()
    assert text.startswith('# AlgoTrace\n')
    headings = re.findall(r'^## (.+)$', text, re.M)
    order = ['Screenshots', 'Features', 'Tech stack', 'Run it locally', 'Run the tests', 'Project structure',
             'Licence', 'Author']
    positions = [headings.index(h) for h in order]
    assert positions == sorted(positions), headings
    # the sentence, the live demo line and the GIF come before the first heading
    lead = text.split('\n## ')[0]
    sentence = lead.split('\n\n')[1]
    assert sentence.startswith('AlgoTrace plays 20 ') and sentence.endswith('.') and '\n' not in sentence
    assert '**Live demo:** https://algotrace-zxiw.onrender.com' in lead
    assert 'TODO' not in text
    assert 'docs/screenshots/predict-demo.gif' in lead
    assert lead.index('Live demo') < lead.index('predict-demo.gif')


def test_the_readme_names_every_feature_the_site_has():
    features = readme().split('## Features')[1].split('## Tech stack')[0]
    for word in ('20 algorithms', 'Five code views', 'Predict', 'Compare', 'Recursion tree', 'presets', 'Variants',
                 'O, Omega and Theta'):
        assert word.lower() in features.lower(), word
    for language in ('Pseudocode', 'Python', 'C++', 'Java'):
        assert language in features


def test_the_readme_has_no_badges_and_claims_no_service_it_does_not_use():
    text = readme()
    assert 'shields.io' not in text and 'badge.svg' not in text and 'badgen' not in text
    assert not re.search(r'!\[[^\]]*\]\(https?://', text), 'every image is in the repository'
    for claim in ('Docker', 'PostgreSQL', 'Redis', 'React', 'npm install', 'coverage'):
        assert claim.lower() not in text.lower().replace('no framework', ''), claim


def test_the_readme_has_a_licence_and_an_author():
    text = readme()
    assert 'MIT, copyright 2026 Yash Maithani' in text
    assert text.rstrip().splitlines()[-1].startswith('Yash Maithani')


def test_every_image_the_readme_shows_exists():
    for path in re.findall(r'!\[[^\]]*\]\(([^)]+)\)', readme()):
        assert os.path.exists(os.path.join(ROOT, path)), path
    for name in PNGS + [GIF]:
        assert 'docs/screenshots/' + name in readme(), name


@pytest.mark.parametrize('name', PNGS)
def test_each_screenshot_is_a_1440_wide_png_and_small(name):
    path = os.path.join(SHOTS, name)
    with open(path, 'rb') as handle:
        head = handle.read(32)
    assert head[:8] == b'\x89PNG\r\n\x1a\n'
    width, height = struct.unpack('>II', head[16:24])
    assert width == 1440 and 800 <= height <= 1400
    assert os.path.getsize(path) < 250 * 1024, 'optimise it: tools/make_screenshots.py does'


def test_the_gif_is_a_real_animation_under_3_mb():
    path = os.path.join(SHOTS, GIF)
    assert os.path.getsize(path) < 3 * 1024 * 1024
    with open(path, 'rb') as handle:
        assert handle.read(6) in (b'GIF87a', b'GIF89a')
    pil = pytest.importorskip('PIL.Image')
    image = pil.open(path)
    assert image.n_frames >= 8
    assert image.size[0] >= 800


def test_the_screenshots_are_made_by_a_script_in_the_repo():
    for name in ('make_screenshots.py', 'make_gif.py', 'make_icons.py'):
        assert os.path.exists(os.path.join(ROOT, 'tools', name)), name
    assert 'tools/make_screenshots.py' in readme()


def test_the_screenshots_are_not_ignored_by_git():
    with open(os.path.join(ROOT, '.gitignore'), encoding='utf-8') as handle:
        rules = [r.strip() for r in handle if r.strip() and not r.startswith('#')]
    assert not any(r.rstrip('/') in ('docs', 'docs/screenshots', '*.png', '*.gif') for r in rules)


def test_the_checklist_lists_what_is_left_for_the_owner():
    with open(os.path.join(ROOT, 'docs', 'development', 'LAUNCH_CHECKLIST.md'), encoding='utf-8') as handle:
        text = handle.read()
    assert '- [x] **Rate limit the `/run_*` endpoints.**' in text
    assert '- [x] **PNG icons and an apple-touch-icon**' in text
    assert '- [x] **A web app manifest**' in text
    assert '- [x] **The Contact section in `/terms`**' in text
    for left in ('Live demo', 'About', 'RATE_LIMIT_PER_MINUTE', 'TRUST_PROXY'):
        assert left in text, left
