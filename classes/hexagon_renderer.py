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
