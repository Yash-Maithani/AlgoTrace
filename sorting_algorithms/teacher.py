"""Teacher payload for one visualization step.

The contract these dicts satisfy is written down in
`static/js/lessons/README.md`. Nothing here touches an algorithm's control
flow: a sort builds one of these alongside each draw call it already made, so
the comparison and swap counts, the number of steps and their order are all
unchanged.
"""


def step(action, indices, values, line, variables, beginner, why):
    """Describe the step a sort is about to draw.

    action    one of compare, swap, overwrite, select, place, done
    indices   the real array positions involved, always ints
    values    the values at those positions right now, same order
    line      id of the code line being executed, or None
    variables the live loop variables at this moment
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
