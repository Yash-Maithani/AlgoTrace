"""Graph step recording.

The step arrays the /run_* endpoints emit are the ones graph_base.html has
always drawn, and they do not change. StepLog keeps a parallel meta list in
lockstep with them, one teacher payload per step, as described in section 4
of static/js/lessons/README.md.

Graph actions extend the sorting vocabulary rather than overloading it:
  visit      a node is settled and will not be looked at again
  enqueue    a node joins the queue, stack or frontier
  consider   an edge or a route through a node is being examined
  relax      a distance improved
  reject     an edge or route was looked at and not taken
  include    an edge joins the tree or the answer
  milestone  a marker that changes no state, such as a pass finishing
  done       the final frame
"""

GRAPH_ACTIONS = {
    "visit", "enqueue", "consider", "relax", "reject", "include",
    "milestone", "done",
}


class StepLog:
    """A step array and its parallel meta list, always appended to together."""

    def __init__(self):
        self.steps = []
        self.meta = []

    def add(self, step, action, beginner, why, indices=(), values=(),
            line=None, variables=None):
        self.steps.append(step)
        self.meta.append({
            "action": action,
            "indices": list(indices),
            "values": list(values),
            "line": line,
            "vars": dict(variables or {}),
            "explain": {"beginner": beginner, "why": why},
        })
        return step

    def payload(self, **extra):
        """The response body: the steps, their meta, and any summary fields."""
        body = {"steps": self.steps, "meta": self.meta}
        body.update(extra)
        return body


# JSON has no literal for infinity: json.dumps(float("inf")) emits a bare Infinity
# token, which JSON.parse rejects. The graph templates already compare rendered
# distances against the string "∞", so unreachable values travel as that label.
INF_LABEL = "∞"


def wire(value):
    # Translate an internal float("inf") into the wire form the templates expect.
    return INF_LABEL if value == float("inf") else value
