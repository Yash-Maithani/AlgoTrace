# PBL2 Rebuild Plan

This plan replaced REDESIGN_PLAN.md, which has since been deleted. Every coding session reads this file first and does ONE phase only.

## Goal

Turn the Algorithm Visualizer into a beginner-friendly learning site: a new layout and visual design, a new Searching section, a teacher mode that explains each step with code, and plain-language time and space complexity next to every visualization.

## Facts about the codebase (checked 16 Oct 2026)

- Flask app, one file: `app.py`. No build step, no frontend framework. Sorting runs as a form POST and the page embeds the steps as JSON. Graph pages fetch steps from `/run_<algo>` JSON endpoints.
- Live templates: `landing.html` (served at `/`), `sorting.html`, `graph_base.html` (3,263 lines; all D3 graph logic inline) plus 7 child templates that only fill `{% block extra_content %}`.
- Every live page is a standalone HTML document with its own head and navbar. There is no shared layout template in use.
- Dead code (not used by `app.py`): `app_new.py`, `routes/`, `services/`, `algorithms/`, `templates/index.html`, `templates/base.html`, `templates/sorting_new.html`, `templates/bellman_ford_new.html`, `static/js/graph-visualizer.js`, and everything after the last `{% endblock %}` in `bfs.html`, `dfs.html`, `dijkstra.html`, `prim.html`.
- Sorting steps are only `{array, compared}`. The page guesses compare vs swap by diffing arrays. Graph steps are typed arrays like `["visit", node]`.
- BFS, DFS and Dijkstra never call `displayResults()`, so their results panel stays empty.
- `static/privacy.html`, `static/terms.html`, `static/favicon.svg`, `static/js/theme.js` (light/dark toggle) already exist.
- D3 v7 is loaded from d3js.org on graph pages only. Font Awesome 5 loads from cdnjs.

### Complexity facts that must match the ACTUAL code, not the textbook

- Bubble Sort here has no early-exit flag, so it always makes n(n-1)/2 comparisons. Its best case is O(n^2), not O(n). The site currently shows O(n). Fix the text, keep the code, and mention the early-exit variant as a side note.
- Quick Sort uses the last element as pivot, so an already sorted array is its worst case: O(n^2) time and O(n) recursion depth.
- Heap Sort's `heapify` is recursive, so auxiliary space is O(log n) recursion stack, not O(1).
- Merge Sort allocates temporary lists while merging: O(n) auxiliary space.
- Dijkstra picks the next node with a linear `min()` scan: O(V^2) time, not O((V+E) log V).
- Prim uses `heapq`: O(E log E) time.
- Re-derive every other algorithm from its code the same way before writing its text.

## Non-negotiable rules

1. Do not change how the sorting bars or graph nodes and edges animate. Layout may move their containers. Before moving any markup, list every id and class the page's JS selects and keep them all.
2. Do not change algorithm results, comparison counts or swap counts. Tests must prove it.
3. Keep the credit line "Yash Maithani" exactly as written.
4. Keep the vibrant palette from commit 83b8f1b in both light and dark mode, and the existing theme toggle.
5. No new frameworks, bundlers or npm packages. Plain HTML, CSS, vanilla JS, Jinja, Python. No new CDN libraries.
6. Never use: purple gradients, pill-shaped buttons, fake reviews, fake metrics, fake user counters, vague hero text, emoji icons, em dashes, over-the-top scroll effects, cursor effects, AI stock photos, AI-sounding copy.
7. Every animation respects `prefers-reduced-motion` (static fallback, nothing hidden).
8. Commit at the end of each phase with a clear message. Run the app and the tests before committing.

## Information architecture

| Route | Page | Status |
|---|---|---|
| `/` | Home (landing) | redesign |
| `/learn` | Algorithm index: every algorithm, grouped, with a suggested beginner order | new (replaces the dead index.html) |
| `/sorting` | Sorting workspace | re-layout |
| `/searching` | Searching workspace | new |
| `/graph?algo=...` | Graph workspace | re-layout |
| `/big-o` | "How complexity works" guide | new |
| `/privacy`, `/terms` | Legal pages inside the shared layout | move from static/ |

