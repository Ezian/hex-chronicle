#!python3.7
import math
from string import Template
import sys

with open('svg_templates/canvas.svg', 'r') as cfile:
    canvas_t = Template( cfile.read() )

with open('svg_templates/hexagon.svg', 'r') as cfile:
    hexagon_t = Template( cfile.read() )

with open('svg_templates/number.svg', 'r') as cfile:
    number_t = Template( cfile.read() )

# Ratio to convert user unit to mm.
mmratio = 2.83463333

def make_grid(width,height,radius):
    """Create a grid of center points for hexes, based on a canvas width

    Args:
        width (integer): canvas width in mm
        height (integer): canvas height in mm
        radius (integer): hex radius in mm (widest)

    Returns:
        list: List of tuples per point. Each tuple contains:
        0: x value
        1: y value
        2: column
        3: row
    """
    points = list()
    radius2 = calc_radius2( radius )
    #points.append([0,0])
    row = 0
    totalcols = math.ceil( width/ (radius*1.5) )
    totalrows = math.ceil( height/ (radius2*2) )
    while row <= totalrows:
        col = 0
        while col <= totalcols:
            y=radius2*2*row + col%2*radius2
            x=radius*1.5*col
            points.append([x,y,col,row])
            col += 1
        row+=1
    return points


def fill_canvas(width,height,radius):
    """Main function. Create a canvas of given width and height and fill it with numbered hexes of the given ratio.

    Args:
        width (integer): canvas width in mm
        height (integer): canvas height in mm
        radius (integer): hex radius in mm (widest)

    Returns:
        string: svg of the entire canvas, ready for writing to a file.
    """
    grid = make_grid(width,height,radius)
    hexes = ''
    numbers = ''
    strokewidth=radius/10
    for point in grid:
        hexes += make_hex(radius,point)
        numbers += make_number(radius,point)
    canvas = canvas_t.substitute(content=hexes+numbers,width=str(width)+"mm",height=str(height)+"mm",stroke=strokewidth)
    return canvas

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
    return number_t.substitute(left=left,top=top,row=point[2]+1,col=point[3]+1,fontsize=fontsize)

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

def make_svg(width,height,radius):
    """Create an svg file of the given dimensions, filled with hexes of the given radius in mm

    Args:
        width (integer): canvas width in mm
        height (integer): canvas height in mm
        radius (integer): hex radius in mm (widest)
    """
    print("Generating canvas of "+str(width)+ " by "+str(height) + "mm filled with hexagons of "+str(radius)+" mm radius")
    with open( 'output/hexgrid-w'+str(width)+'xh'+str(height)+'-'+str(radius)+'.svg', 'w' ) as ofile:
        ofile.write( fill_canvas(width,height,radius) )

def valid_args(args):
    """Check whether provided command line arguments make sense.

    Args:
        args (list): Command line arguments

    Returns:
        boolean: Whether the provided arguments are sensible.
    """
    width = int(args[1])
    height = int(args[2])
    radius = int(args[3])
    if not valid_value(width,1,10000):
        return False
    if not valid_value(height,1,10000):
        return False
    if not valid_value(radius,1,100):
        return False
    if not valid_value(radius,1,width):
        return False
    if not valid_value(radius,1,height):
        return False
    return True

def valid_value(val,min,max):
    """Check whether a particular numerical value is within certain bounds

    Args:
        val (any): the value to check (will be converted to int)
        min (integer): Minimum allowed value
        max (integer): Maximum allowed value

    Returns:
        boolean: Whether the provided value is within bounds.
    """
    try:
        val = int(val)
    except:
        return False
    if val < min:
        return False
    if val > max:
        return False
    return True

def ask_and_make():
    """Prompt the user for values and make the svg based on those.
    """
    width = False
    height = False
    radius = False
    while False == valid_value(width,1,10000):
        try:
            width = int( input("Canvas width (in mm): " ) )
        except:
            width = False
    while False == valid_value(height,1,10000):
        try:
            height = int( input("Canvas height (in mm): " ) )
        except:
            height = False
    while False == valid_value(radius,1,100) or False == valid_value(radius,1,width) or False == valid_value(radius,1,height):
        try:
            radius = int( input("Radius (in mm): " ) )
        except:
            radius = False
    make_svg(width,height,radius)


if len(sys.argv) > 1:
    if len(sys.argv) < 4:
        print("You have provided too few arguments.")
        print("Usage: python tiler.py [width] [height] [radius]")
        print("Or run without arguments to be prompted.")
        cont = input("Prompt for values (Y) or exit (any key)?" )
        if 'Y' == str(cont).upper():
            ask_and_make()
        else:
            exit()
    else:
        if valid_args(sys.argv):
            width = int(sys.argv[1])
            height = int(sys.argv[2])
            radius = int(sys.argv[3])
            make_svg(width,height,radius)
            exit()
        else:
            print("Arguments out of bounds")
            print("Width has to be positive and can be no higher than 10000")
            print("Height has to be positive and can be no higher than 10000")
            print("Radius can be no higher than 100 and no lower than 1")
            print("Radius can't be higher than width or height")
            cont = input("Prompt for values (Y) or exit (any key)?" )
            if 'Y' == str(cont).upper():
                ask_and_make()
            else:
                exit()

ask_and_make()
