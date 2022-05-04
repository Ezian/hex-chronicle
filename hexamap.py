#!/usr/bin/env python3

import argparse
import glob
import os
import re
import sys
from collections import defaultdict
from decimal import *
from pathlib import Path
from string import Template
from typing import Callable, Iterable, List

import frontmatter

from classes.hexagon import HexagonGrid, points_to_polygon_coord, Segment, Hexagon, Point

with open('svg_templates/canvas.svg', 'r') as cfile:
    canvas_t = Template(cfile.read())


def fill_canvas(hexes, col_min, col_max, row_min, row_max, css):
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
    radius: Decimal = Decimal(100)

    grid = HexagonGrid(hexes, col_min, col_max, row_min,
                       row_max, radius=radius)
    svgHexes = ''
    svgGrid = ''
    strokewidth = radius/15
    fontsize = str(Decimal(2.5)*radius)+"%"
    for hex in grid:
        svgHexes += hex.drawContent()
        svgGrid += hex.drawGrid()
    
    declared_zones= set([ zone for h in grid for zone in h .zones])
    with open('svg_templates/polygon.svg', 'r') as cfile:
        polygon_t = Template(cfile.read())
    zones =  [ polygon_t.substitute(
        points=points_to_polygon_coord(polygon),
        cssClass="zone %s"%(z)) for z in declared_zones for polygon in makeCluster(grid,lambda h : z in h.zones)]
  
    canvas = canvas_t.substitute(icons=grid.icons(),
                                 content=svgHexes + svgGrid + "\r\n".join(zones), width=str(grid.width), height=str(grid.height), strokegrid=strokewidth, strokefont=strokewidth/Decimal(1.5), strokepath=strokewidth*Decimal(1.2),
                                 fontsize=fontsize, css=css)
    return canvas


def makeCluster(grid: Iterable[Hexagon], cluster_checker: Callable[[Hexagon],bool])-> List[List[Point]]:
    segments=defaultdict(int)
    for hex in grid:
        if cluster_checker(hex):
            for x in range(0,len(hex.outerPoints)):
                segment = Segment(hex.outerPoints[(x+1)%len(hex.outerPoints)],hex.outerPoints[x])
                segments[segment]+=1                    
    retainedSegments= [k for k , v in segments.items() if v ==1]
    polygons = []
    while len(retainedSegments):
        segment=retainedSegments.pop()
        chain = [segment.a, segment.b] 
        while True:
            newLink = __findConnectingSegment(chain[len(chain)-1],retainedSegments)
            retainedSegments.remove(newLink)
            if newLink.a==chain[len(chain)-1]:
                if newLink.b==chain[0]:
                    polygons.append(chain)
                    break
                else:
                    chain.append(newLink.b)
            else:

                if newLink.a==chain[0]:
                    polygons.append(chain)
                    break
                else:
                    chain.append(newLink.a)
                
    return polygons
            

def __findConnectingSegment(ending,candidates):
    for i in range(0, len(candidates)):
        if candidates[i].touches(ending):
            return candidates[i]
    raise AssertionError("Can't find a new link")

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
    m = re.match('^(-?\d{2})(-?\d{2})-.*\.md$', basename)
    if m is None:
        return error

    col = int(m.group(2))
    row = int(m.group(1))

    with open(filename) as f:
        return True, col, row, frontmatter.load(f)


def generateFromFiles(hexes, output_path, css):
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

    output_file = 'hexgrid-cm' + \
        str(col_min)+'cM'+str(col_max)+'rm' + \
        str(row_min)+'rM'+str(row_max)+'.svg'

    if output_path and Path(output_path).suffix == '.svg':
        output_file = output_path

    elif output_path:
        output_file = Path(output_path).joinpath(output_file)

    with open(output_file, 'w') as ofile:
        # Generating canevas with empty hexes around boundaries
        canvas = fill_canvas(hexes, col_min-1,
                             col_max+1, row_min-1, row_max+1, css)
        ofile.write(canvas)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("src_path", metavar="path", type=str, nargs='*',
                        help="Path to files to be merged; enclose in quotes, accepts * as wildcard for directories or filenames")
    parser.add_argument("--output", type=str, default=None,
                        help="File or directory. If the output end with a .svg extension, it will write the file. Elsewhere, it will put a svg file with a generated name at the location")
    parser.add_argument("--css", type=str, default=None,
                        help="Css file to override default css values")

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
    css = ''

    if args.css and Path(args.css).is_file():
        with open(args.css, 'r') as cfile:
            css = cfile.read()

    generateFromFiles(hexfiles, args.output, css)
