"""hexagon.py

Contains the concept of hexagonal grid, with drawing capabilities

"""

import math
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, localcontext, FloatOperation, Clamped, Rounded, Inexact
from enum import Enum, auto
from pathlib import Path
from string import Template
from typing import List, Dict, Callable
from xml.dom import minidom

import frontmatter

with open('svg_templates/text.svg', 'r', encoding="utf-8") as cfile:
    text_t = Template(cfile.read())

with open('svg_templates/number.svg', 'r', encoding="utf-8") as cfile:
    number_t = Template(cfile.read())

with open('svg_templates/polygon.svg', 'r', encoding="utf-8") as cfile:
    polygon_t = Template(cfile.read())

with open('svg_templates/icon.svg', 'r', encoding="utf-8") as cfile:
    icon_t = Template(cfile.read())

with open('svg_templates/path.svg', 'r', encoding="utf-8") as cfile:
    path_t = Template(cfile.read())


def calc_radius2(radius: Decimal):
    """Calculate the shortest (inner) radius for the given (outer) hex radius

        Args:
        radius (integer): hex radius (widest)

        Returns:
        integer: Inner radius for the given outer radius.
        """

    return (radius ** 2 - (radius / 2) ** 2).sqrt()


@dataclass
class GridBox:
    """Boundaries of the grid
    """
    col_min: int
    col_max: int
    row_min: int
    row_max: int


@dataclass(frozen=True)
class Point:
    """A point on the canevas
    """
    # pylint: disable=invalid-name
    x: Decimal
    y: Decimal


@dataclass(frozen=True)
class Position:
    """A position in the grid
    """
    col: int
    row: int


@dataclass(eq=False, frozen=True)
class Segment:
    """Segment composed of 2 points. Order of the points do not matter"""
    # pylint: disable=invalid-name
    a: Point
    b: Point

    def __eq__(self, other):
        return (self.a == other.a and self.b == other.b) or (self.a == other.b and self.b ==
                                                             other.a)

    def __hash__(self):
        return hash(self.a) + hash(self.b)

    def touches(self, point: Point):
        """
        Predicates which checks if a point touches a segment (i.e. this point is an edge of the
        segment)
        Args:
            point: Point to checkt

        Returns: True if the point is an edge of the segment, false otherwise.

        """
        return point in (self.a, self.b)


def points_to_polygon_coord(points: List[Point]) -> str:
    """Write points as polygon coordinate

    Args:
        points (List[Point]): List of point

    Returns:
        str: List of coordinates ready to be inserted in svg polygon
    """
    return ' '.join(
        [f"{point.x},{point.y}" for point in points])


# Type of terrain


class Cardinal(Enum):
    """Cardinal point, used to identify zones and point
    """
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
        """
        Returns:
            int: the point id corresponding to this cardinal point
        """
        return self.value[1]


# Skip declaration for now, will declare later
# pylint: disable=[missing-class-docstring,too-few-public-methods]
class Hexagon:
    pass


