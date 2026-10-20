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

Two more fields belong to particular sorts (Phase 10):

| Field | Type | Meaning |
| --- | --- | --- |
| `origins` | list of ints | every sorting step, added by app.py: `origins[k]` is the position in the input that the value now at `k` started from. The page tags equal values 5a, 5b from it. Halfway through a merge sort copy back one value can sit in two places, so it is a permutation on every frame except `overwrite` ones |
| `depth`, `range` | int, `[lo, hi]` | every Merge Sort and Quick Sort step: how many calls deep the step is (the first call is 0) and the inclusive range that call owns. The `done` frame is depth 0 over `[0, n-1]`; an empty list's is `[0, -1]` |
| `taken` | `'left'` or `'right'` | Merge Sort `compare` steps only: which half the comparison takes from, so Predict mode can ask about it without guessing. It is not drawn on the stage, and no step array or count depends on it |
| `counts`, `cells` | list of ints, `[lo, hi]` | every Counting Sort step (Phase 19): the count list as it stands, one slot per value from 0 to 99, and the inclusive slots the step is about. A run of empty slots read in a row is one step with `lo < hi`. The strip under the bars draws these |
| `buckets`, `bucket`, `place` | ten lists, int or null, 1 or 10 | every Radix Sort step (Phase 19): the ten buckets as drawn (a bucket being emptied without the values already taken from its front), the bucket the step is about, and the digit place of the pass. The `done` frame has `bucket` and `place` null |

Counting Sort rebuilds its values from the counts, so a value it writes back
started nowhere: its entry in `origins` is `null`, and its run's
`kept_equal_order` is `null`, because there is no starting order to keep.

### `action` vocabulary

| Action | Meaning |
| --- | --- |
| `compare` | two values were read and compared. Nothing moved |
| `swap` | two cells exchanged contents |
| `overwrite` | one cell was written with a value from somewhere else, as in an insertion shift or a merge write back |
| `select` | a position or a candidate was marked, for example the next slot to fill or a new running minimum. Counting Sort uses it for reading slots of its count list |
| `place` | a value reached its final position, as with a quick sort pivot |
| `done` | the final frame. The array is sorted and nothing is highlighted |
| `count` | Counting Sort: a value was read and one slot of the count list went up. Nothing moved |
| `bucket` | Radix Sort: a value was dealt to the back of the bucket for its digit. Nothing moved |

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
| `complexity.time.<case>.theta` | string | Phase 11. The tight bound for that case, derived from this repository's code and measured by `tests/test_phase11.py`. One of `1`, `log n`, `square root of n`, `n`, `n log n`, `n squared`, `V`, `E`, `V squared`, `V cubed`, `V times E`, `E log E`, `k times E` (Bellman-Ford's average, k being its number of passes), `n plus k` (Counting Sort, k the largest key) `d times (n plus b)` (Radix Sort, d digits and b buckets) or `V plus E` (Topological Sort). The case's `value` must read `O(<theta>)` |
| `complexity.overall` | `{O, Omega, Theta}` | the bounds across every input. `O` equals the worst case's theta, `Omega` the best case's, and `Theta` is that bound when the two agree and `null` when they differ |
| `complexity.misconception` | string | the shared note that cases (best, average, worst) and bounds (O, Omega, Theta) are different ideas. Same wording in every lesson, exactly as in `tests/validate_lessons.js` |
| `complexity.caseScope` | string | graph lessons only, required. Which graphs the cases range over, for example graphs where the start reaches every node |
| `complexity.worked` | `{input, comparisons, note}` | an exact count for a real n = 5 input |
| `complexity.space` | `{value, what}` | `what` names the memory, for example "the recursion stack" |
| `complexity.auxiliaryNote` | string | the fixed explanation of what auxiliary means |
| `complexity.thisRun` | string | the fixed sentence for the "this run" box. Two of them: one for a counted family, one for graphs, which show no counted work |
| `complexity.growth` | string or null | which reference curve has this algorithm's shape: `1`, `logn`, `sqrtn`, `n`, `nlogn`, `n2` or `n3`. `null` when the figure needs two numbers at once, such as `O(V times E)`, because no curve on an axis of one variable is that figure |
| `complexity.growthBasis` | string or null | what `n` on the axis stands for when the figure is written in another letter, for example `'V, the number of nodes'`. `null` when the figure is already in `n` |
| `complexity.growthNote` | string or null | why no curve fits. Required when `growth` is null, forbidden otherwise, and it must name the figure it is explaining |
| `complexity.countsNote` | string or null | an explanation of a counter the learner will find surprising, shown under the "this run" box |
| `complexity.divergence` | string or null | how this implementation differs from the textbook figure |
| `presets` | list of strings | optional. Which input presets the page offers: any of `random`, `sorted`, `reversed`, `equal`, `nearly`. Omitted means all five. Binary search sets `['sorted', 'equal']`, because the other three would be refused |
| `presetNotes` | object | sorting and searching only. One sentence per offered preset saying what that input means for this algorithm, drawn from the real counts |
| `stable` | boolean or null | whether equal values keep their original order. `null` where it does not apply, as for a search |
| `codePending` | boolean | present and `true` only while the lesson ships ahead of its implementation. The listing is then the form the later phase must build, and that phase either matches it or updates the lesson in the same commit |
| `countLabel` | string | what the second counter is called, when it is not `swaps`. Merge sort sets `writes`, because it never exchanges a pair: it copies a merged run back over the array, so every value in the run is written whether or not it moved. A lesson that sets this must also explain it in `complexity.countsNote` |

