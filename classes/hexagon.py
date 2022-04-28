
import math
from enum import Enum, auto
from typing import List
from string import Template
import frontmatter


with open('svg_templates/hexagon.svg', 'r') as cfile:
    hexagon_t = Template(cfile.read())

with open('svg_templates/number.svg', 'r') as cfile:
    number_t = Template(cfile.read())


def calc_radius2(radius):
    """Calculate the shortest (inner) radius for the given (outer) hex radius in mm

        Args:
        radius (integer): hex radius in mm (widest)

        Returns:
        integer: Inner radius for the given outer radius.
        """
    return math.sqrt(radius ** 2 - (radius/2) ** 2)


class Point:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y


# Type of terrain
class Terrain(Enum):
    PLAINS = (auto(), 'plain')
    GRASSLAND = (auto(), 'grass')
    LIGHT_WOODS = (auto(), 'lwood')
    HEAVY_WOODS = (auto(), 'hwood')
    MOUNTAINS = (auto(), 'mountain')
    HILLS = (auto(), 'hill')
    MARSH = (auto(), 'marsh')
    DESERT = (auto(), 'desert')
    LAKE = (auto(), 'lake')
    SEA = (auto(), 'sea')
    UNKNOWN = (auto(), 'unknown')

    def css(self):
        return self.value[1]


class HexagonGrid:

    def __init__(self, hexes, col_min: int, col_max: int, row_min: int, row_max: int, radius: float = 20, mmratio: float = 3) -> None:
        self.radius: float = radius
        self.mmratio: float = mmratio
        self.radius2: float = calc_radius2(radius)
        self.row_min: int = row_min
        self.row_max: int = row_max
        self.col_min: int = col_min
        self.col_max: int = col_max
        self.hexes: list[Hexagon] = list()
        row = self.row_min
        while row <= self.row_max:
            col = self.col_min
            while col <= self.col_max:
                y = self.radius2*2*row + col % 2*self.radius2
                x = self.radius*1.5*col
                self.hexes.append(
                    Hexagon(self, col, row, hexes.get((col, row), None)))
                col += 1
            row += 1
        self.width: int = math.ceil((col_max-col_min+1)*self.radius*1.5)
        self.height: int = math.ceil((row_max-row_min+1)*self.radius2*2)

    def __iter__(self):
        ''' Returns the Iterator object '''
        return self.hexes.__iter__()


class Hexagon:

    def __init__(self, grid: HexagonGrid, column: int, row: int, content: frontmatter.Post = None) -> None:
        self.y: float = grid.radius2*2*row + column % 2*grid.radius2
        self.x: float = grid.radius*1.5*column
        self.col: int = column
        self.row: int = row
        self.content = content
        self.grid: HexagonGrid = grid
        self.outerPoints = self.__createOuterPoints()

    def __createOuterPoints(self) -> List[Point]:
        radius = self.grid.radius
        radius2 = self.grid.radius2
        mmratio = self.grid.mmratio
        return [Point(x*mmratio, y*mmratio) for (x, y) in [
            (self.x+radius, self.y),            # E
            (self.x+radius/2, self.y-radius2),  # NE
            (self.x-radius/2, self.y-radius2),  # NO
            (self.x-radius, self.y),            # O
            (self.x-radius/2, self.y+radius2),  # SO
            (self.x+radius/2, self.y+radius2),  # SE
        ]]

    def drawSVG(self):
        """Generate svg code for a hexagon.

        Returns:
        string: svg code for a single hexagon
        """
        terrainCSS = 'st0'
        if self.content:
            terrain = self.content[1].get(
                'terrain', {}).get('type', 'unknown')
            terrainCSS = Terrain[terrain.upper()].css()

        return hexagon_t.substitute(
            ax=self.outerPoints[0].x,
            ay=self.outerPoints[0].y,
            bx=self.outerPoints[1].x,
            by=self.outerPoints[1].y,
            cx=self.outerPoints[2].x,
            cy=self.outerPoints[2].y,
            dx=self.outerPoints[3].x,
            dy=self.outerPoints[3].y,
            ex=self.outerPoints[4].x,
            ey=self.outerPoints[4].y,
            fx=self.outerPoints[5].x,
            fy=self.outerPoints[5].y,
            cssClass=terrainCSS
        )

    def drawNumberSVG(self):
        """Generate svg code for the number to be displayed in a hex.

        Args:
        hex (Hexagon): Hexagon to create a svg number

        Returns:
        string: svg code for a number coordinate
        """
        radius = self.grid.radius
        mmratio = self.grid.mmratio
        left = (self.x-radius/2)*mmratio
        top = (self.y-radius/2)*mmratio
        fontsize = str((radius/10)*mmratio) + "mm"
        return number_t.substitute(left=left, top=top, row=self.row, col=self.col, fontsize=fontsize)
