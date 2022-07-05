"""hexrenderer.py

Render a single hex
"""
import logging
import math
from pathlib import Path
from string import Template
from typing import Dict, List, Tuple
from xml.dom import minidom

from shapely.geometry import Point, Polygon

from classes.tilemetadata import Cardinal, TileMetadata

with open('svg_templates/text.svg', 'r', encoding="utf-8") as cfile:
    text_t = Template(cfile.read())

with open('svg_templates/number.svg', 'r', encoding="utf-8") as cfile:
    number_t = Template(cfile.read())

with open('svg_templates/icon.svg', 'r', encoding="utf-8") as cfile:
    icon_t = Template(cfile.read())

with open('svg_templates/path.svg', 'r', encoding="utf-8") as cfile:
    path_t = Template(cfile.read())


def points_to_polygon_coord(points: List[Point]) -> str:
    """Write points as polygon coordinate

    Args:
        points (List[Point]): List of point

    Returns:
        str: List of coordinates ready to be inserted in svg polygon
    """
    return ' '.join(
        [f"{point.x},{point.y}" for point in points])


def draw_polygon(polygon: Polygon, css_class: str):
    """Draw a polygon from SVG returned by shapely

    Returns:
    string: svg code for a single hexagon
    """
    doc = minidom.parseString(polygon.svg())
    path_dom = doc.getElementsByTagName("path")[0]
    # remove unexpected attribute
    to_be_removed = [k for k in path_dom.attributes.keys() if k not in [
        'd']]

    # pylint: disable=expression-not-assigned
    [path_dom.removeAttribute(k) for k in to_be_removed]

    path_dom.setAttribute("class", css_class)

    return path_dom.toxml()


def fixed_precision_point(p_x: float, p_y: float) -> Point:
    """
    Round the coordinate and return a shapely.Point.

    Returns:
    Point: A point with less precision...
    """
    # Yes I know, it is bad... But float precision is may break clustering.
    # Since we can't have more precision in shapely, having less is preferable and do the same ^^
    digits = 1
    return Point(round(p_x, digits), round(p_y, digits))


