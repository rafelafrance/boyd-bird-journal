"""Grid row."""

from skimage import util


class Rows:
    """Grid row is a pair of horizontal lines."""

    def __init__(self, grid):
        """Get rows from the grid's horizontal lines."""
        self.grid = grid
        self.image = grid.image
        self.rows = list([zip(grid.horiz.lines[:-1], grid.horiz.lines[1:])])

    @property
    def header(self):
        """Get the header row."""
        return self.rows[0]

    def exterior(self):
        """Get the exterior image of all the rows."""
        point1, point2 = self.rows[0][0]
        top = min(point1[0], point2[0])

        point1, point2 = self.rows[-1][1]
        bottom = self.image.shape[0] - max(point1[0], point2[0])

        outside = util.crop(self.image, ((top, bottom), (0, 0)))
        return outside
