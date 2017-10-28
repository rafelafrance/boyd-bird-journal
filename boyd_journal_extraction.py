"""Extract images of Boyd's Bird Journal into computer readable form."""

# pylint: disable=no-member, invalid-name

import os
import csv
import glob
import matplotlib.pyplot as plt
from matplotlib import patches
from lib.util import intersection, extend_line, Crop
from lib.grid import Grid
from lib.cell import Cell


def get_left_side(grid):
    """Get the left side of the grid."""
    right = int(grid.width / 2)
    left_side = Grid(
        grid=grid, crop=Crop(left=0, right=right, top=0, bottom=0))
    left_side.horiz.find_grid_lines()
    left_side.vert.find_grid_lines()
    left_side.vert.insert_line(
        from_this_line=left_side.vert.lines[0], distance=-80)
    left_side.get_cells()
    left_side.get_row_labels()
    return left_side


def crop_rows(grid, top_line, bottom_line):
    """Get the exterior image of all the rows."""
    top_line = extend_line(top_line, grid.width)
    bottom_line = extend_line(bottom_line, grid.width)

    left = int(grid.width / 2) - 200
    left_line = ([left, 0], [left, grid.height])

    right_line = ([grid.width, 0], [grid.width, grid.height])

    top_left = intersection(top_line, left_line)
    top_right = intersection(top_line, right_line)
    bottom_left = intersection(bottom_line, left_line)
    bottom_right = intersection(bottom_line, right_line)

    top = min(top_left.y, top_right.y) - 20
    bottom = grid.height - max(bottom_left.y, bottom_right.y) + 40
    left = max(top_left.x, bottom_left.x)

    return Grid(grid=grid,
                crop=Crop(top=top, bottom=bottom, left=left, right=0))


def get_month_graph_areas(grid, left_side):
    """Chop the right side image into images for each month."""
    months = []

    top_line = left_side.horiz.lines[0]
    start_idx = 0
    for label_idx, label in enumerate(left_side.row_labels[1:], 1):

        prev_idx = label_idx - 1
        prev_label = left_side.row_labels[prev_idx]

        if label and not prev_label:
            start_idx = label_idx
            top_line = left_side.horiz.lines[label_idx - 1]
        elif not label and prev_label:
            row_count = label_idx - start_idx
            if row_count > 5:
                bottom_line = left_side.horiz.lines[label_idx + 1]
                months.append(crop_rows(grid, top_line, bottom_line))
            start_idx = 0

    return months


def build_month_graphs(months):
    """Find the grid for each month."""
    for month in months:
        month.horiz.find_grid_lines()
        month.vert.find_grid_lines()

        # Insert left edge of the graph
        month.vert.insert_line(month.vert.lines[0], distance=-60)

        # Insert right edge of the graph
        right_edge = ([month.width, 0], [month.width, month.height])
        month.vert.add_line(right_edge[0], right_edge[1])

        month.get_cells()
        month.get_col_labels()


def color_row_labels(left_side, ax):
    """Color the row labels in the given image."""
    for row_idx, row in enumerate(left_side.cells):
        if left_side.row_labels[row_idx]:
            top_left, width, height = row[0].get_patch()
            ax.add_patch(patches.Rectangle(
                top_left, width, height, alpha=0.5, facecolor='#feb209'))


def color_col_labels(month, ax):
    """Color the column labels for the given month image."""
    for col, cell in enumerate(month.header_row):
        if month.col_labels[col]:
            top_left, width, height = cell.get_patch()
            ax.add_patch(patches.Rectangle(
                top_left,
                width,
                height,
                alpha=0.5,
                facecolor='#feb209'))


def color_grid_cells(month, month_idx, ax, base_name, writer):
    """
    Color the grid cells with slashes for the given month image.

    Also write row data to the CSV file.
    """
    for row_idx, cell_row in enumerate(month.cells[1:]):
        csv_row = [base_name, month_idx + 1, '', '', row_idx + 1, '']
        csv_cells = ['' for i in range(31)]
        day = -1
        for col, cell in enumerate(cell_row):
            if month.col_labels[col]:
                day += 1
                if cell.has_line(Cell.forward_slashes):
                    csv_cells[day] = 1
                    top_left, width, height = cell.get_patch()
                    ax.add_patch(patches.Rectangle(
                        top_left, width,
                        height,
                        alpha=0.5,
                        facecolor='#39ad48'))
        csv_row += csv_cells
        writer.writerow(csv_row)


def output_results(in_file, csv_path, grid, months, left_side):
    """Output the image and CSV data."""
    file_name = os.path.basename(in_file)

    base_name, _ = os.path.splitext(file_name)
    img_path = os.path.join('output', base_name + '_out.png')

    with open(csv_path, 'a', newline='') as csv_file:
        writer = csv.writer(csv_file)

        fig, ax = plt.subplots(figsize=(10, 15.45), frameon=False)
        ax.imshow(grid.image, cmap=plt.cm.gray)
        ax.axis('off')

        color_row_labels(left_side, ax)

        for month_idx, month in enumerate(months):
            color_col_labels(month, ax)
            color_grid_cells(month, month_idx, ax, base_name, writer)

    fig.savefig(img_path, dpi=300, bbox_inches='tight')


def process_image(file_name, csv_path):
    """Process one image."""
    print(f'Processing: {file_name}')
    grid = Grid(file_name=file_name)

    left_side = get_left_side(grid)

    months = get_month_graph_areas(grid, left_side)
    build_month_graphs(months)

    output_results(file_name, csv_path, grid, months, left_side)
    plt.close()


def init_csv_file(csv_path):
    """Initialize the CSV file."""
    with open(csv_path, 'a', newline='') as csv_file:
        writer = csv.writer(csv_file)
        header = ['file_name', 'chart_in_file',
                  'year', 'month', 'row_no', 'bird_species']
        header += [i for i in range(1, 32)]
        writer.writerow(header)


if __name__ == '__main__':
    CSV_PATH = 'output/boyd_bird_journal.csv'
    init_csv_file(CSV_PATH)
    for image_file_name in sorted(glob.glob('images/*.png')):
        process_image(image_file_name, CSV_PATH)
