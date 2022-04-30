
from cmath import pi
from lib2to3.pygram import python_grammar_no_print_statement
import math
from enum import Enum, auto
from multiprocessing.sharedctypes import Value
from typing import List, Dict
from string import Template
from pathlib import Path
import frontmatter
from xml.dom import minidom


with open('svg_templates/text.svg', 'r') as cfile:
    text_t = Template(cfile.read())

with open('svg_templates/number.svg', 'r') as cfile:
    number_t = Template(cfile.read())

with open('svg_templates/polygon.svg', 'r') as cfile:
    polygon_t = Template(cfile.read())


with open('svg_templates/icon.svg', 'r') as cfile:
    icon_t = Template(cfile.read())


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


def points_to_polygon_coord(points: List[Point]):
    return ' '.join(
        ["{},{}".format(point.x, point.y) for point in points])

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
                self.hexes.append(
                    Hexagon(self, col, row, hexes.get((col, row), None)))
                col += 1
            row += 1
        self.width: int = math.ceil((col_max-col_min+1)*self.radius*1.5)
        self.height: int = math.ceil((row_max-row_min+1)*self.radius2*2)
        self.iconsDict = self.__computeIcons()

    def __computeIcons(self):
        result = dict()
        for hex in self.hexes:
            icon = hex.icon
            if not icon:
                continue

            icon_path = Path(
                'svg_templates/icons/building').joinpath(icon+".svg")
            if not icon_path.is_file():
                continue

            # extract inner svg
            with open(icon_path, 'r') as cfile:
                try:
                    doc = minidom.parseString(cfile.read())
                    svgDom = doc.getElementsByTagName("svg")[0]
                    viewBox = svgDom.getAttribute('viewBox')
                    max_box = max([float(n) for n in viewBox.split(' ')])
                    scale = self.radius2/max_box
                    svgDom.setAttribute("id", icon)
                    svgDom.setAttribute("class", "icon "+icon)
                    result[icon] = Icon(self, icon, scale, svgDom.toxml())
                except:
                    print("Warning: icon format not supported")
                    continue

        return result

    def icons(self) -> str:
        return ''.join([icon.svgDef for icon in self.iconsDict.values()])

    def __iter__(self):
        ''' Returns the Iterator object '''
        return self.hexes.__iter__()


class Icon:
    def __init__(self, grid: HexagonGrid, id: str, scale: float, svgDef: str) -> None:
        self.grid = grid
        self.id = id
        self.scale = scale
        self.svgDef = svgDef
        pass

    def draw(self, tx: float, ty: float) -> str:
        return icon_t.substitute(id=self.id, tx=tx-self.grid.radius, ty=ty-self.grid.radius2, scale=self.scale)


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
        self.pathPoints = self.__createPathPoints()
        self.icon = None
        if self.content:
            self.icon = self.content[1].get(
                'icon', None)

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

    def __createPathPoints(self) -> Dict[Cardinal, Point]:
        radius = self.grid.radius*0.6
        radius2 = self.grid.radius2*0.6
        mmratio = self.grid.mmratio
        dx = radius2*math.cos(pi/6)
        coords = {
            Cardinal.N: Point(self.x, self.y-radius2),
            Cardinal.NO: Point(self.x-dx, self.y-radius2/2),
            Cardinal.NE: Point(self.x+dx, self.y-radius2/2),
            Cardinal.S: Point(self.x, self.y+radius2),
            Cardinal.SO: Point(self.x-dx, self.y+radius2/2),
            Cardinal.SE: Point(self.x+dx, self.y+radius2/2),
            Cardinal.C: Point(self.x, self.y),
        }
        return {key: Point(coords[key].x*mmratio, coords[key].y*mmratio) for key in coords.keys()}

    def drawGrid(self):
        """Generate svg code for a hexagon, containing the grid and the numbers

        Returns:
        string: svg code for a single hexagon
        """
        # Required variables
        radius = self.grid.radius
        mmratio = self.grid.mmratio
        left = (self.x-radius/2)*mmratio
        top = (self.y-radius/2)*mmratio

        # Number
        number_svg = number_t.substitute(
            left=left, top=top, row=self.row, col=self.col)

        # Grid
        grid_svg = polygon_t.substitute(
            points=points_to_polygon_coord(self.outerPoints),
            cssClass="grid"
        )

        return number_svg + grid_svg

    def drawContent(self):
        """Generate svg code for a hexagon with terrain and all description features

        Returns:
        string: svg code for a single hexagon
        """

        # Read metadata
        terrainCSS = ''
        mixedTerrains = []
        alt = None
        if self.content:
            terrain = self.content[1].get(
                'terrain', {}).get('type', 'unknown')
            terrainCSS = terrain.lower()
            mixedTerrains = self.content[1].get(
                'terrain', {}).get('mixed', [])
            alt = self.content[1].get('alt', None)

        # base terrain
        base_terrain = polygon_t.substitute(
            points=points_to_polygon_coord(self.outerPoints),
            cssClass=terrainCSS
        )

        # mixed terrain
        mixed_terrain = ''
        for terrain in mixedTerrains:
            typeCSS = terrain.get('type', 'unknown')
            polygons: List[List[Point]] = self.computePartsPolygons(
                terrain.get('sides', []))

            for polygon in polygons:
                pointStr = points_to_polygon_coord(polygon)
                mixed_terrain += polygon_t.substitute(
                    points=pointStr,
                    cssClass=typeCSS
                )

        # Text or icon
        pointO = self.pin(Cardinal.O)
        pointE = self.pin(Cardinal.E)
        cx = (pointE.x+pointO.x)/2
        cy = pointE.y
        text = ''
        if self.icon:
            text = self.grid.iconsDict[self.icon].draw(cx, cy)
        elif alt:
            text = text_t.substitute(
                cx=cx, cy=cy, text=alt)

        return base_terrain + mixed_terrain + text

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
        card(Cardinal): Position of the point

        Returns:
        Point: the expected point
        """
        if card.pid() is None:
            return None

        return self.innerPoints[card.pid()]

    def pout(self, card: Cardinal) -> Point:
        """Access to an innerPoint through cardinal

        Args:
        card(Cardinal): Position of the point

        Returns:
        Point: the expected point
        """
        if card.pid() is None:
            return None

        return self.outerPoints[card.pid()]
