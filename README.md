# Algorithm Visualizer

A Flask site that plays an algorithm one step at a time, says in plain language
why it made each move, and shows what the move cost.

Fifteen algorithms across three workspaces, each with a Learn panel that
explains the current step, highlights the line of code running, and puts the
counted work next to the formula.

Yash Maithani

## What is on the site

| Route | Page |
|---|---|
| `/` | Home, with a hero that runs a real bubble sort on eight bars and a player that reads one run three ways |
| `/learn` | Every algorithm, grouped, in a suggested beginner order |
| `/sorting` | Sorting workspace, eight algorithms |
| `/compare` | Two sorts side by side on one input, one transport for both |
| `/searching` | Searching workspace, three algorithms |
| `/graph?algo=...` | Graph workspace, eight algorithms, and A* on its own grid workspace (`?algo=astar`, in the same picker) |
| `/big-o` | How complexity works, with a growth chart you can drive |
| `/privacy`, `/terms` | Legal pages |

### Sorting

Bubble, Selection, Insertion, Heap, Merge, Quick, Counting and Radix, in
`sorting_algorithms/`. Each one yields a step for every comparison, swap and
write, and the page replays those steps rather than guessing what changed
between frames.

Counting Sort and Radix Sort (least significant digit first, base 10) never
compare two values. Both are told their key range in advance, whole numbers
from 0 to 99, refuse anything outside it with a message that says why, and
draw their working memory in a strip under the bars: the count list as a
hundred square, or the ten buckets of the current digit pass.

### Searching

Linear, Binary (iterative) and Jump, in `searching_algorithms/`. Binary and
jump search refuse an unsorted array instead of answering wrongly, explain
why, and offer to sort it for you. Jump search jumps a block of floor(sqrt n)
values at a time, then scans the one block that can hold the target.

### Graphs

BFS, DFS, Dijkstra, Prim, Kruskal, Floyd-Warshall and Bellman-Ford, generated
in `app.py` and drawn with D3. Dijkstra scans for its minimum linearly, Prim
uses `heapq`, Kruskal uses union-find and returns a spanning forest when the
graph is disconnected, and Bellman-Ford reports a negative cycle rather than
looping on one.

