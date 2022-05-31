from decimal import (Clamped, Decimal, FloatOperation, Inexact, Rounded,
                     localcontext)
from string import Template
from typing import Dict, List, Tuple

from attr import dataclass

from classes.tilemetadata import Cardinal, TileMetadata

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


@dataclass(frozen=True)
class Point:
    """A point on the canevas
    """
    # pylint: disable=invalid-name
    x: Decimal
    y: Decimal


def points_to_polygon_coord(points: List[Point]) -> str:
    """Write points as polygon coordinate

    Args:
        points (List[Point]): List of point

    Returns:
        str: List of coordinates ready to be inserted in svg polygon
    """
    return ' '.join(
        [f"{point.x},{point.y}" for point in points])


class TilePoints:
    def __init__(self, col: int, row: int, radius: Decimal, radius2: Decimal) -> None:
        # Here, we need to use a high precision decimal context. Otherwise some point that MUST
        # have the same coordinate do not. This breaks Clustering feature.
        # The default precision for Decimal is 28, so we must use a precision sufficient to
        # handle operations like
        # powers, sums and products
        # So why not 35 ?
        # We also enable Traps, so that this can be quickly detected.
        self.radius = radius
        self.radius2 = radius2
        with localcontext() as ctx:
            ctx.traps[FloatOperation] = True
            ctx.traps[Clamped] = True
            ctx.traps[Rounded] = True
            ctx.traps[Inexact] = True
            ctx.prec = 35
            self.center = Point(self.radius * Decimal("1.5") * col,
                                self.radius2 *
                                2 * row + col % 2 * self.radius2)

            self.outer_points = self.__create_outer_points()
            self.inner_points = self.__create_inner_points()
            self.path_points = self.__create_path_points()
            self.bounding_box = self.center.x - self.radius, self.center.y - \
                self.radius2, self.center.x + self.radius, self.center.y + self.radius2

    def __create_outer_points(self) -> List[Point]:
        radius = self.radius
        radius2 = self.radius2
        return [Point(x, y) for (x, y) in [
            (self.center.x + radius, self.center.y),  # E
            (self.center.x + radius / 2, self.center.y - radius2),  # NE
            (self.center.x - radius / 2, self.center.y - radius2),  # NO
            (self.center.x - radius, self.center.y),  # O
            (self.center.x - radius / 2, self.center.y + radius2),  # SO
            (self.center.x + radius / 2, self.center.y + radius2),  # SE
        ]]

    def __create_inner_points(self) -> List[Point]:
        radius = self.radius * Decimal("0.6")
        radius2 = self.radius2 * Decimal("0.6")
        return [Point(x, y) for (x, y) in [
            (self.center.x + radius, self.center.y),  # E
            (self.center.x + radius / 2, self.center.y - radius2),  # NE
            (self.center.x - radius / 2, self.center.y - radius2),  # NO
            (self.center.x - radius, self.center.y),  # O
            (self.center.x - radius / 2, self.center.y + radius2),  # SO
            (self.center.x + radius / 2, self.center.y + radius2),  # SE
        ]]

    def __create_path_points(self) -> Dict[Cardinal, Point]:
        radius2 = self.radius2
        cosx = radius2 * Decimal("0.8660")  # cos(pi/6)
        coords = {
            Cardinal.N: Point(self.center.x, self.center.y - radius2),
            Cardinal.NW: Point(self.center.x - cosx, self.center.y - radius2 / 2),
            Cardinal.NE: Point(self.center.x + cosx, self.center.y - radius2 / 2),
            Cardinal.S: Point(self.center.x, self.center.y + radius2),
            Cardinal.SW: Point(self.center.x - cosx, self.center.y + radius2 / 2),
            Cardinal.SE: Point(self.center.x + cosx, self.center.y + radius2 / 2),
            Cardinal.C: Point(self.center.x, self.center.y),
        }
        return coords


