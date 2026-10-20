# DESIGN.md

Design specification for the PBL2 rebuild. Written in Phase 1 of REBUILD_PLAN.md.

This file contains no code. It is the reference that Phases 2 to 8 build against.
Where it says "token", the name is the CSS custom property that already exists in
`static/styles.css` from commit 83b8f1b.

---

## 1. What is wrong with the layout today

Measured on the running app at 1440px, light theme, before any Phase 1 change.

| Page | Grid | Document height | Problem |
| --- | --- | --- | --- |
| `/graph?algo=kruskal` | 375px / 751px | 2634px | Playback bar sits at y=1104, the canvas it drives starts at y=430 |
| `/sorting` | 375px / 751px | 928px | Same two column split, no learning content anywhere |

Four concrete faults, each of which this spec fixes:

1. **The controls are 674px away from the thing they control.** On the graph page the
   play, pause and reset buttons live at the bottom of the left column while the canvas
   is in the right column. At 900px tall viewports you cannot see both at once.
2. **Everything is wrapped in one 1200px centred white card.** A workspace is not an
   article. The card forces a narrow stage, pushes the page to 2634px, and makes the
   graph canvas 701px wide on a 1440px screen.
3. **There is nowhere to teach.** No panel exists for explanation, code, or complexity,
   which are the point of the rebuild.
4. **Every page is a standalone HTML document** with its own head and navbar, so the
   header, footer and theme script are copied five times.

## 2. The app shell

One shared shell, built in Phase 2, used by every route.

```
+----------------------------------------------------------+
| skip link (visually hidden until focused)                 |
+----------------------------------------------------------+
| HEADER  sticky, 56px                                      |
|  logo  Home Learn Sorting Compare Searching Graphs Complexity |
|                                               theme toggle|
+----------------------------------------------------------+
|                                                           |
|  PAGE SLOT                                                |
|                                                           |
+----------------------------------------------------------+
| FOOTER   credit line        Privacy   Terms               |
+----------------------------------------------------------+
```

- The header is sticky and 56px tall. Nothing else is sticky on desktop, so a focused
  control can never be hidden behind two stacked bars.
- Focusable elements carry `scroll-margin-top` equal to the header height plus 8px, so
  keyboard focus is never obscured by the sticky header (WCAG 2.2, Focus Not Obscured).
- The shell is full width. The 1200px cap applies to reading pages only, not workspaces.

## 3. Layout grid

Two layout families. A page is either a **reading page** or a **workspace**.

### Reading pages (Home, Learn, Big O, Privacy, Terms)

- 12 column grid, 24px gutter, max content width 1200px, centred.
- Prose blocks are capped at 68 characters, which is roughly 7 of the 12 columns.
- Side padding: 16px below 768px, 24px from 768px, 32px from 1024px.

### Workspaces (Sorting, Searching, Graph)

The significant change. Three columns, full width, with a hard cap so it does not
sprawl on very wide monitors.

```
>= 1280px          SETUP          STAGE                    LEARN
                 |<- 300px ->|<-------- 1fr -------->|<- 380px ->|
                 
+----------------+-----------------------------------+-------------+
| Algorithm      |  STAGE                            | Learn panel |
| picker         |  the visualization only           |  [Explain]  |
|                |                                   |  [Code]     |
| Input          |                                   |  [Complexity]|
|  size / values |                                   |  [About]    |
|  start node    +-----------------------------------+             |
|  demo buttons  |  CONTROL BAR  directly under it   |  tab body   |
|                |  |< play pause >| speed  step n/m |  scrolls    |
| Run            +-----------------------------------+  on its own |
|                |  LEGEND  one row, wraps           |             |
+----------------+-----------------------------------+-------------+
```

- Column widths: `300px minmax(0, 1fr) 380px`, 20px gap, outer max width 1680px.
- The stage column is a vertical stack in this fixed order: stage, control bar, legend.
  The control bar is always the element immediately below the stage. This is the single
  most important rule in this file.
