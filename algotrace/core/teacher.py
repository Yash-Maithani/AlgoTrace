"""The teacher payload attached to one visualization step.

One implementation for every family: sorting, searching, A* and, through
StepLog in algorithms/graph/steps.py, graphs. The contract these dicts
satisfy is written down in `static/js/lessons/README.md`.

Nothing here touches an algorithm's control flow. A sort or a search builds
one of these alongside each draw call it already made, so the counts, the
number of steps and their order are unaffected.
"""


def step(action, indices, values, line, variables, beginner, why):
    """Describe the step an algorithm is about to draw.

    action    what happened, from the family's vocabulary
    indices   the real positions involved, always ints
    values    the values at those positions right now, same order
    line      id of the code line being executed, or None
    variables the live variables at this moment
    beginner  one sentence naming the real values
    why       one sentence on what the algorithm is trying to do
    """
    return {
        'action': action,
        'indices': list(indices),
        'values': list(values),
        'line': line,
        'vars': dict(variables),
        'explain': {'beginner': beginner, 'why': why},
    }
