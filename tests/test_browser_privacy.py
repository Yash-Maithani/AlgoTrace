"""The privacy page's storage table fits at every width in both themes.
Needs Playwright; see tests/test_browser_phase14.py and requirements-dev.txt.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_helpers import SKIP_REASON, available, page_for

pytestmark = pytest.mark.skipif(not available(), reason=SKIP_REASON)


@pytest.mark.parametrize('scheme', ['light', 'dark'])
@pytest.mark.parametrize('width,height', [(375, 812), (768, 1024), (1440, 900)])
def test_the_storage_table_is_readable_and_never_widens_the_page(browser, base_url, width, height, scheme):
    page = page_for(browser, base_url, '/privacy', width=width, height=height, scheme=scheme)

    assert page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth") <= 0
    keys = page.evaluate("[...document.querySelectorAll('.table-scroll tbody th code')].map(c => c.textContent)")
    assert keys == ['theme', 'pbl2.codeLanguage', 'pbl2.tourSeen']
    box = page.evaluate("(() => { const r = document.querySelector('.table-scroll').getBoundingClientRect(); return [r.left, r.right]; })()")
    assert box[0] >= 0 and box[1] <= width
    for heading in ('What is stored in your browser', 'How to clear them'):
        assert page.is_visible('text=%s' % heading)
    assert page.errors == []
    page.ctx.close()
