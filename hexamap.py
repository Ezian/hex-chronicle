"""Hex-chronicle

Generate a nice svg map from a bunch of markdown file with medadata.

"""
# !/usr/bin/env python3

import argparse
import glob
import logging
import sys
from pathlib import Path
from typing import List

from classes.grid_renderer import Renderer
from classes.tilemetadata import TileMetadata


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
        canvas = Renderer(add_border_tiles(hexes), css, 100.0).draw_svg()
        ofile.write(canvas)


def add_border_tiles(tiles: List[TileMetadata]) -> List[TileMetadata]:
    """Add empty tiles around the existing one, to have a nicer render

    Args:
        tiles (List[TileMetadata]): Liste of tiles from files

    Returns:
        List[TileMetadata]: The input tiles, plus tiles that are with them.
    """

    if len(tiles) == 0:
        print("Warn: No tiles found")
        return [TileMetadata(0, 0)]

    tmptiles = [[
        TileMetadata(tile.col-1, tile.row-1),
        TileMetadata(tile.col-1, tile.row),
        TileMetadata(tile.col+1, tile.row-1),
        TileMetadata(tile.col+1, tile.row),
    ] for tile in tiles if tile.col % 2 == 0
    ] + [[
        TileMetadata(tile.col-1, tile.row+1),
        TileMetadata(tile.col-1, tile.row),
        TileMetadata(tile.col+1, tile.row+1),
        TileMetadata(tile.col+1, tile.row),
    ] for tile in tiles if tile.col % 2 == 1] + [[
        TileMetadata(tile.col, tile.row-1),
        TileMetadata(tile.col, tile.row+1),
    ] for tile in tiles if tile.col] + [tiles]

    # Contains all tiles from params, and tiles that have a border with them,
    # with no content (they will be drawed with some default contents)

    filtered_tiles = {(tile.col, tile.row): tile for l in tmptiles for tile in l}

    return filtered_tiles.values()


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
            # pylint: disable=broad-except
            try:
                metadatas.append(TileMetadata.from_file(file))
            except Exception as e:
                logging.warning(e)

    CSS = ''

    if args.css and Path(args.css).is_file():
        with open(args.css, 'r', encoding="utf-8") as cfile:
            CSS = cfile.read()

    generate_from_metadatas(metadatas, args.output, CSS)