- The stage sizes to `min(62vh, 620px)` so the control bar stays on screen at 900px tall.
- `minmax(0, 1fr)` on the middle column, not `1fr`, so the canvas can shrink instead of
  forcing the page wider.

### Breakpoints

Four, and only these four.

| Width | Layout |
| --- | --- |
| < 768px | One column. Order: stage, control bar, legend, setup, Learn panel. |
| 768 to 1023px | One column, wider gutters. Setup becomes a two column form. |
| 1024 to 1279px | Two columns: stage block left, Learn panel right at 340px. Setup moves above the stage as a horizontal strip. |
| >= 1280px | Three columns as drawn above. |

On mobile the stage comes first because it is what the page is for. The control bar is
sticky to the bottom of the viewport only while the stage is in view, and it releases
when the user scrolls to the Learn panel. Bottom inset uses `env(safe-area-inset-bottom)`.

## 4. Spacing scale

4px base. These are the only values used.

| Token | Value | Used for |
| --- | --- | --- |
| `--space-1` | 4px | icon to label |
| `--space-2` | 8px | inside a control |
| `--space-3` | 12px | between controls in a group |
| `--space-4` | 16px | between components |
| `--space-6` | 24px | panel padding, between groups |
| `--space-8` | 32px | between panels |
| `--space-12` | 48px | between page sections |

Vertical rhythm on reading pages: 48px between sections, 24px between blocks inside a
section, 16px between paragraph and heading.

## 5. Type scale

Three families, each with one job.

| Family | Role |
| --- | --- |
| **Space Grotesk** | Display. The home hero and page level headings only. |
| **Fira Sans** | Every other piece of interface text: body, labels, buttons, panel titles. |
| **Fira Code** | Code, numbers, matrices, edge weights, anything in a column that must line up. |

Fira Sans and Fira Code are unchanged and are confirmed by the ui-ux-pro-max typography
dataset as its dashboard and data visualization pairing.

**On choosing Space Grotesk.** The typography dataset returned no verified match for a
technical teaching tool. Its display suggestions were all editorial and luxury pairings
(Playfair Display, Libre Bodoni), which are the wrong register for a site that teaches
beginners to read code. So this is a deliberate choice rather than a dataset result, and
the reasoning is:

- It was drawn as the display counterpart to Space Mono, so it has a real kinship with
  monospace. On a site where code and data are first class content, the headings and the
  code share a family resemblance instead of ignoring each other.
- Its character is in the details, the single storey `g`, the flat sided `a`, the slightly
  condensed caps. Those read as personality at 64px where a neutral geometric sans would
  look like every other landing page, and they stay quiet at 24px.
- It is a variable font, weight 300 to 700, so it costs one file.
- It is a grotesque, like Fira Sans, so the two do not fight.

**Where the display font is allowed.** The hero, and `h1` and `h2` on reading pages. Never
in a workspace panel, never on a control, never below 20px. Workspace headings stay Fira
Sans so the dense side of the product reads as an instrument, not a poster.

### Scale

| Token | Size | Line height | Family | Use |
| --- | --- | --- | --- | --- |
| `--text-xs` | 12px | 1.4 | Sans | legend keys, axis labels, table captions |
| `--text-sm` | 14px | 1.5 | Sans / Code | control labels, helper text, code |
| `--text-base` | 16px | 1.6 | Sans | body, inputs (never smaller on mobile) |
| `--text-lg` | 18px | 1.5 | Sans | panel titles, Learn tab headings |
| `--text-xl` | 20px | 1.4 | Sans | workspace section headings |
| `--text-2xl` | 24px | 1.3 | Display | workspace page heading (`h1`), reading page section headings (`h2`) |
| `--text-3xl` | 32px | 1.2 | Display | reading page heading (`h1`) |
| `--text-hero` | fluid, see below | 1.05 | Display | home hero only |

