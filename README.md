*This activity has been created as part of the 42 curriculum by ddervish, dshabani.*

# A-Maze-ing

A Python maze generator with an interactive terminal renderer. The program reads a configuration file, generates a maze (perfect or non-perfect), writes the spec-compliant output file with the BFS shortest path, and lets you explore the result in your terminal.

## Description

`a_maze_ing.py` builds mazes using an iterative randomised **Prim's algorithm** over the grid's cells. A "42" pattern is reserved at the centre as fully-closed cells and the algorithm grows the spanning tree around it. In non-perfect mode an extra pass randomly removes additional walls while preserving the "no 3×3 open area" rule of the subject. The result is always:

- bordered (outer walls always closed);
- wall-coherent (neighbouring cells agree on every shared wall);
- fully connected over non-logo cells;
- equipped with a BFS-computed shortest path from entry to exit.

The reusable generator code lives in the standalone `mazegen/` package, packaged as `mazegen-1.0.0-py3-none-any.whl` at the repository root so it can be `pip install`'d directly into any future project.

## Instructions

### Requirements

- Python 3.10 or later.
- A POSIX terminal that understands 24-bit ANSI colour escapes.

### Installation

```bash
make install
```

This creates `maze_env/`, upgrades `pip`, installs `flake8`, `mypy`, `build`, and then `pip install`s `mazegen-1.0.0-py3-none-any.whl` from the repo root.

### Running

```bash
make run                       # uses config.txt
# or directly:
python3 a_maze_ing.py config.txt
# or with a different filename:
python3 a_maze_ing.py my_other_config.txt
```

The maze is written to the file named by `OUTPUT_FILE` on the first generation and on every subsequent regeneration from the menu.

### Debug mode

```bash
make debug
```

Launches the script under `pdb`.

### Linting

```bash
make lint           # flake8 + mypy with the required flags
make lint-strict    # flake8 + mypy --strict
```

### Cleaning

```bash
make clean
```

Removes `maze_env/`, `build/`, `dist/`, `__pycache__/`, and `.mypy_cache/`.

### Rebuilding the wheel

```bash
make build
```

Produces a fresh `mazegen-1.0.0-py3-none-any.whl` at the repo root from the current `mazegen/` sources.

## Configuration file

The complete structure and format of the config file:

| Key | Type | Required | Example |
|---|---|---|---|
| `WIDTH` | positive integer | yes | `WIDTH=20` |
| `HEIGHT` | positive integer | yes | `HEIGHT=15` |
| `ENTRY` | `x,y` integers | yes | `ENTRY=0,0` |
| `EXIT` | `x,y` integers | yes | `EXIT=19,14` |
| `OUTPUT_FILE` | string | yes | `OUTPUT_FILE=output_maze.txt` |
| `PERFECT` | `True` or `False` | yes | `PERFECT=True` |
| `SEED` | integer (optional) | no | `SEED=42` |

Rules:

- One `KEY=VALUE` pair per line.
- Lines beginning with `#` are comments; blank lines are ignored.
- Whitespace around `=` is allowed.
- `ENTRY` and `EXIT` must be different cells, both inside the grid, neither overlapping the "42" pattern.
- Empty `SEED` (or omitted line) → random RNG seed. Any non-empty integer → reproducible run.

A complete `config.txt` is committed at the repository root.

## Output file format

```
<hex-row 0>\n
<hex-row 1>\n
...
\n
<entry-x>,<entry-y>\n
<exit-x>,<exit-y>\n
<path string of N/E/S/W>\n
```

Each cell is one hex digit. Bit 0 = N, 1 = E, 2 = S, 3 = W; a set bit means the wall is closed. Every line, including the last, ends with `\n`. The output is accepted by the `output_validator.py` script shipped alongside the subject.

## Visual display & controls

The interactive terminal display uses ASCII box-drawing characters plus ANSI colour. From the menu you can:

| Choice | Action |
|---|---|
| 1 | Regenerate the maze (overwrites the output file) |
| 2 | Show/hide the shortest path |
| 3 | Switch to another colour theme (emerald, ocean, amber, violet, rose, crimson, forest, neon, ice, gold) |
| 4 | Quit |

Entry is rendered as `S`, exit as `E`, the path as `★`, and the "42" logo as solid `███` blocks in a contrasting colour.

## Maze generation algorithm

**Iterative randomised Prim's** is used for the perfect-maze build.

- Reserve all "42" logo cells (`is_logo = True`); never carve into them.
- Mark the entry cell as in-tree, push every wall to neighbours of the entry to the frontier list.
- While the frontier is non-empty:
  - Pop a *random* wall from the frontier.
  - If the cell on the far side is not yet in-tree and is not part of the logo, carve that wall and add the new cell's outgoing walls to the frontier.
- The result is a spanning tree over the non-logo cells — one unique path between any two of them.

For non-perfect mazes a second pass iterates each interior wall in a random order and, with probability `loop_probability`, tries to remove it. The change is committed only when no 3×3 cell block becomes fully open after the removal.

