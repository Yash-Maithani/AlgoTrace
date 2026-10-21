"""Sorting: the /sorting workspace and its form post, /run_sort and /compare.

POST /sorting and /run_sort both go through sort_payload, so the page cannot
be served one run and the endpoint another.
"""
import random

from flask import jsonify, render_template, request

from ..algorithms.sorting.counting_sort import KEY_MAX
from ..catalog import SORT_LESSON_IDS, SORT_PICK_NOTES, sorting_algo_dict
from . import SiteBlueprint
from .values import parse_values

bp = SiteBlueprint("sorting", __name__)

# The two sorts that never compare values. Both are told the range of their
# keys in advance, whole numbers from 0 to KEY_MAX, and refuse anything else.
KEYED_SORTS = {"Counting Sort", "Radix Sort"}

# What the info block of a run says about each sort.
sorting_algo_details = {
    "Bubble Sort": {
        "description": "Bubble Sort repeatedly steps through the list, compares adjacent elements and swaps them if they are in the wrong order. This implementation has no early exit, so it always makes n(n-1)/2 comparisons, even on a sorted list.",
        "time_complexity": {"Best": "O(n^2)", "Average/Worst": "O(n^2)"},
        "space_complexity": "O(1)",
        "stable": True
    },
    "Selection Sort": {
        "description": "Selection Sort repeatedly finds the minimum element from the unsorted part and puts it at the beginning.",
        "time_complexity": {"Best": "O(n^2)", "Average/Worst": "O(n^2)"},
        "space_complexity": "O(1)",
        "stable": False
    },
    "Insertion Sort": {
        "description": "Insertion Sort builds the sorted array one item at a time by repeatedly picking the next item and inserting it into its correct position.",
        "time_complexity": {"Best": "O(n)", "Average/Worst": "O(n^2)"},
        "space_complexity": "O(1)",
        "stable": True
    },
    "Heap Sort": {
        "description": "Heap Sort builds a heap from the input data and repeatedly extracts the maximum element from the heap and rebuilds the heap.",
        "time_complexity": {"Best": "O(n)", "Average/Worst": "O(n log n)"},
        "space_complexity": "O(log n)",
        "stable": False
    },
    "Merge Sort": {
        "description": "Merge Sort divides the array into halves, sorts them recursively, and then merges the sorted halves.",
        "time_complexity": {"Best": "O(n log n)", "Average/Worst": "O(n log n)"},
        "space_complexity": "O(n)",
        "stable": False
    },
    "Quick Sort": {
        "description": "Quick Sort picks a pivot element, partitions the array around the pivot, and recursively sorts the partitions. This implementation always picks the last element, so an already sorted list is its worst case.",
        "time_complexity": {"Best": "O(n log n)", "Average/Worst": "O(n^2)"},
        "space_complexity": "O(n)",
        "stable": False
    },
    "Counting Sort": {
        "description": "Counting Sort counts how many times each value from 0 to 99 appears, then rewrites the list from those counts. It never compares two values.",
        "time_complexity": {"Best": "O(n + k)", "Average/Worst": "O(n + k)"},
        "space_complexity": "O(k)",
        "stable": None
    },
    "Radix Sort": {
        "description": "Radix Sort deals the values into ten buckets by their ones digit, collects them in order, then does the same by the tens digit. It never compares two values.",
        "time_complexity": {"Best": "O(d(n + b))", "Average/Worst": "O(d(n + b))"},
        "space_complexity": "O(n + b)",
        "stable": True
    }
}


