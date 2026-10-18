# Reference code: C, C++ and Java

One real, compilable program per algorithm per language, each a line by line
translation of the Python in `sorting_algorithms/` and `searching_algorithms/`.
They copy this repository's behaviour, not the textbook's: no early exit in
bubble sort unless the variant asks for it, `<` in merge sort unless the
variant says `<=`, the last element as pivot unless the variant says
otherwise, and the same seeded generator (mulberry32) for the random pivot.

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
step meta.

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
