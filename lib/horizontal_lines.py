"""Contains logic that is unique to the horizontal grid lines."""

from lib.grid_lines import GridLines


class Horizontal(GridLines):
    """Contains logic that is unique to the horizontal grid lines."""

    def __init__(self, image):
        """Build horizontal grid lines."""
        super().__init__(image)
        self.size = image.shape[1]
        self.thetas = self.near_horiz
        self.threshold = self.size * 0.4

    def find_grid_lines(self):
        """Find horizontal grid lines and add extra lines."""
        super().find_line_end_points()

        line = ([0, 0], [self.image.shape[1], 0])
        if not self.too_close(line, self.lines[0]):
            self.add_line(line[0], line[1])

        line = ([0, self.image.shape[0]],
                [self.image.shape[1], self.image.shape[0]])
        if not self.too_close(line, self.lines[-1]):
            self.add_line(line[0], line[1])

    def insert_line(self, from_this_line, distance=-50):
        """
        Add a horizontal line to the grid.

        We use this for finding labels.
        """
        point1 = [0, from_this_line[0][1] + distance]
        point2 = [self.size, from_this_line[1][1] + distance]
        self.add_line(point1, point2)

    @staticmethod
    def sort_key(key):
        """Horizontal lines are sorted by their distance on the y-axis."""
        return key[0][1]
