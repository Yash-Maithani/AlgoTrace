# AlgoTrace: project summary

AlgoTrace is a Flask web site that plays an algorithm one step at a time, says in plain
language why it made each move, shows the line of code that ran, and counts what the move
cost. It is a learning tool for students, and a student project: no accounts, no
database, no analytics.

Source: https://github.com/Yash-Maithani/AlgoTrace (branch `main`). Licence: MIT,
copyright 2026 Yash Maithani.

## What it teaches

Twenty algorithms in three workspaces:

- **Sorting**: bubble, selection, insertion, heap, merge, quick, counting and radix sort.
  Merge sort has a stable variant, quick sort three pivot rules, bubble sort an early exit.
- **Searching**: linear, binary and jump search.
- **Graphs**: BFS, DFS, Dijkstra, Prim, Kruskal, Floyd-Warshall, Bellman-Ford and
  topological sort on a graph you type or generate, and A* on a grid you draw walls on.

Every workspace has the same layout: set up a run on the left, the visualization with
its control bar in the middle, and a Learn panel on the right with four tabs.

- **Explain**: the current step in one sentence with the real values, and a one line why.
- **Code**: pseudocode, Python, C, C++ or Java with the running line highlighted and the
  live variables beside it.
- **Complexity**: best, average and worst case with the tight bound (Theta) of each, the
  overall O, Omega and Theta, a worked example, the extra memory, and the count from this
  run beside what the formula predicts.
- **About**: the idea, an everyday analogy, and when to use it.

Other pages: **Home** (a real bubble sort played three ways), **Learn** (all twenty in a
suggested order), **Compare** (two sorts on one input), **Complexity** (O, Omega, Theta
with a chart you can drive), **Privacy** and **Terms**.

Teaching features: **Predict** mode asks what the next step will do before it plays;
**input presets** (sorted, reversed, nearly sorted, all equal); a **call tree** for the
recursion of merge and quick sort; **keyboard shortcuts** (Space, arrows, R).

## How it is built

- Flask, one `app.py`, Jinja templates, vanilla JavaScript, plain CSS. No build step,
  no bundler, no framework. D3 7.9.0 is self-hosted in `static/vendor/`.
- Algorithms are Python (`sorting_algorithms/`, `searching_algorithms/`,
  `grid_algorithms/`, and the graph algorithms in `app.py`). Each yields a step for every
  comparison, swap or write; the page replays those steps rather than guessing.
- Lesson content (idea, analogy, code listings, complexity figures) lives in
  `static/js/lessons/<algorithm>.js`, and is the single source of truth for every
  complexity figure on the site.
- All twenty algorithms also exist as real, compilable C, C++ and Java programs in
  `reference_code/`, checked step for step against the Python. The listings on the Code
  tab are extracted from them by `tools/extract_code.py`.
- `siteconfig.py` holds what a public site needs: meta tags, `SITE_URL`, robots and
  sitemap, error pages, cache and security headers.

## Properties worth knowing

- Complexity text describes this code, not the textbook. Bubble sort here has no early
  exit, so its best case is quadratic; quick sort takes the last element as its pivot, so a
  sorted list is its worst case.
- Large runs are gzipped on the way out (a 100 value bubble sort is about 7 MB of steps,
  about 256 KB on the wire).
- Pages carry a Content-Security-Policy: this site's scripts and styles and the Google
  Fonts it imports, with a nonce on every inline script and no inline event handlers.
- Every page is keyboard operable, meets 4.5:1 text contrast in both themes, and has a
  `prefers-reduced-motion` fallback.
- The browser stores two preferences in localStorage (`theme` and `pbl2.codeLanguage`),
  nothing else, and nothing is sent to a server.

## Quality checks

About 2,500 automated tests, among them: every sort's output and counts against recorded
baselines, every graph endpoint's steps against a recorded baseline, every stated
complexity bound measured by growing the input, the C, C++ and Java programs compiled and
run against the Python, and a real browser (Playwright) checking behaviour, layout at 375,
768 and 1440 pixels in both themes, reduced motion, and the Content-Security-Policy with
the network off. `python tools/check_banned_patterns.py .` enforces the writing rules.

## Deployment

Deployed on Render from the `main` branch with `gunicorn wsgi:app` (`render.yaml`).
`LAUNCH_CHECKLIST.md` lists what is done and what is left.
