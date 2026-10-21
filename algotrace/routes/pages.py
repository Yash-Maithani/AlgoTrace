"""Home, /learn, /big-o and the two legal pages."""
from flask import render_template, request

from ..algorithms.sorting.bubble_sort import bubble_sort
from ..catalog import LEARN_ORDER, START_HERE_COUNT, algorithm_counts
from . import SiteBlueprint
from .graphs import handle_graph
from .sorting import handle_sorting, sort_payload

bp = SiteBlueprint("pages", __name__)

# ---------------------------------------------------------------------------
# Home page demonstration data.
#
# Both of these call the real bubble_sort from sorting_algorithms, the same
# function the /sorting page uses. Nothing here reimplements an algorithm or
# hand writes a step, so if that code changes these change with it.
# ---------------------------------------------------------------------------

HERO_ARRAY = [42, 17, 93, 8, 61, 29, 75, 36]
BAND_ARRAY = [17, 11, 32, 45, 9]


def _bubble_steps(values):
    """Run the real bubble sort over `values` and collect its draw calls."""
    data = list(values)
    steps = []
    stats = {"swaps": 0, "comparisons": 0}

    def draw(array_state, compared_indices=None, meta=None):
        # The hero only needs the bars, so the teacher payload is accepted
        # and dropped. See static/js/lessons/README.md for its shape.
        steps.append({
            "array": array_state[:],
            "compared": compared_indices[:] if compared_indices else [],
        })

    bubble_sort(data, draw, lambda: None, stats)
    return steps, stats


def _player_payload():
    """The run the Home player plays: the real bubble sort over BAND_ARRAY,
    exactly the steps /run_sort would send for it, trimmed to what the player
    draws. `origins[i]` says which starting position the cell now at i began
    in, which is how a swapped pair can slide past each other instead of
    being redrawn."""
    run = sort_payload("Bubble Sort", list(BAND_ARRAY), None, None)
    steps = [{
        "array": s["array"],
        "origins": s["origins"],
        "action": s["action"],
        "indices": s["indices"],
        "line": s["line"],
        "comparisons": s["vars"].get("comparisons", 0),
        "swaps": s["vars"].get("swaps", 0),
        "explain": s["explain"],
    } for s in run["steps"]]
    return {
        "start": list(BAND_ARRAY),
        "steps": steps,
        "total": run["result"]["comparisons"],
        "n": run["result"]["n"],
        # The step the page is served on, and shows when motion is reduced.
        "frozen": next((i for i, s in enumerate(steps) if i >= 4 and s["action"] == "compare"), 0),
    }


@bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        algo_type = request.form.get("algo_type", "sorting")
        if algo_type == "sorting":
            return handle_sorting()
        else:
            return handle_graph()
    hero_steps, hero_stats = _bubble_steps(HERO_ARRAY)
    return render_template(
        "landing.html",
        start_here=LEARN_ORDER[:START_HERE_COUNT],
        counts=algorithm_counts(),
        hero_steps=hero_steps,
        hero_start=HERO_ARRAY,
        hero_sorted=sorted(HERO_ARRAY),
        hero_comparisons=hero_stats["comparisons"],
        player=_player_payload(),
    )


_NUMBER_WORDS = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight",
                 "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
                 "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]


@bp.app_template_filter("words")
def _words(number):
    """A count as a word, for running text: 8 -> eight."""
    return _NUMBER_WORDS[number] if 0 <= number < len(_NUMBER_WORDS) else str(number)


@bp.route("/learn")
def learn():
    """Algorithm index with a suggested beginner order."""
    return render_template("learn.html", learn_order=LEARN_ORDER, counts=algorithm_counts())


@bp.route("/big-o")
def big_o_page():
    """How complexity works. Every figure on it comes from this repository."""
    return render_template("big_o.html")


@bp.route("/privacy")
def privacy():
    """Privacy policy, rendered inside the shared layout."""
    return render_template("privacy.html")


@bp.route("/terms")
def terms():
    """Terms and conditions, rendered inside the shared layout."""
    return render_template("terms.html")
