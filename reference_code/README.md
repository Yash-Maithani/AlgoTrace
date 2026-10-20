# Reference code: C, C++ and Java

One real, compilable program per algorithm per language, each a line by line
translation of the Python in `sorting_algorithms/`, `searching_algorithms/`
and the seven graph endpoints in `app.py`. They copy this repository's
behaviour, not the textbook's: no early exit in bubble sort unless the variant
asks for it, `<` in merge sort unless the variant says `<=`, the last element
as pivot unless the variant says otherwise, the same seeded generator
(mulberry32) for the random pivot, queue and stack membership checked by a
linear scan as the endpoints do, Dijkstra's first-listed tie-break, a stable
sort in Kruskal, and Prim's heap ordered by the whole (weight, u, v) tuple.

| Language | Standard | Folder | File name |
| --- | --- | --- | --- |
| C | C11 | `c/` | `<algo>.c` |
| C++ | C++17 | `cpp/` | `<algo>.cpp` |
| Java | Java 17 (`javac --release 17`) | `java/` | `<Algo>.java` |

`tests/test_reference_code.py` compiles every program and checks it against
the Python, step by step. `tools/extract_code.py` turns the teaching part of
each file into `static/js/lessons/code/<algo>.js`, which the Code tab will
read; never edit those by hand.

## Input

Every program reads the same format on standard input, so one test batch
drives all of them:

```
<number of cases>
<variant> <seed> <target>
<n>
<n whole numbers>
... the next case ...
```

`variant` is the option id from the lesson (`off`, `on`, `lt`, `le`, `last`,
`middle`, `random`) or `-` for an algorithm without a switch. `seed` is used
only by the random pivot and `target` only by the searches; the others read
and ignore them. An unknown variant is an error.

## Output

For each case, one line per frame the site draws, then the answer and the
counts the site reports, then `end`:

```
step <action> <line id or -> <index>:<value> ... [depth=<d> range=<lo>:<hi>]
sorted <values>          (sorts)       index <i or -1>   (searches)
comparisons <count>
swaps <count>            (sorts only; merge sort's are writes, as on the site)
end
```

`depth` and `range` appear on merge sort and quick sort frames, as in their
step meta. Counting sort frames add `cells=<lo>:<hi> count=<count[lo]>`, the
slots of the count list the frame is about; radix sort frames add
`bucket=<b> size=<values in it as drawn> place=<1 or 10>`.

Counting sort and radix sort take whole numbers from 0 to 99 only, like
`/run_sort`. A value outside that range is an error: the program prints
`error value <v> is outside 0 to 99` and exits with a non-zero status.

## Markers

The teaching part of a file sits between two comment lines:

```
// lesson:start
...
// lesson:end
```

A file may have several such blocks; the listing is them in file order.
Inside a block a trailing comment carries tags:

| Tag | Meaning |
| --- | --- |
| `@<line id>` | the line has this id, the same id as in the Python listing, so a step lights up the same line in every language |
| `@hide` | plumbing: a counter, a step trace, or a brace that only selects a variant at run time. Left out of the listing |
| `@only:<v>[,<v>]` | shown only in the listing of these variants |

A file with variants names them on a line `// lesson:variants <default> <other> ...`,
default first. A hidden line that opens a brace does not indent the listing,
so a variant's lines read as they would in a program with only that variant.
Blank lines and comment-only lines inside a block are left out.

## Graph programs (Phase 13)

BFS, DFS, Dijkstra, Prim, Kruskal, Bellman-Ford, Floyd-Warshall and Topological
Sort (Phase 20) copy the eight `/run_*` endpoints in `app.py`. They read one graph format:

```
<number of cases>
<start node, or - for Kruskal and Floyd-Warshall>
<k>                                   then k node lines, in input order:
<name> <d> <neighbour> <weight> ...   d neighbours, in input order
<m>                                   then m edge lines, in input order:
<u> <v> <weight>
```

The node lines are the adjacency the endpoint receives (`graph` in the
request), keys in order, each with its neighbours in order, because Python
dicts keep insertion order and the result depends on it. BFS and DFS take
plain neighbour lists, so their weights are placeholders and ignored.
Kruskal and Floyd-Warshall take `nodes` and `edges`: their node lines have
no neighbours and the edges follow. Names are single tokens without spaces
and weights are whole numbers, as every graph the site sends is.

Each case prints one line per entry in the endpoint's `meta`, then the
result, then `end`:

```
step <action> <line id or -> <node> ... | <value> ...
```

Unreachable distances print as `∞`, the endpoint's wire form. The result
lines are those of the endpoint's final step (or, for Bellman-Ford, its
summary fields):

| Program | Result lines |
| --- | --- |
| BFS, DFS | `path <nodes in visiting order>` |
| Dijkstra | `distance <node> <d>` per node, `path <node> <nodes>` per reached node, both by node name |
| Prim, Kruskal | `edge <u> <v> <w>` per tree edge in order, `total <w>` |
| Floyd-Warshall | `row <node> <d> ...` per node in input order, `path <from> <to> <d> <nodes>` per pair with a route, by from then to name |
| Bellman-Ford | `distance <node> <d>` by node name, `negative_cycle true|false`, `iterations <n>` |
| Topological Sort | `order <nodes>`, `remaining <nodes left over>`, `cycle <nodes>` (the last two empty when there is no cycle) |

Maps come out in order of name because that is how they reach the browser:
the endpoints answer with Flask's `jsonify`, which sorts object keys. For
Bellman-Ford it is also the only reproducible order, since the endpoint
builds its distances from a Python set, whose order changes from one process
to the next. Lists, such as the meta, the tree edges and the matrix rows,
keep the order the endpoint built them in.

## Helpers

Code the lesson leans on but does not teach, such as a queue, a stack, a
binary heap, union-find, a stable sort or looking a node up by name, sits in
blocks of its own:

```
// lesson:helpers
...
// lesson:end
```

`tools/extract_code.py` writes those lines to a separate `helpers` listing
per language, so the Code tab shows the algorithm and offers the helpers
behind a toggle. Helper lines carry no line ids.

## Grid programs (Phase 21)

A* copies `grid_algorithms/astar.py`, including its binary heap, so the same
entries come out in the same order with the same number of comparisons.
Moves are tried up, right, down, left; every move costs 1; h is the
Manhattan distance, or 0 for Dijkstra. The heap orders entries by lowest f,
then lowest h, then push order. A cell whose g improves is pushed again, and
its older entry is skipped (a `reject stale` step) when it comes out.

```
<number of cases>
<manhattan|zero> <rows> <cols>
<start row> <start column> <goal row> <goal column>
<rows lines of . (free) and # (wall)>
```

Each case prints one line per step, `step <action> <line id> <cells> | <values>`
with cells written `r,c` (an `enqueue` or `relax` names the cell then the
cell it was reached from, and its values are g and h), then:

```
path <cells from start to goal, or nothing>
expanded <cells expanded>
comparisons <heap comparisons>
end
```
