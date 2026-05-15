"""Spec output-file serialisation.

Output layout (subject §4.5):
    * One hex digit per cell, MSB→LSB encoding W S E N closed-walls.
    * One row per line, no separator between digits.
    * Empty line.
    * Entry "x,y", exit "x,y", path "NESW…", each on its own line.
    * Every line, including the last, ends with ``\\n``.
"""

from __future__ import annotations

from pathlib import Path

from .grid import Grid


_HEX_CHARS = "0123456789ABCDEF"


def cell_to_hex(walls: int) -> str:
    """Encode a wall mask (0..15) as a single uppercase hex digit."""
    if not 0 <= walls <= 0xF:
        raise ValueError(f"wall mask out of range: {walls}")
    return _HEX_CHARS[walls]


def hex_to_walls(ch: str) -> int:
    """Decode a single hex digit to a wall mask 0..15."""
    if len(ch) != 1 or ch.upper() not in _HEX_CHARS:
        raise ValueError(f"invalid hex digit: {ch!r}")
    return int(ch, 16)


def grid_to_text(
    grid: Grid,
    entry: tuple[int, int],
    exit_pt: tuple[int, int],
    path: str,
) -> str:
    """Render the grid plus solution into the spec text format."""
    lines: list[str] = []
    for y in range(grid.height):
        lines.append(
            "".join(
                cell_to_hex(grid.cell(x, y).walls)
                for x in range(grid.width)
            )
        )
    lines.append("")
    lines.append(f"{entry[0]},{entry[1]}")
    lines.append(f"{exit_pt[0]},{exit_pt[1]}")
    lines.append(path)
    return "\n".join(lines) + "\n"


def write_output(
    path_file: str,
    grid: Grid,
    entry: tuple[int, int],
    exit_pt: tuple[int, int],
    path: str,
) -> None:
    """Write the maze output file at *path_file* in UTF-8."""
    text = grid_to_text(grid, entry, exit_pt, path)
    Path(path_file).write_text(text, encoding="utf-8", newline="\n")
