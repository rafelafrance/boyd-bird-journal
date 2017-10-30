"""The main grid class."""

# pylint: disable=too-many-instance-attributes

from skimage import io
from skimage import util
from lib.util import Offset, Crop
from lib.horizontal_lines import Horizontal
from lib.vertical_lines import Vertical
from lib.cell import Cell


class Grid:
    """
    Container for other classes.

    Contains horizontal and vertical grid lines as well as the grid cells.
    """

    split_limit = 32

    def __init__(self, *, file_name=None, grid=None, crop=None, split=False):
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

        self.top = None
        self.bottom = None
        self.split = split
        self.mid_point = 999

    @property
    def header_row(self):
        """Return the row with the column headers."""
        return self.top.header_row if self.top else self.cells[0]

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

        if self.split and len(self.horiz.lines) > self.split_limit:
            self.mid_point = int(len(self.horiz.lines) / 2)
            point1, _ = self.horiz.lines[self.mid_point]
            split = point1[1]

            self.top = Grid(
                grid=self,
                crop=Crop(top=0,
                          bottom=self.height - split - 20,
                          left=0,
                          right=0))
            self.top.find_grid_lines()

            self.bottom = Grid(
                grid=self,
                crop=Crop(top=split - 20,
                          bottom=0,
                          left=0,
                          right=0))
            self.bottom.find_grid_lines()
            if len(self.bottom.vert.lines) != len(self.top.vert.lines):
                self.bottom = None

    def get_cells(self):
        """Build the grid cells from the grid lines."""
        top_cells = []
        bottom_cells = []
        for row_idx, (top, bottom) in enumerate(zip(self.horiz.lines[:-1],
                                                    self.horiz.lines[1:])):
            if row_idx < self.mid_point:
                cells = top_cells
            elif row_idx >= self.mid_point:
                cells = bottom_cells

            cells.append([])
            for (left, right) in zip(
                    self.vert.lines[:-1], self.vert.lines[1:]):
                cells[-1].append(Cell(self, top, bottom, left, right))

        if self.top:
            self.top.get_cells()
            top_cells = self.top.cells
        if self.bottom:
            self.bottom.get_cells()
            bottom_cells = self.bottom.cells

        self.cells = top_cells + bottom_cells

    def vert_add_line(self, point1, point2):
        """Add a vertical line to the grid."""
        self.vert.add_line(point1, point2)
        if self.top:
            self.top.vert.add_line(point1, (point2[0], self.top.vert.size))
        if self.bottom:
            self.bottom.vert.add_line(
                point1, (point2[0], self.bottom.vert.size))

    def vert_insert_line(self, line_idx, distance=-50):
        """Insert a vertical grid line relative to another line."""
        self.vert.insert_line(self.vert.lines[line_idx], distance=distance)
        if self.top:
            self.top.vert.insert_line(
                self.top.vert.lines[line_idx], distance=distance)
        if self.bottom:
            self.bottom.vert.insert_line(
                self.bottom.vert.lines[line_idx], distance=distance)

    def get_row_labels(self):
        """Get row labels for the cells."""
        self.row_labels = [row[0].is_label() for row in self.cells]

        # Remove isolated labels
        for i in range(2, len(self.row_labels) - 3):
            if (self.row_labels[i - 2] or self.row_labels[i - 1]) and (
                    self.row_labels[i + 1] or self.row_labels[i + 2]):
                self.row_labels[i] = True

    def get_col_labels(self):
        """Get column labels for the cells."""
        labels = [cell.is_label() for cell in self.header_row]

        first_label = [i for i, val in enumerate(labels) if val][0]

        # The first column is not a header if there are no values in it
        labels[first_label] = sum([len(row[first_label].has_line(
            Cell.forward_slashes)) for row in self.cells[1:]]) > 0

        # Set the first 31 columns to be a label
        first_label = [i for i, val in enumerate(labels) if val][0]
        self.col_labels = [(i >= first_label and i < first_label + 31)
                           for i, _ in enumerate(labels)]