@bp.route("/sorting", methods=["GET", "POST"])
def sorting_page():
    if request.method == "POST":
        # Handle form submission - call the handle_sorting function
        return handle_sorting()
    else:
        # GET request - just display the form
        # Get algorithm from query parameter, default to Bubble Sort
        selected_algo = request.args.get('algorithm', 'Bubble Sort')
        if selected_algo not in sorting_algo_dict:
            selected_algo = "Bubble Sort"

        return render_template(
            "sorting.html",
            sorting_algorithms=list(sorting_algo_dict.keys()),
            selected_algo=selected_algo,
            lesson_ids=SORT_LESSON_IDS,
            pick_notes=SORT_PICK_NOTES,
            sort_variants=_variants_for_template(),
            keyed_sorts=sorted(KEYED_SORTS),
            key_max=KEY_MAX,
            initial_run=None,
            error="",
        )


# ---------------------------------------------------------------------------
# Variant switches (Phase 10).
#
# Three sorts have one switch each. The first option of each is the version
# the site has always run, so a request that names no variant reproduces
# every earlier run and every baseline exactly. `kwargs` is what the option
# passes to the sorting function; `info` corrects the legacy info block for
# the variants that change a figure in it. The lesson file's `variants`
# block uses the same keys and option ids.
# ---------------------------------------------------------------------------

SORT_VARIANTS = {
    "Bubble Sort": {
        "key": "early_exit",
        "label": "Early exit",
        "options": [
            ("off", "Off", {"early_exit": False}, {}),
            ("on", "On", {"early_exit": True},
             {"time_complexity": {"Best": "O(n)", "Average/Worst": "O(n^2)"}}),
        ],
    },
    "Merge Sort": {
        "key": "compare",
        "label": "Merge comparison",
        "options": [
            ("lt", "left < right", {"stable": False}, {}),
            ("le", "left <= right", {"stable": True}, {"stable": True}),
        ],
    },
    "Quick Sort": {
        "key": "pivot",
        "label": "Pivot",
        "options": [
            ("last", "Last", {"pivot_rule": "last"}, {}),
            ("middle", "Middle", {"pivot_rule": "middle"},
             {"time_complexity": {"Best": "O(n log n)", "Average/Worst": "O(n^2)"}}),
            ("random", "Random (seeded)", {"pivot_rule": "random"},
             {"time_complexity": {"Best": "O(n log n)", "Average/Worst": "O(n^2)"}}),
        ],
    },
}

# Seeds are whole numbers in this range, so one fits on screen and in a
# 32 bit integer in the C and Java translations.
MAX_SEED = 2 ** 31 - 1


def _variant_options(name):
    spec = SORT_VARIANTS.get(name)
    return {opt[0]: opt for opt in spec["options"]} if spec else {}


def _default_variant(name):
    spec = SORT_VARIANTS.get(name)
    return spec["options"][0][0] if spec else None


def _read_variant(name, raw_variant, raw_seed):
    """Check the requested variant and seed. Returns (variant, seed, error).

    An algorithm with no switch accepts no variant. Only the random pivot
    takes a seed; when it is asked for without one, the server picks one and
    reports it, so the run can still be replayed from what is on screen."""
    options = _variant_options(name)
    if raw_variant in (None, ""):
        variant = _default_variant(name)
    elif raw_variant not in options:
        if not options:
            return None, None, "%s has no variants." % name
        return None, None, "%s has no variant %r. Choose one of: %s." % (
            name, raw_variant, ", ".join(options))
    else:
        variant = raw_variant

    if not (name == "Quick Sort" and variant == "random"):
        return variant, None, None
    if raw_seed in (None, ""):
        return variant, random.randint(1, 99999), None
    if isinstance(raw_seed, bool):
        return None, None, "The seed must be a whole number."
    try:
        seed = int(str(raw_seed).strip())
    except ValueError:
        return None, None, "The seed must be a whole number."
    if not 0 <= seed <= MAX_SEED:
        return None, None, "The seed must be between 0 and %d." % MAX_SEED
    return variant, seed, None


class _Tracked(int):
    """An int that remembers the position it started at.

    The sorts only compare and move values, so they carry this through
    untouched, and every frame can say where each value came from. That is
    what lets the page tag equal values 5a and 5b and show whether a sort
    kept them in order."""

    def __new__(cls, value, origin):
        item = int.__new__(cls, value)
        item.origin = origin
        return item


