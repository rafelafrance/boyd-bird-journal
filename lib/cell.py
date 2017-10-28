"""Data and functions for dealing with cell contents."""

# pylint: disable=no-member, too-many-instance-attributes, too-many-arguments


import numpy as np
from skimage import util
from skimage.transform import probabilistic_hough_line
from lib.util import Crop, Offset, intersection


class Cell:
    """Data and functions for dealing with cell contents."""

    row_label_threshold = 20
    col_label_threshold = 15
    crop = Crop(top=4, bottom=4, left=4, right=4)
    forward_slashes = np.deg2rad(np.linspace(65.0, 25.0, num=161))

    def __init__(self, grid, top=None, bottom=None, left=None, right=None):
        """
        Build a cell from the 4 surrounding grid lines.

        We will also get the for corners of the cell by finding the
        intersection of the grid lines.
        """
        self.image = grid.edges
        self.top_left = intersection(top, left)
        self.bottom_left = intersection(bottom, left)
        self.top_right = intersection(top, right)
        self.bottom_right = intersection(bottom, right)
        self.width = self.top_right.x - self.top_left.x
        self.height = self.bottom_left.y - self.top_left.y
        self.offset = Offset(x=grid.offset.x + self.top_left.x,
                             y=grid.offset.y + self.top_left.y)

    def interior(self, crop=None):
        """
        Get the interior image of the cell.

        Sometimes we will want to crop the interior to try and remove the
        surrounding grid lines. That is, we want the cell contents, not the
        grid lines.
        """
        top = max(0, self.top_left.y, self.top_right.y)
        bottom = max(0, self.image.shape[0] - min(
            self.bottom_left.y, self.bottom_right.y))
        left = max(0, self.top_left.x, self.bottom_left.x)
        right = max(0, self.image.shape[1] - min(
            self.top_right.x, self.bottom_right.x))

        inside = util.crop(self.image, ((top, bottom), (left, right)))

        if crop and inside.shape[1] > (crop.right + crop.left) \
                and inside.shape[0] > (crop.bottom + crop.top):
            inside = util.crop(
                inside,
                ((crop.top, crop.bottom), (crop.left, crop.right)))

        return inside

    def is_label(self, crop=None):
        """Determine if the cell is a column label."""
        if not crop:
            crop = self.crop
        inside = self.interior(crop=crop)
        lines = self.has_line(line_length=15)
        if not min(inside.shape):
            return False
        return bool(len(lines)) or np.mean(inside) > self.col_label_threshold

    def has_line(self, angles=None, line_length=15):
        """Determine if the cell has a line at any of the given angles."""
        return probabilistic_hough_line(
            self.interior(crop=self.crop),
            line_length=line_length,
            line_gap=2,
            theta=angles)

    def get_patch(self):
        """Get the cell patch for output."""
        width = self.top_right.x - self.top_left.x
        height = self.bottom_left.y - self.top_left.y
        offset_x = self.offset.x
        offset_y = self.offset.y
        return (offset_x, offset_y), width, height
