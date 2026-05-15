"""mazegen — random maze generation library.

Public entry points:
    :class:`MazeGenerator` — build a maze from explicit parameters.
    :func:`shortest_path` — BFS solver returning an N/E/S/W string.
    :func:`path_coords`  — BFS solver returning a list of coordinates.
    :func:`write_output`  — serialise a generated maze to the spec text format.

A short usage walk-through lives in ``mazegen/README.md``.
"""

from .generator import (
    LOGO_HEIGHT,
    LOGO_PATTERN,
    LOGO_WIDTH,
    MazeGenerator,
)
from .grid import Cell, Direction, Grid
from .io_format import cell_to_hex, grid_to_text, hex_to_walls, write_output
from .solver import path_coords, shortest_path

__all__ = [
    "Cell",
    "Direction",
    "Grid",
    "LOGO_HEIGHT",
    "LOGO_PATTERN",
    "LOGO_WIDTH",
    "MazeGenerator",
    "cell_to_hex",
    "grid_to_text",
    "hex_to_walls",
    "path_coords",
    "shortest_path",
    "write_output",
]
__version__ = "1.0.0"
