"""The main grid class."""

# pylint: disable=too-many-instance-attributes

from skimage import io
from skimage import util
from lib.util import Offset
from lib.horizontal_lines import Horizontal
from lib.vertical_lines import Vertical
from lib.cell import Cell


class Grid:
    """
    Container for other classes.

    Contains horizontal and vertical grid lines as well as the grid cells.
    """

    def __init__(self, *, file_name=None, grid=None, crop=None):
        """Make a new gird from either an image file or another grid."""
        if file_name:
            self.image = io.imread(file_name)
            self.offset = Offset(0, 0)
        elif grid:
            self.image = grid.image
            self.offset = grid.offset
            if crop:
                self.image = util.crop(
                    self.image,
                    ((crop.top, crop.bottom), (crop.left, crop.right)))
                self.offset = Offset(x=self.offset.x + crop.left,
                                     y=self.offset.y + crop.top)

        self.edges = util.invert(self.image)

        self.horiz = Horizontal(self.edges)
        self.vert = Vertical(self.edges)

        self.rows = None

        self.cells = []
        self.row_labels = []
        self.col_labels = []

    @property
    def header_row(self):
        """Return the row with the column headers."""
        return self.cells[0]

    @property
    def width(self):
        """Make it easy to get the image width."""
        return self.horiz.size

    @property
    def height(self):
        """Make it easy to get the image height."""
        return self.vert.size

    def find_grid_lines(self):
        """Find horizontal and vertical grid lines."""
        self.horiz.find_grid_lines()
        self.vert.find_grid_lines()

    def get_cells(self):
        """Build the grid cells from the grid lines."""
        self.cells = []
        for row, (top, bottom) in enumerate(zip(self.horiz.lines[:-1],
                                                self.horiz.lines[1:])):
            self.cells.append([])
            for (left, right) in zip(self.vert.lines[:-1],
                                     self.vert.lines[1:]):
                self.cells[row].append(Cell(self, top, bottom, left, right))

    def get_row_labels(self):
        """Get row labels for the cells."""
        self.row_labels = [row[0].is_label() for row in self.cells]

        # Remove isolated labels
        for i in range(1, len(self.row_labels) - 2):
            if self.row_labels[i - 1] == self.row_labels[i + 1]:
                self.row_labels[i] = self.row_labels[i - 1]

    def get_col_labels(self):
        """Get column labels for the cells."""
        labels = [cell.is_label() for cell in self.header_row]

        # Remove isolated labels
        for i in range(1, len(labels) - 2):
            if labels[i - 1] == labels[i + 1]:
                labels[i] = labels[i - 1]

        # The first column is not a header if there are no values in it
        first_label = [i for i, val in enumerate(labels) if val][0]
        labels[first_label] = sum([len(row[first_label].has_line(
            Cell.forward_slashes)) for row in self.cells[1:]]) > 0

        # Limit number of days to no more than 31
        labels = [v and sum(labels[:i]) < 31 for i, v in enumerate(labels)]

        # Fill in the column labels
        first_label = [i for i, val in enumerate(labels) if val][0]
        last_label = [i for i, val in enumerate(labels) if val][-1]
        for i in range(first_label, last_label):
            labels[i] = True

        self.col_labels = labels
