# Redesign Plan — Algorithm Visualizer

Order of work for applying [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md).

**Constraints for every stage below.** No changes to backend logic, routes, algorithm
code, Jinja block structure, or text content — including credits and names. Presentation
only: CSS, markup structure, class names, ARIA attributes.

**No git in this repository.** There is no way to revert selectively, so each stage
should be verified in the browser before the next one starts.

---

## Stage 0 — Token foundation

**Touches:** `static/styles.css`

Nothing visual ships here. Define the full token set from DESIGN_SYSTEM.md §2–§4 and §8
at the top of the stylesheet, wire the three-selector theme mechanism, and add the font
`@import`. Leave every existing rule in place.

Two cleanups that belong here because they are duplicate definitions fighting each
other, not redesign decisions:

- `.step-counter` is declared twice (`styles.css:476` and `:492`) with different
  padding and radius; the second silently wins.
- `.speed-control.active` is declared twice (`:459` and `:469`).

**Done when:** tokens resolve in both themes, nothing looks different yet.

---

## Stage 1 — Shared chrome

**Touches:** `static/styles.css`

The header, nav, footer, buttons, inputs, panels and focus states that every page
inherits. Convert them from hardcoded hex to tokens. Raise buttons and inputs to 44px,
replace `transition: all`, and bring the slider thumb from 22px to a 44px hit area.

This stage is where most of the 465 hardcoded colours and 38 `transition: all`
occurrences in the stylesheet get resolved.

**Done when:** all three live pages already look coherent despite no page-level work,
and keyboard tabbing shows a visible ring on every control in both themes.

---

## Stage 2 — `/sorting`

**Touches:** `templates/sorting.html`

First page, because it is the smallest real surface (380 lines, no inline `<style>`)
and the least entangled — a good place to prove the tokens before touching the graph
engine.

- Fix the heading jump: `h1 → h3` with no `h2`.
- Add the four breakpoints; this file currently has **zero** media queries.
- Bar container from a fixed `350px` to `min(45vh, 350px)`.
- Tabular numerals on the step counter and the comparison/swap statistics.
- Two emoji to replace with icons.

**Done when:** usable at 375px with no horizontal scroll, and the bar animation still
reads correctly.

---

## Stage 3 — `/` landing

**Touches:** `templates/landing.html`

Second, because it is self-contained — nothing extends it and it extends nothing — so
it can absorb a large change safely.

The main job is extraction: **614 of its 785 lines are an inline `<style>` block.** Move
what is shared into the stylesheet, delete what the tokens now provide, and keep only
genuinely page-specific rules. Collapse its four breakpoints (480/600/768/800) to the
standard set.

Leave all copy untouched, including the credit line at `landing.html:660`.

**Done when:** the inline block is a fraction of its current size and the page is
unchanged in content.

---

## Stage 4 — `/graph` shell

**Touches:** `templates/graph_base.html`

The largest and highest-risk file — 3,147 lines, 342 of them inline CSS — and the parent
of all seven algorithm pages, so a mistake here breaks everything at once.

- Lift the 342 inline CSS lines into the stylesheet as tokens.
- Remove `min-width: 500px` from the visualisation stage and let the SVG scale by
  `viewBox`; add the breakpoints, of which this file currently has none.
- Fix the hierarchy: 1×`h1`, 5×`h3`, 11×`h4`, with `h2` skipped entirely.
- Promote the legend to the persistent component described in DESIGN_SYSTEM.md §5.
- Replace the 25 emoji in this file with SVG icons.
- **Add Kruskal, Floyd-Warshall and Bellman-Ford to the algorithm nav.** Lines 373–376
  link only BFS, DFS, Dijkstra and Prim; the other three work but are reachable only by
  typing `?algo=` manually. This is a markup addition, not a routing change.

Preserve the reduced-motion contract: every d3 duration routes through the `dur()`
helper, and under `prefers-reduced-motion` motion stops while state colours still change.

**Done when:** all seven algorithms still animate, all seven appear in the nav, and the
page works at 375px.

---

## Stage 5 — Data palette migration

**Touches:** `static/styles.css`, `templates/graph_base.html`

Deliberately separate from Stage 4, because this is the one stage that changes what the
user *sees as meaning* rather than how it looks, and it deserves its own verification
pass.

Apply the six state roles from DESIGN_SYSTEM.md §2: unvisited red → slate, MST
deep-orange → violet, red reserved for rejection. Add the second non-colour channel —
stroke width for nodes, dash pattern for edges — and update the legend labels to match.

`static/js/common.js` holds a `COLORS` map with the old values. It is not loaded by any
live page, so it does not need to change for this to work; if it is updated, keep it in
sync rather than letting it contradict the stylesheet.

**Done when:** a run of Kruskal and a run of BFS are both readable in greyscale.

---

## Stage 6 — Algorithm info panels

**Touches:** `templates/bfs.html`, `dfs.html`, `dijkstra.html`, `prim.html`,
`kruskal.html`, `floyd_warshall.html`, `bellman_ford.html`

Last, because each is small and purely additive once the parent is done. Three of these
are already minimal info blocks (18–50 lines); the work is mostly `dijkstra.html`, which
carries **244 lines of inline CSS duplicating `graph_base.html`**, and `kruskal.html`,
which holds 12 emoji.

Keep every word of the explanatory copy, complexity figures and input-format examples.

**Done when:** no template outside `graph_base.html` has a `<style>` block, and the
seven pages are visually consistent.

---

## Out of scope

Not touched by this plan:

- `app.py`, `app_new.py`, `routes/`, `services/`, `algorithms/`, `sorting_algorithms/`,
  `tests/` — all backend and algorithm code.
- Jinja block structure and template inheritance.
- All text content, credits and names.

Dead templates, intentionally skipped — nothing renders them, so restyling them is
wasted effort:

| File | Status |
| --- | --- |
| `templates/base.html` | only `sorting_new.html` extends it; nothing renders that |
| `templates/sorting_new.html` | not referenced by any route |
| `templates/index.html` | not referenced by any route |
| `templates/bellman_ford_new.html` | not referenced by any route |
| `templates/error.html` | rendered only by `app_new.py`, which cannot import |

---

## Verification per stage

1. All three live routes return 200: `/`, `/sorting`, `/graph?algo=<each of seven>`.
2. 375px and 768px, portrait and landscape, no horizontal scroll.
3. Keyboard tab through every control — visible ring, order matches layout.
4. Both themes checked independently, not inferred from one.
5. `prefers-reduced-motion` on — animation stops, state colours still change.
6. Console clean.
