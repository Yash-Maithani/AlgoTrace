# Algorithm Visualizer

A Flask site that plays an algorithm one step at a time, says in plain language
why it made each move, and shows what the move cost.

Fifteen algorithms across three workspaces, each with a Learn panel that
explains the current step, highlights the line of code running, and puts the
counted work next to the formula.

Team Tri Logic: Yash Maithani

## What is on the site

| Route | Page |
|---|---|
| `/` | Home, with a hero that runs a real bubble sort on eight bars |
| `/learn` | Every algorithm, grouped, in a suggested beginner order |
| `/sorting` | Sorting workspace, six algorithms |
| `/searching` | Searching workspace, two algorithms |
| `/graph?algo=...` | Graph workspace, seven algorithms |
| `/big-o` | How complexity works, with a growth chart you can drive |
| `/privacy`, `/terms` | Legal pages |

### Sorting

Bubble, Selection, Insertion, Heap, Merge and Quick, in `sorting_algorithms/`.
Each one yields a step for every comparison, swap and write, and the page
replays those steps rather than guessing what changed between frames.

### Searching

Linear and Binary (iterative), in `searching_algorithms/`. Binary search
refuses an unsorted array instead of answering wrongly, explains why, and
offers to sort it for you.

### Graphs

BFS, DFS, Dijkstra, Prim, Kruskal, Floyd-Warshall and Bellman-Ford, generated
in `app.py` and drawn with D3. Dijkstra scans for its minimum linearly, Prim
uses `heapq`, Kruskal uses union-find and returns a spanning forest when the
graph is disconnected, and Bellman-Ford reports a negative cycle rather than
looping on one.

### The Learn panel

Four tabs beside every visualization, driven by `static/js/teacher.js`:

- **Explain**: the current step in one sentence, with the real values, plus a
  one line reason. Updates on every step, forwards and backwards.
- **Code**: pseudocode or Python, the running line highlighted, and the live
  variables beside it.
- **Complexity**: best, average and worst, each tied to a line of the code; a
  worked example at n = 5; auxiliary space; and the count from this run beside
  what the formula predicts for this n.
- **About**: the idea in three sentences, an analogy, and when to reach for it.

The complexity text describes this code, not the textbook. Bubble sort here has
no early-exit flag, so its best case is quadratic. Quick sort takes the last
element as its pivot, so a sorted array is its worst case. Heap sort's
`heapify` recurses, so it carries a logarithmic stack. Merge sort allocates
while merging and is not stable.

## Running it

Python 3.11 or newer.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

The site is then at http://localhost:5002.

`python app.py` starts Flask's development server, which is for development
only. See [LAUNCH_CHECKLIST.md](LAUNCH_CHECKLIST.md) before putting it on the
internet.

## Tests

```bash
pytest -q
```

1,118 tests. Most of them exist to prove that visual work did not change any
algorithm's behaviour:

| File | What it holds to account |
|---|---|
| `test_sorting_parity.py` | Every sort's output, comparison count and swap count against a baseline recorded before the rebuild, over 17 inputs |
| `test_graph_parity.py` | Every `/run_*` endpoint's step array, byte for byte, against its own recorded baseline, including disconnected, negative weight and negative cycle graphs |
| `test_lessons.py` | Every lesson file has the fields the step contract requires |
| `test_searching.py` | Found first, middle and last; not found; duplicates; size one; binary search blocked on unsorted input |
| `test_sorting_workspace.py`, `test_graph_workspace.py` | The ids and hooks the shared workspace code depends on |
| `test_big_o.py` | Every figure the Big O page quotes, re-derived by running the code |
| `test_kruskal.py` | Union-find behaviour on disconnected input |

Two more checks are not pytest:

```bash
python tools/check_banned_patterns.py .
node tests/validate_lessons.js
```

The first enforces the project's writing rules against em dashes and emoji. It
decodes JavaScript escapes, surrogate pairs and HTML entities before it looks,
because a plain search over the source misses every one of those forms and this
project has shipped all of them. The second parses every lesson file.

## How it is built

No build step, no bundler, no frontend framework, no CDN libraries except D3 on
the graph pages. Plain CSS, vanilla JavaScript, Jinja templates and one Flask
file.

```
app.py                     every route, and the seven graph algorithms
teacher.py                 the one builder every step passes through
sorting_algorithms/        six sorts, each yielding teacher steps
searching_algorithms/      linear and binary search
templates/
  layout.html              the shell every page extends
  landing.html             Home
  learn.html               the algorithm index
  sorting.html             sorting workspace
  searching.html           searching workspace
  big_o.html               the complexity guide
  graph_base.html          the graph workspace and the whole D3 visualizer
  bfs.html ... etc         seven children, each only an information panel
  privacy.html, terms.html
static/
  styles.css               the whole design system, one light set and one dark
  js/workspace.js          run, play, pause, step, reset, speed
  js/teacher.js            the Learn panel
  js/growth.js             the growth chart, shared by /big-o and the panel
  js/nav.js                the narrow header menu
  js/theme.js              the light and dark toggle
  js/lessons/*.js          fifteen lesson files, one per algorithm
  js/lessons/README.md     the step contract every phase follows
tests/                     pytest suites and the two recorded baselines
tools/check_banned_patterns.py
DESIGN.md                  the design spec
REBUILD_PLAN.md            the plan the rebuild followed
LAUNCH_CHECKLIST.md        what is left before this goes live
```

### The step contract

Every step carries `action`, `indices`, `values`, `line`, `vars` and
`explain: {beginner, why}`. Sorting and searching steps keep their original
`array` and `compared` fields alongside, so the drawing code did not have to
change. Graph endpoints keep their typed step arrays and return a parallel
`meta` list of the same length. `static/js/lessons/README.md` is the
authoritative description.

### Endpoints that return steps

| Method | Route | Returns |
|---|---|---|
| POST | `/run_sort` | `{steps, meta, result}` for one sort |
| POST | `/run_search` | `{steps, meta, result}` for one search |
| POST | `/run_bfs`, `/run_dfs`, `/run_dijkstra`, `/run_prim`, `/run_bellman_ford` | `{steps, meta, ...}` from `{"graph": {...}, "start": "A"}` |
| POST | `/run_kruskal`, `/run_floyd_warshall` | `{steps, meta, ...}` from `{"nodes": [...], "edges": [[u, v, w], ...]}` |
| POST | `/generate_random_graph` | a connected random graph |

Unreachable distances come back as the string for infinity, never a bare
`Infinity`, because JSON has no infinity literal and `JSON.parse` rejects one.
`_wire()` in `app.py` is the only place that converts, and `isUnreachable()` in
`graph_base.html` is the only place that reads it.

## Accessibility and motion

Every page is keyboard operable end to end, with a visible focus ring on every
stop. Text meets 4.5:1 in both themes, state is never carried by colour alone,
and the colour keys name every state in words. Every animation has a
`prefers-reduced-motion` fallback that stops the movement and keeps the state
colours, so nothing is hidden by turning motion off. Checked at 375px, 768px
and 1440px.

## Licence

None chosen yet. See [LAUNCH_CHECKLIST.md](LAUNCH_CHECKLIST.md).
