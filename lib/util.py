"""Utility functions."""

# pylint: disable=invalid-name

from collections import namedtuple


# Using tuples as lightweight objects
Crop = namedtuple('Crop', 'top bottom left right')
Offset = namedtuple('Offset', 'x y')
Point = namedtuple('Point', 'x y')


def intersection(line1, line2):
    """Given two lines find their intersection."""
    (x1, y1), (x2, y2) = line1
    (x3, y3), (x4, y4) = line2
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    num1 = x1 * y2 - y1 * x2
    num2 = x3 * y4 - y3 * x4
    px = num1 * (x3 - x4) - (x1 - x2) * num2
    px /= denom
    py = num1 * (y3 - y4) - (y1 - y2) * num2
    py /= denom
    return Point(int(px), int(py))
