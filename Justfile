# vacant-py — common dev tasks. `just <target>` or `just` for the menu.

default:
    @just --list

# Build the maturin extension into the local venv.
develop:
    uv run --with maturin maturin develop --uv

# Format + lint + tests.
check:
    uv run ruff format --check .
    uv run ruff check .
    uv run pytest

# Build a release wheel locally.
wheel:
    uv run --with maturin maturin build --release

# Build a source distribution.
sdist:
    uv run --with maturin maturin sdist
