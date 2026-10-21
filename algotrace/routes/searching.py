"""Searching: the /searching workspace and /run_search."""
from flask import jsonify, render_template, request

from ..algorithms.searching.binary_search import is_sorted
from ..catalog import SEARCH_ALGORITHMS, SEARCH_PICKER
from . import SiteBlueprint
from .values import parse_values

bp = SiteBlueprint("searching", __name__)

# ---------------------------------------------------------------------------
# Searching.
#
# Steps follow section 1 of static/js/lessons/README.md: array and compared
# drive the stage, the six teacher fields drive the Learn panel. The search
# actions extend the shared vocabulary rather than overloading it:
#   compare   a value was read and tested against the target
#   discard   binary search threw away the half that cannot hold the target
#   found     the target was located at this position
#   missing   the search ended without a match
# ---------------------------------------------------------------------------

SEARCH_ACTIONS = {"compare", "discard", "found", "missing"}

# The searches that are only correct on a sorted list, and the one sentence
# that says why when a run is refused.
NEEDS_SORTED = {
    "binary_search": "Binary search only works on a sorted list, because it "
                     "throws away half the range based on the value in the middle.",
    "jump_search": "Jump search only works on a sorted list, because it skips a "
                   "whole block once the block's last value is smaller than the target.",
}

MAX_SEARCH_SIZE = 30


@bp.route("/searching")
def searching_page():
    """The searching workspace. The run itself goes through /run_search.

    ?algorithm= opens on that one, the same way /sorting does, because the
    Learn page links straight to a named algorithm.
    """
    selected = request.args.get("algorithm", "linear_search")
    if selected not in SEARCH_ALGORITHMS:
        selected = "linear_search"

    return render_template(
        "searching.html",
        algorithms=SEARCH_PICKER,
        selected_algo=selected,
    )


@bp.route("/run_search", methods=["POST"])
def run_search():
    try:
        data = request.json or {}
        name = data.get("algorithm", "linear_search")
        if name not in SEARCH_ALGORITHMS:
            return jsonify({"error": "Unknown search algorithm %r." % name}), 400

        values, problem = parse_values(data.get("array"), MAX_SEARCH_SIZE)
        if problem:
            return jsonify({"error": problem}), 400

        raw_target = data.get("target")
        if isinstance(raw_target, bool) or raw_target is None or raw_target == "":
            return jsonify({"error": "Enter a target to search for."}), 400
        try:
            target = int(str(raw_target).strip())
        except (ValueError, TypeError):
            return jsonify({"error": "%s is not a whole number." % raw_target}), 400

        # Binary search is only correct on a sorted list, so the run is
        # blocked rather than quietly returning a wrong answer. The sorted
        # copy travels with the refusal so the page can offer to fix it.
        if name in NEEDS_SORTED and not is_sorted(values):
            return jsonify({
                "error": NEEDS_SORTED[name],
                "unsorted": True,
                "sorted_array": sorted(values),
            }), 400

        steps = []

        def draw(indices, meta):
            step_data = {
                "array": list(values),
                "compared": list(indices),
            }
            step_data.update(meta)
            steps.append(step_data)

        stats = {"comparisons": 0}
        found_at = SEARCH_ALGORITHMS[name](values, target, draw, None, stats)

        return jsonify({
            "steps": steps,
            "array": values,
            "target": target,
            "algorithm": name,
            "result": {
                "found": found_at != -1,
                "index": found_at,
                "comparisons": stats["comparisons"],
            },
        })
    except Exception as e:
        return jsonify({"error": "An error occurred: %s" % e}), 500