class HexagonGrid:
    """Hexagonal grid, which can be drawed as a SVG file
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, hexes, grid_box: GridBox,
                 radius: Decimal = 20) -> None:
        self.radius: Decimal = radius
        self.radius2: Decimal = calc_radius2(radius)
        self.row_min: int = grid_box.row_min
        self.row_max: int = grid_box.row_max
        self.col_min: int = grid_box.col_min
        self.col_max: int = grid_box.col_max
        self.hexes: List[Hexagon] = []
        self.origin = Point(self.radius * Decimal("1.5") * grid_box.col_min - 2*self.radius +
                            grid_box.row_min % 2 * self.radius,
                            self.radius2 * 2 * grid_box.row_min +
                            grid_box.col_min % 2 * self.radius2 - self.radius2)
        row = self.row_min

        # Here, we need to use a high precision decimal context. Otherwise some point that MUST
        # have the same coordinate do not. This breaks Clustering feature.
        # The default precision for Decimal is 28, so we must use a precision sufficient to
        # handle operations like
        # powers, sums and products
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
                    center = Point(self.radius * Decimal("1.5") * col - self.origin.x,
                                   self.radius2 *
                                   2 * row + col % 2 * self.radius2 - self.origin.y)
                    pos = Position(col, row)
                    self.hexes.append(
                        Hexagon(self, center, pos, hexes.get((col, row), None)))
                    col += 1
                row += 1

        hex_width = grid_box.col_max - grid_box.col_min + 1
        hex_height = grid_box.row_max - grid_box.row_min + 1
        self.width: int = math.ceil(
            (hex_width + hex_width % 2) * self.radius * Decimal("1.5") + self.radius)
        self.height: int = math.ceil(
            (hex_height + hex_height % 2) * self.radius2 * 2)
        self.icons_dict = self.__compute_icons()

    def draw(self):
        """
        Create the SVG representation of this grid and hexagons
        Returns: the SVG string, ready to be written.

        """
        draws = [h.draw_content() for h in self]
        draws += [h.draw_grid() for h in self]
        draws += [self.draw_clusters()]
        return "\n".join(draws)

    def __compute_icons(self):
        # pylint: disable=too-many-locals
        result = {}
        for hexagon in self.hexes:
            icon = hexagon.icon
            if not icon:
                continue

            icon_path = Path(
                'svg_templates/icons/building').joinpath(icon + ".svg")
            if not icon_path.is_file():
                continue

            # extract inner svg
            with open(icon_path, 'r', encoding="UTF-8") as icon_file:
                try:
                    doc = minidom.parseString(icon_file.read())
                    svg_dom = doc.getElementsByTagName("svg")[0]
                    view_box = svg_dom.getAttribute('viewBox')
                    x_0, y_0, x_1, y_1 = [Decimal(n)
                                          for n in view_box.split(' ')]
                    max_box = max(x_1 - x_0, y_1 - y_0)

                    scale = self.radius2 / max_box / Decimal(1.1)
                    svg_dom.removeAttribute('viewBox')
                    svg_dom.setAttribute("id", icon)
                    svg_dom.setAttribute("class", "icon " + icon)
                    origin = Point(scale * (x_1 - x_0) / 2,
                                   scale * (y_1 - y_0) / 2)
                    result[icon] = Icon(
                        self, icon, origin, scale, svg_dom.toxml())
                except:  # pylint: disable=bare-except
                    print("Warning: icon format not supported")
                    continue

        return result

    def draw_clusters(self):
        """
        Create the SVG representation of clusters edges
        Returns: the SVG representation of the cluster edges, ready to be written.

        """
        declared_zones = {zone for h in self for zone in h.zones}
        return "".join([polygon_t.substitute(
            points=points_to_polygon_coord(polygon),
            cssClass=f"zone {z}") for z in declared_zones for polygon in
            self.make_cluster(lambda h, zone=z: zone in h.zones)])

    def make_cluster(self, cluster_checker: Callable[[Hexagon], bool]) -> List[List[Point]]:
        """
        Filters Hexagon of the grid and computes edge point of the cluster(s) border(s).
        Args:
            cluster_checker: lambda Hexagon ->boolean indicating members of the cluster

        Returns: One or several Point lists representing cluster(s) border(s).

        """

        # First let's construct all segment around the retained edges
        segments = defaultdict(int)
        for hexagon in self:
            if cluster_checker(hexagon):
                # pylint: disable=consider-using-enumerate
                for i in range(0, len(hexagon.outer_points)):
                    segment = Segment(hexagon.outer_points[(i + 1) % len(hexagon.outer_points)],
                                      hexagon.outer_points[i])
                    segments[segment] += 1

        # Then we remove all segments present more than once (i.e. shared by more than 1 hexagon,
        # thus not on an edge)
        retained_segments = [k for k, v in segments.items() if v == 1]
        polygons = []

        # Build polygons with these segments.
        # First let's select one segment, then look in the bag for another one connected to the
        # previous one.Keep on linking segments as long as we did not complete a loop .
        # If loop is complete, This is the border of one cluster. We must rerun the algorithm as
        # long as we have segments to dry out all clusters (non-contiguous zones)
        # Beware, while this algorithm is true with hexagon tiling, it is globally false.
        # (It is true iff there is at most in any vertices no more than 3 distinct edges)
        while len(retained_segments):
            segment = retained_segments.pop()
            chain = [segment.a, segment.b]
            while True:
                new_link = [
                    s for s in retained_segments if s.touches(chain[- 1])][0]
                retained_segments.remove(new_link)
                if new_link.a == chain[len(chain) - 1]:
                    if new_link.b == chain[0]:
                        polygons.append(chain)
                        break

                    chain.append(new_link.b)
                else:

                    if new_link.a == chain[0]:
                        polygons.append(chain)
                        break

                    chain.append(new_link.a)

        return polygons

    def icons(self) -> str:
        """List all existing icons to add it as def in svg

        Returns:
            str: svg string containing all icons
        """
        return ''.join([icon.svg_def for icon in self.icons_dict.values()])

    def __iter__(self):
        """ Returns the Iterator object """
        return self.hexes.__iter__()


class Icon:
    """Draw an icon over the map
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, grid: HexagonGrid, icon_id: str,
                 origin: Point, scale: Decimal, svg_def: str) -> None:
        # pylint: disable=too-many-arguments
        self.grid = grid
        self.icon_id = icon_id
        self.scale = scale
        self.svg_def = svg_def
        self.origin = origin

    def draw(self, translate_to: Point) -> str:
        """Draw the icon over the hex

        Args:
            translate_to (Decimal): offset where to translate the icon

        Returns:
            str: a svg string correctly translated to be drawed over the map
        """
        return icon_t.substitute(id=self.icon_id,
                                 tx=translate_to.x - self.origin.x,
                                 ty=translate_to.y - self.origin.y,
                                 scale=self.scale)


