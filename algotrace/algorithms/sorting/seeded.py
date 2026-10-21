"""A small seeded random number generator, the same one static/js/presets.js
uses (mulberry32). Quick sort's random pivot draws from it, so a run is fully
described by its seed, and the C, C++ and Java translations of a later phase
can reproduce it with nothing but 32 bit integer arithmetic.
"""

MASK = 0xFFFFFFFF


def _imul(a, b):
    return (a * b) & MASK


def mulberry32(seed):
    """Return a function giving floats in [0, 1), seeded by `seed`."""
    state = [seed & MASK]

    def next_float():
        state[0] = (state[0] + 0x6D2B79F5) & MASK
        t = state[0]
        t = _imul(t ^ (t >> 15), t | 1)
        t ^= (t + _imul(t ^ (t >> 7), t | 61)) & MASK
        return ((t ^ (t >> 14)) & MASK) / 4294967296.0

    return next_float