class TileShape:
    """TileShape

    Contains all required properties to draw an hexagon

    """
    # pylint: disable=too-many-instance-attributes

    def __init__(self, col: int, row: int, radius: float, radius2: float) -> None:
        self.radius = radius
        self.radius2 = radius2
        self.center = fixed_precision_point(self.radius * 1.5 * col,
                                            self.radius2 *
                                            2 * row + col % 2 * self.radius2)

        self.outer_points = self.__create_outer_points()
        self.inner_points = self.__create_inner_points()
        self.path_points = self.__create_path_points()
        self.shape = Polygon([self.outer_points[c] for c in [
            Cardinal.E,
            Cardinal.NE,
            Cardinal.NW,
            Cardinal.W,
            Cardinal.SW,
            Cardinal.SE]])
        self.__zones = {}

    @property
    def bounding_box(self):
        """
        Returns:
            tuple(float,float,float,float): the bouding box of the hexagon (xmin, ymin, xmax, ymax)
        """
        return self.shape.bounds

    def get_zone(self, card: Cardinal) -> Polygon:
        """
        Get the polygon corresponding to a mixed zone
        Args:
            card (Cardinal): Cardinal of the mixed zone (NE, N, NW, SW, S or SE )

        Returns:
            Polygon: A polygon correspondint to the shape of the zone
        """
        result = self.__zones.get(card)
        if not result:
            result = self.__compute_parts_polygon(card)
            self.__zones[card] = result
        return result

    def __create_outer_points(self) -> Dict[Cardinal, Point]:
        radius = self.radius
        radius2 = self.radius2
        return {
            Cardinal.E: fixed_precision_point(self.center.x + radius, self.center.y),
            Cardinal.NE: fixed_precision_point(self.center.x + radius / 2, self.center.y - radius2),
            Cardinal.NW: fixed_precision_point(self.center.x - radius / 2, self.center.y - radius2),
            Cardinal.W: fixed_precision_point(self.center.x - radius, self.center.y),
            Cardinal.SW: fixed_precision_point(self.center.x - radius / 2, self.center.y + radius2),
            Cardinal.SE: fixed_precision_point(self.center.x + radius / 2, self.center.y + radius2),
        }

    def __create_inner_points(self) -> Dict[Cardinal, Point]:
        radius = self.radius * 0.6
        radius2 = self.radius2 * 0.6
        return {
            Cardinal.E: fixed_precision_point(self.center.x + radius, self.center.y),
            Cardinal.NE: fixed_precision_point(self.center.x + radius / 2, self.center.y - radius2),
            Cardinal.NW: fixed_precision_point(self.center.x - radius / 2, self.center.y - radius2),
            Cardinal.W: fixed_precision_point(self.center.x - radius, self.center.y),
            Cardinal.SW: fixed_precision_point(self.center.x - radius / 2, self.center.y + radius2),
            Cardinal.SE: fixed_precision_point(self.center.x + radius / 2, self.center.y + radius2),
        }

    def __create_path_points(self) -> Dict[Cardinal, Point]:
        radius2 = self.radius2
        cosx = radius2 * 0.8660  # cos(pi/6)
        coords = {
            Cardinal.N: fixed_precision_point(self.center.x, self.center.y - radius2),
            Cardinal.NW: fixed_precision_point(self.center.x - cosx, self.center.y - radius2 / 2),
            Cardinal.NE: fixed_precision_point(self.center.x + cosx, self.center.y - radius2 / 2),
            Cardinal.S: fixed_precision_point(self.center.x, self.center.y + radius2),
            Cardinal.SW: fixed_precision_point(self.center.x - cosx, self.center.y + radius2 / 2),
            Cardinal.SE: fixed_precision_point(self.center.x + cosx, self.center.y + radius2 / 2),
            Cardinal.C: fixed_precision_point(self.center.x, self.center.y),
        }
        return coords

    def __compute_parts_polygon(self, card: Cardinal) -> Polygon:
        """Compute parts of polygon of one zone

        Args:
            side: side to compute

        Returns:
            Polygon: The polygon of the side passed as argument
        """
        # pylint: disable=too-many-return-statements
        if card is Cardinal.N:
            return Polygon([
                self.pin(Cardinal.NE), self.pin(
                    Cardinal.NW), self.pout(Cardinal.NW), self.pout(Cardinal.NE),
            ])
        if card is Cardinal.NE:
            return Polygon([
                self.pin(Cardinal.E), self.pin(
                    Cardinal.NE), self.pout(Cardinal.NE), self.pout(Cardinal.E),
            ])
        if card is Cardinal.SE:
            return Polygon([
                self.pin(Cardinal.E), self.pin(
                    Cardinal.SE), self.pout(Cardinal.SE), self.pout(Cardinal.E),
            ])
        if card is Cardinal.S:
            return Polygon([
                self.pin(Cardinal.SE), self.pin(
                    Cardinal.SW), self.pout(Cardinal.SW), self.pout(Cardinal.SE),
            ])
        if card is Cardinal.SW:
            return Polygon([
                self.pin(Cardinal.W), self.pin(
                    Cardinal.SW), self.pout(Cardinal.SW), self.pout(Cardinal.W),
            ])
        if card is Cardinal.NW:
            return Polygon([
                self.pin(Cardinal.W), self.pin(
                    Cardinal.NW), self.pout(Cardinal.NW), self.pout(Cardinal.W),
            ])
        if card is Cardinal.C:
            return Polygon([self.inner_points[c] for c in [
                Cardinal.E,
                Cardinal.NE,
                Cardinal.NW,
                Cardinal.W,
                Cardinal.SW,
                Cardinal.SE]])

        raise ValueError(f'No zone for this Cardinal: {card}')

    def pin(self, card: Cardinal) -> Point:
        """Access to an innerPoint through cardinal

        Args:
        card(Cardinal): Position of the point

        Returns:
        Point: the expected point
        """
        if card.pid() is None:
            return None

        return self.inner_points[card]

    def pout(self, card: Cardinal) -> Point:
        """Access to an innerPoint through cardinal

        Args:
        card(Cardinal): Position of the point

        Returns:
        Point: the expected point
        """
        if card.pid() is None:
            return None

        return self.outer_points[card]