| `complexity.claims` | list | the figures the text states, in a form the tests can measure. Each is `{input, comparisons, bound, where}` or `{input, sameAs, where}`. `input` is `sorted`, `reversed`, `equal`, `random` or `nearly`; `comparisons` is a formula in `n` using `+ - * / ( )`, `log2`, `H` (harmonic number), `ceil`, `floor`; `bound` is `exact`, `atMost` or `mean` (averaged over seeds); `sameAs` says the count equals that of another input; `where` names the text it backs, such as `time.best`, `presetNotes.equal` or `divergence`. Required on a lesson with `variants` |
| `complexity.worked.seed` | number | only where the count depends on a seed, as with a random pivot |
| `variants` | object | optional, sorting only. A switch with `{key, label, default, options}`. `key` and the option ids match `SORT_VARIANTS` in app.py, and `default` is the first, the version the site always ran. Each option has `label` and `note` (one sentence shown under the switch). Every other option may override `idea`, `stable`, `presetNotes` (merged per preset), `code` (both listings, replaced whole), and `complexity` (merged per key, `time` per case). An option that changes `time` or `worked` gives its own `claims`. `static/js/variants.js` applies an option, and the validator checks every option as the page will show it |

The two code listings show the algorithm, not the plumbing. The `draw` and `stats`
calls that exist in the Python file are instrumentation for the visualization and are
left out of the listing, because a learner reading the Code tab is not reading them.

**The lesson is the single source of truth for complexity.** Nothing else may state a
figure for the algorithm. The Complexity tab prints `complexity.time.worst.value`
verbatim in its caption, its "this run" row and the chart's accessible name, and the
curve named by `growth` is only ever offered as the shape that figure has, never as the
figure itself. The old per algorithm panels under the graph workspace used to carry
their own copy; four of the seven contradicted the tab, so they now carry none.

A case is a kind of input; a bound is a statement about growth. Every case
has its own Theta, and the overall line follows from the extreme cases: the
growth on any input is at most the worst case's and at least the best
case's. The `growth` curve is the shape of the worst case's theta, or `null`
when that theta names two variables. The validator enforces all of this.

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

## 6. Listings in other languages (Phase 12)

`code/<algorithm>.js` holds the C, C++ and Java listings. They are generated by
`tools/extract_code.py` from the programs in `reference_code/`; the markers
those programs use are documented in `reference_code/README.md`. Never edit a
generated file: change the program and rerun the tool.

```js
window.LESSON_CODE = window.LESSON_CODE || {};
window.LESSON_CODE.bubble_sort = {
    c:    { source: 'reference_code/c/bubble_sort.c',
            listings: { off: [...], on: [...] },
            helpers: [...] },
    cpp:  { ... },
    java: { ... }
};
```

Each listing is a list of `{id, text, indent}` lines, the same shape as
`code.python`. A lesson with a switch has one listing per option id; one
without has a single listing called `default`. `helpers` holds the lines of the
program's `lesson:helpers` blocks, such as a queue, a binary heap, union-find or
looking a node up by name: code the algorithm calls but does not teach, for a
"Show helpers" toggle. Helper lines never carry an id, so showing them cannot
move the highlight. `node tests/validate_lessons.js` requires every lesson to
have the file, every listing to use exactly the set of line ids of the matching
Python listing, so a step lights up the same line in whichever language is
shown, and every language to list its helpers, even when there are none.