Navbar: Home, Learn, Sorting, Searching, Graphs, Big O, theme toggle. Footer: credit line, Privacy, Terms.

Suggested beginner order on `/learn`: Linear Search, Binary Search, Bubble, Selection, Insertion, Merge, Quick, Heap, BFS, DFS, Dijkstra, Prim, Kruskal, Bellman-Ford, Floyd-Warshall.

## Shared workspace layout (sorting, searching, graph)

- Desktop: left column for algorithm picker and input; center stage for the visualization with a control bar directly under it (play, pause, step back, step forward, reset, speed) and a color legend; right column is a tabbed Learn panel.
- Learn panel tabs:
  - Explain: the current step in one beginner sentence with real values, plus a one-line "why". Updates on every step.
  - Code: pseudocode and Python tabs, current line highlighted, live variables (i, j, low, mid, high, pivot, queue, visited...).
  - Complexity: see the complexity spec below.
  - About: the idea in 3 sentences, a real-world analogy, when to use it.
- Mobile: stage first, sticky control bar, then the Learn panel as tabs below. No horizontal scrolling at 375px.

## Complexity spec (every algorithm, including search)

1. Time: best, average, worst, each with a one-line reason tied to the code ("the inner loop runs n-1, then n-2... times").
2. Worked example: a tiny input (n = 5) with the exact count of comparisons for that input.
3. Auxiliary space: name the extra memory (a few variables, a temp list, the recursion stack, a queue and visited set, a distance matrix) and its Big O. Explain "auxiliary" means memory used on top of the input.
4. "This run" box: the counted comparisons/swaps from the visualization next to the formula's value for this n, with the sentence: "Big O describes how work grows as the input grows and ignores constants. The counter shows the exact work for this one input."
5. A small growth bar comparing this algorithm's curve with O(1), O(log n), O(n), O(n log n), O(n^2) for the current n. Drawn with plain SVG.

## Searching section spec

- Algorithms: Linear Search and Binary Search (iterative). Steps generated in Python like sorting, new folder `searching_algorithms/`, new JSON endpoint `/run_search`.
- Input: generate random array (size 5 to 30), or type comma-separated integers, with validation messages. Target: type a number, or buttons "pick a value that exists" and "pick a value that does not exist".
- Binary Search must have sorted input. If the array is unsorted, block the run, explain why in one sentence, and offer a "Sort it for me" button. Explain that each step halves the range.
- Visual: array cells with index labels; current cell highlighted; for binary search show low, mid, high pointers and grey out the discarded range; comparisons counter; final banner "Found 42 at index 6 after 3 comparisons" or "42 is not in the array. Checked 4 values."
- Controls: play, pause, step forward, step back, reset, speed.
- Each step carries action, indices, low/mid/high, line id, and explanation text, matching the step format below.

## Step format (teacher mode)

Sorting and searching steps keep their existing fields and add:
`action`, `indices`, `values`, `line`, `vars`, `explain: {beginner, why}`.
Graph endpoints keep their current step arrays and add a parallel `meta` list with the same fields.
Lesson content lives in `static/js/lessons/<algorithm>.js`: pseudocode and Python with line ids, idea, analogy, when to use, complexity text.

## Phases

