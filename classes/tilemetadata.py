import errno
import os
import re
from pathlib import Path

import frontmatter


class TileMetada:
    def __init__(self, filename: Path) -> None:
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

        self.col = int(match.group(2))
        self.row = int(match.group(1))

        with open(filename, 'r', encoding="utf-8") as hex_file:
            self.content = frontmatter.load(hex_file).content