# pylint: disable=function-redefined
class Hexagon:
    """Represents an hexagon, with its zone and some data used to draw everything
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, grid: HexagonGrid, center: Point,
                 position: Position, content: frontmatter.Post = None) -> None:
        self.center = center
        self.position = position
        self.content = content
        self.grid: HexagonGrid = grid
        self.outer_points = self.__create_outer_points()
        self.inner_points = self.__create_inner_points()
        self.path_points = self.__create_path_points()
        self.icon = None
        self.zones = []
        if self.content:
            self.zones = self.content[1].get('zone', []) if isinstance(
                self.content[1].get('zone', []), List) else [
                self.content[1].get('zone', [])]
            self.icon = self.content[1].get(
                'icon', None)

    def __create_outer_points(self) -> List[Point]:
        radius = self.grid.radius
        radius2 = self.grid.radius2
        return [Point(x, y) for (x, y) in [
            (self.center.x + radius, self.center.y),  # E
            (self.center.x + radius / 2, self.center.y - radius2),  # NE
            (self.center.x - radius / 2, self.center.y - radius2),  # NO
            (self.center.x - radius, self.center.y),  # O
            (self.center.x - radius / 2, self.center.y + radius2),  # SO
            (self.center.x + radius / 2, self.center.y + radius2),  # SE
        ]]

    def __create_inner_points(self) -> List[Point]:
        radius = self.grid.radius * Decimal("0.6")
        radius2 = self.grid.radius2 * Decimal("0.6")
        return [Point(x, y) for (x, y) in [
            (self.center.x + radius, self.center.y),  # E
            (self.center.x + radius / 2, self.center.y - radius2),  # NE
            (self.center.x - radius / 2, self.center.y - radius2),  # NO
            (self.center.x - radius, self.center.y),  # O
            (self.center.x - radius / 2, self.center.y + radius2),  # SO
            (self.center.x + radius / 2, self.center.y + radius2),  # SE
        ]]

    def __create_path_points(self) -> Dict[Cardinal, Point]:
        radius2 = self.grid.radius2
        cosx = radius2 * Decimal("0.8660")  # cos(pi/6)
        coords = {
            Cardinal.N: Point(self.center.x, self.center.y - radius2),
            Cardinal.NO: Point(self.center.x - cosx, self.center.y - radius2 / 2),
            Cardinal.NE: Point(self.center.x + cosx, self.center.y - radius2 / 2),
            Cardinal.S: Point(self.center.x, self.center.y + radius2),
            Cardinal.SO: Point(self.center.x - cosx, self.center.y + radius2 / 2),
            Cardinal.SE: Point(self.center.x + cosx, self.center.y + radius2 / 2),
            Cardinal.C: Point(self.center.x, self.center.y),
        }
        return coords

    def draw_grid(self):
        """Generate svg code for a hexagon, containing the grid and the numbers

        Returns:
        string: svg code for a single hexagon
        """
        # Required variables
        radius = self.grid.radius
        left = (self.center.x - radius / 2)
        top = (self.center.y - radius / 2)

        # Number
        number_svg = number_t.substitute(
            left=left, top=top, row=self.position.row, col=self.position.col)

        # Grid
        grid_svg = polygon_t.substitute(
            points=points_to_polygon_coord(self.outer_points),
            cssClass="grid"
        )

        return number_svg + grid_svg

    def draw_content(self):
        """Generate svg code for a hexagon with terrain and all description features

        Returns:
        string: svg code for a single hexagon
        """

        # Read metadata
        terrain_css = ''
        mixed_terrains = []
        alt = None
        if self.content:
            terrain = self.content[1].get(
                'terrain', {}).get('type', 'unknown')
            terrain_css = terrain.lower()
            mixed_terrains = self.content[1].get(
                'terrain', {}).get('mixed', [])
            alt = self.content[1].get('alt', None)

        # base terrain
        base_terrain = polygon_t.substitute(
            points=points_to_polygon_coord(self.outer_points),
            cssClass=terrain_css
        )

        # mixed terrain
        mixed_terrain = ''
        for terrain in mixed_terrains:
            type_css = terrain.get('type', 'unknown')
            polygons: List[List[Point]] = self.compute_parts_polygons(
                terrain.get('sides', []))

            for polygon in polygons:
                point_str = points_to_polygon_coord(polygon)
                mixed_terrain += polygon_t.substitute(
                    points=point_str,
                    cssClass=type_css
                )

        # Text or icon
        center = self.path_points[Cardinal.C]
        text = ''
        if self.icon:
            text = self.grid.icons_dict[self.icon].draw(center)
        elif alt:
            text = text_t.substitute(
                cx=center.x, cy=center.y, text=alt)

        road = self.__compute_path('roads')
        river = self.__compute_path('rivers')

        return base_terrain + mixed_terrain + road + river + text

    def __compute_path(self, type_of_path: str) -> str:
        paths = []
        result = ''
        if self.content:
            paths = self.content[1].get(
                type_of_path, [])

        for path in paths:
            try:
                first, last = [self.path_points[Cardinal[k.upper()]]
                               for k in path.split()]
                center = self.path_points[Cardinal.C]
                result += path_t.substitute(type=type_of_path,
                                            bx=first.x, by=first.y,
                                            ex=last.x, ey=last.y,
                                            cx=center.x, cy=center.y)
            except:  # pylint: disable=bare-except
                print("Warning: fail compute " + str(type) + " '" + path + "'")

        return result

    def compute_parts_polygons(self, sides: List[str]) -> List[List[Point]]:
        """Compute parts of polygon, for each zone.

        Args:
            sides (List[str]): List of side to compute

        Returns:
            List[List[Point]]: List of polygon for each side passed as argument
        """
        result: List[List[Point]] = []

        for side in sides:
            card = None
            try:
                card = Cardinal[side.upper()]
            except KeyError:
                pass  # do nothing
            if card is Cardinal.N:
                result.append([
                    self.pin(Cardinal.NE), self.pin(
                        Cardinal.NO), self.pout(Cardinal.NO), self.pout(Cardinal.NE),
                ])
            if card is Cardinal.NE:
                result.append([
                    self.pin(Cardinal.E), self.pin(
                        Cardinal.NE), self.pout(Cardinal.NE), self.pout(Cardinal.E),
                ])
            if card is Cardinal.SE:
                result.append([
                    self.pin(Cardinal.E), self.pin(
                        Cardinal.SE), self.pout(Cardinal.SE), self.pout(Cardinal.E),
                ])
            if card is Cardinal.S:
                result.append([
                    self.pin(Cardinal.SE), self.pin(
                        Cardinal.SO), self.pout(Cardinal.SO), self.pout(Cardinal.SE),
                ])
            if card is Cardinal.SO:
                result.append([
                    self.pin(Cardinal.O), self.pin(
                        Cardinal.SO), self.pout(Cardinal.SO), self.pout(Cardinal.O),
                ])
            if card is Cardinal.NO:
                result.append([
                    self.pin(Cardinal.O), self.pin(
                        Cardinal.NO), self.pout(Cardinal.NO), self.pout(Cardinal.O),
                ])
            if card is Cardinal.C:
                result.append(self.inner_points)

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

        return self.inner_points[card.pid()]

    def pout(self, card: Cardinal) -> Point:
        """Access to an innerPoint through cardinal

        Args:
        card(Cardinal): Position of the point

        Returns:
        Point: the expected point
        """
        if card.pid() is None:
            return None

        return self.outer_points[card.pid()]
