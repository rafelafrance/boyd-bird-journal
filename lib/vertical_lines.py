"""Contains logic that is unique to the vertical grid lines."""

from lib.grid_lines import GridLines


class Vertical(GridLines):
    """Contains logic that is unique to the vertical grid lines."""

    def __init__(self, image):
        """Build vertical grid lines."""
        super().__init__(image)
        self.size = image.shape[0]
        self.thetas = self.near_vert
        self.threshold = self.size * 0.4

    def find_grid_lines(self):
        """Find vertical grid lines and add extra lines."""
        super().find_line_end_points()

        line = ([0, 0], [0, self.image.shape[0]])
        if not self.too_close(line, self.lines[0]):
            self.add_line(line[0], line[1])

        line = ([self.image.shape[1], 0],
                [self.image.shape[1], self.image.shape[0]])
        if not self.too_close(line, self.lines[-1]):
            self.add_line(line[0], line[1])

    def insert_line(self, from_this_line, distance=-50):
        """
        Add a vertical line to the grid.

        We use this for finding labels.
        """
        point1 = [from_this_line[0][0] + distance, 0]
        point2 = [from_this_line[1][0] + distance, self.size]
        self.add_line(point1, point2)

    @staticmethod
    def sort_key(key):
        """Verical lines are sorted by their distance on the x-axis."""
        return key[0][0]