`--text-hero` is `clamp(2rem, 1.25rem + 3.5vw, 4rem)`, which resolves to:

| Viewport | Hero size |
| --- | --- |
| 375px | 33px |
| 768px | 47px |
| 1024px | 56px |
| 1280px and above | 64px (capped) |

So the hero sits in the 48 to 64px band across desktop and steps down to a readable 33px
on a phone without a media query. Line height tightens to 1.05 at hero size, because 1.2
leaves a visible gap between two lines of 64px type.

Weights: 400 body, 500 labels, 600 headings and buttons, 700 hero only.

**Loading cost.** This adds one variable font file to the existing Google Fonts request.
Request only `wght 300..700`, keep `display=swap`, and keep the two existing preconnect
hints. Do not add a separate stylesheet request for it.

Every number that changes during a run uses `font-variant-numeric: tabular-nums`: step
counter, comparison and swap counts, distance matrices, edge weights, complexity figures.
Without it the row jitters on every tick.

Headings use `text-wrap: balance`. Long identifiers and pasted graph input use
`overflow-wrap: anywhere`, never `word-break: break-all`.

## 6. Colour

**Unchanged from commit 83b8f1b.** This spec adds no colours and renames nothing.

The rule that governs it stays in force: chrome may not use any hue the data uses. The
nine state accents keep the same hue in both themes, and dark mode lightens rather than
mutes them. Light mode uses the darker ink tier wherever a label sits on an accent, and
`--on-state` flips the label between white and near black.

New surfaces introduced by this spec map onto existing tokens:

| New surface | Token |
| --- | --- |
| Workspace page background | `--bg` |
| Setup column, Learn panel | `--surface` with 1px `--border` |
| Stage well | `--sunken` |
| Control bar | `--surface`, 1px `--border` top |
| Active Learn tab | `--surface`, 2px `--accent` bottom rule |
| Inactive Learn tab | transparent, `--text-muted` |
| Current code line | `--active-wash`, 3px `--active` left rule |
| Growth chart reference curves | `--text-muted` at 40 percent |
| Growth chart this algorithm | `--accent` |
| Link, every state | `--accent`, underlined; hover `--accent-hover` with a thicker underline; keyboard focus a 3px `--focus-ring` outline. Set once, at zero specificity, so a component's own link style wins |
| Growth chart on `/big-o` (the curves are the subject) | one palette ink per curve, with its own dash: O(1) `--done-ink` dotted, O(log n) `--idle-sort-ink` short dash, O(n) `--queued-ink` long dash, O(n log n) `--active-ink` dash and dot, O(n squared) `--reject-ink` solid, and a legend naming each |
| Fieldset (`.input-method`) | `--surface`, 1px `--border`, `--radius-md`, a 600 weight legend: the same panel as the algorithm pickers on Compare |

## 7. Components

### Control bar

The defining component. One row, directly under the stage, in this order left to right:

`step back | play or pause | step forward | reset | speed slider | step n of m`

- Transport buttons are 44px circles. Round is reserved for transport and nothing else.
- Play and pause are one button that swaps icon and label, not two buttons. The current
  pages have separate play and pause buttons that each dim to 0.5 opacity, which reads as
  broken rather than stateful.
- Step back and step forward are new in this spec and required by the plan.
- The step counter is right aligned and uses tabular figures.
- At < 768px the bar wraps to two rows: transport on the first, speed and counter on the
  second, and it sticks to the bottom of the viewport while the stage is in view.

### Learn panel

Four tabs: Explain, Code, Complexity, About. Tabs are a real tablist: arrow keys move
between tabs, Home and End jump to first and last, and the panel is labelled by its tab.

- Tab strip is 44px tall, scrolls horizontally at narrow widths rather than wrapping.
- The body scrolls independently of the page on desktop so the stage stays in view.
- Explain updates on every step. It must never reflow the panel: reserve two lines of
  height so a one line and a two line explanation do not move the tabs.
