"""Draws the PNG icons from algotrace/static/favicon.svg.

    python tools/make_icons.py

Writes algotrace/static/favicon-32.png, icon-192.png, icon-512.png and apple-touch-icon.png.
The first three keep the SVG's rounded corners. The Apple one is a full square,
because iOS rounds the corners itself and fills any transparent corner with black.
Needs Playwright (requirements-dev.txt); the PNGs are committed, so a deployment
does not.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))

from browser_helpers import launch, sync_playwright  # noqa: E402

STATIC = os.path.join(ROOT, "algotrace", "static")
SIZES = [("favicon-32.png", 32, False), ("icon-192.png", 192, False),
         ("icon-512.png", 512, False), ("apple-touch-icon.png", 180, True)]


def main():
    with open(os.path.join(STATIC, "favicon.svg"), encoding="utf-8") as handle:
        svg = handle.read()
    with sync_playwright() as p:
        browser = launch(p)
        for name, size, square in SIZES:
            source = svg.replace('rx="6"', 'rx="0"', 1) if square else svg
            page = browser.new_page(viewport={"width": size, "height": size}, device_scale_factor=1)
            page.set_content('<style>html,body{margin:0;background:transparent}svg{display:block;width:%dpx;height:%dpx}</style>%s'
                             % (size, size, source))
            page.screenshot(path=os.path.join(STATIC, name), omit_background=True)
            page.close()
            print("wrote algotrace/static/" + name)
        browser.close()


if __name__ == "__main__":
    main()