def _plain(value):
    """A step field with the tracked ints turned back into plain ones."""
    if isinstance(value, _Tracked):
        return int(value)
    if isinstance(value, list):
        return [_plain(v) for v in value]
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    return value


def _variants_for_template():
    """The switches as the Setup column draws them: display name to
    {key, label, options: [[id, label], ...]}."""
    return {
        name: {"key": spec["key"], "label": spec["label"],
               "options": [[opt[0], opt[1]] for opt in spec["options"]]}
        for name, spec in SORT_VARIANTS.items()
    }


def sort_payload(name, values, variant=None, seed=None):
    """One run, in the shape /run_sort answers with.

    POST /sorting and /run_sort both go through here, so the page cannot be
    served one thing and the endpoint another. `variant` defaults to the
    algorithm's first option, which is the version the site always ran.
    """
    steps = []
    if variant is None:
        variant = _default_variant(name)
    kwargs = {}
    info_overrides = {}
    if variant is not None:
        _, _, kwargs, info_overrides = _variant_options(name)[variant]
        kwargs = dict(kwargs)
        if kwargs.get("pivot_rule") == "random":
            kwargs["seed"] = seed

    def draw(array_state, compared_indices=None, meta=None):
        step_data = {
            "array": [int(v) for v in array_state],
            "compared": compared_indices[:] if compared_indices else [],
            # Where each value on screen started, for the stability tags.
            # Counting sort writes new copies made from its tallies, which
            # started nowhere, so their origin is None.
            "origins": [getattr(v, "origin", None) for v in array_state],
        }
        if meta:
            step_data.update(_plain(meta))
        # The work done so far, read off the counter the result reports, so
        # the running total on screen cannot drift from the final one. The
        # Learn panel shows these as the run plays.
        step_data.setdefault("vars", {})
        step_data["vars"] = dict(step_data["vars"],
                                 comparisons=stats["comparisons"],
                                 swaps=stats["swaps"])
        steps.append(step_data)

    stats = {"swaps": 0, "comparisons": 0}
    working = [_Tracked(v, i) for i, v in enumerate(values)]
    sorting_algo_dict[name](working, draw, lambda: None, stats, **kwargs)
    details = dict(sorting_algo_details[name], **info_overrides)

    return {
        "steps": steps,
        "array": list(values),
        "sorted": [int(v) for v in working],
        "algorithm": name,
        # The run records which version of the algorithm made it, and the
        # seed when there is one, so it can be replayed exactly.
        "variant": variant,
        "seed": seed if kwargs.get("pivot_rule") == "random" else None,
        "result": {
            "comparisons": stats["comparisons"],
            "swaps": stats["swaps"],
            "n": len(values),
            "kept_equal_order": _kept_equal_order(working),
        },
        "info": {
            "stable": details["stable"],
            "time_complexity": details["time_complexity"],
            "space_complexity": details["space_complexity"],
            "description": details["description"],
        },
    }


def _kept_equal_order(final):
    """True when every group of equal values ended in its starting order.

    None when the input had no equal values, because then there was nothing
    for a sort to keep or break."""
    if any(not hasattr(item, "origin") for item in final):
        # Rebuilt from counts: no value on screen is one that was read, so
        # there is no starting order to keep or break.
        return None
    seen = {}
    for item in final:
        seen.setdefault(int(item), []).append(item.origin)
    groups = [g for g in seen.values() if len(g) > 1]
    if not groups:
        return None
    return all(g == sorted(g) for g in groups)


# ---------------------------------------------------------------------------
# Sorting over JSON.
#
# POST /sorting still renders the page with its steps embedded, which is how
# the form has always worked. /run_sort answers the same run as JSON so the
# workspace can start one without reloading. Both call the same six
# functions, so neither can drift from the other.
# ---------------------------------------------------------------------------

