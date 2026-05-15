# mazegen

Reusable maze-generation library for the A-Maze-ing project.

## Install

```bash
pip install mazegen-1.0.0-py3-none-any.whl
```

Or, from a checkout of the source tree:

```bash
pip install build
python -m build --wheel
pip install dist/mazegen-1.0.0-py3-none-any.whl
```

## Basic usage

```python
from mazegen import MazeGenerator, write_output

gen = MazeGenerator(
    width=20,
    height=15,
    entry=(0, 0),
    exit_pt=(19, 14),
    perfect=True,
    seed=42,
)
gen.generate()

print(gen.solution())            # "SSEESSE..."
write_output("maze.txt", gen.grid, gen.entry, gen.exit, gen.solution())
```

## Custom parameters

| Parameter | Type | Meaning |
|---|---|---|
| `width`, `height` | `int` | Maze dimensions in cells. |
| `entry`, `exit_pt` | `tuple[int, int]` | Must differ; must be inside the grid; must not overlap the 42 logo. |
| `perfect` | `bool` | When True, exactly one path between any two cells. |
| `seed` | `int \| None` | RNG seed for reproducibility. `None` for fresh random. |
| `loop_probability` | `float` | Non-perfect mode only; chance of attempting each extra wall removal. |

## Accessing the maze and the solution

```python
maze = gen.grid                   # mazegen.Grid
cell = maze.cell(3, 5)            # mazegen.Cell at (x=3, y=5)
cell.walls                        # int 0..15; 1=closed in N/E/S/W bits
cell.has_wall(Direction.N)        # bool
cell.is_logo                      # True if part of the "42" pattern
cell.is_entry, cell.is_exit       # markers

path_letters = gen.solution()                 # "SESESS..."
from mazegen import path_coords
path_cells = path_coords(maze, gen.entry, gen.exit)   # [(x, y), ...]
```

`MazeGenerator.grid` is the canonical access point; the spec output file
format is produced by :func:`mazegen.write_output`.
