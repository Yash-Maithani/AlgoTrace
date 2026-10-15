# Design System — Algorithm Visualizer

One design direction for this project. Chrome is quiet and neutral; colour is spent
almost entirely on the algorithm state it encodes.

**Scope.** This document covers presentation only. It does not change backend logic,
routes, algorithm code, Jinja block structure, or any text content including credits
and names.

---

## 1. The governing constraint

This project has a property most UIs don't: **colour already carries meaning.** Node
fill and edge stroke encode algorithm state — queued, processing, visited, in-MST,
rejected — and that encoding is the product. Everything else follows from one rule:

> **The interface chrome may not use any hue the data uses.**

A blue button beside a blue "queued" node teaches the user that blue means two
different things. So chrome is neutral slate plus a single indigo accent, and the
data palette below is reserved exclusively for the visualisation.

This is also why the direction is **not** glassmorphism. Frosted translucent panels
put a blurred, variable backdrop behind coloured graph nodes and distance matrices,
which attacks the one thing that must stay legible. Opaque surfaces with a clear
border do the same structural job with none of the contrast risk.

---

## 2. Colour

### Chrome — light

| Role | Hex | Notes |
| --- | --- | --- |
| `--bg` | `#F8FAFC` | page background |
| `--surface` | `#FFFFFF` | cards, panels, controls |
| `--surface-sunken` | `#F1F5F9` | wells: visualisation stage, code blocks |
| `--border` | `#E2E8F0` | 1px dividers and card edges |
| `--border-strong` | `#CBD5E1` | input borders, needs to read as interactive |
| `--text` | `#0F172A` | body — 16.9:1 on `--bg` |
| `--text-muted` | `#475569` | labels, captions — 7.4:1 on `--bg` |
| `--primary` | `#4F46E5` | buttons, links, active nav |
| `--primary-hover` | `#4338CA` | |
| `--on-primary` | `#FFFFFF` | 6.3:1 on `--primary` |
| `--focus-ring` | `#4F46E5` | 3px solid, 2px offset |

### Chrome — dark

| Role | Hex | Notes |
| --- | --- | --- |
| `--bg` | `#0B1120` | |
| `--surface` | `#151D2E` | |
| `--surface-sunken` | `#0F1626` | |
| `--border` | `#2A3650` | must stay visible — do not reuse the light value |
| `--border-strong` | `#3B4A68` | input borders |
| `--text` | `#E8EDF5` | 14.1:1 on `--surface` |
| `--text-muted` | `#9AA8BF` | 6.5:1 on `--surface` — above the 4.5:1 body threshold |
| `--primary` | `#818CF8` | lightened, not the light-mode value |
| `--primary-hover` | `#A5B4FC` | |
| `--on-primary` | `#0B1120` | |
| `--focus-ring` | `#A5B4FC` | |

Dark mode is a desaturated re-tone, not an inversion. Every pair above was chosen
against its own background.

### Data — algorithm state

Six roles, each distinguishable from the others in both themes.

| State | Light | Dark | Used by |
| --- | --- | --- | --- |
| Idle / unvisited | `#94A3B8` | `#64748B` | all |
| Queued / frontier | `#2563EB` | `#60A5FA` | BFS, DFS, Prim |
| Processing / current | `#D97706` | `#FBBF24` | all |
| Visited / settled | `#059669` | `#34D399` | all |
| Selected (MST, path) | `#7C3AED` | `#A78BFA` | Prim, Kruskal, Dijkstra, Floyd-Warshall |
| Rejected (cycle, no-relax) | `#DC2626` | `#F87171` | Kruskal, Bellman-Ford |

Three deliberate changes from what the code does today:

1. **Unvisited moves from red to slate.** Red currently means "not yet visited,"
   which reads as an error state. Red is reassigned to genuine rejection — Kruskal's
   cycle-closing edges, Bellman-Ford's failed relaxations — where it is accurate.
2. **MST and processing stop colliding.** `#ff6d00` and `#ff9800` are
   near-identical; selected becomes violet, leaving amber unambiguous.
3. **The red/green pair is broken up.** Unvisited/visited was the textbook
   deuteranopia failure. Slate against emerald survives it.

**Colour is never the only channel.** Every state also carries a non-colour cue:
stroke width for nodes (2px idle → 4px active), stroke dash for edges (solid
selected, dashed rejected), and a text label in the legend and step description.
A viewer who cannot distinguish two hues can still read the run.

---

## 3. Typography

Google Fonts, two families from one superfamily so they share metrics:

```css
@import url('https://fonts.googleapis.com/css2?family=Fira+Sans:wght@400;500;600;700&family=Fira+Code:wght@400;500&display=swap');
```

- **Fira Sans** — all UI text: headings, body, labels, buttons.
- **Fira Code** — only code blocks, the input-format examples, the Floyd-Warshall
  distance matrix, and node/edge weights.

Fira Code is deliberately *not* the heading font. Monospace headings read as a
stylistic tic and wrap badly; reserving the mono for actual code and actual numbers
makes it information rather than decoration.

### Scale

| Token | Size | Line height | Use |
| --- | --- | --- | --- |
| `--text-xs` | 12px | 1.4 | legend keys, axis labels |
| `--text-sm` | 14px | 1.5 | captions, helper text |
| `--text-base` | 16px | 1.6 | body — never go below this on mobile |
| `--text-lg` | 18px | 1.5 | panel titles |
| `--text-xl` | 20px | 1.4 | section headings |
| `--text-2xl` | 24px | 1.3 | page heading |
| `--text-3xl` | 32px | 1.2 | landing hero |

Weights: 400 body, 500 labels, 600 headings, 700 hero only.