SORT_ACTIONS = {"compare", "swap", "overwrite", "select", "place", "done",
                "count", "bucket"}

MAX_SORT_SIZE = 100


# Every random value on the site is a whole number from 1 to RANDOM_MAX: here,
# the presets (static/js/presets.js), Compare (which uses the presets) and the
# searching page's Random array. One range, inside the 0 to KEY_MAX that
# Counting and Radix Sort accept, so any generated input runs on every sort.
RANDOM_MAX = 99


def _random_values(name, size):
    """A random input of `size` values from 1 to RANDOM_MAX, whichever sort
    it is for."""
    return [random.randint(1, RANDOM_MAX) for _ in range(size)]


def _check_keys(name, values):
    """Counting and Radix Sort take whole numbers from 0 to KEY_MAX only.
    Returns the message for the first value outside that range, or None."""
    if name not in KEYED_SORTS:
        return None
    for v in values:
        if v < 0 or v > KEY_MAX:
            return ("%s takes whole numbers from 0 to %d only, and %d is %s. "
                    "%s" % (name, KEY_MAX, v, "negative" if v < 0 else "too big",
                            KEY_PROBLEM[name]))
    return None


KEY_PROBLEM = {
    "Counting Sort": "Its count list has one slot for each value from 0 to %d, "
                     "so a value outside that range has nowhere to be counted." % KEY_MAX,
    "Radix Sort": "It sorts by the ones digit and then the tens digit, so it "
                  "needs values of at most two digits and no minus sign.",
}


@bp.route("/run_sort", methods=["POST"])
def run_sort():
    try:
        data = request.json or {}
        name = data.get("algorithm", "Bubble Sort")
        if name not in sorting_algo_dict:
            return jsonify({"error": "Unknown sorting algorithm %r." % name}), 400

        if data.get("values") in (None, "", []):
            try:
                size = int(data.get("size", 30))
            except (TypeError, ValueError):
                return jsonify({"error": "Array size must be a whole number."}), 400
            if not 5 <= size <= MAX_SORT_SIZE:
                return jsonify({
                    "error": "Array size must be between 5 and %d." % MAX_SORT_SIZE
                }), 400
            values = _random_values(name, size)
        else:
            values, problem = parse_values(data.get("values"), MAX_SORT_SIZE)
            if problem:
                return jsonify({"error": problem}), 400
            problem = _check_keys(name, values)
            if problem:
                return jsonify({"error": problem}), 400

        variant, seed, problem = _read_variant(name, data.get("variant"), data.get("seed"))
        if problem:
            return jsonify({"error": problem}), 400

        return jsonify(sort_payload(name, values, variant, seed))
    except Exception as e:
        return jsonify({"error": "An error occurred: %s" % e}), 500


# ---------------------------------------------------------------------------
# Compare mode (Phase 17).
#
# Two sorts on one input with one transport. Each side runs through
# /run_sort, the same endpoint /sorting uses, so the counts on /compare are
# the counts /sorting shows for that input and variant.
# ---------------------------------------------------------------------------