class HexagonRenderer:
    def __init__(self, radius: Decimal) -> None:
        self.radius = radius
        self.radius2 = (radius ** 2 - (radius / 2) ** 2).sqrt()
        self.computed_points = {}

    def compute_points(self, tile: TileMetadata) -> TilePoints:
        result = self.computed_points.get((tile.col, tile.row))
        if not result:
            result = TilePoints(tile.col, tile.row, self.radius, self.radius2)
            self.computed_points[tile.col, tile.row] = result

        return result

    def get_outer_points(self, tile: TileMetadata) -> List[Point]:
        return self.compute_points(tile).outer_points

    def get_inner_points(self, tile: TileMetadata) -> List[Point]:
        return self.compute_points(tile).inner_points

    def get_path_points(self, tile: TileMetadata) -> List[Point]:
        return self.compute_points(tile).path_points

    def bounding_box(self, tile: TileMetadata) -> Tuple[Decimal, Decimal, Decimal, Decimal]:
        return self.compute_points(tile).bounding_box

    def draw_grid(self, tile: TileMetadata) -> str:
        """Draw the grid for an hexagon

        Returns:
        string: svg code for a single hexagon
        """

        return polygon_t.substitute(
            points=points_to_polygon_coord(self.get_outer_points(tile)),
            cssClass="grid"
        )

    def draw_numbers(self, tile: TileMetadata) -> str:
        """draw the number of an hexagon

        Returns:
        string: svg code for a single hexagon
        """

        position = self.get_inner_points(tile)[2]
        return number_t.substitute(
            left=position.x, top=position.y, row=tile.row, col=tile.col)

    def draw_content(self, tile: TileMetadata):
        """Generate svg code for a hexagon with terrain and all description features

        Returns:
        string: svg code for a single hexagon
        """

        # Read metadata
        terrain_css = ''
        mixed_terrains = []
        alt = None
        if tile.content:
            terrain = tile.content.get(
                'terrain', {}).get('type', 'unknown')
            terrain_css = terrain.lower()
            mixed_terrains = tile.content.get(
                'terrain', {}).get('mixed', [])
            alt = tile.content.get('alt', None)

        # base terrain
        base_terrain = polygon_t.substitute(
            points=points_to_polygon_coord(self.get_outer_points(tile)),
            cssClass=terrain_css
        )

        # mixed terrain
        mixed_terrain = ''
        for terrain in mixed_terrains:
            type_css = terrain.get('type', 'unknown')
            polygons: List[List[Point]] = self.compute_parts_polygons(tile,
                                                                      terrain.get('sides', []))

            for polygon in polygons:
                point_str = points_to_polygon_coord(polygon)
                mixed_terrain += polygon_t.substitute(
                    points=point_str,
                    cssClass=type_css
                )

        # Text or icon
        center = self.get_path_points(tile)[Cardinal.C]
        text = ''
        # TODO icon
        # if self.icon:
        #     text = self.grid.icons_dict[self.icon].draw(center)
        # elif alt:
        if alt:
            text = text_t.substitute(
                cx=center.x, cy=center.y, text=alt)

        road = self.__compute_path(tile, 'roads')
        river = self.__compute_path(tile, 'rivers')

        return base_terrain + mixed_terrain + road + river + text

    def __compute_path(self, tile: TileMetadata, type_of_path: str) -> str:
        paths = []
        result = ''
        if tile.content:
            paths = tile.content.get(
                type_of_path, [])

        path_points = self.get_path_points(tile)

        for path in paths:
            try:
                first, last = [path_points[
                    Cardinal[k]
                ]
                    for k in path.split()]
                center = path_points[Cardinal.C]
                result += path_t.substitute(type=type_of_path,
                                            bx=first.x, by=first.y,
                                            ex=last.x, ey=last.y,
                                            cx=center.x, cy=center.y)
            except:  # pylint: disable=bare-except
                print("Warning: fail compute " + str(type) + " '" + path + "'")

        return result

    def compute_parts_polygons(self, tile: TileMetadata, sides: List[str]) -> List[List[Point]]:
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
                card = Cardinal[side]
            except KeyError:
                pass  # do nothing
            if card is Cardinal.N:
                result.append([
                    self.pin(tile, Cardinal.NE), self.pin(tile,
                                                          Cardinal.NW), self.pout(tile, Cardinal.NW), self.pout(tile, Cardinal.NE),
                ])
            if card is Cardinal.NE:
                result.append([
                    self.pin(tile, Cardinal.E), self.pin(tile,
                                                         Cardinal.NE), self.pout(tile, Cardinal.NE), self.pout(tile, Cardinal.E),
                ])
            if card is Cardinal.SE:
                result.append([
                    self.pin(tile, Cardinal.E), self.pin(tile,
                                                         Cardinal.SE), self.pout(tile, Cardinal.SE), self.pout(tile, Cardinal.E),
                ])
            if card is Cardinal.S:
                result.append([
                    self.pin(tile, Cardinal.SE), self.pin(tile,
                                                          Cardinal.SW), self.pout(tile, Cardinal.SW), self.pout(tile, Cardinal.SE),
                ])
            if card is Cardinal.SW:
                result.append([
                    self.pin(tile, Cardinal.W), self.pin(tile,
                                                         Cardinal.SW), self.pout(tile, Cardinal.SW), self.pout(tile, Cardinal.W),
                ])
            if card is Cardinal.NW:
                result.append([
                    self.pin(tile, Cardinal.W), self.pin(tile,
                                                         Cardinal.NW), self.pout(tile, Cardinal.NW), self.pout(tile, Cardinal.W),
                ])
            if card is Cardinal.C:
                result.append(self.get_inner_points(tile))

        return result

    def pin(self, tile: TileMetadata, card: Cardinal) -> Point:
        """Access to an innerPoint through cardinal

        Args:
        card(Cardinal): Position of the point

        Returns:
        Point: the expected point
        """
        if card.pid() is None:
            return None

        return self.get_inner_points(tile)[card.pid()]

    def pout(self, tile: TileMetadata, card: Cardinal) -> Point:
        """Access to an innerPoint through cardinal

        Args:
        card(Cardinal): Position of the point

        Returns:
        Point: the expected point
        """
        if card.pid() is None:
            return None

        return self.get_outer_points(tile)[card.pid()]
