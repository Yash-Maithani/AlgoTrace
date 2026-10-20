"""Records the README's demo GIF: a bubble sort played with Predict on.

Used by tools/make_screenshots.py. The run is fixed (seven values), and each
question is answered from the numbers in its own prompt, one of them deliberately
wrong so the GIF shows what a wrong answer looks like.
"""
import io
import os
import re

from PIL import Image

from browser_helpers import returning_visitor

VIEW = (1280, 760)
OUT_WIDTH = 960
VALUES = "45, 22, 78, 10, 91, 33, 60"
QUESTIONS = 4
WRONG_ON = 3                      # the third question is answered wrongly, on purpose


def snap(page):
    return Image.open(io.BytesIO(page.screenshot())).convert("RGB")


def click(page, selector):
    """Click from script, so the page never scrolls to bring the button into view."""
    page.evaluate("(s) => document.querySelector(s).click()", selector)
    page.wait_for_timeout(350)


def answer(page, number):
    prompt = page.inner_text(".predict-prompt")
    left, right = (int(n) for n in re.search(r"compares (\d+) and (\d+)", prompt).groups())
    swaps = left > right
    if number == WRONG_ON:
        swaps = not swaps
    click(page, '.predict-option[data-option="%s"]' % ("yes" if swaps else "no"))


def build(frames, path, limit):
    """frames: [(image, milliseconds)]. One shared palette, so colours do not flicker."""
    width = OUT_WIDTH
    height = round(frames[0][0].height * width / frames[0][0].width)
    sized = [(img.resize((width, height), Image.LANCZOS), ms) for img, ms in frames]
    for colours in (128, 64, 32):
        montage = Image.new("RGB", (width, height * len(sized)))
        for i, (img, _) in enumerate(sized):
            montage.paste(img, (0, i * height))
        palette = montage.quantize(colors=colours, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        paletted = [img.quantize(palette=palette, dither=Image.Dither.NONE) for img, _ in sized]
        paletted[0].save(path, save_all=True, append_images=paletted[1:], duration=[ms for _, ms in sized],
                         loop=0, optimize=True, disposal=1)
        size = os.path.getsize(path)
        if size <= limit:
            break
    print("wrote %s (%d KB, %d frames, %d colours)" % (os.path.relpath(path), size // 1024, len(sized), colours))
    if size > limit:
        raise SystemExit("the GIF is over %d bytes" % limit)


def record(browser, base, path, limit):
    context = browser.new_context(viewport={"width": VIEW[0], "height": VIEW[1]}, color_scheme="light",
                                  reduced_motion="no-preference", bypass_csp=True)
    returning_visitor(context)
    page = context.new_page()
    page.goto(base + "/sorting")
    page.wait_for_load_state("networkidle")
    page.click('#algo-picker button[data-algorithm="Bubble Sort"]')
    page.check("#manual-input-choice")
    page.fill("#manual-input", VALUES)
    page.evaluate("window.scrollTo(0, 0)")
    page.mouse.move(2, 2)
    frames = [(snap(page), 1200)]                       # the page before anything has run

    page.check("#predict-toggle")
    page.evaluate("window.scrollTo(0, 0)")
    click(page, "#run-button")
    page.evaluate("window.scrollTo(0, 0)")
    frames.append((snap(page), 900))                    # Predict on, run loaded

    for number in range(1, QUESTIONS + 1):
        click(page, "#step-forward")
        while not page.query_selector(".predict-card"):
            click(page, "#step-forward")
        page.evaluate("window.scrollTo(0, 0)")
        frames.append((snap(page), 1700))               # the question
        answer(page, number)
        page.evaluate("window.scrollTo(0, 0)")
        frames.append((snap(page), 2300))               # what the answer was, and the score

    for _ in range(3):                                  # then let it play a little
        for _ in range(4):
            click(page, ".predict-skip") if page.query_selector(".predict-card") else click(page, "#step-forward")
        page.evaluate("window.scrollTo(0, 0)")
        frames.append((snap(page), 900))
    context.close()
    build(frames, path, limit)
