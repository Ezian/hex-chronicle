
#!/usr/bin/env python3

import argparse, glob, sys, os,re, math
from posixpath import basename
from string import Template


with open('svg_templates/canvas.svg', 'r') as cfile:
   canvas_t = Template( cfile.read() )

with open('svg_templates/hexagon.svg', 'r') as cfile:
   hexagon_t = Template( cfile.read() )

with open('svg_templates/number.svg', 'r') as cfile:
   number_t = Template( cfile.read() )
   
# hex radius in mm (widest)
radius = 20

# Ratio to convert user unit to mm.
mmratio = 2.83463333

def calc_radius2(radius):
   """Calculate the shortest (inner) radius for the given (outer) hex radius in mm

   Args:
      radius (integer): hex radius in mm (widest)

   Returns:
      integer: Inner radius for the given outer radius.
   """
   return math.sqrt( radius ** 2 - (radius/2) ** 2 )

def make_number(radius,point):
   """Generate svg code for the number to be displayed in a hex.

   Args:
      radius (integer): hex radius in mm (widest)
      point (list): tuple for a single point with these values:
      0: x value
      1: y value
      2: column
      3: row

   Returns:
      string: svg code for a number coordinate
   """
   left = (point[0]-radius/2)*mmratio
   top  = (point[1]-radius/2)*mmratio
   fontsize = str((radius/10)*mmratio) + "mm"
   return number_t.substitute(left=left,top=top,row=point[2],col=point[3],fontsize=fontsize)

def make_hex(radius=1,origin=[0,0]):
   """Generate svg code for a hexagon.

   Args:
      radius (int, optional): hex radius in mm (widest)
      origin (list, optional): [description]. Defaults to [0,0].

   Returns:
      string: svg code for a single hexagon
   """
   points = list()

   radius2 = calc_radius2( radius )
   points.append(
      [
         origin[0]+radius,
         origin[1]
      ]
   )
   points.append(
      [
         origin[0]+radius/2,
         origin[1]-radius2
      ]
   )
   points.append(
      [
         origin[0]-radius/2,
         origin[1]-radius2
      ]
   )
   points.append(
      [
         origin[0]-radius,
         origin[1]
      ]
   )
   points.append(
      [
         origin[0]-radius/2,
         origin[1]+radius2
      ]
   )
   points.append(
      [
         origin[0]+radius/2,
         origin[1]+radius2
      ]
   )

   output = hexagon_t.substitute(
      ax = mmratio*points[0][0],
      ay = mmratio*points[0][1],
      bx = mmratio*points[1][0],
      by = mmratio*points[1][1],
      cx = mmratio*points[2][0],
      cy = mmratio*points[2][1],
      dx = mmratio*points[3][0],
      dy = mmratio*points[3][1],
      ex = mmratio*points[4][0],
      ey = mmratio*points[4][1],
      fx = mmratio*points[5][0],
      fy = mmratio*points[5][1]
   )

   return output

def make_grid(col_min, col_max, row_min, row_max):
   """Create a grid of center points for hexes, based on a boundaries

   Args:
   col_min (integer): minimal Column ID
   col_max (integer): maximal Column ID
   row_min (integer): minimal Row ID
   row_max (integer): maximal Row ID

   Returns:
      list: List of tuples per point. Each tuple contains:
         0: x value
         1: y value
         2: column
         3: row
      integer: width of the grid
      height: height of the grid
   """
   points = list()
   radius2 = calc_radius2( radius )
   row = row_min
   while row <= row_max:
      col = col_min
      while col <= col_max:
         y=radius2*2*row + col%2*radius2
         x=radius*1.5*col
         points.append([x,y,col,row])
         col += 1
      row+=1   
   width=math.ceil((col_max-col_min+1)*radius*1.5)
   height=math.ceil((row_max-row_min+1)*radius2*2)
   return points, width, height


def fill_canvas(col_min, col_max, row_min, row_max):
   """Main function. Create a canvas of given boundaries and fill it with numbered hexes.

   Args:
      col_min (integer): minimal Column ID
      col_max (integer): maximal Column ID
      row_min (integer): minimal Row ID
      row_max (integer): maximal Row ID

   Returns:
      string: svg of the entire canvas, ready for writing to a file.
   """
   grid, width, height = make_grid(col_min, col_max, row_min, row_max)
   hexes = ''
   numbers = ''
   strokewidth=radius/10
   for point in grid:
      hexes += make_hex(radius,point)
      numbers += make_number(radius,point)
   canvas = canvas_t.substitute(content=hexes+numbers,width=str(width)+"mm",height=str(height)+"mm",stroke=strokewidth)
   return canvas
   return ""
   


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
   
   col = int(m.group(1))
   row = int(m.group(2))
   
   return True, col, row, dict()

def generateFromFiles(hexes):
   # find map boundary
   col_min, col_max = None, None
   row_min, row_max = None, None
   for col,row in hexes.keys():
      if not col_min or col_min > col:
         col_min = col
      if not row_min or row_min > row:
         row_min = row
      if not col_max or col_max < col:
         col_max = col
      if not row_max or row_max < row:
         row_max = row
         
   with open( 'output/hexgrid-cm'+str(col_min)+'cM'+str(col_max)+'rm'+str(row_min)+'rM'+str(row_max)+'.svg', 'w' ) as ofile:
      # Generating canevas with empty hexes around boundaries
      ofile.write( fill_canvas(col_min-1,col_max+1, row_min-1, row_max+1) )

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
         isHexFile, x, y, contents = parseHexFile(file)
         if isHexFile:
            hexfiles[x,y] = file, contents
   
   generateFromFiles(hexfiles)
         