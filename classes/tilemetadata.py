"""tilemedata.py

Define Metadata and useful types to work with tiles
"""
import errno
import logging
import os
import re
from enum import Enum, EnumMeta, auto
from pathlib import Path
from typing import Any, Dict, List

import frontmatter
import yaml


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

    @staticmethod
    def valid_zone(zone) -> bool:
        """
        Check if the passed zone is valid
        Args:
            zone (Cardinal | str): The zone to check

        Returns:
            bool: true, except for W and O, which are not valid zone.
        """
        check = None
        if isinstance(zone, Cardinal):
            check = zone
        if isinstance(zone, str):
            try:
                check = Cardinal[zone]
            except KeyError:
                return False
        if not check:
            return False

        return check not in [
            Cardinal.E,
            Cardinal.W]


class TileMetadata:
    """Metadata for a tile
    """

    def __init__(self, col: int, row: int, content: Dict[str, Any] = None) -> None:
        self.col = col
        self.row = row
        self.content = {}
        if content:
            self.content = content
        self.icon = None
        self.zones = self.content.get('zone', []) if isinstance(
            self.content.get('zone', []), List) else [
            self.content.get('zone', [])]

        # Icon from Building
        icon_path = self.content.get(
            'icon', None)
        if icon_path:
            self.icon = 'building/' + icon_path

        # icon from Terrain
        if not icon_path:
            center_tile = [terrain for terrain in self.content.get("terrain", {}).get(
                "mixed", []) if 'C' in terrain.get("sides", [])]
            if not center_tile:
                icon_path = self.content.get("terrain", {}).get("type", None)
            else:
                icon_path = center_tile[0].get("type", None)
            if icon_path:
                self.icon = 'terrain/' + icon_path

    @staticmethod
    def from_file(filename: Path):
        """Check an Hexfile, and if it's valide, return a tuple with useful information

        Args:
            filename (filepath): the relative or absolute path of the file to parse

        Returns:
            List[TileMetadata]: One or several TileMetadata described in the file
        """
        # The file must exists
        if not os.path.isfile(filename):
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), filename)

        # The filename should follow the pattern XXYY-<some_name>.md
        basename = os.path.basename(filename)
        match_md = re.match(r'^(-?\d{2})(-?\d{2})(?:-|_).*\.md$', basename)
        match_yaml = re.match(r'^.*\.(?:yaml|yml)$', basename)

        if match_md is not None:
            col = int(match_md.group(2))
            row = int(match_md.group(1))
            content: Dict[str:Any] = {}

            with open(filename, 'r', encoding="utf-8") as hex_file:
                content = frontmatter.load(hex_file).metadata

            return [TileMetadata(col, row, content)]
        if match_yaml is not None:
            result = []
            with open(filename, 'r', encoding="utf-8") as hex_file:
                for doc in yaml.load_all(hex_file, Loader=yaml.Loader):
                    for (key, value) in doc.items():
                        match_xy = re.match(r'^(-?\d{2})(-?\d{2})$', key)
                        if match_xy is None:
                            logging.warning(
                                '%s in file %s is not a valid coordinate', key, filename)
                            continue
                        col = int(match_xy.group(2))
                        row = int(match_xy.group(1))
                        result.append(TileMetadata(col, row, value))
            return result

        # No matching case
        raise ValueError(f'{basename} is not a valid basename.')

    def __getitem__(self, key: str) -> Any:
        return self.content[key]

    def get(self, key: str, default: Any) -> Any:
        """Access to metadata
        Args:
            key (str): Key of the metadata item
            default (Any): Default value if it doesn't exists

        Returns:
            Any: The item
        """
        return self.content.get(key, default)
