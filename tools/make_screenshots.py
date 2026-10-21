"""Captures the README's screenshots and demo GIF with Playwright.

    python tools/make_screenshots.py              start the site here and capture everything
    python tools/make_screenshots.py --url http://localhost:5057   capture from a running site
    python tools/make_screenshots.py --only gif   one capture: home, sorting, compare, graph, astar, complexity, growth, gif

Writes docs/screenshots/*.png (light theme, 1440 wide) and docs/screenshots/predict-demo.gif.
Needs Playwright and Pillow (requirements-dev.txt). The images are committed, so
nothing at run time needs either. Every run uses fixed inputs, so a capture is the
same picture each time apart from the Home page's own animation.
"""
import io
import os
import sys
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "0")

from PIL import Image  # noqa: E402

from browser_helpers import launch, returning_visitor, sync_playwright  # noqa: E402

OUT = os.path.join(ROOT, "docs", "screenshots")
WIDTH, HEIGHT = 1440, 900
GIF_LIMIT = 3 * 1024 * 1024

SORT_VALUES = "34, 12, 55, 7, 81, 23, 66, 41, 9, 72, 18, 48"
COMPARE_VALUES = "34, 12, 55, 7, 81, 23, 66, 41, 9, 72, 18, 48, 60, 3"



def start_site():
    from werkzeug.serving import make_server
    from wsgi import app
    server = make_server("127.0.0.1", 0, app, threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return "http://127.0.0.1:%d" % server.server_port, server


def new_page(browser, base, path, width=WIDTH, height=HEIGHT):
    context = browser.new_context(viewport={"width": width, "height": height}, color_scheme="light",
                                  reduced_motion="no-preference", bypass_csp=True)
    returning_visitor(context)                         # no tour over the screenshot
    page = context.new_page()
    page.goto(base + path)
    page.wait_for_load_state("networkidle")
    page.context_ref = context
    return page


def step_total(page):
    return int(page.inner_text("#step-counter").split("of")[-1].strip().split()[0])


def go_to(page, fraction):
    """Press Step forward until the run is `fraction` of the way through."""
    total = step_total(page)
    target = max(1, int(total * fraction))
    page.evaluate("""(n) => { const b = document.getElementById('step-forward'); for (let i = 0; i < n; i++) b.click(); }""", target)
    page.wait_for_timeout(400)


def shrink(png_bytes, path, colours=256):
    """Palette-quantise and optimise. The interface is flat colour, so this is
    visually the same picture at a third of the size."""
    image = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    image = image.quantize(colors=colours, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    image.save(path, optimize=True)
    print("wrote %s (%d KB)" % (os.path.relpath(path, ROOT), os.path.getsize(path) // 1024))


def shot(page, name, to=None):
    """`to`: a selector to bring to the top of the window; by default the top of the page."""
    page.evaluate("""(sel) => { const e = sel && document.querySelector(sel);
                               window.scrollTo(0, e ? e.getBoundingClientRect().top + window.scrollY - 76 : 0); }""", to)
    page.wait_for_timeout(250)
    shrink(page.screenshot(), os.path.join(OUT, name))
    page.context_ref.close()


def home(browser, base):
    page = new_page(browser, base, "/")
    page.wait_for_timeout(2600)                        # the hero is running a real bubble sort
    shot(page, "home.png")


def sorting(browser, base):
    page = new_page(browser, base, "/sorting")
    page.click('#algo-picker button[data-algorithm="Quick Sort"]')
    page.check("#manual-input-choice")
    page.fill("#manual-input", SORT_VALUES)
    page.click("#run-button")
    page.wait_for_selector("#step-forward:not([disabled])")
    page.click("#learn-tab-code")
    go_to(page, 0.35)
    page.mouse.move(5, 5)
    shot(page, "sorting-code.png")


def compare(browser, base):
    page = new_page(browser, base, "/compare")
    page.check("#manual-input-choice")
    page.fill("#manual-input", COMPARE_VALUES)
    page.click("#run-button")
    page.wait_for_selector("#step-forward:not([disabled])")
    go_to(page, 0.4)
    page.mouse.move(5, 5)
    shot(page, "compare.png", to=".compare-stages")


def graph(browser, base):
    page = new_page(browser, base, "/graph?algo=dijkstra")
    page.click("#run-button")
    page.wait_for_selector("#step-forward:not([disabled])")
    go_to(page, 0.45)
    page.mouse.move(5, 5)
    shot(page, "graph-dijkstra.png")


def astar(browser, base):
    page = new_page(browser, base, "/graph?algo=astar")
    page.click("text=Simple maze")
    page.click("#run-button")
    page.wait_for_selector("#step-forward:not([disabled])")
    go_to(page, 0.5)
    page.mouse.move(5, 5)
    shot(page, "astar.png")


def complexity(browser, base):
    page = new_page(browser, base, "/big-o")
    page.wait_for_timeout(500)
    shot(page, "complexity.png", to="#notations")


def growth(browser, base):
    page = new_page(browser, base, "/big-o")
    page.fill("#growth-n", "30")
    page.dispatch_event("#growth-n", "input")
    page.check("#growth-log")                          # the log axis keeps all five curves readable
    page.evaluate("document.activeElement.blur()")
    page.wait_for_timeout(500)
    shot(page, "complexity-chart.png", to=".growth-explorer")


CAPTURES = {"home": home, "sorting": sorting, "compare": compare, "graph": graph,
            "astar": astar, "complexity": complexity, "growth": growth}


def gif(browser, base):
    from make_gif import record
    record(browser, base, os.path.join(OUT, "predict-demo.gif"), GIF_LIMIT)


def main(argv):
    os.makedirs(OUT, exist_ok=True)
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    server = None
    if "--url" in argv:
        base = argv[argv.index("--url") + 1].rstrip("/")
    else:
        base, server = start_site()
    with sync_playwright() as p:
        browser = launch(p)
        for name, capture in CAPTURES.items():
            if only in (None, name):
                capture(browser, base)
        if only in (None, "gif"):
            gif(browser, base)
        browser.close()
    if server:
        server.shutdown()


if __name__ == "__main__":
    main(sys.argv[1:])