class Icon:
    """Draw an icon over the map
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, icon_id: str,
                 origin: Point, scale: float, svg_def: str) -> None:
        # pylint: disable=too-many-arguments
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


class HexagonRenderer:
    """Render an hexagon
    """

    def __init__(self, radius: float) -> None:
        self.__radius = radius
        self.__radius2 = math.sqrt(radius ** 2 - (radius / 2) ** 2)
        self.__computed_points = {}
        self.icons_dict = {}

    def compute_shape(self, tile: TileMetadata) -> TileShape:
        """Compute the shape of an tile from its metadata.
        The shape is cached to avoid performance issues.

        Args:
            tile (TileMetadata): tilemetadata

        Returns:
            TileShape: The shape of the hexagon with a lot of helper functiont to draw many things
        """
        result = self.__computed_points.get((tile.col, tile.row))
        if not result:
            result = TileShape(tile.col, tile.row,
                               self.__radius, self.__radius2)
            self.__computed_points[tile.col, tile.row] = result

        return result

    def get_shape(self, tile: TileMetadata) -> Polygon:
        """
        Args:
            tile (TileMetadata): a tile medata

        Returns:
            Polygon: the shape of the tile metadata
        """
        return self.compute_shape(tile).shape

    def get_coord_pos(self, tile: TileMetadata) -> Point:
        """
        Args:
            tile (TileMetadata): a tile medata

        Returns:
            Point: The position of the coordinates
        """
        return self.compute_shape(tile).inner_points[Cardinal.NW]

    def get_zone(self, tile: TileMetadata, card: Cardinal) -> Polygon:
        """
        Args:
            tile (TileMetadata): a tile medata
            card (Cardinal): A position in the tile

        Returns:
            Polygon: The shape of the polygon at the position.
        """
        return self.compute_shape(tile).get_zone(card)

    def get_path_points(self, tile: TileMetadata) -> List[Point]:
        """
        Args:
             tile (TileMetadata): a tile medata

        Returns:
            List[Point]: The points used to pass path (to draw rivers and roads)
        """
        return self.compute_shape(tile).path_points

    def bounding_box(self, tile: TileMetadata) -> Tuple[float, float, float, float]:
        """
        Args:
            tile (TileMetadata): a tile medata

        Returns:
            Tuple[float, float, float, float]: the bounding box (xmin, ymin, xmax, ymax)
        """
        return self.compute_shape(tile).bounding_box

    def load_icon(self, tile: TileMetadata) -> str:
        """
        Loads icons and return defs to avoid multiple declaration of heavy icons.
        Args:
             tile (TileMetadata): a tile medata

        Returns:
            str: a defs to insert in <defs></defs> in the svg file
        """
        # pylint: disable=too-many-locals
        if not tile.icon:
            return ""

        icon_path = Path(
            'svg_templates/icons').joinpath(tile.icon + ".svg")
        if not icon_path.is_file():
            # Don't print an error message for missing terrain icon. It's usually normal.
            if not tile.icon.startswith("terrain"):
                logging.warning(
                    "%s is not a valid icon (icon path '%s' isn't a file)", tile.icon, icon_path)
            return ""

        # extract inner svg
        with open(icon_path, 'r', encoding="UTF-8") as icon_file:
            try:
                doc = minidom.parseString(icon_file.read())
                svg_dom = doc.getElementsByTagName("svg")[0]
                view_box = svg_dom.getAttribute('viewBox')
                x_0, y_0, x_1, y_1 = [float(n)
                                      for n in view_box.split(' ')]
                max_box = max(x_1 - x_0, y_1 - y_0)

                scale = self.__radius2 / max_box / float(1.1)
                svg_dom.removeAttribute('viewBox')
                svg_dom.setAttribute("id", tile.icon)
                svg_dom.setAttribute("class", " ".join(
                    ["icon"] + tile.icon.split("/")))
                origin = fixed_precision_point(scale * (x_1 - x_0) / 2,
                                               scale * (y_1 - y_0) / 2)
                icon = Icon(tile.icon, origin, scale, svg_dom.toxml())
                self.icons_dict[tile.icon] = icon
                return icon.svg_def
            except Exception as exception:  # pylint: disable=broad-except
                logging.warning("icon format not supported (error=%s)",
                                exception, exc_info=True)

        return ""

    def draw_grid(self, tile: TileMetadata) -> str:
        """Draw the grid for an hexagon

        Returns:
        string: svg code for a single hexagon
        """

        return draw_polygon(polygon=self.get_shape(tile),
                            css_class="grid"
                            )

    def draw_numbers(self, tile: TileMetadata) -> str:
        """draw the number of an hexagon

        Returns:
        string: svg code for a single hexagon
        """

        position = self.get_coord_pos(tile)
        return number_t.substitute(
            left=position.x, top=position.y, row=tile.row, col=tile.col)

    def draw_content(self, tile: TileMetadata):
        # pylint: disable=too-many-locals
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
        base_terrain = draw_polygon(
            polygon=self.get_shape(tile),
            css_class=f"terrain {terrain_css}"
        )

        # mixed terrain
        mixed_terrain = ''
        for terrain in mixed_terrains:
            type_css = terrain.get('type', 'unknown')
            polygons: List[Polygon] = [self.get_zone(tile, Cardinal[side]) for side in terrain.get(
                'sides', []) if Cardinal.valid_zone(side)]

            for polygon in polygons:
                mixed_terrain += draw_polygon(polygon=polygon,
                                              css_class=f"terrain {type_css}"
                                              )

        # Text or icon
        center = self.get_path_points(tile)[Cardinal.C]
        text = ''
        if tile.icon:
            the_icon = self.icons_dict.get(tile.icon, None)
            if the_icon:
                text = the_icon.draw(center)

        if len(text) == 0 and alt:
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
            except Exception as exception:   # pylint: disable=broad-except
                logging.warning(
                    "Warning: fail compute %s '%s' (error=%s)",
                    str(type), path, exception, exc_info=True)

        return result
