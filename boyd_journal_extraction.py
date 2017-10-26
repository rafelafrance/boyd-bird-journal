"""Extract images of Boyd's Bird Journal into computer readable form."""

# pylint: disable=no-member

import os
import csv
import glob
from collections import namedtuple
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import patches
from skimage import io
from skimage import util
from skimage.transform import hough_line, hough_line_peaks
from skimage.transform import probabilistic_hough_line


# Using tuples as lightweight objects
Crop = namedtuple('Crop', 'top bottom left right')
Offset = namedtuple('Offset', 'x y')
Point = namedtuple('Point', 'x y')


def intersection(line1, line2):
    """Given two lines find their intersection."""
    (x_1, y_1), (x_2, y_2) = line1
    (x_3, y_3), (x_4, y_4) = line2
    denom = (x_1 - x_2) * (y_3 - y_4) - (y_1 - y_2) * (x_3 - x_4)
    num1 = x_1 * y_2 - y_1 * x_2
    num2 = x_3 * y_4 - y_3 * x_4
    point_x = num1 * (x_3 - x_4) - (x_1 - x_2) * num2
    point_x /= denom
    point_y = num1 * (y_3 - y_4) - (y_1 - y_2) * num2
    point_y /= denom
    return Point(int(point_x), int(point_y))


