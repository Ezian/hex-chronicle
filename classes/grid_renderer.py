from string import Template
from typing import Callable, List, Tuple

from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

from classes.hexagon_renderer import HexagonRenderer, polygon_to_svg_coord
from classes.tilemetadata import TileMetadata

with open('svg_templates/canvas.svg', 'r', encoding="utf-8") as cfile:
    canvas_t = Template(cfile.read())

with open('svg_templates/polygon.svg', 'r', encoding="utf-8") as cfile:
    polygon_t = Template(cfile.read())


class Renderer:
    def __init__(self, tiles: List[TileMetadata], css: str,
                 radius: float = 20) -> None:
        self.hexRenderer = HexagonRenderer(radius)
        self.strokewidth = radius / 15
        self.fontsize = str(2.5 * radius) + "%"
        self.css = css

        tmptiles = {(h.col, h.row): h for h in tiles}

        tmptiles = [[
            TileMetadata(tile.col-1, tile.row-1),
            TileMetadata(tile.col-1, tile.row),
            TileMetadata(tile.col+1, tile.row-1),
            TileMetadata(tile.col+1, tile.row),
        ] for tile in tiles if tile.col % 2 == 0
        ] + [[
            TileMetadata(tile.col-1, tile.row+1),
            TileMetadata(tile.col-1, tile.row),
            TileMetadata(tile.col+1, tile.row+1),
            TileMetadata(tile.col+1, tile.row),
        ] for tile in tiles if tile.col % 2 == 1] + [[
            TileMetadata(tile.col, tile.row-1),
            TileMetadata(tile.col, tile.row+1),
        ] for tile in tiles if tile.col] + [tiles]

        # Contains all tiles from params, and tiles that have a border with them,
        # with no content (they will be drawed with some default contents)
        self.tiles = {(tile.col, tile.row): tile for l in tmptiles for tile in l}

        if len(self.tiles) == 0:
            print("Warn: No tiles found")
            self.tiles = [TileMetadata(0, 0)]

        self.viewBox = self.__compute_view_box()

    def __compute_view_box(self) -> Tuple[float, float, float, float]:
        x_min = None
        y_min = None
        x_max = None
        y_max = None
        for (x0, y0, x1, y1) in [self.hexRenderer.bounding_box(tile) for tile in self.tiles.values()]:
            if not x_min or x0 < x_min:
                x_min = x0
            if not y_min or y0 < y_min:
                y_min = y0
            if not x_max or x1 > x_max:
                x_max = x1
            if not y_max or y1 > y_max:
                y_max = y1
        return x_min - self.strokewidth, y_min - self.strokewidth, x_max - x_min + self.strokewidth*2, y_max - y_min + self.strokewidth * 2

    def draw_svg(self) -> str:

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
                                   content=''.join(layers),
                                   viewBox=" ".join([str(s)
                                                    for s in self.viewBox]),
                                   strokegrid=self.strokewidth, strokefont=self.strokewidth /
                                   float("1.5"),
                                   strokepath=self.strokewidth *
                                   float("1.2"),
                                   fontsize=self.fontsize, css=self.css)

    def __load_icons(self) -> str:
        return "".join([self.hexRenderer.load_icon(tile) for tile in self.tiles.values()])

    def __draw_grid(self) -> str:
        return "".join([self.hexRenderer.draw_grid(tile) for tile in self.tiles.values()])

    def __draw_numbers(self) -> str:
        return "".join([self.hexRenderer.draw_numbers(tile) for tile in self.tiles.values()])

    def __draw_content(self) -> str:
        return "".join([self.hexRenderer.draw_content(tile) for tile in self.tiles.values()])

    def __draw_zones(self) -> str:
        declared_zones = {zone for tile in self.tiles.values()
                          for zone in tile.zones}
        return "".join([polygon_t.substitute(
            points=polygon_to_svg_coord(polygon),
            cssClass=f"zone {z}") for z in declared_zones for polygon in
            self.__make_cluster(lambda h, zone=z: zone in h.zones)])

    def __make_cluster(self, cluster_checker: Callable[[TileMetadata], bool]) -> List[Polygon]:
        """
        Filters Hexagon of the grid and computes edge point of the cluster(s) border(s).
        Args:
            cluster_checker: lambda Hexagon ->boolean indicating members of the cluster

        Returns: One or several Point lists representing cluster(s) border(s).

        """
        polygons = unary_union([self.hexRenderer.get_shape(
            tile) for tile in self.tiles.values() if cluster_checker(tile)])

        if isinstance(polygons, MultiPolygon):
            return [Polygon(geom) for geom in polygons.geoms]

        return [polygons]
