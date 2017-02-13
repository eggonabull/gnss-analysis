import math


def diff(a, b):
    return [b[0] - a[0], b[1] - a[1]]


def scale(vec, scalar):
    return [vec[0] * scalar, vec[1] * scalar]


def abs(vec):
    return math.sqrt(vec[0] * vec[0] + vec[1] * vec[1])


def unit(vec):
    if vec == [0.0, 0.0]:
        return vec
    return scale(vec, 1 / abs(vec))