- Code shows pseudocode and Python as a sub toggle, with the current line marked by a left
  rule and a wash, not by colour alone. Live variables sit in a small table below.
- About and Complexity are static per algorithm and do not re-render on step changes.

### Complexity block

Fixed order, same on every algorithm, as specified in the plan: best, average and worst
with a reason tied to the code; a worked example at n equals 5; auxiliary space; a "this
run" box comparing counted work against the formula; and a growth chart.

The growth chart is plain SVG, around 160px tall, plotting O(1), O(log n), O(n),
O(n log n) and O(n squared) as faint reference curves with this algorithm's curve in
`--accent`. It carries a text summary for screen readers and a data table alternative,
because a chart alone is not accessible.

Complexity text is derived from the actual code in this repository, not from a textbook.
The plan lists the known divergences; re-derive the rest the same way.

### Setup column

Algorithm picker, then input, then the run button, in that order. The picker is a list of
links, one per line at desktop, each carrying its own accent on a 3px left rule. This
replaces the current wrapping row of pills, which gives every algorithm equal visual
weight and no room for a description.

### Legend

One row under the control bar, wrapping. Each item is a swatch plus a label. Swatch shape
carries meaning: circle for nodes, short bar for edges, square for sorting bars. Colour is
never the only channel.

### Buttons

Modest 6px radius. No pills. One primary action per panel. Press feedback is
`transform: scale(0.97)`, which is the only transform allowed on a button.

## 8. Page wireframes

### `/` Home

```
HERO            display heading, one sentence, two buttons: Start learning, Browse algorithms
                right side: a live 8 bar sort running the real bubble sort
ONE STEP, READ  the annotated step band (below)
THREE WAYS
TRACKS          three tiles: Sorting, Searching, Graphs
START HERE      the suggested beginner order as a numbered list, first item emphasised
```

The hero visualization runs the real algorithm on 8 bars, not a decorative loop. Under
reduced motion it renders the sorted end state and does not animate.

#### The annotated step band

This replaces a generic three card feature row. A feature row would say "see it run, read
why, understand the cost", which is marketing. The band shows the same claim by doing it:
one real step from a real bubble sort, frozen, with the three readings a learner gets on
every step of this site lined up underneath it.

```
+----------------------------------------------------------------------+
|  One step, read three ways                                            |
|                                                                       |
|   +--------------------------------------------------------------+   |
|   |   [17] [32] [11] [45] [9]      bars, 32 and 11 highlighted    |   |  stage strip
|   |         ^^^^  ^^^^              as "comparing"                |   |
|   +--------------------------------------------------------------+   |
|                                                                       |
|   +------------------+  +------------------+  +------------------+   |
|   | EXPLAIN          |  | CODE             |  | COST             |   |
|   |                  |  |                  |  |                  |   |
|   | 32 is bigger     |  | if arr[j] >      |  | 4 comparisons    |   |
|   | than 11, so      |  |    arr[j+1]:     |  | so far           |   |
|   | they swap.       |  |   swap them      |  |                  |   |
|   |                  |  |                  |  | Bubble sort      |   |
|   | Bubble sort      |  | the matching     |  | always does      |   |
|   | walks the list   |  | line marked      |  | n(n-1)/2 = 10    |   |
|   | and fixes any    |  | with a left      |  | for n = 5        |   |
|   | pair that is     |  | rule and a       |  |                  |   |
|   | out of order.    |  | wash             |  | [tiny growth     |   |
|   |                  |  |                  |  |  chart, n=5]     |   |
|   +------------------+  +------------------+  +------------------+   |
|                                                                       |
|   This is what every step looks like.  ->  Open the sorting workspace |
+----------------------------------------------------------------------+
```

Rules for the band:

- **The values are real.** The array, the highlighted pair, the comparison count and the
  code line all come from an actual bubble sort run on `[17, 32, 11, 45, 9]`, step 4. If
  the array changes, every number in the band changes with it. Nothing here is a
  screenshot or a hand written sample.
