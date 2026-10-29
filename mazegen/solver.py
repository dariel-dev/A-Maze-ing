"""Breadth-first shortest path on a generated maze.

Two helpers are exposed:
    * :func:`shortest_path` — returns the path as an "NESW" letter string.
    * :func:`path_coords`  — returns the list of (x, y) cells along the path.
Both raise :class:`ValueError` when *goal* is unreachable from *start*.
"""

from __future__ import annotations

from collections import deque

from .grid import ALL_DIRECTIONS, Direction, Grid


def _bfs(
    grid: Grid,
    start: tuple[int, int],
    goal: tuple[int, int],
) -> dict[tuple[int, int], tuple[tuple[int, int], Direction]]:
    """Run BFS from *start* until *goal* is reached; return the parent map."""
    parent: dict[tuple[int, int], tuple[tuple[int, int], Direction]] = {}
    queue: deque[tuple[int, int]] = deque([start])
    visited: set[tuple[int, int]] = {start}

    while queue:
        x, y = queue.popleft()
        if (x, y) == goal:
            return parent
        cell = grid.cell(x, y)
        for d in ALL_DIRECTIONS:
            if cell.has_wall(d):
                continue
            n = grid.neighbour(x, y, d)
            if n is None or n in visited:
                continue
            visited.add(n)
            parent[n] = ((x, y), d)
            queue.append(n)

    raise ValueError(f"no path from {start} to {goal}")


def _validate_endpoints(
    grid: Grid,
    start: tuple[int, int],
    goal: tuple[int, int],
) -> None:
    """Reject path endpoints outside the grid."""
    for x, y in (start, goal):
        if not grid.in_bounds(x, y):
            raise ValueError(
                f"cell coordinates ({x},{y}) are outside grid bounds "
                f"{grid.width}x{grid.height}"
            )


def shortest_path(
    grid: Grid,
    start: tuple[int, int],
    goal: tuple[int, int],
) -> str:
    """Return the BFS shortest path from *start* to *goal* as letters."""
    _validate_endpoints(grid, start, goal)
    if start == goal:
        return ""
    parent = _bfs(grid, start, goal)
    steps: list[str] = []
    cur = goal
    while cur != start:
        prev, d = parent[cur]
        name = d.name
        assert name is not None
        steps.append(name)
        cur = prev
    steps.reverse()
    return "".join(steps)


def path_coords(
    grid: Grid,
    start: tuple[int, int],
    goal: tuple[int, int],
) -> list[tuple[int, int]]:
    """Return the BFS shortest path as a list of (x, y) cells inclusive."""
    _validate_endpoints(grid, start, goal)
    if start == goal:
        return [start]
    parent = _bfs(grid, start, goal)
    coords: list[tuple[int, int]] = [goal]
    while coords[-1] != start:
        prev, _ = parent[coords[-1]]
        coords.append(prev)
    coords.reverse()
    return coords
