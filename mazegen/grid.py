"""Grid and cell primitives shared by the rest of the package.

The wall encoding follows the spec exactly:
    bit 0 (LSB) = North, bit 1 = East, bit 2 = South, bit 3 = West.
A bit set to 1 means the wall is *closed*.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntFlag
from typing import Iterator


class Direction(IntFlag):
    """Cardinal direction encoded as its spec bit value."""

    N = 1
    E = 2
    S = 4
    W = 8


ALL_DIRECTIONS: tuple[Direction, ...] = (
    Direction.N,
    Direction.E,
    Direction.S,
    Direction.W,
)

_VECTOR: dict[Direction, tuple[int, int]] = {
    Direction.N: (0, -1),
    Direction.E: (1, 0),
    Direction.S: (0, 1),
    Direction.W: (-1, 0),
}

_OPPOSITE: dict[Direction, Direction] = {
    Direction.N: Direction.S,
    Direction.E: Direction.W,
    Direction.S: Direction.N,
    Direction.W: Direction.E,
}


def vector(d: Direction) -> tuple[int, int]:
    """Return the (dx, dy) unit step for direction *d*."""
    return _VECTOR[d]


def opposite(d: Direction) -> Direction:
    """Return the direction opposite to *d*."""
    return _OPPOSITE[d]


@dataclass
class Cell:
    """A single cell of the maze."""

    walls: int = 0xF
    is_logo: bool = False
    is_entry: bool = False
    is_exit: bool = False

    def has_wall(self, d: Direction) -> bool:
        """Return True when wall *d* is closed."""
        return bool(self.walls & int(d))

    def open_wall(self, d: Direction) -> None:
        """Open wall *d* on this cell (keeps the mask in 0..15)."""
        self.walls &= 0xF ^ int(d)

    def close_wall(self, d: Direction) -> None:
        """Close wall *d* on this cell."""
        self.walls |= int(d)


@dataclass
class Grid:
    """Rectangular grid of :class:`Cell` objects."""

    width: int
    height: int
    cells: list[list[Cell]] = field(init=False)

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError(
                "grid dimensions must be positive, got "
                f"{self.width}x{self.height}"
            )
        self.cells = [
            [Cell() for _ in range(self.width)] for _ in range(self.height)
        ]

    def in_bounds(self, x: int, y: int) -> bool:
        """Return True if (x, y) is inside the grid."""
        return 0 <= x < self.width and 0 <= y < self.height

    def cell(self, x: int, y: int) -> Cell:
        """Return the cell at (x, y), rejecting out-of-bounds coordinates."""
        if not self.in_bounds(x, y):
            raise ValueError(
                f"cell coordinates ({x},{y}) are outside grid bounds "
                f"{self.width}x{self.height}"
            )
        return self.cells[y][x]

    def neighbour(
        self, x: int, y: int, d: Direction
    ) -> tuple[int, int] | None:
        """Return the cell adjacent to (x, y) in direction *d*, or None."""
        if not self.in_bounds(x, y):
            return None
        dx, dy = vector(d)
        nx, ny = x + dx, y + dy
        return (nx, ny) if self.in_bounds(nx, ny) else None

    def carve(self, x: int, y: int, d: Direction) -> None:
        """Open the wall between (x, y) and its neighbour in direction *d*.

        Both cells are updated so wall coherence is preserved.
        """
        n = self.neighbour(x, y, d)
        if n is None:
            raise ValueError(
                f"no neighbour of ({x},{y}) in direction {d.name}"
            )
        self.cell(x, y).open_wall(d)
        self.cell(*n).open_wall(opposite(d))

    def iter_cells(self) -> Iterator[tuple[int, int, Cell]]:
        """Yield ``(x, y, cell)`` for every cell, in row-major order."""
        for y in range(self.height):
            for x in range(self.width):
                yield x, y, self.cells[y][x]
