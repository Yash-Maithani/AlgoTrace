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
| `complexity.thisRun` | string | the fixed sentence for the "this run" box |
| `complexity.growth` | string | which curve to draw: `1`, `logn`, `n`, `nlogn` or `n2` |
| `complexity.divergence` | string or null | how this implementation differs from the textbook figure |
| `stable` | boolean or null | whether equal values keep their original order. `null` where it does not apply, as for a search |
| `codePending` | boolean | present and `true` only while the lesson ships ahead of its implementation. The listing is then the form the later phase must build, and that phase either matches it or updates the lesson in the same commit |

The two code listings show the algorithm, not the plumbing. The `draw` and `stats`
calls that exist in the Python file are instrumentation for the visualization and are
left out of the listing, because a learner reading the Code tab is not reading them.

`complexity.auxiliaryNote` and `complexity.thisRun` are the same wording on every
algorithm, so the learner reads one explanation rather than six paraphrases:

- auxiliaryNote: "Auxiliary space is the memory the algorithm needs on top of the input
  array itself."
- thisRun: "Big O describes how work grows as the input grows and ignores constants. The
  counter shows the exact work for this one input."

## 4. Graphs (Phase 4b)

Graph endpoints keep their current typed step arrays, for example `["visit", "C"]`, and
gain a parallel `meta` list of the same length. `meta[k]` carries the same eight fields as
a sorting step, except that `indices` holds node or edge ids rather than array positions,
and `values` holds the numbers on them, such as a distance or an edge weight.

## 5. Known gaps for the UI phases

- `insertion_sort` never draws the frame where the held key is written back into the gap,
  so the array appears to shift without the key landing. Phase 6 should render that from
  the following step rather than adding a draw call here, which would change the step
  count this contract freezes.
- `merge_sort` highlights `start + i` and `start + j` while comparing, but the right hand
  value actually lives at `start + len(left) + j`, so the stage highlights the wrong cell
  on the right. `indices`, `values` and `explain` all carry the true positions and values,
  so only `compared` is wrong. Phase 6 owns the fix, since changing `compared` changes the
  animation this contract freezes.
- `heap_sort` passes colour names in `compared` on its extract step. `indices` carries the
  real pair.
