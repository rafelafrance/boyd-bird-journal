"""Utility functions."""

# pylint: disable=invalid-name

from collections import namedtuple
import numpy as np


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


def extend_line(line, length):
    """Create a new line given a point and an angle."""
    p1, p2 = line  # Get line end points

    line_len = np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    x = p2[0] + (p2[0] - p1[0]) / line_len * length
    y = p2[1] + (p2[1] - p1[1]) / line_len * length
    return (p1, [int(x), int(y)])


def too_close(line1, line2, threshold=40):
    """
    Find lines that are too close to each other.

    We are looking at the two end points of the line segments and seeing if
    each of them are too close.
    """
    p1, p2 = line1  # Get line end points
    p3, p4 = line2  # Get line end points

    dist1 = np.sqrt((p1[0] - p3[0])**2 + (p1[1] - p3[1])**2)
    dist2 = np.sqrt((p2[0] - p4[0])**2 + (p2[1] - p4[1])**2)

    return min(dist1, dist2) < threshold