| # | Phase | Model, effort |
|---|---|---|
| 0 | Restore tag, delete dead code, fix empty results panel for BFS/DFS/Dijkstra | Sonnet, Low |
| 1 | Design spec: write DESIGN.md (layout grid, type scale, spacing, components, page wireframes in text, motion rules). No code. | Opus, Medium |
| 2 | Shared layout template + CSS tokens + navbar/footer; move privacy/terms into it | Sonnet, Medium |
| 3 | Home and /learn pages with purposeful animations | Sonnet, Medium |
| 4 | Step data and lesson content for all algorithms + tests (no UI) | Opus, Medium |
| 5 | Searching workspace (built natively in the new layout) | Sonnet, Medium |
| 6 | Sorting page moved into the workspace layout with Learn panel | Sonnet, Medium |
| 7 | Graph pages moved into the workspace layout with Learn panel | Sonnet, High |
| 8 | /big-o guide, mobile pass, accessibility review (web-design-guidelines) | Sonnet, Medium |

### Phase details

- Phase 3 animations: a hero that runs a real small sort on 8 bars (not a fake loop of numbers), a staggered section reveal on first view, tiles with a short preview on hover or focus. All off under reduced motion.
- Phase 6 and 7: wrap the existing visualization; do not rewrite it. After each page, play every algorithm and compare against the behaviour on the commit before the phase.
- Phase 7 puts new teacher JS in `static/js/teacher.js`, not inside graph_base.html.

## Definition of done for every phase

- App runs, every existing algorithm plays start to finish in both themes.
- `pytest` passes.
- Checked at 375px, 768px and 1440px.
- No em dashes, emoji or banned patterns introduced. Run
  `python tools/check_banned_patterns.py .`, which must exit 0.
  A plain grep is not enough: it misses the escaped forms, and this project has
  shipped all of them. The check decodes before it looks, so it catches:
  - JavaScript escapes, `\u2014` and `\u{1F680}`
  - surrogate pairs, `\uD83D\uDE80` being one emoji
  - HTML entities, `&mdash;`, `&#8212;` and `&#x2014;`
  It allows the typography the project does use: the infinity label, the arrow in
  a path, the ellipsis, curly quotes, and the times, minus and degree signs.
  There is no carve-out. The three documents that used to have one are gone:
  README.md was rewritten in Phase 8B, and DESIGN_SYSTEM.md and REDESIGN_PLAN.md
  were deleted as superseded by DESIGN.md and this plan.
  A file that has to spell these patterns out, as the lines above do, carries the
  marker `banned-check: documents-the-patterns` once and is skipped.
- One commit, and a short note: files changed, how to check it.

## Report format (end every phase with this, nothing else after it)

Finish your reply with one fenced code block, under 25 lines, so the user can copy it:

```
PHASE: <number and name>
COMMIT: <hash>
STATUS: done | partly done | blocked
CHANGED: <files, grouped, short>
DECISIONS: <anything you chose that the plan did not specify>
DEVIATIONS: <anything you did differently from the plan, and why>
NOT DONE / ISSUES: <bugs found, things skipped, open questions>
CHECKS: app runs Y/N | all algorithms play Y/N | pytest X passed | 375/768/1440 Y/N | banned patterns 0 Y/N
HOW TO CHECK: <one or two lines>
```

Do not include logs, terminal output or step-by-step narration in the report.

---

# Part 2: Teaching upgrades (Phases 9 to 23)

Part 1 rules, definition of done and report format still apply to every phase below. Each phase leaves the site working, so the work can stop after any phase.

## New non-negotiable rules for Part 2

1. Defaults never change. Every new option (variant, preset, mode) is off or set to today's behaviour by default, so existing baselines and tests stay valid.
2. Anything random (Quick Sort random pivot, presets) uses a seed that is shown on screen and reused on step back and replay, so a run is reproducible.
3. Every algorithm, variant and language added must follow the lessons/README.md contract and pass `node tests/validate_lessons.js`.
4. From Phase 12 on, any phase that adds an algorithm or variant also adds its C, C++ and Java code through the reference_code system.

## Feature specs

### Input presets (Phase 9)
- Buttons in the Setup column of Sorting and Searching: Random, Already sorted, Reversed, All equal, Nearly sorted (sorted, then about 10 percent of adjacent pairs swapped, seeded).
- Under the buttons, one line from the lesson data says what the chosen preset means for the chosen algorithm, e.g. "Already sorted is the worst case for Quick Sort with the last element as pivot". Add a `presetNotes` field to each lesson.
- Binary and jump search only offer presets that stay sorted.

