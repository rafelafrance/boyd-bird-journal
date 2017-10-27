"""Extract images of Boyd's Bird Journal into computer readable form."""

# pylint: disable=no-member, invalid-name

import os
import csv
import glob
import matplotlib.pyplot as plt
from matplotlib import patches
from lib.util import Crop
from lib.grid import Grid
from lib.cell import Cell


def split_image(full_image):
    """Split the image into left and right halves."""
    crop_right_side = int(full_image.width / 2) + 200
    crop_left_side = full_image.width - crop_right_side

    right_side = Grid(grid=full_image, crop=Crop(
        top=0, bottom=0, left=crop_left_side, right=0))

    return right_side


def get_month_graph_areas(full_image, right_side):
    """Chop the right side image into images for each month."""
    months = []

    for curr_row, row in enumerate(full_image.row_labels[1:-1], 1):

        prev_row = curr_row - 1
        if not full_image.row_labels[prev_row] and row:
            top = min(full_image.cells[prev_row][0].top_right.y,
                      full_image.cells)

        if full_image.row_labels[prev_row] and not row:
            bottom = full_image.cells[curr_row + 1][1].bottom_right.y
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
        month.horiz.find_grid_lines()
        month.vert.find_grid_lines()
        month.vert.insert_line(month.vert.lines[1], distance=-60)

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

        _, ax = plt.subplots(figsize=(10, 15.45), frameon=False)
        ax.imshow(full_image.image, cmap=plt.cm.gray)
        ax.axis('off')

        # Color in row labels
        for curr_row, row in enumerate(left_side.cells):
            if left_side.row_labels[curr_row]:
                top_left, width, height = row[1].get_patch()
                ax.add_patch(patches.Rectangle(
                    top_left, width, height, alpha=0.5, facecolor='#feb209'))

        for month_idx, month in enumerate(months):

            # Color in column labels
            for col, cell in enumerate(month.header_row):
                if month.col_labels[col]:
                    top_left, width, height = cell.get_patch()
                    ax.add_patch(patches.Rectangle(
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
                            ax.add_patch(patches.Rectangle(
                                top_left, width,
                                height,
                                alpha=0.5,
                                facecolor='#39ad48'))
                row += csv_cells
                writer.writerow(row)

    plt.savefig(img_path, dpi=300, bbox_inches='tight')
    return plt


def process_image(file_name, csv_path):
    """Process one image."""
    print(f'Processing: {file_name}')
    full_image = Grid(file_name=file_name)

    right_side = split_image(full_image)

    full_image.horiz.find_grid_lines()
    full_image.vert.find_grid_lines()

    full_image.vert.insert_line(from_this_line=full_image.vert.lines[1],
                                distance=-50)

    full_image.get_cells()
    full_image.get_row_labels()

    months = get_month_graph_areas(full_image, right_side)
    build_month_graphs(months)

    plt = output_results(file_name, csv_path, full_image, months)
    plt.close()


if __name__ == '__main__':
    CSV_PATH = 'output/boyd_bird_journal.csv'
    init_csv_file(CSV_PATH)
    for image_file_name in sorted(glob.glob('images/*.png')):
        process_image(image_file_name, CSV_PATH)