### Why Prim's?

- **No recursion limit issues** — fully iterative, fine for large mazes (the recursive backtracker used by other implementations needs `sys.setrecursionlimit` bumps).
- **Naturally compatible with reserved cells**: protected (logo) cells are simply never added to the frontier.
- **Random-uniform wall selection** produces visually busier, less "snake-like" mazes than recursive DFS, which is interesting for the visualisation step.
- **Easy to seed** — pass an integer `SEED` and the same maze is reconstructed deterministically (the RNG state is the only source of non-determinism).

### 42 logo

A 5×7 pattern (`mazegen.LOGO_PATTERN`) is placed in the centre of the grid before generation. Its "1" cells become `is_logo` cells, kept fully closed and unreachable from the maze paths — they remain isolated by design, as the subject explicitly allows. If the grid is too small to host the pattern plus a 1-cell border, the program prints an info message and continues without the logo.

## Code reusability

The maze logic is exposed through the `mazegen` package and is fully importable without depending on `display.py` or `a_maze_ing.py`.

```python
from mazegen import MazeGenerator, write_output

gen = MazeGenerator(
    width=20, height=15,
    entry=(0, 0), exit_pt=(19, 14),
    perfect=True, seed=42,
)
gen.generate()

# Access the structure
grid = gen.grid                       # mazegen.Grid
cell = grid.cell(3, 5)                # mazegen.Cell
print(cell.walls, cell.is_logo)

# Access a solution
print(gen.solution())                 # "NESW..." string

# Serialise to the spec output format
write_output("maze.txt", grid, gen.entry, gen.exit, gen.solution())
```

The package is shipped as `mazegen-1.0.0-py3-none-any.whl` at the repo root. To reinstall it in any other virtualenv: `pip install mazegen-1.0.0-py3-none-any.whl`. To rebuild it from the source under `mazegen/`: `make build`.

## Resources

### References

- *Maze generation algorithm — Prim's* — <https://en.wikipedia.org/wiki/Maze_generation_algorithm#Randomized_Prim's_algorithm>
- *Breadth-first search* — <https://en.wikipedia.org/wiki/Breadth-first_search>
- *Spanning tree* — <https://en.wikipedia.org/wiki/Spanning_tree>
- *PEP 257 — docstring conventions* — <https://peps.python.org/pep-0257/>
- *flake8* — <https://flake8.pycqa.org/>
- *mypy* — <https://mypy.readthedocs.io/>
- *Python packaging tutorial* — <https://packaging.python.org/en/latest/tutorials/packaging-projects/>

### How AI was used

| Task | Part affected | Use |
|---|---|---|
| Discussion of Prim's vs DFS trade-offs | `mazegen/generator.py` | Sanity-checked the algorithmic choice against the spec's "no 3×3 open area" rule before implementation. |
| Review of edge cases | `mazegen/generator.py`, `a_maze_ing.py` | Asked an AI assistant to enumerate failure cases for config parsing and logo placement; we tested each manually and added explicit error messages where we agreed. |
| Wording polish for this README | `README.md` | AI rewrote rough notes into the current prose; every claim was cross-checked against the actual code. |

No code was pasted in without being read and understood. All bug-fixes were authored after we could explain *why* the fix worked.

## Team & project management

### Roles

| Member | Responsibility |
|---|---|
| ddervish | `mazegen/` package (grid, generator, solver, serialiser), wheel packaging, output format compliance |
| dshabani | `a_maze_ing.py`, `display.py`, themes, interactive loop, configuration parsing, README & Makefile |

### Planning and how it evolved

- **Week 1:** Read the subject, agreed on iterative Prim's, split the file ownership above. Designed the wall encoding and the cell/grid API together so the display and the generator could be written in parallel.
- **Week 2:** Stubbed the public API of `mazegen.MazeGenerator` first; that let `display.py` be written against a known shape before the generator was finished.
- **Week 3:** Integration. Discovered the "no 3×3 open area" rule needed a local check after each loop-injection knock, not a global pass. Added the 5x7 "42" pattern and verified the spanning tree still covers all non-logo cells.

### What worked well

- Defining the public surface of `MazeGenerator` early, so both halves of the project could integrate cleanly.
- Producing the spec output format from the `Grid` itself rather than from internal state — the same function works for any maze, including ones produced by hand.
- Picking an iterative algorithm — we never had to fight Python's recursion limit.

### What could be improved

- The interactive display is single-window; a multi-pane TUI (e.g. via `curses`) would let us show stats alongside the maze.
- We could add more algorithms (Kruskal's, Wilson's) selectable from the config file.

### Tools used

- **Python 3.12** — language runtime
- **flake8 + mypy** — lint & static typing (CI-style, run via `make lint`)
- **`build`** — wheel packaging (`make build`)
- **Git** — version control
- **Claude (Anthropic)** — sounding board for design questions and prose review (see *How AI was used* above)
