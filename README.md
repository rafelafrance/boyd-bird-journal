# This repository has been archived.

# Extract images of Boyd's Bird Journal into computer readable form

## Summary

(See images below)

The journals are PDFs containing a series of scanned images of observations of birds. The observations are scanned handwritten notes on graph paper. There are bird species labels running down the left side of the page and date information across the top. The charts are organized by month with days of the month being column headings. There are between up to three months of information for each image.

Each cell has a mark indicating the presence or absence of a bird species on a given day. So there is, potentially, one mark per bird species per day. The mark on the page is typically a forward slash "/", but it can also be an "x" or an asterisk. We are treating all types of marks the same, a cell either has a mark, or it doesn't.

Some things to note here:
- The graphs are not clean and contain notes and stray marks.
- The scans do not always have nice strong lines to pick out.
- The scans of the graphs are crooked and contain distortions, so the lines are slightly bent, typically near the edges.
- Some lines are incomplete or missing. In the image below, May 1986 has more grid cells than June 1986, and the line to the left of May 1st is incomplete.

We want to take the first image and produce two items from it.
1. An image indicating what we have extracted. Shown below.
    - Row and column labels are given a golden color.
    - Cells win a slash have a green color.
1. We are also producing a CSV file that can be used for analysis. Shown below the images.

### Input image

![Input image](assets/Boyd_M_Bird_journal_section1-024_in.png "Input image")

### Output image

This image is primarily useful for quality control checks.

![Output image](assets/Boyd_M_Bird_journal_section1-024_out.png "Output image")

### Output CSV file

file_name | chart_in_file | year | month | row_no | bird_species | 1 | 2 | 3 | 4 | 5 | 6 | ... | 30 | 31
--------- | --------------| ---- | ----- | ------ | ------------ | - | - | - | - | - | - | --- | -- | --
Boyd_M_Bird_journal_section1-024 | 1 | | | 1 | | 1 | 1 |   |   |   |   | ... |    |
Boyd_M_Bird_journal_section1-024 | 1 | | | 2 | | 1 | 1 | 1 | 1 | 1 | 1 | ... | 1  | 1
Boyd_M_Bird_journal_section1-024 | 1 | | | 3 | | 1 | 1 | 1 | 1 | 1 | 1 | ... |    |
Boyd_M_Bird_journal_section1-024 | 1 | | | 4 | | 1 | 1 |   | 1 |   | 1 | ... |    |
Boyd_M_Bird_journal_section1-024 | 1 | | | 5 | | 1 | 1 | 1 | 1 | 1 | 1 | ... | 1  | 1

## Heuristics outline

As described in the summary the images are distorted and inconsistent. The general idea is to chop the image into workable pieces and parse that. Once we have parsed the image pieces we will reassemble the image for output. See below.

1. Chop the image into left and right halves. The left side will contain row labels, and the right side contains the data grids with the slashes.
1. Find the grid lines and grid cells on the left side. (red and magenta lines) We use the *Hough Transform* to look for both vertical and horizontal grid lines. We do one pass for the horizontal lines and one for the vertical lines. Cells are the area between pairs of adjacent horizontal grid lines and pairs of vertical grid lines.
1. Examine the 1st cell of every row and look for writing in it. Because this particular cell is wide, we will only look at the last ~80 pixels of that cell. We will use both a mean pixel brightness and the *Probabilistic Hough Transform* for this.
1. We then group the rows with contiguous row labels into grids. In the image below there are two grids. We are assuming that each grid represents a month of data, days 1 up to 31.
1. Find the grid lines and cells for each grid on the right side of the image. (red and yellow lines) This uses the *Hough Transform* mentioned above.
1. Look for column headers for each of the grids on the right side. We will use both a mean pixel brightness and the *Probabilistic Hough Transform* for this.
1. Scan the grids for slashes. We only look at rows that have a row label and columns that have a column header. The scan uses the *Probabilistic Hough Transform* tuned to look for forward slashes.
1. Output the results to the output image file and to the CSV file.

The whole messy process for figuring this out is shown in the [experiments notebook](experiments_for_boyd_journal_extraction.ipynb).

![Output image](assets/algorithm.png "How the algorithm slices the image")
