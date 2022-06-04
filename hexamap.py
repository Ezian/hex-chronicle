"""Hex-chronicle

Generate a nice svg map from a bunch of markdown file with medadata.

"""
# !/usr/bin/env python3

import argparse
import glob
import sys
from pathlib import Path
from string import Template
from typing import List

import frontmatter

from classes.grid_renderer import Renderer
from classes.hexagon import GridBox, HexagonGrid
from classes.hexagon_renderer import HexagonRenderer
from classes.tilemetadata import TileMetadata

with open('svg_templates/canvas.svg', 'r', encoding="utf-8") as cfile:
    canvas_t = Template(cfile.read())


def generate_from_metadatas(hexes: List[TileMetadata], output_path: Path, css: str):
    """Generate the grid from files

    Args:
        hexes (dict[col, row]Hexagon): set of hexagons identified by a tuple (col, row)
        output_path (_type_): The file to write
        css (_type_): A custom css to insert in the final file
    """
    # find map boundary
    col_min, col_max = None, None
    row_min, row_max = None, None
    for col, row in [(h.col, h.row) for h in hexes]:
        if col_min is None or col_min > col:
            col_min = col
        if row_min is None or row_min > row:
            row_min = row
        if col_max is None or col_max < col:
            col_max = col
        if row_max is None or row_max < row:
            row_max = row

    output_file = 'hexgrid-cm' + \
                  str(col_min) + 'cM' + str(col_max) + 'rm' + \
                  str(row_min) + 'rM' + str(row_max) + '.svg'

    if output_path and Path(output_path).suffix == '.svg':
        output_file = output_path

    elif output_path:
        output_file = Path(output_path).joinpath(output_file)

    with open(output_file, 'w', encoding="utf-8") as ofile:
        # Generating canevas with empty hexes around boundaries
        canvas = Renderer(hexes, 100.0).draw_svg()
        ofile.write(canvas)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("src_path", metavar="path", type=str, nargs='*',
                        help="Path to files to be merged; enclose in quotes, accepts * as " +
                             "wildcard for directories or filenames")
    parser.add_argument("--output", type=str, default=None,
                        help="File or directory. If the output end with a .svg extension," +
                             " it will write the file. Elsewhere, it will put a svg file with " +
                             "a generated name at the location")
    parser.add_argument("--css", type=str, default=None,
                        help="Css file to override default css values")

    args = parser.parse_args()

    metadatas = []

    for arg in args.src_path:
        files = glob.glob(arg)

        if not files:
            print('File does not exist: ' + arg, file=sys.stderr)
        for file in files:
            try:
                metadatas.append(TileMetadata.from_file(file))
            except Exception as e:
                print(e)

    CSS = ''

    if args.css and Path(args.css).is_file():
        with open(args.css, 'r', encoding="utf-8") as cfile:
            CSS = cfile.read()

    generate_from_metadatas(metadatas, args.output, CSS)