### Keyboard shortcuts (Phase 9)
- Space play/pause, Left/Right step back/forward, R reset. Implemented once in workspace.js.
- Ignored while focus is in an input, textarea or select. Exposed with `aria-keyshortcuts` and a small "Keyboard shortcuts" disclosure in the control bar.

### Variant switches (Phase 10)
- Bubble Sort: early exit off (default) / on. Shows best case dropping from n(n-1)/2 to n-1 comparisons.
- Merge Sort: `<` (default, unstable) / `<=` (stable). Pair with a stability demo: duplicate values get letter tags (5a, 5b) on the bars so students see whether equal values keep their order.
- Quick Sort pivot: last (default) / middle / random (seeded).
- Variant chosen in the Setup column, sent to /run_sort, recorded in the run. Lesson files gain a `variants` block that overrides code lines, complexity and notes per variant.
- Merge and Quick Sort meta gain `depth` and `range: [lo, hi]` on every step (needed by the recursion tree in Phase 17).

### Omega and Theta (Phase 11 data, Phase 14 UI)
- Teach correctly: O, Omega and Theta are upper, lower and tight bounds. Best, average and worst are cases. Each case can have its own tight bound. Never teach "O = worst, Omega = best, Theta = average"; show that misconception in a callout and explain why it is wrong.
- Lesson `complexity.time.<case>` gains `theta`. `complexity.overall` gains `O`, `Omega`, and `Theta` (null when best and worst differ).
- Tests: overall O equals the worst case bound, overall Omega equals the best case bound, Theta present only when they match; counted comparisons on generated best and worst inputs grow in line with the stated bounds.
- UI: Complexity tab shows a small table (case, Theta, reason) plus an Overall line. /big-o gains a "Three notations" section with an SVG chart of f(n) between c1*g(n) and c2*g(n) after n0, with sliders. Navbar label may become "Complexity"; the /big-o URL stays.

### Multi-language code (Phases 12 and 13 data, Phase 14 UI)
- One real, compilable file per algorithm per language:
  `reference_code/c/<algo>.c`, `reference_code/cpp/<algo>.cpp`, `reference_code/java/<Algo>.java` (C11, C++17, Java 17).
- The teaching part is wrapped in `lesson:start` / `lesson:end` comments; teaching lines carry `@<line id>` tags using the same ids as the Python listing.
- `tools/extract_code.py` writes the extracted listings to `static/js/lessons/code/<algo>.js` (generated, never hand-edited). A test fails if the generated files are out of date.
- Each program reads the same input format, prints output plus comparison and swap counts; tests compile and run all three and must match Python exactly. Missing compiler: the test skips with a clear message naming what to install.
- Translations copy the Python behaviour exactly (no early exit unless the variant says so, last-element pivot by default, `<` in merge). Variants are covered too.
- C graph code uses small helper functions (queue, stack, binary heap). The listing shows the main function; helpers sit behind a "Show helpers" toggle. Prim in C must use a real heap.

### Code panel UI (Phase 14)
- Tabs: Pseudocode, Python, C, C++, Java. Rectangular, 6px radius, no pills.
- Animation: selected-tab background slides via transform (about 180ms, ease-out); code crossfades (about 120ms). The highlighted line stays on the same line id when the language changes. Reduced motion: instant.
- Chosen language saved in localStorage (try/catch), shared by every page and the Home code card. Default Python.
- Long lines wrap with a hanging indent, never horizontal scroll. "Expand code" opens a native `<dialog>` with the full listing (focus trapped, Esc closes).
- Below 520px wide the tabs become a `<select>`.
- "Live values" shows "Run the algorithm to see values change" before a run.