- The three columns are the same three Learn panel tabs a learner will use on every
  workspace, in the same order, with the same headings. The home page is teaching the
  interface, not advertising it.
- The highlighted bars use the real `comparing` state colour, so the legend a learner
  meets later is already familiar.
- The cost column states the honest figure for the code in this repository: bubble sort
  here has no early exit, so it always performs n(n-1)/2 comparisons. That matches
  REBUILD_PLAN section "Complexity facts".
- Layout: three equal columns at 1024px and up, stacked in the same order below that. The
  stage strip is full width at every size.
- Motion: the band is static by default. The bars do not loop. One optional affordance is
  a single "play this step" control that advances to the next step once and stops, which
  is off under reduced motion.

#### Track tiles

Three tiles, equal weight, in the suggested learning order: **Sorting**, **Searching**,
**Graphs**. Each tile carries its section accent on a top rule, a one line description, a
count of algorithms, and links straight into the workspace. Three columns at 1024px and
up, one column below.

### `/learn` Algorithm index

```
INTRO           one paragraph on how to use the site
SUGGESTED ORDER numbered, 20 items, each a row: name, one line, difficulty, time
BY CATEGORY     Searching (3), Sorting (8), Graphs (9, with A* on its grid), each a grid of
                cards, then a card for the complexity guide
```

The order, the counts and the cards all come from one registry in `app.py`, so adding an
algorithm changes the page and Home's "Start here" together and no number is typed twice.
Each card: name, one sentence, best and worst time, a link to its workspace. The best and
worst figures are filled in by the browser from the lesson files (`static/js/learnfigures.js`)
so they cannot disagree with the Complexity tab; the space for them is reserved in the
markup, so a card is the same size before and after they arrive. Cards carry the algorithm
accent on a left rule.

### `/sorting`, `/searching`, `/graph` Workspaces

The three column layout from section 3. Identical structure across all three, so a learner
who understands one understands the others. Only the stage contents differ: bars, array
cells, or a node and edge canvas.

Counting Sort and Radix Sort (Phase 19) show their working memory in a strip **inside the
stage, under the bars**: the count list as a hundred square (row r, column c is the slot
for 10r + c, every slot drawn because every slot is read), or the ten buckets of the
current digit pass, one value per line with the front at the top. Inside the stage, so
the control bar is still the element immediately below it. While the strip shows, the bar
area keeps its full 324px (a 99 is 297px tall plus its label) and the stage grows to fit,
rather than squeezing the bars; the strip scrolls inside itself past 320px and keeps the
active slot or bucket in view. Jump Search adds an `end` pointer, the block end it is
checking, next to `low` and `high` on the searching stage.

Topological Sort (Phase 20) is the one directed graph page. Its links carry an arrowhead
marker coloured by the line (`context-stroke`, so every edge state colours it) and stop at
the target node's rim; each node has an in-degree badge to its upper right; and a strip
inside the stage under the graph shows the queue of in-degree 0 nodes (front outlined),
the order so far joined by arrows, and the closing message. The seven undirected pages
draw no arrowheads, no badges and no strip.

A* (Phase 21) is a fourth workspace, the grid, reached from the Graphs picker rather than
the navbar. It keeps the workspace layout: setup (picker, grid size, presets, the run
buttons), the stage with the control bar directly below it, the legend, and the Learn
panel. The stage holds a board of square cells sized to fit (at most 64px); a cell of 46px
or more shows f with g and h under it, 26px or more f alone, smaller none. A cell's kind
(free, wall, start S, goal G) is its fill; what the run did to it (open, expanded, current,
path) is a wash and an inset border, so S and G keep their colour. The board is one
`role="grid"` with a cell cursor through `aria-activedescendant`, so the keyboard edits it
without leaving it, and it carries `data-keys="own"` so the transport shortcuts stay off
while it has focus. Phones start at 8 by 10 cells, larger screens at 12 by 20.

