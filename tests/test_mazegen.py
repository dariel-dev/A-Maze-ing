import tempfile
import unittest
from pathlib import Path

from mazegen import (
    Direction,
    Grid,
    MazeGenerator,
    grid_to_text,
    path_coords,
    shortest_path,
    write_output,
)


def make_maze(
    perfect: bool = True, seed: int | None = 42
) -> MazeGenerator:
    return MazeGenerator(
        20, 15, (0, 0), (19, 14), perfect=perfect, seed=seed
    )


class GridTests(unittest.TestCase):
    def test_dimensions_and_boundaries(self) -> None:
        with self.assertRaises(ValueError):
            Grid(0, 2)
        grid = Grid(2, 2)
        self.assertIsNone(grid.neighbour(0, 0, Direction.N))
        self.assertIsNone(grid.neighbour(1, 1, Direction.E))
        self.assertIsNone(grid.neighbour(-1, 0, Direction.E))
        with self.assertRaises(ValueError):
            grid.cell(-1, 0)
        with self.assertRaises(ValueError):
            grid.cell(2, 0)

    def test_carving_opens_both_sides(self) -> None:
        grid = Grid(2, 1)
        grid.carve(0, 0, Direction.E)
        self.assertFalse(grid.cell(0, 0).has_wall(Direction.E))
        self.assertFalse(grid.cell(1, 0).has_wall(Direction.W))

    def test_carving_boundary_raises(self) -> None:
        with self.assertRaises(ValueError):
            Grid(2, 2).carve(0, 0, Direction.N)
        with self.assertRaises(ValueError):
            Grid(2, 2).carve(-1, 0, Direction.E)


class GeneratorTests(unittest.TestCase):
    def test_invalid_parameters_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            MazeGenerator(0, 15, (0, 0), (19, 14))
        with self.assertRaises(ValueError):
            MazeGenerator(20, 15, (0, 0), (0, 0))
        with self.assertRaises(ValueError):
            MazeGenerator(20, 15, (0, 0), (20, 14))
        with self.assertRaises(ValueError):
            MazeGenerator(
                20, 15, (0, 0), (19, 14), loop_probability=1.1
            )

    def test_seeded_generation_is_reproducible(self) -> None:
        first, second = make_maze(), make_maze()
        first.generate()
        second.generate()
        first_walls = [
            [cell.walls for cell in row] for row in first.grid.cells
        ]
        second_walls = [
            [cell.walls for cell in row] for row in second.grid.cells
        ]
        self.assertEqual(first_walls, second_walls)

    def test_logo_cells_remain_closed(self) -> None:
        maze = make_maze()
        maze.generate()
        logo = [
            cell for _, _, cell in maze.grid.iter_cells() if cell.is_logo
        ]
        self.assertTrue(logo)
        self.assertTrue(all(cell.walls == 0xF for cell in logo))

    def test_solution_and_boundary_walls(self) -> None:
        maze = make_maze()
        maze.generate()
        path = maze.solution()
        coords = path_coords(maze.grid, maze.entry, maze.exit)
        self.assertEqual(coords[0], maze.entry)
        self.assertEqual(coords[-1], maze.exit)
        self.assertEqual(len(path), len(coords) - 1)

        for step, (x, y) in zip(path, coords):
            self.assertFalse(
                maze.grid.cell(x, y).has_wall(Direction[step])
            )

        for x, y, cell in maze.grid.iter_cells():
            if y == 0:
                self.assertTrue(cell.has_wall(Direction.N))
            if y == maze.height - 1:
                self.assertTrue(cell.has_wall(Direction.S))
            if x == 0:
                self.assertTrue(cell.has_wall(Direction.W))
            if x == maze.width - 1:
                self.assertTrue(cell.has_wall(Direction.E))

    def test_perfect_maze_has_tree_edge_count(self) -> None:
        maze = make_maze()
        maze.generate()
        edges = 0
        cells = 0
        for x, y, cell in maze.grid.iter_cells():
            if cell.is_logo:
                continue
            cells += 1
            if x + 1 < maze.width:
                neighbour = maze.grid.cell(x + 1, y)
                if not neighbour.is_logo and not cell.has_wall(Direction.E):
                    edges += 1
            if y + 1 < maze.height:
                neighbour = maze.grid.cell(x, y + 1)
                if not neighbour.is_logo and not cell.has_wall(Direction.S):
                    edges += 1
        self.assertEqual(edges, cells - 1)

    def test_nonperfect_maze_avoids_open_three_by_three(self) -> None:
        maze = make_maze(perfect=False, seed=7)
        maze.generate()
        for x in range(maze.width - 2):
            for y in range(maze.height - 2):
                self.assertFalse(maze._is_block_fully_open(x, y))


class SolverAndOutputTests(unittest.TestCase):
    def test_shortest_path(self) -> None:
        grid = Grid(2, 2)
        grid.carve(0, 0, Direction.E)
        grid.carve(1, 0, Direction.S)
        self.assertEqual(shortest_path(grid, (0, 0), (1, 1)), "ES")
        self.assertEqual(
            path_coords(grid, (0, 0), (1, 1)),
            [(0, 0), (1, 0), (1, 1)],
        )

    def test_unreachable_goal_raises(self) -> None:
        with self.assertRaises(ValueError):
            shortest_path(Grid(2, 1), (0, 0), (1, 0))

    def test_invalid_path_endpoints_raise(self) -> None:
        grid = Grid(2, 2)
        for solver in (shortest_path, path_coords):
            with self.subTest(solver=solver.__name__):
                with self.assertRaisesRegex(ValueError, "outside grid bounds"):
                    solver(grid, (-1, 0), (-1, 0))
                with self.assertRaisesRegex(ValueError, "outside grid bounds"):
                    solver(grid, (0, 0), (2, 0))

    def test_output_format_and_file_write(self) -> None:
        grid = Grid(2, 1)
        expected = "FF\n\n0,0\n1,0\nE\n"
        self.assertEqual(
            grid_to_text(grid, (0, 0), (1, 0), "E"), expected
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "maze.txt"
            write_output(str(output), grid, (0, 0), (1, 0), "E")
            self.assertEqual(
                output.read_text(encoding="utf-8"), expected
            )


if __name__ == "__main__":
    unittest.main()
