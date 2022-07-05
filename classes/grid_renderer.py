"""gridrenderer.py

Render a full hex grid
"""
from string import Template
from typing import Callable, List, Tuple

from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

from classes.hexagon_renderer import HexagonRenderer, draw_polygon
from classes.tilemetadata import TileMetadata

with open('svg_templates/canvas.svg', 'r', encoding="utf-8") as cfile:
    canvas_t = Template(cfile.read())


class Renderer:
    """ Render the map, from a list of TileMetadata

    Raises:
        ValueError: If there is no tiles to render
    """

    # pylint: disable=too-few-public-methods
    def __init__(self, tiles: List[TileMetadata], css: str,
                 radius: float = 20) -> None:
        if len(tiles) == 0:
            raise ValueError("No tiles to render")

        self.hex_renderer = HexagonRenderer(radius)
        self.strokewidth = radius / 15
        self.fontsize = str(2.5 * radius) + "%"
        self.css = css
        self.tiles = {(tile.col, tile.row): tile for tile in tiles}

        self.view_box = self.__compute_view_box()

    def __compute_view_box(self) -> Tuple[float, float, float, float]:
        x_min = None
        y_min = None
        x_max = None
        y_max = None
        for (x_0, y_0, x_1, y_1) in [self.hex_renderer.bounding_box(tile)
                                     for tile in self.tiles.values()]:
            if not x_min or x_0 < x_min:
                x_min = x_0
            if not y_min or y_0 < y_min:
                y_min = y_0
            if not x_max or x_1 > x_max:
                x_max = x_1
            if not y_max or y_1 > y_max:
                y_max = y_1
        return (round(k) for k in (x_min - self.strokewidth,
                                   y_min - self.strokewidth,
                                   x_max - x_min + self.strokewidth*2,
                                   y_max - y_min + self.strokewidth * 2))

    def draw_svg(self) -> str:
        """draw_svg
        Compute a string that contains all svg element to display for drawing the map
        Returns:
            str: a simple, svg-formatted string that display the map
        """
        defs = self.__load_icons()
        layers = [
            # First layers are on top of the elevation
            self.__draw_zones(),
            self.__draw_numbers(),
            self.__draw_grid(),
            self.__draw_content(),
        ]
        layers.reverse()

        return canvas_t.substitute(defs=defs,
                                   content='\n'.join(layers),
                                   viewBox=" ".join([str(s)
                                                    for s in self.view_box]),
                                   strokegrid=self.strokewidth, strokefont=self.strokewidth /
                                   float("1.5"),
                                   strokepath=self.strokewidth *
                                   float("1.2"),
                                   fontsize=self.fontsize, css=self.css)

    def __load_icons(self) -> str:
        return "".join(sorted([self.hex_renderer.load_icon(tile)
                               for tile in self.tiles.values()]))

    def __draw_grid(self) -> str:
        return "".join(sorted([self.hex_renderer.draw_grid(tile)
                               for tile in self.tiles.values()]))

    def __draw_numbers(self) -> str:
        return "".join(sorted([self.hex_renderer.draw_numbers(tile)
                               for tile in self.tiles.values()]))

    def __draw_content(self) -> str:
        return "".join(sorted([self.hex_renderer.draw_content(tile)
                               for tile in self.tiles.values()]))

    def __draw_zones(self) -> str:
        declared_zones = {zone for tile in self.tiles.values()
                          for zone in tile.zones}
        return "".join(sorted([draw_polygon(polygon=polygon,
                                            css_class=f"zone {z}")
                               for z in declared_zones for polygon in
                               self.__make_cluster(lambda h, zone=z: zone in h.zones)]))

    def __make_cluster(self, cluster_checker: Callable[[TileMetadata], bool]) -> List[Polygon]:
        """
        Filters Hexagon of the grid and computes edge point of the cluster(s) border(s).
        Args:
            cluster_checker: lambda Hexagon ->boolean indicating members of the cluster

        Returns: One or several Point lists representing cluster(s) border(s).

        """
        polygons = unary_union([self.hex_renderer.get_shape(
            tile) for tile in self.tiles.values() if cluster_checker(tile)])

        if isinstance(polygons, MultiPolygon):
            return [Polygon(geom) for geom in MultiPolygon(polygons).geoms]

        return [polygons]
