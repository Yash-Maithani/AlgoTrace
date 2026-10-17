# Step format and lesson contract

This is the contract between the Python that generates steps, the lesson files in this
folder, and the Learn panel that renders them. Phase 4b (graphs), Phase 5 (searching) and
the UI phases all follow it. If you need to change the shape, change it here first.

## 1. A step

Sorting and searching steps keep the two fields the page already relied on and add six
more. Every field is present on every step.

| Field | Type | Meaning |
| --- | --- | --- |
| `array` | list of numbers | the whole array as it stands after this step |
| `compared` | list | what the stage highlights. Usually indices, but some algorithms pass colour names on their final frame. Treat it as opaque and do not parse it for meaning |
| `action` | string | what happened. Vocabulary below |
| `indices` | list of ints | the real indices this step acts on, always ints, never colour names. Read this, not `compared`, when you need to know where something happened |
| `values` | list of numbers | the values sitting at `indices` when the step was emitted, in the same order |
| `line` | string or null | the id of the code line this step is executing, matching an id in the lesson's `code` listing. `null` when no single line applies, as on the final frame |
| `vars` | object | the live variables at this moment, for example `{"i": 2, "j": 5, "n": 30}`. Keys differ per algorithm |
| `explain` | object | `{beginner, why}`, two plain sentences. `beginner` names the real values involved. `why` says what the algorithm is trying to achieve, and is allowed to repeat across steps of the same kind |

### `action` vocabulary

| Action | Meaning |
| --- | --- |
| `compare` | two values were read and compared. Nothing moved |
| `swap` | two cells exchanged contents |
| `overwrite` | one cell was written with a value from somewhere else, as in an insertion shift or a merge write back |
| `select` | a position or a candidate was marked, for example the next slot to fill or a new running minimum |
| `place` | a value reached its final position, as with a quick sort pivot |
| `done` | the final frame. The array is sorted and nothing is highlighted |

Graph algorithms add their own, because none of the above fits a traversal:

| Action | Meaning |
| --- | --- |
| `visit` | a node is settled and will not be looked at again |
| `enqueue` | a node joins the queue, the stack or the frontier |
| `consider` | an edge, or a route through a node, is being examined |
| `relax` | a distance improved |
| `reject` | an edge or route was examined and not taken |
| `include` | an edge joins the tree or the answer |
| `milestone` | a marker that changes no state, such as a pass finishing |

Add to these lists rather than overloading an existing action. The set in force for
graphs is `GRAPH_ACTIONS` in app.py.

## 2. Rules

1. **Numbers are generated, never written by hand.** Every value in `values`, `vars` and
   `explain` comes from the running algorithm. If the input changes, the text changes.
2. **Adding teacher fields must not change behaviour.** The number of steps, the order of
   steps, the contents of `array` and `compared`, and the comparison and swap counts stay
   exactly as they were. `tests/test_sorting_parity.py` enforces this against the golden
   file recorded at commit e0fe171.
3. **`line` ids are shared.** The same id labels the matching line in both the pseudocode
   and the Python listing, so the Code tab can highlight either view from one step.
4. **Complexity text describes the code in this repository**, not the textbook. Where they
   differ, say so in `complexity.divergence`. See the "Complexity facts" section of
   REBUILD_PLAN.md.

## 3. A lesson file

One file per algorithm, `static/js/lessons/<algorithm>.js`, no build step, no module
system. Each file attaches itself to a global registry:

```js
window.LESSONS = window.LESSONS || {};
window.LESSONS.bubble_sort = { /* the object below */ };
```