### `/compare` Compare mode (Phase 17)

Two sorting algorithms on one input. Not a three column workspace: there is no Learn
panel, because the point of the page is the side by side.

```
SETUP          left pick (algorithm, variant, seed) | right pick
               one input: random or typed, the /sorting presets, Run both
STAGES         left stage            | right stage        (stacked below 900px)
               counters, status      | counters, status
CONTROL BAR    one transport for both, then the legend and the finish banner
WHAT TO TRY    pairs that make one idea visible, each a button that sets up and runs
```

- The nav is its own exception: seven items need 1024px to stay on one row, so the
  menu button takes over below 1024px (measured: it wrapped at 991px).
- The one exception to the four breakpoints: the stages go side by side from 900px,
  because below that two stages of bars are too narrow to read.
- Both sides' rows are aligned (CSS subgrid), so a title that wraps on one side does not
  push its stage below the other's.
- Each side is a workspace in its own root, found by `data-part` rather than by id; the
  shared transport is a `Workspace.group`. When one side finishes it holds its last step
  while the other carries on.

### `/big-o` guide

```
WHAT BIG O IS       plain language, no formulas above the fold
THE COMMON CURVES   one section each for O(1), O(log n), O(n), O(n log n), O(n squared),
                    each with a real example from this site
GROWTH CHART        the same SVG component, interactive n slider
COUNTING WORK       why the counter and the formula disagree, and why that is fine
AUXILIARY SPACE     what it means, with the recursion stack as the worked case
```

### `/privacy`, `/terms`

Reading pages inside the shell. Content moves unchanged from `static/`.

## 9. Motion rules

Applying the emil-design-eng framework. Every animation answers "why does this animate"
before it is written.

### Durations and easing

| Element | Duration | Easing |
| --- | --- | --- |
| Button press | 120ms | `--ease-out` |
| Tab change, tooltip | 150ms | `--ease-out` |
| Panel or disclosure open | 200ms | `--ease-out` |
| Stage transitions | 260ms | `--ease-out` |
| On screen movement | 240ms | `--ease-in-out` |

Curves, stronger than the CSS defaults:

- `--ease-out: cubic-bezier(0.23, 1, 0.32, 1)`
- `--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1)`

No UI animation exceeds 300ms. `ease-in` is never used on UI: it delays the first frame,
which is exactly when the user is watching.

### Rules

1. **Never animate the step transport.** Play, pause, step forward and step back are
   pressed repeatedly. The button gets press feedback; the step change does not get an
   entrance animation.
2. **The algorithm animation is content, not chrome.** It keeps its own user controlled
   speed and is exempt from the table above.
3. Only `transform` and `opacity` animate. Never `transition: all`.
4. Nothing enters from `scale(0)`. Entrances start at `scale(0.96)` with `opacity: 0`.
5. Use CSS transitions, not keyframes, for anything that can be retriggered quickly, so it
   retargets instead of restarting.
6. Stagger on first view only, 40ms between items, maximum 6 items. Never block
   interaction while a stagger plays.
7. Hover effects are wrapped in `@media (hover: hover) and (pointer: fine)` so a tap on a
   touch device does not leave a stuck hover state.
8. Exit is faster than enter, roughly 60 to 70 percent of the enter duration.

### Reduced motion

Under `prefers-reduced-motion: reduce`, movement stops and meaning survives. Nothing is
hidden and no content disappears.

- Position and scale animations are removed.
- Colour and opacity transitions are kept, because state colour is the information this
  project exists to show.
- The hero sort renders its final sorted state.
- The growth chart draws complete instead of sweeping.
- The algorithm stage jumps between steps rather than tweening, and still recolours.

## 10. Selector contract

REBUILD_PLAN rule 1 requires that every id and class the page JS selects survives any
markup move. This is that list, captured from the current templates. Phases 6 and 7 must
keep every one of these, or update the JS in the same commit.

