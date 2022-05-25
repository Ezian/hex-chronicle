import errno
import os
import re
from enum import Enum, EnumMeta, auto
from pathlib import Path
from typing import Any, Dict

import frontmatter


class CardinalEnumMeta(EnumMeta):
    """ Metaclass to replace Ouest by West and handle yaml no as North West instead of false

    Args:
        EnumMeta (Class): class enumeration
    """

    def __getitem__(cls, name):
        if isinstance(str, bool) and not str:
            return Cardinal.NW  # Handle NO value from yml
        name = name.upper().replace('O', 'W')
        return super().__getitem__(name)


class Cardinal(Enum, metaclass=CardinalEnumMeta):
    """Cardinal point, used to identify zones and point
    """
    # the second element of tuple allow to get the id of a point in inner and outerpoint
    N = (auto(), None)
    NW = (auto(), 2)
    W = (auto(), 3)
    SW = (auto(), 4)
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


class TileMetadata:
    def __init__(self, col: int, row: int, content={}) -> None:
        self.col = col
        self.row = row
        self.content: Dict[str:Any] = content

    @staticmethod
    def from_file(filename: Path):
        """Check an Hexfile, and if it's valide, return a tuple with useful information

        Args:
            filename (filepath): the relative or absolute path of the file to pase

        Returns:
            (boolean, int, int, dict): First return indicates if it's a valid file,
            second and third the x and y position in grid, and the last a bunch of
            values extracted from the file
        """
        # The file must exists
        if not os.path.isfile(filename):
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), filename)

        # The filename should follow the pattern XXYY-<some_name>.md
        basename = os.path.basename(filename)
        match = re.match(r'^(-?\d{2})(-?\d{2})-.*\.md$', basename)
        if match is None:
            raise ValueError(f'{basename} is not a valid basename.')

        col = int(match.group(2))
        row = int(match.group(1))
        content: Dict[str:Any] = {}

        with open(filename, 'r', encoding="utf-8") as hex_file:
            content = frontmatter.load(hex_file).metadata

        return TileMetadata(col, row, content)

    def __getitem__(self, key: str) -> Any:
        return self.content[key]

    def get(self, key: str, default: Any) -> Any:
        return self.content.get(key, default)