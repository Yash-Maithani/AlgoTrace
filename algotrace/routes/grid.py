"""A* on a grid: /run_astar. The grid workspace page itself is /graph?algo=astar."""
from flask import jsonify, request

from ..algorithms.grid.astar import astar
from . import SiteBlueprint

bp = SiteBlueprint("grid", __name__)

# ---------------------------------------------------------------------------
# A* on a grid (Phase 21). The grid workspace posts the grid; the steps are
# objects like the sorting and searching steps, with cells named "r,c". The
# code is algotrace/algorithms/grid/astar.py; Dijkstra is the same code with h = 0.
# ---------------------------------------------------------------------------

GRID_ROWS = (5, 20)
GRID_COLS = (6, 30)


def _read_cell(value, rows, cols, what):
    if (not isinstance(value, (list, tuple)) or len(value) != 2
            or not all(isinstance(v, int) and not isinstance(v, bool) for v in value)):
        return None, "The %s must be a cell, [row, column]." % what
    r, c = value
    if not (0 <= r < rows and 0 <= c < cols):
        return None, "The %s (%d, %d) is outside the %d by %d grid." % (what, r, c, rows, cols)
    return (r, c), None


@bp.route("/run_astar", methods=["POST"])
def run_astar():
    try:
        data = request.json or {}
        rows, cols = data.get("rows"), data.get("cols")
        for value, (low, high), name in ((rows, GRID_ROWS, "rows"), (cols, GRID_COLS, "columns")):
            if not isinstance(value, int) or isinstance(value, bool) or not low <= value <= high:
                return jsonify({"error": "The grid needs %d to %d %s." % (low, high, name)}), 400
        start, problem = _read_cell(data.get("start"), rows, cols, "start")
        if problem:
            return jsonify({"error": problem}), 400
        goal, problem = _read_cell(data.get("goal"), rows, cols, "goal")
        if problem:
            return jsonify({"error": problem}), 400
        if start == goal:
            return jsonify({"error": "The start and the goal must be different cells."}), 400
        walls = set()
        for item in data.get("walls") or []:
            cell, problem = _read_cell(item, rows, cols, "wall")
            if problem:
                return jsonify({"error": problem}), 400
            walls.add(cell)
        if start in walls or goal in walls:
            return jsonify({"error": "The start and the goal cannot be walls."}), 400
        heuristic = data.get("heuristic", "manhattan")
        if heuristic not in ("manhattan", "zero"):
            return jsonify({"error": "The heuristic is manhattan, or zero for Dijkstra."}), 400

        steps = []
        stats = {}
        path = astar(rows, cols, walls, start, goal, steps.append, heuristic, stats)
        other_heuristic = "zero" if heuristic == "manhattan" else "manhattan"
        other_stats = {}
        other_path = astar(rows, cols, walls, start, goal, None, other_heuristic, other_stats)
        return jsonify({
            "steps": steps,
            "algorithm": "astar",
            "heuristic": heuristic,
            "grid": {"rows": rows, "cols": cols, "walls": sorted([list(w) for w in walls]),
                     "start": list(start), "goal": list(goal)},
            "result": {
                "found": path is not None,
                "path": [list(c) for c in path] if path else [],
                "length": len(path) - 1 if path else None,
                "expanded": stats["expanded"],
                "pushes": stats["pushes"],
                "comparisons": stats["comparisons"],
                "other": {"heuristic": other_heuristic, "expanded": other_stats["expanded"],
                          "length": len(other_path) - 1 if other_path else None},
            },
        })
    except Exception as e:
        return jsonify({"error": "An error occurred: %s" % e}), 500
