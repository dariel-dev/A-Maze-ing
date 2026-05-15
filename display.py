"""Interactive ASCII display for A-Maze-ing.

Rendering uses Unicode box-drawing characters and ANSI 24-bit colours.
The user navigates via a numbered menu — works on any TTY without raw
input or extra dependencies.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from mazegen import Direction, path_coords

if TYPE_CHECKING:
    from a_maze_ing import Config
    from mazegen import Grid, MazeGenerator


@dataclass(frozen=True)
class Glyphs:
    """Character set used to draw the maze."""

    corner: str
    wall_h: str
    wall_v: str
    empty: str
    path: str
    entry: str
    exit: str
    logo: str


LINE_GLYPHS = Glyphs(
    corner="+",
    wall_h="───",
    wall_v="│",
    empty="   ",
    path=" ★ ",
    entry=" S ",
    exit=" E ",
    logo="███",
)


_CORNERS = {
    (False, False, False, False): " ",
    (True, False, False, False): "│",
    (False, True, False, False): "─",
    (False, False, True, False): "│",
    (False, False, False, True): "─",
    (True, True, False, False): "└",
    (True, False, True, False): "│",
    (True, False, False, True): "┘",
    (False, True, True, False): "┌",
    (False, True, False, True): "─",
    (False, False, True, True): "┐",
    (True, True, True, False): "├",
    (True, True, False, True): "┴",
    (True, False, True, True): "┤",
    (False, True, True, True): "┬",
    (True, True, True, True): "┼",
}


@dataclass(frozen=True)
class Theme:
    """A colour theme for the rendered maze."""

    name: str
    wall: str
    logo: str
    path: str
    entry: str
    exit: str


RESET = "\x1b[0m"


def _rgb(r: int, g: int, b: int) -> str:
    return f"\x1b[38;2;{r};{g};{b}m"


THEMES: tuple[Theme, ...] = (
    Theme(
        name="emerald",
        wall=_rgb(60, 180, 110),
        logo=_rgb(240, 200, 60),
        path=_rgb(220, 110, 200),
        entry=_rgb(255, 255, 255),
        exit=_rgb(250, 80, 80),
    ),
    Theme(
        name="ocean",
        wall=_rgb(100, 180, 230),
        logo=_rgb(255, 230, 120),
        path=_rgb(200, 80, 200),
        entry=_rgb(255, 255, 255),
        exit=_rgb(255, 100, 100),
    ),
    Theme(
        name="amber",
        wall=_rgb(220, 160, 70),
        logo=_rgb(255, 100, 100),
        path=_rgb(110, 200, 230),
        entry=_rgb(255, 255, 255),
        exit=_rgb(120, 220, 120),
    ),
    Theme(
        name="violet",
        wall=_rgb(170, 100, 230),
        logo=_rgb(250, 200, 80),
        path=_rgb(120, 230, 180),
        entry=_rgb(255, 255, 255),
        exit=_rgb(250, 100, 100),
    ),
    Theme(
        name="rose",
        wall=_rgb(240, 130, 180),
        logo=_rgb(255, 230, 100),
        path=_rgb(100, 220, 220),
        entry=_rgb(255, 255, 255),
        exit=_rgb(250, 70, 70),
    ),
    Theme(
        name="crimson",
        wall=_rgb(220, 60, 60),
        logo=_rgb(255, 220, 100),
        path=_rgb(255, 255, 255),
        entry=_rgb(140, 240, 140),
        exit=_rgb(255, 150, 50),
    ),
    Theme(
        name="forest",
        wall=_rgb(80, 140, 70),
        logo=_rgb(220, 200, 70),
        path=_rgb(230, 180, 100),
        entry=_rgb(255, 255, 255),
        exit=_rgb(250, 80, 80),
    ),
    Theme(
        name="neon",
        wall=_rgb(255, 80, 220),
        logo=_rgb(80, 255, 220),
        path=_rgb(80, 220, 255),
        entry=_rgb(255, 255, 80),
        exit=_rgb(255, 80, 80),
    ),
    Theme(
        name="ice",
        wall=_rgb(150, 220, 240),
        logo=_rgb(255, 240, 180),
        path=_rgb(250, 130, 200),
        entry=_rgb(255, 255, 255),
        exit=_rgb(255, 100, 100),
    ),
    Theme(
        name="gold",
        wall=_rgb(220, 180, 60),
        logo=_rgb(255, 240, 200),
        path=_rgb(110, 180, 220),
        entry=_rgb(255, 255, 255),
        exit=_rgb(220, 50, 50),
    ),
)


def _h_wall(grid: "Grid", cx: int, cy: int) -> bool:
    """Is there a horizontal wall segment east-of-corner (cx, cy)?"""
    if cx >= grid.width:
        return False
    if cy == 0 or cy == grid.height:
        return True
    return grid.cell(cx, cy - 1).has_wall(Direction.S)


def _v_wall(grid: "Grid", cx: int, cy: int) -> bool:
    """Is there a vertical wall segment south-of-corner (cx, cy)?"""
    if cy >= grid.height:
        return False
    if cx == 0 or cx == grid.width:
        return True
    return grid.cell(cx - 1, cy).has_wall(Direction.E)


def _corner_char(grid: "Grid", cx: int, cy: int) -> str:
    """Return the right box-drawing char at corner (cx, cy)."""
    n = cy > 0 and _v_wall(grid, cx, cy - 1)
    e = _h_wall(grid, cx, cy)
    s = _v_wall(grid, cx, cy)
    w = cx > 0 and _h_wall(grid, cx - 1, cy)
    return _CORNERS[(n, e, s, w)]


def render(
    gen: "MazeGenerator",
    theme: Theme,
    show_path: bool,
) -> str:
    """Return the maze rendered as a string."""
    grid = gen.grid
    if show_path:
        path_set: set[tuple[int, int]] = set(
            path_coords(grid, gen.entry, gen.exit)
        )
    else:
        path_set = set()

    out: list[str] = []
    wall = theme.wall
    logo_col = theme.logo
    path_col = theme.path
    entry_col = theme.entry
    exit_col = theme.exit
    g = LINE_GLYPHS

    def corner(cx: int, cy: int) -> str:
        return _corner_char(grid, cx, cy)

    top_parts = [wall, corner(0, 0)]
    for x in range(grid.width):
        top_parts.append(g.wall_h)
        top_parts.append(corner(x + 1, 0))
    top_parts.append(RESET)
    out.append("".join(top_parts))

    for y in range(grid.height):
        mid = wall + g.wall_v + RESET
        bot_parts = [wall, corner(0, y + 1)]
        for x in range(grid.width):
            cell = grid.cell(x, y)
            if cell.is_logo:
                token = logo_col + g.logo + RESET
            elif cell.is_entry:
                token = entry_col + g.entry + RESET
            elif cell.is_exit:
                token = exit_col + g.exit + RESET
            elif (x, y) in path_set:
                token = "\x1b[1m" + path_col + g.path + RESET
            else:
                token = g.empty
            mid += token
            if cell.has_wall(Direction.E):
                mid += wall + g.wall_v + RESET
            else:
                mid += " "
            if cell.has_wall(Direction.S):
                bot_parts.append(g.wall_h)
            else:
                bot_parts.append(g.empty)
            bot_parts.append(corner(x + 1, y + 1))
        bot_parts.append(RESET)
        out.append(mid)
        out.append("".join(bot_parts))
    return "\n".join(out)


def _random_theme(current: int) -> int:
    if len(THEMES) <= 1:
        return current
    options = [i for i in range(len(THEMES)) if i != current]
    return random.choice(options)


def interactive(gen: "MazeGenerator", cfg: "Config") -> None:
    """Run the menu-driven interactive loop."""
    from a_maze_ing import run

    theme_idx = next(
        (i for i, t in enumerate(THEMES) if t.name == "crimson"),
        0,
    )
    show_path = True
    print()
    while True:
        theme = THEMES[theme_idx]
        print(render(gen, theme, show_path))
        print()
        path_state = "on" if show_path else "off"
        logo_state = "embedded" if gen.has_logo else "omitted (too small)"
        print(
            f"=== A-Maze-ing ===   theme={theme.name}   path={path_state}"
        )
        print(f"Logo: {logo_state}")
        print("1. Regenerate maze")
        print("2. Show/Hide path")
        print("3. Change wall color")
        print("4. Quit")
        try:
            choice = input("Choice? (1-4): ").strip()
        except EOFError:
            print()
            return
        if choice == "1":
            gen = run(cfg)
        elif choice == "2":
            show_path = not show_path
        elif choice == "3":
            theme_idx = _random_theme(theme_idx)
        elif choice == "4":
            print("bye.")
            return
        else:
            print("unknown choice")
        print()
