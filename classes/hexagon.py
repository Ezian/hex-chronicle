import math
from decimal import *
from enum import Enum, auto
from pathlib import Path
from string import Template
from typing import List, Dict
from xml.dom import minidom

import frontmatter

with open('svg_templates/text.svg', 'r') as cfile:
    text_t = Template(cfile.read())

with open('svg_templates/number.svg', 'r') as cfile:
    number_t = Template(cfile.read())

with open('svg_templates/polygon.svg', 'r') as cfile:
    polygon_t = Template(cfile.read())

with open('svg_templates/icon.svg', 'r') as cfile:
    icon_t = Template(cfile.read())

with open('svg_templates/path.svg', 'r') as cfile:
    path_t = Template(cfile.read())


def calc_radius2(radius: Decimal):
    """Calculate the shortest (inner) radius for the given (outer) hex radius

        Args:
        radius (integer): hex radius (widest)

        Returns:
        integer: Inner radius for the given outer radius.
        """

    return (radius ** 2 - (radius / 2) ** 2).sqrt()


class Point:
    def __init__(self, x: Decimal, y: Decimal) -> None:
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Point({self.x}, {self.y})"

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash(self.x) + hash(self.y)


class Segment:
    def __init__(self, a: Point, b: Point) -> None:
        self.a = a
        self.b = b

    def __eq__(self, other):
        return (self.a == other.a and self.b == other.b) or (self.a == other.b and self.b == other.a)

    def __hash__(self):
        return hash(self.a) + hash(self.b)

    def touches(self, p: Point):
        return self.a == p or self.b == p

    def __repr__(self):
        return f"Segment({self.a} - {self.b})"


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

    def __init__(self, hexes, col_min: int, col_max: int, row_min: int, row_max: int, radius: Decimal = 20) -> None:
        self.radius: Decimal = radius
        self.radius2: Decimal = calc_radius2(radius)
        self.row_min: int = row_min
        self.row_max: int = row_max
        self.col_min: int = col_min
        self.col_max: int = col_max
        self.hexes: list[Hexagon] = list()
        self.y0: Decimal = self.radius2 * 2 * row_min + \
                           col_min % 2 * self.radius2 - self.radius2
        self.x0: Decimal = self.radius * col_min
        row = self.row_min
        
        ## Here, we need to use a high precision decimal context. Otherwise some point that MUST have the same
        # coordinate do not. This breaks Clustering feature.
        # The default precision for Decimal is 28, so we must use a precision sufficient to hold this + powers and products
        # So why not 35 ? 
        # We also enable Traps, so that this can be quickly detected.
        with localcontext() as ctx:
            ctx.traps[FloatOperation] = True
            ctx.traps[Clamped] = True
            ctx.traps[Rounded] = True
            ctx.traps[Inexact] = True
            ctx.prec = 35
            while row <= self.row_max:
                col = self.col_min
                while col <= self.col_max:
                    y = self.radius2 * 2 * row + col % 2 * self.radius2
                    x = self.radius * Decimal("1.5") * col
                    hexagon = Hexagon(self, x - self.x0, y - self.y0, col, row, hexes.get((col, row), None))
                    self.hexes.append(
                        hexagon)
                    col += 1
                row += 1
        self.width: int = math.ceil(
            (col_max - col_min + 1) * self.radius * Decimal("1.5") + self.radius)
        self.height: int = math.ceil((row_max - row_min + 1) * self.radius2 * 2)
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
                    x0, y0, x1, y1 = [Decimal(n) for n in viewBox.split(' ')]
                    max_box = max(x1 - x0, y1 - y0)

                    scale = self.radius2 / max_box / Decimal(1.1)
                    svgDom.removeAttribute('viewBox')
                    svgDom.setAttribute("id", icon)
                    svgDom.setAttribute("class", "icon "+icon)
                    result[icon] = Icon(
                        self, icon, scale*(x1 - x0)/2, scale*(y1 - y0)/2, scale, svgDom.toxml())
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
    def __init__(self, grid: HexagonGrid, id: str, ox: Decimal, oy: Decimal, scale: Decimal, svgDef: str) -> None:
        self.grid = grid
        self.id = id
        self.scale = scale
        self.svgDef = svgDef
        self.oy = oy
        self.ox = ox
        pass

    def draw(self, tx: Decimal, ty: Decimal) -> str:
        return icon_t.substitute(id=self.id, tx=tx - self.ox, ty=ty - self.oy, scale=self.scale)


