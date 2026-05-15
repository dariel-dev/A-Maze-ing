"""A-Maze-ing main entry point.

Usage:
    python3 a_maze_ing.py [config.txt]

Reads the configuration file passed on the command line (defaults to
``config.txt``), generates the maze, writes the spec output file, then
launches the interactive terminal display.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from mazegen import MazeGenerator, write_output


@dataclass(frozen=True)
class Config:
    """Parsed configuration."""

    width: int
    height: int
    entry: tuple[int, int]
    exit_pt: tuple[int, int]
    output_file: str
    perfect: bool
    seed: int | None


REQUIRED_KEYS = ("WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT")


def parse_coord(value: str, key: str) -> tuple[int, int]:
    """Parse "x,y" into a tuple of ints."""
    parts = [p.strip() for p in value.split(",")]
    if len(parts) != 2:
        raise ValueError(f"{key}: expected 'x,y', got {value!r}")
    try:
        return int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise ValueError(f"{key}: not an integer pair: {value!r}") from exc


def parse_bool(value: str, key: str) -> bool:
    """Parse 'True'/'False' (case-insensitive)."""
    v = value.strip().lower()
    if v in ("true", "1", "yes"):
        return True
    if v in ("false", "0", "no"):
        return False
    raise ValueError(f"{key}: expected True or False, got {value!r}")


def parse_seed(value: str) -> int | None:
    """Parse an optional integer seed; empty value means random."""
    v = value.strip()
    if not v:
        return None
    try:
        return int(v, 0)
    except ValueError as exc:
        raise ValueError(f"SEED: not an integer: {value!r}") from exc


def load_config(path: str) -> Config:
    """Read a KEY=VALUE config file and validate required fields."""
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"config file not found: {path}") from exc
    except OSError as exc:
        raise OSError(f"cannot read config file {path}: {exc}") from exc

    settings: dict[str, str] = {}
    for line_no, raw_line in enumerate(raw.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(
                f"{path}:{line_no}: expected KEY=VALUE, got {raw_line!r}"
            )
        key, _, value = line.partition("=")
        settings[key.strip()] = value.strip()

    missing = [k for k in REQUIRED_KEYS if k not in settings]
    if missing:
        raise ValueError(f"missing required keys: {', '.join(missing)}")

    try:
        width = int(settings["WIDTH"])
        height = int(settings["HEIGHT"])
    except ValueError as exc:
        raise ValueError("WIDTH and HEIGHT must be integers") from exc
    if width <= 0 or height <= 0:
        raise ValueError(
            f"WIDTH and HEIGHT must be positive (got {width}x{height})"
        )

    entry = parse_coord(settings["ENTRY"], "ENTRY")
    exit_pt = parse_coord(settings["EXIT"], "EXIT")
    output_file = settings["OUTPUT_FILE"]
    if not output_file:
        raise ValueError("OUTPUT_FILE must not be empty")
    perfect = parse_bool(settings["PERFECT"], "PERFECT")
    seed = parse_seed(settings.get("SEED", ""))

    return Config(
        width=width,
        height=height,
        entry=entry,
        exit_pt=exit_pt,
        output_file=output_file,
        perfect=perfect,
        seed=seed,
    )


def build_generator(cfg: Config) -> MazeGenerator:
    """Instantiate :class:`MazeGenerator` from a parsed :class:`Config`."""
    return MazeGenerator(
        width=cfg.width,
        height=cfg.height,
        entry=cfg.entry,
        exit_pt=cfg.exit_pt,
        perfect=cfg.perfect,
        seed=cfg.seed,
    )


def run(cfg: Config) -> MazeGenerator:
    """Generate the maze, write the output file, return the generator."""
    gen = build_generator(cfg)
    gen.generate()
    solution = gen.solution()
    write_output(cfg.output_file, gen.grid, gen.entry, gen.exit, solution)
    print(f"[ok] maze written to {cfg.output_file}")
    return gen


def main(argv: list[str]) -> int:
    """CLI entry point."""
    config_path = argv[1] if len(argv) > 1 else "config.txt"
    try:
        cfg = load_config(config_path)
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    try:
        gen = run(cfg)
    except (ValueError, RuntimeError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    try:
        from display import interactive
    except ImportError:
        return 0

    try:
        interactive(gen, cfg)
    except KeyboardInterrupt:
        print()
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