### Home "One step, read three ways" player (Phase 15)
- Plays one real full pass of bubble sort on 17, 11, 32, 45, 9 from the real step data. Stage, Explain, Code and Cost cards change together; swapped cells slide past each other (transform only).
- Starts when scrolled into view, pauses when out of view. Play/pause and Step buttons. Code card follows the saved language.
- Reduced motion: frozen step as now, Step button still works.

### Predict mode (Phase 16)
- A "Predict" toggle in the control bar. Before a step that can be asked about, the Explain tab shows a question built from the next step's meta: sorting compare "Will these two swap?"; search compare "Found, go left, or go right?"; graph "Which node is visited next?" (options from the current frontier).
- Answer, then feedback with the real explanation, then the step plays. Skip button. Score for this run only. Fully keyboard operable. Step back always works.

### Compare mode (Phase 17)
- New route /compare: two sorting stages side by side (stacked on mobile), same input and presets, one shared transport, separate live counters, a finish banner saying which finished in fewer comparisons and by how much.
- Requires workspace.js to support more than one instance on a page (scope by root element instead of global ids). Existing pages must keep working unchanged; tests prove it.

### Recursion tree (Phase 18)
- For Merge and Quick Sort, a panel under the stage drawing the call tree as SVG boxes labelled with their range. The active call (from meta `depth` and `range`) is highlighted; finished calls dim. Collapsible; hidden by default on mobile.

### New algorithms (Phases 19 to 21)
- Jump Search (sorted input, block size floor(sqrt(n))), Counting Sort (non-negative integers, shows the count array), Radix Sort (LSD, base 10, shows the ten buckets per digit pass). These run in the existing Searching and Sorting workspaces.
- Topological Sort (Kahn's algorithm) needs directed graph support on the graph page: arrowheads, directed input format, and a clear message when a cycle makes an order impossible.
- A* on a new grid workspace: click to draw walls, drag start and goal, Manhattan heuristic, live g, h and f values, open and closed sets. A "Run Dijkstra on the same grid" button shows how the heuristic saves work.
- Each one ships with its lesson, Theta and Omega data, presets where relevant, C, C++ and Java code, and tests.

## Phases

| # | Phase | Model, effort |
|---|---|---|
| 9 | Quick wins: Home Searching tile, Live values text, input presets, keyboard shortcuts | Sonnet 5.5, Medium |
| 10 | Variant switches (data, UI, lessons, stability tags) + depth/range meta | Opus 5.5, Medium |
| 11 | Omega and Theta data for all algorithms and variants + tests (no UI) | Opus 5.5, Medium |
| 12 | reference_code system + C, C++, Java for 6 sorts (with variants) and 2 searches + compile tests | Opus 5.5, Medium |
| 13 | C, C++, Java for the 7 graph algorithms, with helpers + compile tests | Opus 5.5, Medium |
| 14 | Code panel UI (tabs, animation, wrap, Expand, select) + Theta table + Three notations section | Sonnet 5.5, High |
| 15 | Home "One step, read three ways" player | Sonnet 5.5, Medium |
| 16 | Predict mode | Sonnet 5.5, High |
| 17 | Compare mode (multi-instance workspace.js) | Opus 5.5, Medium |
| 18 | Recursion tree for Merge and Quick Sort | Sonnet 5.5, High |
| 19 | Jump Search, Counting Sort, Radix Sort | Opus 5.5, Medium |
| 20 | Topological Sort + directed graph support | Opus 5.5, Medium |
| 21 | A* grid workspace | Opus 5.5, High |
| 22 | Independent review (report only), then one fix session | Opus 5.5 Medium, then Sonnet 5.5 Medium |
| 23 | Launch prep (production server, meta tags, self-hosted D3, LICENSE, documentation) | Sonnet 5.5, Low |

Priority if time or usage runs short: 9 to 15 are the core. 16 to 18 are strong extras. 19 to 21 are optional. Always finish with 22 and 23.
