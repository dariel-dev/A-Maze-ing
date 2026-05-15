"""Maze construction using iterative randomised Prim's algorithm.

The :class:`MazeGenerator` orchestrates three phases:

1. Reserve the "42" logo cells: they are flagged ``is_logo`` and kept
   fully walled. The maze is generated *around* them.
2. Grow a spanning tree over the remaining cells with iterative Prim's,
   picking a random wall from the active frontier and carving through it
   whenever it lands on an unvisited, non-logo cell.
3. If ``perfect=False``, run a controlled loop-injection pass that
   knocks down extra walls subject to the spec's "no 3×3 open area"
   constraint (subject §4.4).

The result is a valid maze: borders closed, walls coherent, all
non-logo cells in a single connected component, and (in non-perfect
mode) loops added without producing fully-open 3×3 blocks.
"""

from __future__ import annotations

import random

from .grid import (
    ALL_DIRECTIONS,
    Cell,
    Direction,
    Grid,
    opposite,
)
from .solver import shortest_path


LOGO_PATTERN: tuple[tuple[int, ...], ...] = (
    (1, 0, 1, 0, 1, 1, 1),
    (1, 0, 1, 0, 0, 0, 1),
    (1, 1, 1, 0, 1, 1, 1),
    (0, 0, 1, 0, 1, 0, 0),
    (0, 0, 1, 0, 1, 1, 1),
)

LOGO_HEIGHT = len(LOGO_PATTERN)
LOGO_WIDTH = len(LOGO_PATTERN[0])
_LOGO_MARGIN = 1


