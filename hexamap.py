
#!/usr/bin/env python3

import argparse
import glob
import sys
import os
import re
import math
from string import Template

import frontmatter

from classes.hexagon import Hexagon, HexagonGrid


with open('svg_templates/canvas.svg', 'r') as cfile:
    canvas_t = Template(cfile.read())


def fill_canvas(hexes, col_min, col_max, row_min, row_max):
    """Main function. Create a canvas of given boundaries and fill it with numbered hexes.

    Args:
       hexes (dict): key: tuple (col,row), values: tuple (filename, frontmatter content)
       col_min (integer): minimal Column ID
       col_max (integer): maximal Column ID
       row_min (integer): minimal Row ID
       row_max (integer): maximal Row ID

    Returns:
       string: svg of the entire canvas, ready for writing to a file.
    """
    # Wider radius of the hexagon
    radius: float = 20

    # Ratio to convert user unit to mm.
    mmratio = 3

    grid = HexagonGrid(hexes, col_min, col_max, row_min,
                       row_max, radius=radius, mmratio=mmratio)
    svgHexes = ''
    svgGrid = ''
    strokewidth = radius/10
    for hex in grid:
        svgHexes += hex.drawContent()
        svgGrid += hex.drawGrid()
    canvas = canvas_t.substitute(
        content=svgHexes + svgGrid, width=str(grid.width)+"mm", height=str(grid.height)+"mm", stroke=strokewidth,
        fontsize=str((radius/10)*mmratio) + "mm")
    return canvas


def parseHexFile(filename):
    """Check an Hexfile, and if it's valide, return a tuple with useful information

    Args:
       filename (filepath): the relative or absolute path of the file to pase

    Returns:
       (boolean, int, int, dict): First return indicates if it's a valid file, second and third the x and y position in grid, and the last a bunch of values extracted from the file
    """
    error = False, 0, 0, dict()
    # The file must exists
    if not os.path.isfile(filename):
        return error
    # The filename should follow the pattern XXYY-<some_name>.md
    basename = os.path.basename(filename)
    m = re.match('^(\d{2})(\d{2})-.*\.md$', basename)
    if m is None:
        return error

    col = int(m.group(2))
    row = int(m.group(1))

    with open(filename) as f:
        return True, col, row, frontmatter.load(f)


def generateFromFiles(hexes):
    # find map boundary
    col_min, col_max = None, None
    row_min, row_max = None, None
    for col, row in hexes.keys():
        if col_min is None or col_min > col:
            col_min = col
        if row_min is None or row_min > row:
            row_min = row
        if col_max is None or col_max < col:
            col_max = col
        if row_max is None or row_max < row:
            row_max = row

    with open('output/hexgrid-cm'+str(col_min)+'cM'+str(col_max)+'rm'+str(row_min)+'rM'+str(row_max)+'.svg', 'w') as ofile:
        # Generating canevas with empty hexes around boundaries
        ofile.write(fill_canvas(hexes, col_min-1,
                    col_max+1, row_min-1, row_max+1))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("src_path", metavar="path", type=str, nargs='*',
                        help="Path to files to be merged; enclose in quotes, accepts * as wildcard for directories or filenames")

    args = parser.parse_args()

    hexfiles = dict()

    for arg in args.src_path:
        files = glob.glob(arg)

        if not files:
            print('File does not exist: ' + arg, file=sys.stderr)
        for file in files:
            isHexFile, col, row, contents = parseHexFile(file)
            if isHexFile:
                hexfiles[col, row] = file, contents

    generateFromFiles(hexfiles)