Topological Sort (Kahn's algorithm) reads its graph as one way arrows: the
format guide gives the directed input (`from to` per line), the arrows are
drawn with arrowheads, and Random makes a graph with no cycle. Each node shows
its in-degree in a badge, and a strip under the graph shows the queue of nodes
with in-degree 0 and the order as it builds. When a cycle makes an order
impossible the run stops and names the cycle and the nodes waiting on it. The
seven undirected algorithms read and draw their graphs exactly as before.

A* has a grid workspace of its own, reached from the same Graphs picker:
draw walls by clicking or dragging, drag the start and the goal, or use the
keyboard (arrow keys move a cursor, Space toggles a wall, S and G place the
start and goal). Moves go up, right, down and left at cost 1, the heuristic
is the Manhattan distance, and the open set is a binary heap ordered by lowest
f, then lowest h, then the order cells were pushed, so every run, and every
language, takes the same steps. Cells show f, or g, h and f when they are big
enough. "Run Dijkstra on the same grid" runs the same code with h = 0, and
the closing line compares the cells each expanded on that one grid. Presets:
Empty, Wall with a gap, Simple maze, No path.

### Predict mode

The control bar on every workspace has a **Predict** switch, off by default. When it
is on, the run pauses before some steps and asks what happens next: whether a
compared pair will swap, whether a search finds, goes left or goes right, which
node a graph search visits or joins next. The answer is read from the step that
really follows and the options come from the run's own queue, stack or
unvisited set. A score counts the run, Skip is always there, and Step back never
re-asks an answered question. The questions are built in `static/js/predict.js`;
the shared shell only asks it whether a step may play. Every algorithm has a
question: bubble sort "will these two swap?", selection sort "is this the new
smallest value?", insertion sort "will this value shift right?", merge sort
"which half is written next?", quick sort "is it smaller than the pivot?", heap
sort "will the parent move down?", counting sort "which count goes up?", radix
sort "which bucket does this value go into?", jump search "jump again or scan
back?", Kruskal "added, or a cycle?", Bellman-Ford
"will this edge shorten the distance?" and Floyd-Warshall "is the path through
k shorter?" and topological sort "which node is removed next?" and A* "which cell is expanded next?". A run with no step that can be asked about says so instead.

### The call tree

Under the stage on /sorting, Merge Sort and Quick Sort draw their recursion as a
tree of boxes (`static/js/calltree.js`). It is built only from the `depth` and
`range` every step of those two sorts already carries, so it agrees with the
stage by construction and works for every variant. A box appears when its call
starts, the call at work is highlighted and announced in words, finished calls
dim, and a merge call shows its merged result when it finishes. It is open by
default from 900px up and collapsed below, and a large tree scrolls inside its
own box.

### The Learn panel

Four tabs beside every visualization, driven by `static/js/teacher.js`:

- **Explain**: the current step in one sentence, with the real values, plus a
  one line reason. Updates on every step, forwards and backwards.
- **Code**: pseudocode, Python, C, C++ or Java, the running line highlighted, and
  the live variables beside it.
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

Install the test tools once. Playwright drives a real browser, which is how the
reduced motion, width and theme checks run against the CSS the site ships:

```bash
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
```

The second line downloads Chromium (about 150 MB, once). If you skip it, the
browser tests use a Chrome or Edge that is already installed, and if there is
none they skip. A run without them says so in a warning at the top and the
bottom, so a green result is never mistaken for a complete one. Browser tests
are in `tests/test_browser_phase14.py` and the files that follow it.

Two ways to run them:

```bash
pytest -q
```

```bash
pytest -q -m "not slow"
```

The first runs everything. The second leaves out the tests marked `slow`, the
ones that measure how counts grow across many input sizes, the ones that
compile and run the C, C++ and Java reference programs, and every test that
drives a real browser, and finishes in about fifteen seconds. Use it while working; run the full set before a commit. The
marker is registered in `pytest.ini`.

The compile tests need `gcc`, `g++` and a JDK 17 or newer (`javac` and `java`)
on the path. Without one, that language's tests skip and say what to install.

Most tests exist to prove that visual work did not change any algorithm's
behaviour:

| File | What it holds to account |
|---|---|
| `test_sorting_parity.py` | Every sort's output, comparison count and swap count against a baseline recorded before the rebuild, over 17 inputs |
| `test_graph_parity.py` | Every `/run_*` endpoint's step array, byte for byte, against its own recorded baseline, including disconnected, negative weight and negative cycle graphs |
| `test_lessons.py` | Every lesson file has the fields the step contract requires |
| `test_searching.py` | Found first, middle and last; not found; duplicates; size one; binary search blocked on unsorted input |
| `test_sorting_workspace.py`, `test_graph_workspace.py` | The ids and hooks the shared workspace code depends on |
| `test_big_o.py` | Every figure the Big O page quotes, re-derived by running the code |
| `test_kruskal.py` | Union-find behaviour on disconnected input |
| `test_variants.py` | Every variant switch: output, counts, stability, seeds, and each lesson claim measured against the code |
| `test_phase11.py` | Each case's stated Theta, checked by growing the input and counting real work (slow) |
| `test_reference_code.py` | The C, C++ and Java sorts and searches, compiled and run, match the Python step by step (slow) |
| `test_compare.py`, `test_browser_phase17.py` | `/compare`: counts equal `/run_sort`'s, both sides finish and the shorter waits, every "What to try" sentence holds, layout at 375 to 1440 in both themes, reduced motion, and the three workspaces still run after the refactor (browser half slow) |
| `test_reference_graphs.py` | The C, C++ and Java graph programs match every `/run_*` endpoint step by step on the recorded graphs and on generated ones built to hit ties, negative weights and negative cycles (slow) |
| `test_code_listings.py` | The listings generated from those programs are current and use the lesson's line ids |
| `test_phase14b.py` | Every visible source line is in its generated listing, and a statement over several lines carries its id on all of them |
| `test_browser_phase14.py` | In a real browser: reduced motion, the Code panel in every language, the Complexity tab for every algorithm and variant, no sideways scroll at 375, 768 and 1440 in both themes |
| `test_phase15.py`, `test_browser_phase15.py` | The Home player: its steps are the real `/run_sort` steps, all four cards change together on every step, it starts and pauses with the viewport, and under emulated reduced motion it stays on its frozen step while Step still works |
| `test_phase16.py`, `test_browser_phase16.py` | Predict mode: every question the builders ask, over real runs of every algorithm, has an answer that matches the step that really follows and options taken from the run; in a browser, the flow, the score, Step back, autoplay waiting, keyboard, widths and themes |
| `test_random_range.py` | One range for every random value, 1 to 99: server random arrays, presets and the searching page; every preset at every size runs on every sort, so Compare never refuses a generated input |
| `test_phase21.py`, `test_browser_phase21.py`, `test_reference_grid.py` | A*: on 400 random grids the path is as short as a BFS shortest path and valid, no path is reported exactly when BFS finds none, A* never expands more cells than Dijkstra, the tie-break and stale entries, the endpoint's refusals, the cases measured (Theta(1) and Theta(V log V) heap comparisons), the presets, the Predict question against the real open set; in a browser, drawing and erasing walls by pointer and by keyboard, moving start and goal, the Dijkstra button and result line, and the page at 375, 768 and 1440 in both themes; C, C++ and Java take the same steps with the same heap comparisons |
| `test_phase20.py`, `test_browser_phase20.py` | Topological sort: on 300 random DAGs every arrow u to v has u before v; on 300 graphs with a planted cycle the run stops, names the nodes left, and the cycle it reports is real; the step meta; exactly 2(V + E) + 1 steps on a DAG; Theta(V + E) measured; the Predict question against the real queue; in a browser, arrowheads that stop at the node's rim, no arrows on the seven undirected pages, badges and strip at 375, 768 and 1440 in both themes, step back, the random DAG generator and reduced motion |
| `test_phase19.py`, `test_browser_phase19.py` | Jump, Counting and Radix: sorted output and found index against Python's `sorted` and `index` on random, sorted, reversed, all equal, duplicate and edge-size inputs; zero comparisons; the 0 to 99 rule and its messages; every worked figure; Theta per case measured (n + k over a grid of n and k, d(n + b) as n and d grow, 1 and square root of n); the three new Predict questions against the real steps; in a browser, the strips at 375, 768 and 1440 in both themes with no bar clipped, reduced motion, and the Compare banner counting steps when a side never compares |
| `test_phase18.py`, `test_browser_phase18.py` | The call tree matches the recursion the real merge and quick sort functions made (found by profiling them, not from the step meta) for 200 runs across every variant; in a browser, the toggle, stepping forward and back, large arrays, both themes, and the seven item navbar at desktop widths |
| `test_browser_visibility.py` | What is on screen, asked of the browser rather than read from an attribute: only the chosen algorithm's variant switch, the seed only for a random pivot, on /sorting and both sides of /compare |
| `test_browser_review_fixes.py` | A run is cleared when its input changes (sorting and searching), every graph page opens with a runnable graph, every Learn panel says what to do before a run, the graph canvas and A* grid have a role and a name, and the Counting Sort count list reads at 4.5:1 in both themes |

Two more checks are not pytest:

```bash
python tools/check_banned_patterns.py .
node tests/validate_lessons.js
python tools/extract_code.py --check
```

The first enforces the project's writing rules against em dashes and emoji. It
decodes JavaScript escapes, surrogate pairs and HTML entities before it looks,
because a plain search over the source misses every one of those forms and this
project has shipped all of them. The second parses every lesson file. The third
says whether the code listings need regenerating: after editing anything in
`reference_code/`, run `python tools/extract_code.py`.

## How it is built

No build step, no bundler, no frontend framework, no CDN libraries except D3 on
the graph pages. Plain CSS, vanilla JavaScript, Jinja templates and one Flask
file.

```
app.py                     every route, and the eight graph algorithms
grid_algorithms/           A* on a grid (Dijkstra is the same code with h = 0)
teacher.py                 the one builder every step passes through
sorting_algorithms/        eight sorts, each yielding teacher steps
searching_algorithms/      linear, binary and jump search
reference_code/            all twenty algorithms in C, C++ and Java
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
  js/lessons/*.js          twenty lesson files, one per algorithm
  js/lessons/README.md     the step contract every phase follows
  js/lessons/code/*.js     C, C++ and Java listings, generated, never edited
tests/                     pytest suites and the two recorded baselines
tools/check_banned_patterns.py
tools/extract_code.py      writes js/lessons/code/ from reference_code/
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