Numeric display — step counters, weights, distance matrices, complexity figures —
uses `font-variant-numeric: tabular-nums` so values don't jitter as they change
during an animation.

---

## 4. Spacing, radius, elevation

4px base, dashboard density:

```css
--space-1: 4px;   --space-2: 8px;   --space-3: 12px;  --space-4: 16px;
--space-6: 24px;  --space-8: 32px;  --space-12: 48px; --space-16: 64px;
```

Vertical rhythm tiers: 8px inside a component, 16px between components, 32px between
panels, 48px between page sections.

```css
--radius-sm: 6px;    /* inputs, small buttons */
--radius-md: 10px;   /* cards, panels */
--radius-full: 999px; /* pills, icon buttons */
```

Elevation is a three-step scale, no ad-hoc shadows:

```css
--shadow-1: 0 1px 2px rgb(15 23 42 / 0.06);              /* resting cards */
--shadow-2: 0 4px 12px rgb(15 23 42 / 0.08);             /* raised, hover */
--shadow-3: 0 12px 32px rgb(15 23 42 / 0.16);            /* modals, popovers */
```

In dark mode, shadows do almost nothing — lean on `--border` and `--surface`
lightness for separation instead of deepening the shadow.

---

## 5. Components

**Buttons.** 44px minimum height. Primary is filled `--primary`; secondary is
`--surface` with `--border-strong`; destructive uses the rejected red. One primary
action per panel. Press feedback is opacity and colour, not a transform that shifts
layout. Disabled is 0.45 opacity plus the real `disabled` attribute.

**Icon-only controls** (play, pause, reset) are 44×44 pills with an `aria-label` and
`aria-hidden="true"` on the glyph. Replace the 55 emoji currently used as structural
icons with a single SVG set — the project already loads Font Awesome, so stay with it
rather than adding a second icon family. Emoji are font-dependent, can't be themed,
and are read aloud literally by screen readers.

**Inputs.** Visible `<label>` above every field, never placeholder-as-label. Helper
text persists below rather than appearing only on error. Errors sit next to their
field with `role="alert"`, and the first invalid field takes focus on submit. Minimum
44px height; 16px text to stop iOS auto-zoom.

**Range slider** (animation speed). Thumb goes to 44×44 — currently 22px, which fails
the pointer-target minimum. Keep the visible track slim and expand the hit area.

**Panels.** `--surface`, `--radius-md`, 1px `--border`, `--shadow-1`, `--space-6`
padding. The visualisation stage is `--surface-sunken` so the graph reads as content
sitting *in* the page rather than floating on it.

**Legend.** Promote it to a first-class component, always visible beside the stage,
one row per state: swatch, stroke sample, label. This is what makes the data palette
legible and discharges the colour-not-only requirement.

---

## 6. Layout

Breakpoints — pick these four and use only these four:

```
375px   480px   768px   1024px   1440px (max container)
```

Container is `max-width: 1200px` with a 16px gutter on mobile, 24px from 768px.

**The controls/stage split.** Above 1024px, controls sit in a left column and the
stage takes the rest. Below 1024px they stack, controls first. The current
`min-width: 500px` on the stage must go — it forces horizontal scroll on every phone.
Let the SVG scale with `viewBox` and `width: 100%` instead of a pixel floor.

**Sorting bars.** The fixed 350px bar container becomes `min(45vh, 350px)` so it
survives landscape phones.

**Sticky header.** Keep it, but ensure it never covers a focused control — add
`scroll-margin-top` equal to the header height on focusable targets.

---

## 7. Motion

Tokens:

```css
--dur-fast: 120ms;   /* press, hover */
--dur-base: 200ms;   /* state change, panel open */
--dur-slow: 320ms;   /* stage transitions */
--ease-out: cubic-bezier(0.2, 0, 0, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
```

Animate `transform` and `opacity` only. No `transition: all` — there are 38
occurrences today and each makes the browser watch every property.

Algorithm step animation keeps its own user-controlled speed and is exempt from the
tokens above; it is the content, not chrome.

**Reduced motion is already wired** — `graph_base.html` routes every d3 duration
through a `dur()` helper that collapses to 0 under `prefers-reduced-motion`, and the
stylesheet has a matching media block. Preserve that contract: under reduced motion,
motion stops but **state colours still change**, because colour is the information.

---

## 8. Theming mechanics

Today `body.dark-theme` exists in CSS with no toggle anywhere and no
`prefers-color-scheme` hook, so it is unreachable. Fix the plumbing:

```css
:root { /* light tokens */ }

@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { /* dark tokens */ }
}

:root[data-theme="dark"] { /* dark tokens */ }
```

Add `<meta name="theme-color">` matching the page background and `color-scheme` on
`:root` so form controls and scrollbars follow the theme. An explicit toggle is
optional; respecting the system preference is not.

---

## 9. What to avoid

- **Glassmorphism, blur, translucency.** Variable backdrops behind encoded colour.
- **Scroll-triggered storytelling.** This is a tool, not a marketing page. The
  controls must be reachable without scrolling.
- **Emoji as icons.** All 55 occurrences go.
- **Hardcoded hex in templates.** There are 465 literal colours against 49 defined
  custom properties. Every colour becomes a token.
- **Per-page `<style>` blocks.** 1,606 lines of inline CSS across the templates,
  with `dijkstra.html` alone carrying 244 that duplicate `graph_base.html`. One
  stylesheet, one source of truth.
- **A fifth breakpoint.** Four exist in `landing.html` alone (480/600/768/800) and
  none in `sorting.html`. Converge.
- **Red for "not yet done."** Red means rejected. Nothing else.
- **Colour as the only signal.** Every state needs a second channel.
- **Decorative gradients behind data.** The speed slider's three-colour gradient
  track implies a scale it doesn't have.