class Grid:
    """
    Container for other classes.

    The horizontal and vertical grid lines as well as the grid cells.
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

        self.cells = []
        self.row_labels = []
        self.col_labels = []

    @property
    def header_row(self):
        """Return the row with the column headers."""
        return self.cells[0]

    @property
    def shape(self):
        """Make it easy to get the image shape."""
        return self.edges.shape

    @property
    def width(self):
        """Make it easy to get the image width."""
        return self.horiz.size

    @property
    def height(self):
        """Make it easy to get the image height."""
        return self.vert.size

    def get_cells(self):
        """Build the grid cells from the grid lines."""
        self.cells = []
        for row, (top, bottom) in enumerate(zip(self.horiz.lines[:-1],
                                                self.horiz.lines[1:])):
            self.cells.append([])
            for (left, right) in zip(
                    self.vert.lines[:-1], self.vert.lines[1:]):
                self.cells[row].append(Cell(self, top, bottom, left, right))

    def get_row_labels(self):
        """Get row labels for the cells."""
        self.row_labels = [row[1].is_row_label() for row in self.cells]
        for i in range(1, len(self.row_labels) - 2):
            if self.row_labels[i - 1] and self.row_labels[i + 1]:
                self.row_labels[i] = True

    def get_col_labels(self):
        """Get column labels for the cells."""
        self.col_labels = []
        for cell in self.header_row:
            self.col_labels.append(False)
            days = sum(self.col_labels)
            proper_size = cell.width > 8 and cell.height > 8
            if proper_size and days:
                self.col_labels[-1] = days < 31 and cell.is_col_label()
            elif proper_size:
                # proper_shape = cell.width / cell.height < 2
                # self.col_labels[-1] = proper_shape and cell.is_col_label()
                self.col_labels[-1] = cell.is_col_label()
        for i in range(1, len(self.col_labels) - 2):
            if self.col_labels[i - 1] and self.col_labels[i + 1]:
                self.col_labels[i] = True


class GridLines:
    """The base object for both hoizontal and vertical grid lines."""

    near_horiz = np.deg2rad(np.linspace(-2.0, 2.0, num=41))
    near_vert = np.deg2rad(np.linspace(88.0, 92.0, num=41))

    # I'm not sure why this is required?!
    near_horiz, near_vert = near_vert, near_horiz

    def __init__(self, image):
        """Initialize data common to all grid lines."""
        self.image = image
        self.thetas = None
        self.angles = []
        self.dists = []
        self.lines = []
        self.threshold = 500
        self.min_distance = 40

    def find_lines(self):
        """Find the grid lines using the Hough Transform."""
        h_matrix, h_angles, h_dist = hough_line(self.image, self.thetas)

        _, self.angles, self.dists = hough_line_peaks(
            h_matrix,
            h_angles,
            h_dist,
            threshold=self.threshold,
            min_distance=self.min_distance)

    def polar2endpoints(self, theta, rho):
        """
        Convert a line given in polar coordinates to line segment end points.

        The Hough Transform returns the lines in polar form but matplotlib uses
        line segment end points.
        """
        if np.abs(theta) > np.pi / 4:
            x_0 = 0
            x_1 = self.image.shape[1]
            y_0 = int(np.round(rho / np.sin(theta)))
            y_1 = int(np.round((rho - x_1 * np.cos(theta)) / np.sin(theta)))
        else:
            y_0 = 0
            y_1 = self.image.shape[0]
            x_0 = int(np.round(rho / np.cos(theta)))
            x_1 = int(np.round((rho - y_1 * np.sin(theta)) / np.cos(theta)))

        return [x_0, y_0], [x_1, y_1]

    def add_line(self, point1, point2):
        """
        Add a line to the list of lines.

        Because of the way we use line pair for finding grid cells we need to
        keep the list of lines sorted.
        """
        self.lines.append((point1, point2))
        self.sort_lines()

    def sort_lines(self):
        """Sort lines by its distance from the origin."""
        self.lines = sorted(self.lines, key=self.sort_key)

    @staticmethod
    def sort_key(key):
        """Horizontal lines are sorted by their distance on the y-axis."""
        return key[0][1]

    def find_line_end_points(self):
        """Find, convert, and sort the grid lines."""
        self.find_lines()

        self.lines = [self.polar2endpoints(theta, rho)
                      for (theta, rho) in zip(self.angles, self.dists)]

        self.sort_lines()


class Horizontal(GridLines):
    """Contains logic that is unique to the horizontal grid lines."""

    def __init__(self, image):
        """Build horizontal grid lines."""
        super().__init__(image)
        self.size = image.shape[1]
        self.thetas = self.near_horiz
        self.threshold = self.size * 0.4

    def find_grid_lines(self, add_top_edge=False, add_bottom_edge=False):
        """Find horizontal grid lines and add extra lines."""
        super().find_line_end_points()

        if add_top_edge:
            self.add_line([0, 0], [self.image.shape[1], 0])

        if add_bottom_edge:
            self.add_line([0, self.image.shape[0]],
                          [self.image.shape[1], self.image.shape[0]])

    @staticmethod
    def sort_key(key):
        """Horizontal lines are sorted by their distance on the y-axis."""
        return key[0][1]


class Vertical(GridLines):
    """Contains logic that is unique to the vertical grid lines."""

    def __init__(self, image):
        """Build vertical grid lines."""
        super().__init__(image)
        self.size = image.shape[0]
        self.thetas = self.near_vert
        self.threshold = self.size * 0.4

    def find_grid_lines(self, add_left_edge=False, add_right_edge=False):
        """Find vertical grid lines and add extra lines."""
        super().find_line_end_points()

        if add_left_edge:
            self.add_line([0, 0], [0, self.image.shape[0]])

        if add_right_edge:
            self.add_line([self.image.shape[1], 0],
                          [self.image.shape[1], self.image.shape[0]])

    @staticmethod
    def sort_key(key):
        """Verical lines are sorted by their distance on the x-axis."""
        return key[0][0]


class Cell:
    """Data and functions for dealing with cell contents."""

    row_label_threshold = 20
    col_label_threshold = 20
    crop = ((4, 4), (4, 4))
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
        top = max(self.top_left.y, self.top_right.y)
        bottom = self.image.shape[0] - min(
            self.bottom_left.y, self.bottom_right.y)
        left = max(self.top_left.x, self.bottom_left.x)
        right = self.image.shape[1] - min(
            self.top_right.x, self.bottom_right.x)

        inside = util.crop(self.image, ((top, bottom), (left, right)))

        if crop:
            inside = util.crop(inside, crop)

        return inside

    def is_row_label(self):
        """Determine if the cell is a row label."""
        return np.mean(self.interior(self.crop)) > self.row_label_threshold

    def is_col_label(self):
        """Determine if the cell is a column label."""
        inside = self.interior(crop=self.crop)
        lines = self.has_line()
        return bool(len(lines)) or np.mean(inside) > self.col_label_threshold

    def has_line(self, angles=None):
        """Determine if the cell has a line at any of the given angles."""
        return probabilistic_hough_line(
            self.interior(crop=self.crop),
            line_length=15,
            line_gap=2,
            theta=angles)

    def get_patch(self):
        """Get the cell patch for output."""
        width = self.top_right.x - self.top_left.x
        height = self.bottom_left.y - self.top_left.y
        offset_x = self.offset.x
        offset_y = self.offset.y
        return (offset_x, offset_y), width, height


def split_image(image):
    """Split the image into left and right halves."""
    crop_right_side = int(image.width / 2) + 200
    crop_left_side = image.width - crop_right_side

    left_side = Grid(grid=image, crop=Crop(
        top=0, bottom=0, left=0, right=crop_right_side))
    right_side = Grid(grid=image, crop=Crop(
        top=0, bottom=0, left=crop_left_side, right=0))

    return left_side, right_side


def add_vert_line(image, *, after_this_line=None, width=200):
    """
    Add a vertical line to the grid.

    We use this for finding row labels.
    """
    left = after_this_line[0][0] + width
    point1 = [left, 0]
    point2 = [left, image.height]
    image.vert.add_line(point1, point2)


def get_month_graph_areas(left_side, right_side):
    """Chop the right side image into images for each month."""
    months = []
    for curr_row, row in enumerate(left_side.row_labels[1:], 1):

        prev_row = curr_row - 1
        if not left_side.row_labels[prev_row] and row:
            top = left_side.cells[prev_row][1].top_right.y

        if left_side.row_labels[prev_row] and not row:
            bottom = left_side.cells[curr_row][1].bottom_right.y
            months.append(Grid(
                grid=right_side,
                crop=Crop(top=top,
                          bottom=right_side.height - bottom,
                          left=0,
                          right=0)))

    return months


def build_month_graphs(months):
    """Find the grid for each month."""
    for month in months:
        month.horiz.find_grid_lines(add_bottom_edge=True)
        month.vert.find_grid_lines(add_left_edge=True, add_right_edge=True)

        month.get_cells()
        month.get_col_labels()


def init_csv_file(csv_path):
    """Initialize the CSV file."""
    with open(csv_path, 'a', newline='') as csv_file:
        writer = csv.writer(csv_file)
        header = ['file_name', 'chart_in_file',
                  'year', 'month', 'row_no', 'bird_species']
        header += [i for i in range(1, 32)]
        writer.writerow(header)


def output_results(in_file, csv_path, full_image, left_side, months):
    """Output the image and CSV data."""
    file_name = os.path.basename(in_file)

    base_name, _ = os.path.splitext(file_name)
    img_path = os.path.join('output', base_name + '_out.png')

    with open(csv_path, 'a', newline='') as csv_file:
        writer = csv.writer(csv_file)

        fig, axis = plt.subplots(figsize=(10, 15.45), frameon=False)
        axis.imshow(full_image.image, cmap=plt.cm.gray)
        axis.axis('off')

        # Color in row labels
        for curr_row, row in enumerate(left_side.cells):
            if left_side.row_labels[curr_row]:
                top_left, width, height = row[0].get_patch()
                axis.add_patch(patches.Rectangle(
                    top_left, width, height, alpha=0.5, facecolor='#feb209'))

        for month_idx, month in enumerate(months):

            # Color in column labels
            for col, cell in enumerate(month.header_row):
                if month.col_labels[col]:
                    top_left, width, height = cell.get_patch()
                    axis.add_patch(patches.Rectangle(
                        top_left,
                        width,
                        height,
                        alpha=0.5,
                        facecolor='#feb209'))

            # Color in grid cells with slashes
            for curr_row, cell_row in enumerate(month.cells[1:-1]):
                row = [base_name, month_idx + 1, '', '', curr_row + 1, '']
                csv_cells = ['' for i in range(31)]
                day = -1
                for col, cell in enumerate(cell_row):
                    if month.col_labels[col]:
                        day += 1
                        if cell.has_line(Cell.forward_slashes):
                            csv_cells[day] = 1
                            top_left, width, height = cell.get_patch()
                            axis.add_patch(patches.Rectangle(
                                top_left, width,
                                height,
                                alpha=0.5,
                                facecolor='#39ad48'))
                row += csv_cells
                writer.writerow(row)

    plt.savefig(img_path, dpi=300, bbox_inches='tight')
    plt.close(fig)


def process_image(file_name, csv_path):
    """Process one image."""
    print(f'Processing: {file_name}')
    full_image = Grid(file_name=file_name)

    left_side, right_side = split_image(full_image)

    left_side.horiz.find_grid_lines(add_top_edge=True,
                                    add_bottom_edge=True)
    left_side.vert.find_grid_lines(add_left_edge=True,
                                   add_right_edge=True)

    add_vert_line(left_side, after_this_line=left_side.vert.lines[1])

    left_side.get_cells()
    left_side.get_row_labels()

    months = get_month_graph_areas(left_side, right_side)
    build_month_graphs(months)

    output_results(file_name, csv_path, full_image, left_side, months)


if __name__ == '__main__':
    CSV_PATH = 'output/boyd_bird_journal.csv'
    init_csv_file(CSV_PATH)
    for image_file_name in sorted(glob.glob('images/*.png')):
        process_image(image_file_name, CSV_PATH)