# The "What to try" pairs. Each sentence states only what the code does on
# that kind of input, and tests/test_compare.py runs every pair to check it.
COMPARE_TRIES = [
    {"left": "Bubble Sort", "left_variant": "off", "right": "Merge Sort", "right_variant": "lt",
     "preset": "reversed", "size": 20, "title": "Bubble vs Merge on Reversed",
     "text": "Bubble Sort compares every neighbouring pair on every pass; Merge Sort "
             "halves the list. Merge Sort finishes long before Bubble Sort does."},
    {"left": "Insertion Sort", "left_variant": None, "right": "Quick Sort", "right_variant": "last",
     "preset": "sorted", "size": 20, "title": "Insertion vs Quick on Already sorted",
     "text": "Already sorted is Insertion Sort's best case, n-1 comparisons, and the worst "
             "case for Quick Sort with the last element as pivot."},
    {"left": "Quick Sort", "left_variant": "last", "right": "Quick Sort", "right_variant": "middle",
     "preset": "sorted", "size": 20, "title": "Quick (last pivot) vs Quick (middle pivot) on Already sorted",
     "text": "The same partition with a different pivot. The middle pivot splits a sorted "
             "list evenly, so it needs far fewer comparisons."},
    {"left": "Merge Sort", "left_variant": "lt", "right": "Merge Sort", "right_variant": "le",
     "preset": "equal", "size": 12, "title": "Merge < vs Merge <= on All equal",
     "text": "On equal values < takes the right value first and <= the left. Watch the "
             "letter tags: only <= keeps them in order, and it needs fewer comparisons."},
    {"left": "Bubble Sort", "left_variant": "off", "right": "Bubble Sort", "right_variant": "on",
     "preset": "nearly", "size": 20, "title": "Bubble vs Bubble with early exit on Nearly sorted",
     "text": "The same swaps on both sides, but the early exit stops after the first pass "
             "that changes nothing."},
    {"left": "Counting Sort", "left_variant": None, "right": "Merge Sort", "right_variant": "lt",
     "preset": "random", "size": 30, "title": "Counting vs Merge on Random",
     "text": "Counting Sort never compares two values, so the banner compares the steps "
             "each side shows instead. Merge Sort makes over a hundred comparisons on 30 "
             "values; Counting Sort makes none and still finishes first."},
]


@bp.route("/compare")
def compare_page():
    """Two sorting algorithms side by side on the same input."""
    names = list(sorting_algo_dict.keys())
    left = request.args.get("left", "Bubble Sort")
    right = request.args.get("right", "Merge Sort")
    return render_template(
        "compare.html",
        sorting_algorithms=names,
        lesson_ids=SORT_LESSON_IDS,
        sort_variants=_variants_for_template(),
        left=left if left in sorting_algo_dict else "Bubble Sort",
        right=right if right in sorting_algo_dict else "Merge Sort",
        tries=COMPARE_TRIES,
        max_size=MAX_SORT_SIZE,
    )


def handle_sorting():
    """The form POST. Still runs the sort here and still renders the page.

    The page is the workspace now, so the run travels as initial_run in the
    shape /run_sort answers with, and the workspace loads it on arrival.
    """
    selected_algo = request.form.get("algorithm", "Bubble Sort")
    if selected_algo not in sorting_algo_dict:
        selected_algo = "Bubble Sort"
    input_method = request.form.get("input_method", "random")
    error = ""
    values = []

    if input_method == "manual":
        values, error = parse_values(request.form.get("manual_input", ""),
                                      MAX_SORT_SIZE)
        if not error:
            error = _check_keys(selected_algo, values) or ""
        if error:
            values = []
    else:
        try:
            size = int(request.form.get("size", 30))
        except ValueError:
            error = "Invalid array size. Please enter a valid number."
            size = None
        if size is not None:
            if not 5 <= size <= MAX_SORT_SIZE:
                error = "Array size must be between 5 and %d." % MAX_SORT_SIZE
            else:
                values = _random_values(selected_algo, size)

    variant, seed = None, None
    if not error:
        variant, seed, error = _read_variant(selected_algo,
                                             request.form.get("variant"),
                                             request.form.get("seed"))
        if error:
            values = []

    return render_template(
        "sorting.html",
        sorting_algorithms=list(sorting_algo_dict.keys()),
        selected_algo=selected_algo,
        lesson_ids=SORT_LESSON_IDS,
        pick_notes=SORT_PICK_NOTES,
        sort_variants=_variants_for_template(),
        keyed_sorts=sorted(KEYED_SORTS),
        key_max=KEY_MAX,
        initial_run=None if error else sort_payload(selected_algo, values, variant, seed),
        error=error,
    )
