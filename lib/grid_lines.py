"""The base object for both horizontal and vertical grid lines."""

# pylint: disable=no-member, invalid-name


import numpy as np
from skimage.transform import hough_line, hough_line_peaks


class GridLines:
    """The base object for both horizontal and vertical grid lines."""

    min_distance = 30

    near_horiz = np.deg2rad(np.linspace(-3.0, 3.0, num=61))
    near_vert = np.deg2rad(np.linspace(87.0, 93.0, num=61))

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
            x0 = 0
            x1 = self.image.shape[1]
            y0 = int(np.round(rho / np.sin(theta)))
            y1 = int(np.round((rho - x1 * np.cos(theta)) / np.sin(theta)))
        else:
            y0 = 0
            y1 = self.image.shape[0]
            x0 = int(np.round(rho / np.cos(theta)))
            x1 = int(np.round((rho - y1 * np.sin(theta)) / np.cos(theta)))

        return [x0, y0], [x1, y1]

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

    def find_grid_lines(self):
        """Find, convert, and sort the grid lines."""
        self.find_lines()

        self.lines = [self.polar2endpoints(theta, rho)
                      for (theta, rho) in zip(self.angles, self.dists)]

        self.sort_lines()

    @staticmethod
    def too_close(line1, line2, threshold=40):
        """Find lines that are too close to each other."""
        p1, p2 = line1  # Get line end points
        p3, p4 = line2  # Get line end points

        dist1 = np.sqrt((p1[0] - p3[0])**2 + (p1[1] - p3[1])**2)
        dist2 = np.sqrt((p2[0] - p4[0])**2 + (p2[1] - p4[1])**2)

        return min(dist1, dist2) < threshold
