# PBL2 Rebuild Plan

This plan replaces REDESIGN_PLAN.md. Every coding session reads this file first and does ONE phase only.

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
3. Keep the credit line "Team Tri Logic: Yash Maithani" exactly as written.
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
- No em dashes, emoji or banned patterns introduced (grep for them).
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
