
import math
from enum import Enum, auto
from multiprocessing.sharedctypes import Value
from typing import List
from string import Template
import frontmatter


with open('svg_templates/hexagon.svg', 'r') as cfile:
    hexagon_t = Template(cfile.read())

with open('svg_templates/number.svg', 'r') as cfile:
    number_t = Template(cfile.read())

with open('svg_templates/polygon.svg', 'r') as cfile:
    polygon_t = Template(cfile.read())


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


class Cardinal(Enum):
    # the second element of tuple allow to get the id of a point in inner and outerpoint
    N = (auto(), None)
    NO = (auto(), 2)
    O = (auto(), 3)
    SO = (auto(), 4)
    S = (auto(), None)
    SE = (auto(), 5)
    E = (auto(), 0)
    NE = (auto(), 1)
    C = (auto(), None)

    def pid(self):
        return self.value[1]

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
        self.innerPoints = self.__createInnerPoints()

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

    def __createInnerPoints(self) -> List[Point]:
        radius = self.grid.radius*0.6
        radius2 = self.grid.radius2*0.6
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
        terrainCSS = ''
        if self.content:
            terrain = self.content[1].get(
                'terrain', {}).get('type', 'unknown')
            terrainCSS = terrainCSS + " " + Terrain[terrain.upper()].css()

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
        ) + self.drawMixedTerrainSVG()

    def drawNumberSVG(self):
        """Generate svg code for the number to be displayed in a hex.
        Returns:
        string: svg code for a number coordinate
        """
        radius = self.grid.radius
        mmratio = self.grid.mmratio
        left = (self.x-radius/2)*mmratio
        top = (self.y-radius/2)*mmratio
        fontsize = str((radius/10)*mmratio) + "mm"
        return number_t.substitute(left=left, top=top, row=self.row, col=self.col, fontsize=fontsize)

    def drawMixedTerrainSVG(self):
        """Generate svg code for a hexagon.

        Returns:
        string: svg code for a single hexagon
        """
        mixedTerrains = []
        if self.content:
            mixedTerrains = self.content[1].get(
                'terrain', {}).get('mixed', [])

        result = ''

        for terrain in mixedTerrains:
            typeCSS = terrain.get('type', 'unknown')
            polygons: List[List[Point]] = self.computePartsPolygons(
                terrain.get('sides', []))

            for polygon in polygons:
                pointStr = ' '.join(
                    ["{},{}".format(point.x, point.y) for point in polygon])
                result += polygon_t.substitute(
                    points=pointStr,
                    cssClass=typeCSS
                )
        return result

    def computePartsPolygons(self, sides: List[str]):
        # TODO optimiser en regroupant les formes afin de faire moins de polygones
        result: List[List[Point]] = []

        for side in sides:
            c = None
            try:
                c = Cardinal[side.upper()]
            except KeyError:
                pass  # do nothing
            if c is Cardinal.N:
                result.append([
                    self.pin(Cardinal.NE), self.pin(
                        Cardinal.NO), self.pout(Cardinal.NO), self.pout(Cardinal.NE),
                ])
            if c is Cardinal.NE:
                result.append([
                    self.pin(Cardinal.E), self.pin(
                        Cardinal.NE), self.pout(Cardinal.NE), self.pout(Cardinal.E),
                ])
            if c is Cardinal.SE:
                result.append([
                    self.pin(Cardinal.E), self.pin(
                        Cardinal.SE), self.pout(Cardinal.SE), self.pout(Cardinal.E),
                ])
            if c is Cardinal.S:
                result.append([
                    self.pin(Cardinal.SE), self.pin(
                        Cardinal.SO), self.pout(Cardinal.SO), self.pout(Cardinal.SE),
                ])
            if c is Cardinal.SO:
                result.append([
                    self.pin(Cardinal.O), self.pin(
                        Cardinal.SO), self.pout(Cardinal.SO), self.pout(Cardinal.O),
                ])
            if c is Cardinal.NO:
                result.append([
                    self.pin(Cardinal.O), self.pin(
                        Cardinal.NO), self.pout(Cardinal.NO), self.pout(Cardinal.O),
                ])
            if c is Cardinal.C:
                result.append(self.innerPoints)

        return result

    def pin(self, card: Cardinal) -> Point:
        """Access to an innerPoint through cardinal

        Args:
        card (Cardinal): Position of the point

        Returns:
        Point: the expected point
        """
        if card.pid() is None:
            return None

        return self.innerPoints[card.pid()]

    def pout(self, card: Cardinal) -> Point:
        """Access to an innerPoint through cardinal

        Args:
        card (Cardinal): Position of the point

        Returns:
        Point: the expected point
        """
        if card.pid() is None:
            return None

        return self.outerPoints[card.pid()]