class MazeGenerator:
    """Build a valid A-Maze-ing maze from explicit parameters."""

    def __init__(
        self,
        width: int,
        height: int,
        entry: tuple[int, int],
        exit_pt: tuple[int, int],
        *,
        perfect: bool = True,
        seed: int | None = None,
        loop_probability: float = 0.18,
    ) -> None:
        """Validate inputs, build the empty grid, and place the 42 logo.

        Args:
            width: Maze width in cells, must be positive.
            height: Maze height in cells, must be positive.
            entry: ``(x, y)`` of the entry cell.
            exit_pt: ``(x, y)`` of the exit cell. Must differ from entry.
            perfect: When True, the maze has exactly one entry→exit path.
            seed: Optional integer seed for reproducible runs.
            loop_probability: For non-perfect mode, the probability of
                trying to remove each interior wall during the loop pass.
        """
        if width <= 0 or height <= 0:
            raise ValueError(f"invalid maze size {width}x{height}")
        if entry == exit_pt:
            raise ValueError("entry and exit must be different cells")
        for label, point in (("entry", entry), ("exit", exit_pt)):
            px, py = point
            if not (0 <= px < width and 0 <= py < height):
                raise ValueError(
                    f"{label} {point} out of bounds for {width}x{height}"
                )
        if not 0.0 <= loop_probability <= 1.0:
            raise ValueError(
                f"loop_probability must be in [0, 1], got {loop_probability}"
            )

        self.width = width
        self.height = height
        self.entry = entry
        self.exit = exit_pt
        self.perfect = perfect
        self.loop_probability = loop_probability
        self._seed = seed
        self._rng = random.Random(seed)
        self._logo_placed = False

        self.grid = Grid(width, height)
        self._place_logo()
        self._mark_endpoints()

    @property
    def seed(self) -> int | None:
        """Return the RNG seed if one was supplied."""
        return self._seed

    @property
    def has_logo(self) -> bool:
        """Return True if the 42 pattern fit inside this maze."""
        return self._logo_placed

    def generate(self) -> None:
        """Carve the maze in place. Subsequent calls re-randomise it."""
        for _, _, cell in self.grid.iter_cells():
            if not cell.is_logo:
                cell.walls = 0xF
        self._prim()
        if not self.perfect:
            self._inject_loops()

    def solution(self) -> str:
        """Return the BFS shortest-path string from entry to exit."""
        return shortest_path(self.grid, self.entry, self.exit)

    def _place_logo(self) -> None:
        """Mark the 42 cells as protected if the maze is large enough."""
        min_w = LOGO_WIDTH + 2 * _LOGO_MARGIN
        min_h = LOGO_HEIGHT + 2 * _LOGO_MARGIN
        if self.width < min_w or self.height < min_h:
            print(
                "[info] maze too small to embed the 42 pattern; skipping logo "
                f"(need at least {min_w}x{min_h})"
            )
            return
        origin_x = (self.width - LOGO_WIDTH) // 2
        origin_y = (self.height - LOGO_HEIGHT) // 2
        for ly, row in enumerate(LOGO_PATTERN):
            for lx, value in enumerate(row):
                if value:
                    self.grid.cell(origin_x + lx, origin_y + ly).is_logo = True
        self._logo_placed = True

    def _mark_endpoints(self) -> None:
        """Sanity-check endpoints and mark them on the grid."""
        ex, ey = self.entry
        xx, xy = self.exit
        entry_cell = self.grid.cell(ex, ey)
        exit_cell = self.grid.cell(xx, xy)
        if entry_cell.is_logo:
            raise ValueError(
                f"entry {self.entry} lies on a 42 logo cell; "
                "pick another cell or use a larger maze"
            )
        if exit_cell.is_logo:
            raise ValueError(
                f"exit {self.exit} lies on a 42 logo cell; "
                "pick another cell or use a larger maze"
            )
        entry_cell.is_entry = True
        exit_cell.is_exit = True

    def _prim(self) -> None:
        """Iterative randomised Prim's over non-logo cells."""
        start = self.entry
        in_tree: set[tuple[int, int]] = {start}
        frontier: list[tuple[tuple[int, int], Direction]] = []
        self._push_frontier(start, in_tree, frontier)

        while frontier:
            idx = self._rng.randrange(len(frontier))
            (x, y), d = frontier[idx]
            frontier[idx] = frontier[-1]
            frontier.pop()
            n = self.grid.neighbour(x, y, d)
            if n is None or n in in_tree:
                continue
            if self.grid.cell(*n).is_logo:
                continue
            self.grid.carve(x, y, d)
            in_tree.add(n)
            self._push_frontier(n, in_tree, frontier)

        for x, y, cell in self.grid.iter_cells():
            if cell.is_logo or (x, y) in in_tree:
                continue
            raise RuntimeError(
                f"cell {(x, y)} is unreachable — the 42 logo is "
                "partitioning the maze; pick a larger maze size"
            )

    def _push_frontier(
        self,
        origin: tuple[int, int],
        in_tree: set[tuple[int, int]],
        frontier: list[tuple[tuple[int, int], Direction]],
    ) -> None:
        ox, oy = origin
        for d in ALL_DIRECTIONS:
            n = self.grid.neighbour(ox, oy, d)
            if n is None or n in in_tree:
                continue
            if self.grid.cell(*n).is_logo:
                continue
            frontier.append((origin, d))

    def _inject_loops(self) -> None:
        """Knock down extra walls subject to the no-3×3-open invariant."""
        candidates: list[tuple[int, int, Direction]] = []
        for x, y, cell in self.grid.iter_cells():
            if cell.is_logo:
                continue
            for d in (Direction.E, Direction.S):
                if not cell.has_wall(d):
                    continue
                n = self.grid.neighbour(x, y, d)
                if n is None or self.grid.cell(*n).is_logo:
                    continue
                candidates.append((x, y, d))

        self._rng.shuffle(candidates)
        for x, y, d in candidates:
            if self._rng.random() > self.loop_probability:
                continue
            cell = self.grid.cell(x, y)
            n = self.grid.neighbour(x, y, d)
            if n is None:
                continue
            n_cell = self.grid.cell(*n)
            self.grid.carve(x, y, d)
            if self._creates_3x3_open(x, y, d):
                cell.close_wall(d)
                n_cell.close_wall(opposite(d))

    def _creates_3x3_open(
        self, x: int, y: int, d: Direction
    ) -> bool:
        """Check whether the freshly-opened wall caused a 3×3 open area."""
        cells: list[tuple[int, int]] = [(x, y)]
        n = self.grid.neighbour(x, y, d)
        if n is not None:
            cells.append(n)
        affected: set[tuple[int, int]] = set()
        for cx, cy in cells:
            for bx in range(cx - 2, cx + 1):
                for by in range(cy - 2, cy + 1):
                    if (
                        0 <= bx <= self.width - 3
                        and 0 <= by <= self.height - 3
                    ):
                        affected.add((bx, by))
        return any(self._is_block_fully_open(bx, by) for bx, by in affected)

    def _is_block_fully_open(self, x0: int, y0: int) -> bool:
        """Return True if the 3×3 block at (x0, y0) has no inner walls."""
        block_cells: list[Cell] = []
        for j in range(3):
            for i in range(3):
                block_cells.append(self.grid.cell(x0 + i, y0 + j))
        if any(c.is_logo for c in block_cells):
            return False
        for j in range(3):
            for i in range(3):
                cell = block_cells[j * 3 + i]
                if i < 2 and cell.has_wall(Direction.E):
                    return False
                if j < 2 and cell.has_wall(Direction.S):
                    return False
        return True