**Ids (32).** `algorithm-status`, `array-container`, `completion-message`,
`format-content`, `fw-matrix`, `graph-container`, `graph-input`, `header`,
`manual-graph-input`, `manual-input`, `manualRadio`, `matrix-content`, `matrix-display`,
`matrix-title`, `num-edges`, `num-nodes`, `pause-btn`, `pause-button`, `pauseBtn`,
`play-btn`, `play-button`, `random-graph-input`, `random-input`, `randomRadio`,
`reset-button`, `result-content`, `result-panel`, `speed-slider`, `speed-tooltip`,
`start-node`, `status-content`, `step-display`.

Phase 6 unified the duplicated transport ids. Sorting moved to the workspace contract, so
`play-btn` and `pause-btn` are gone from it; `play-button` in graph_base was renamed to
`play-pause` to match; and `pauseBtn`, which no element ever carried, went with the dead
functions that reached for it. All three pages now name the transport the same way.

**Sorting bar state classes.** `bar`, `bar-value`, `comparing`, `swapping`, `pivot`,
`sorted`, `is-visible`, `updated`.

**Graph state classes set through d3 `.classed()`.** `node-visited`, `node-frontier`,
`node-current`, `node-ignored`, `node-unvisited`, `edge-mst`, `mst-edge`,
`edge-considering`, `edge-ignored`, `edge-default`, `shortest-path`.

**Other classes the JS touches.** `link`, `edge-label`, `edge-label-bg`, `edge-pulse`,
`node-pulse`, `matrix-updated`, `kr-verdict`, `step-updated`, `success-flash`, `temp`,
`highlight`, `animating`.

`graph_base.html` also defines about 75 global functions. Phase 7 moves teacher code to
`static/js/teacher.js`; it must not move these, because the inline `onclick` attributes in
the markup call them by name from the global scope.

**The algorithm picker, settled in Phase 8B.** Two kinds of entry share one look. On the
graph page each algorithm is its own URL, so those entries are `<a href>` and the current
one carries `aria-current="page"`. On sorting and searching the picker swaps the algorithm
on the page you are already on, so those entries are `<button type="button">` and the
current one carries `aria-current="true"`. They were links to `#`, which told a screen
reader they led somewhere and ignored the space bar. `workspace.js` finds either by
`[data-algorithm]`, so neither page needs its own code. Do not turn them back into links.

## 11. Accessibility rules

- Minimum pointer target 44px. Inputs at 16px text so iOS does not zoom on focus.
- Visible focus on every control: 3px `--focus-ring`, 2px offset, via `:focus-visible`.
- One `h1` per page, then `h2` and `h3` with no level skipped. On a workspace it is
  `.workspace-title`, above the columns at every width.
- Anything clickable is a `<button>` or an `<a>`. Never a `<span onclick>`: it cannot be
  reached by tab, cannot be pressed by key, and announces as nothing.
- A fill that carries text uses the label tier, not the bar tier. The nine accents are
  sized so a light mode fill clears 3:1, which is right for a bar or a node body and
  short of the 4.5:1 a label on top of it needs; `--active-solid`, `--done-solid` and
  `--reject-solid` are the versions to paint text on.
- A box that scrolls is a focus stop with a name, so a keyboard can reach what has
  overflowed. The stage, the code listing and the worked code samples all are.
- The step counter is a polite live region. Validation errors use `role="alert"` and sit
  next to the field they concern, and the first invalid field takes focus on submit.
- Charts and canvases carry a text alternative. The growth chart also offers a table.
- Colour is never the only channel: pair it with shape, a left rule, a dash pattern, or a
  label.
- Tablists support arrow keys, Home and End.
- No horizontal scrolling at 375px.

## 12. Out of scope for this file

- Lesson copy and pseudocode, which are Phase 4.
- The step data format, which is specified in REBUILD_PLAN.md and built in Phase 4.
- Any colour value. The palette is fixed at commit 83b8f1b.
- Anything about Flask routing beyond the route list already in the plan.
