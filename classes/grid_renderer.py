from decimal import Decimal
from string import Template
from typing import List, Tuple

from classes.hexagon_renderer import HexagonRenderer
from classes.tilemetadata import Cardinal, TileMetadata

with open('svg_templates/canvas.v2.svg', 'r', encoding="utf-8") as cfile:
    canvas_t = Template(cfile.read())


class Renderer:
    def __init__(self, tiles: List[TileMetadata],
                 radius: Decimal = 20) -> None:
        self.hexRenderer = HexagonRenderer(radius)
        self.strokewidth = radius / 15
        self.fontsize = str(Decimal(2.5) * radius) + "%"
        self.css = ""  # TODO

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
        ] for tile in tiles if tile.col % 2 == 1] + [tiles]

        # Contains all tiles from params, and tiles that have a border with them,
        # with no content (they will be drawed with some default contents)
        self.tiles = {(tile.col, tile.row): tile for l in tmptiles for tile in l}

        self.viewBox = self.__compute_view_box()

    def __compute_view_box(self) -> Tuple[Decimal, Decimal, Decimal, Decimal]:
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
        # TODO Render SVG
        content = self.__draw_content() + self.__draw_grid() + self.__draw_numbers()

        return canvas_t.substitute(icons="",
                                   content=content,
                                   viewBox=" ".join([str(s)
                                                    for s in self.viewBox]),
                                   strokegrid=self.strokewidth, strokefont=self.strokewidth /
                                   Decimal("1.5"),
                                   strokepath=self.strokewidth *
                                   Decimal("1.2"),
                                   fontsize=self.fontsize, css=self.css)

    def __draw_grid(self) -> str:
        return "".join([self.hexRenderer.draw_grid(tile) for tile in self.tiles.values()])

    def __draw_numbers(self) -> str:
        return "".join([self.hexRenderer.draw_numbers(tile) for tile in self.tiles.values()])

    def __draw_content(self) -> str:
        return "".join([self.hexRenderer.draw_content(tile) for tile in self.tiles.values()])