| Key | Type | Notes |
| --- | --- | --- |
| `id` | string | matches the file name and the registry key |
| `name` | string | display name, for example `Bubble Sort` |
| `family` | string | `sorting`, `searching` or `graph` |
| `idea` | list of 3 strings | the About tab. Three sentences, no more |
| `analogy` | string | one everyday comparison |
| `whenToUse` | string | one or two sentences on where it earns its place |
| `code.pseudocode` | list of `{id, text, indent}` | `id` is null for a line no step ever lands on |
| `code.python` | list of `{id, text, indent}` | the same ids, matching the real file in `sorting_algorithms/` |
| `complexity.time` | `{best, average, worst}` | each `{value, reason}`, the reason tied to the code |
| `complexity.worked` | `{input, comparisons, note}` | an exact count for a real n = 5 input |
| `complexity.space` | `{value, what}` | `what` names the memory, for example "the recursion stack" |
| `complexity.auxiliaryNote` | string | the fixed explanation of what auxiliary means |
| `complexity.thisRun` | string | the fixed sentence for the "this run" box. Two of them: one for a counted family, one for graphs, which show no counted work |
| `complexity.growth` | string or null | which reference curve has this algorithm's shape: `1`, `logn`, `n`, `nlogn`, `n2` or `n3`. `null` when the figure needs two numbers at once, such as `O(V times E)`, because no curve on an axis of one variable is that figure |
| `complexity.growthBasis` | string or null | what `n` on the axis stands for when the figure is written in another letter, for example `'V, the number of nodes'`. `null` when the figure is already in `n` |
| `complexity.growthNote` | string or null | why no curve fits. Required when `growth` is null, forbidden otherwise, and it must name the figure it is explaining |
| `complexity.countsNote` | string or null | an explanation of a counter the learner will find surprising, shown under the "this run" box |
| `complexity.divergence` | string or null | how this implementation differs from the textbook figure |
| `presets` | list of strings | optional. Which input presets the page offers: any of `random`, `sorted`, `reversed`, `equal`, `nearly`. Omitted means all five. Binary search sets `['sorted', 'equal']`, because the other three would be refused |
| `presetNotes` | object | sorting and searching only. One sentence per offered preset saying what that input means for this algorithm, drawn from the real counts |
| `stable` | boolean or null | whether equal values keep their original order. `null` where it does not apply, as for a search |
| `codePending` | boolean | present and `true` only while the lesson ships ahead of its implementation. The listing is then the form the later phase must build, and that phase either matches it or updates the lesson in the same commit |
| `countLabel` | string | what the second counter is called, when it is not `swaps`. Merge sort sets `writes`, because it never exchanges a pair: it copies a merged run back over the array, so every value in the run is written whether or not it moved. A lesson that sets this must also explain it in `complexity.countsNote` |

The two code listings show the algorithm, not the plumbing. The `draw` and `stats`
calls that exist in the Python file are instrumentation for the visualization and are
left out of the listing, because a learner reading the Code tab is not reading them.

**The lesson is the single source of truth for complexity.** Nothing else may state a
figure for the algorithm. The Complexity tab prints `complexity.time.worst.value`
verbatim in its caption, its "this run" row and the chart's accessible name, and the
curve named by `growth` is only ever offered as the shape that figure has, never as the
figure itself. The old per algorithm panels under the graph workspace used to carry
their own copy; four of the seven contradicted the tab, so they now carry none.

`complexity.auxiliaryNote` is the same wording on every algorithm and `complexity.thisRun`
the same within a family, so the learner reads one explanation rather than fifteen
paraphrases:

- auxiliaryNote: "Auxiliary space is the memory the algorithm needs on top of the input
  array itself."
- thisRun, for a sorting or searching lesson: "Big O describes how work grows as the
  input grows and ignores constants. The counter shows the exact work for this one
  input."
- thisRun, for a graph lesson: "Big O describes how work grows as the input grows and
  ignores constants. The sizes above are this one graph; the figure is how the work
  would grow if the graph got bigger." A graph run shows its node and edge counts and
  no counted work, because the seven algorithms do not count one shared unit, and the
  sentence must not promise a counter the box does not have.

## 4. Graphs (Phase 4b)

Graph endpoints keep their current typed step arrays, for example `["visit", "C"]`, and
gain a parallel `meta` list of the same length. `meta[k]` carries the same eight fields as
a sorting step, except that `indices` holds node or edge ids rather than array positions,
and `values` holds the numbers on them, such as a distance or an edge weight.

## 5. Gaps closed in Phase 6

These three were recorded here while Phase 4 froze the step arrays, because
fixing any of them changed what the stage was sent. Phase 6 fixed all three.

- `insertion_sort` now draws the frame where the held key lands in its gap.
  This is the only one that changed a frame count: one extra frame per outer
  loop pass. Comparisons, swaps and the sorted output are unchanged, and
  `tests/baseline_sorting.json` records the new counts.
- `merge_sort` now highlights `start + len(left) + j` for the right hand
  value, which is where it actually sits, rather than `start + j`, which
  pointed into the left half. `compared` and `indices` now agree.
- `heap_sort` now sends `[0, i]` on its extract frame instead of a list of
  colour names, one per bar. `compared` and `indices` now agree.

One legacy marker is left on purpose: every sort still ends by passing
`['green'] * n` as `compared` on its final frame. `action: "done"` is the
reliable signal, and changing that frame would move every baseline for no
gain. Read `action`, not `compared`, to find the end of a run.