class Hexagon:

    def __init__(self, grid: HexagonGrid, x: Decimal, y: Decimal, column: int, row: int,
                 content: frontmatter.Post = None) -> None:
        self.x = x
        self.y = y
        self.col: int = column
        self.row: int = row
        self.content = content
        self.grid: HexagonGrid = grid
        self.outerPoints = self.__createOuterPoints()
        self.innerPoints = self.__createInnerPoints()
        self.pathPoints = self.__createPathPoints()
        self.icon = None
        self.zones = []
        if self.content:
            self.zones = self.content[1].get('zone', []) if isinstance(self.content[1].get('zone', []), List) else [
                self.content[1].get('zone', [])]
            self.icon = self.content[1].get(
                'icon', None)

    def __createOuterPoints(self) -> List[Point]:
        radius = self.grid.radius
        radius2 = self.grid.radius2
        return [Point(x, y) for (x, y) in [
            (self.x+radius, self.y),            # E
            (self.x+radius/2, self.y-radius2),  # NE
            (self.x-radius/2, self.y-radius2),  # NO
            (self.x-radius, self.y),            # O
            (self.x-radius/2, self.y+radius2),  # SO
            (self.x+radius/2, self.y+radius2),  # SE
        ]]

    def __createInnerPoints(self) -> List[Point]:
        radius = self.grid.radius * Decimal("0.6")
        radius2 = self.grid.radius2 * Decimal("0.6")
        return [Point(x, y) for (x, y) in [
            (self.x+radius, self.y),            # E
            (self.x+radius/2, self.y-radius2),  # NE
            (self.x-radius/2, self.y-radius2),  # NO
            (self.x-radius, self.y),            # O
            (self.x-radius/2, self.y+radius2),  # SO
            (self.x+radius/2, self.y+radius2),  # SE
        ]]

    def __createPathPoints(self) -> Dict[Cardinal, Point]:
        radius = self.grid.radius
        radius2 = self.grid.radius2
        dx = radius2 * Decimal("0.8660")  # cos(pi/6)
        coords = {
            Cardinal.N: Point(self.x, self.y-radius2),
            Cardinal.NO: Point(self.x-dx, self.y-radius2/2),
            Cardinal.NE: Point(self.x+dx, self.y-radius2/2),
            Cardinal.S: Point(self.x, self.y+radius2),
            Cardinal.SO: Point(self.x-dx, self.y+radius2/2),
            Cardinal.SE: Point(self.x+dx, self.y+radius2/2),
            Cardinal.C: Point(self.x, self.y),
        }
        return {key: Point(coords[key].x, coords[key].y) for key in coords.keys()}

    def drawGrid(self):
        """Generate svg code for a hexagon, containing the grid and the numbers

        Returns:
        string: svg code for a single hexagon
        """
        # Required variables
        radius = self.grid.radius
        left = (self.x-radius/2)
        top = (self.y-radius/2)

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
        c = self.pathPoints[Cardinal.C]
        text = ''
        if self.icon:
            text = self.grid.iconsDict[self.icon].draw(c.x, c.y)
        elif alt:
            text = text_t.substitute(
                cx=c.x, cy=c.y, text=alt)

        road = self.__computePath('roads')
        river = self.__computePath('rivers')

        return base_terrain + mixed_terrain + road + river + text

    def __computePath(self, typeOfPath: str) -> str:
        paths = []
        result = ''
        if self.content:
            paths = self.content[1].get(
                typeOfPath, [])

        for path in paths:
            try:
                b, e = [self.pathPoints[Cardinal[k.upper()]]
                        for k in path.split()]
                c = self.pathPoints[Cardinal.C]
                result += path_t.substitute(type=typeOfPath,
                                            bx=b.x, by=b.y, ex=e.x, ey=e.y, cx=c.x, cy=c.y)
            except:
                print("Warning: fail compute " + str(type) + " '" + path + "'")

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
