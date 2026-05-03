# vacant — domain availability via authoritative DNS

[![PyPI](https://img.shields.io/pypi/v/vacant.svg)](https://pypi.org/project/vacant/)
[![crates.io](https://img.shields.io/crates/v/vacant.svg)](https://crates.io/crates/vacant)

Python bindings for the [vacant](https://github.com/alltuner/vacant) Rust engine. Asks the authoritative TLD nameservers directly instead of WHOIS — fast, no rate limits, no waiting.

The wheel ships the same Rust engine compiled in, with a small Python facade and a `vacant` CLI entry point. Lockstep-versioned with the `vacant` crate: `vacant 0.3.x` (Python) wraps `vacant 0.3.x` (Rust) exactly.

## Install

Pick the path that matches how you'll use it:

### CLI

```bash
brew install alltuner/tap/vacant   # macOS, Linux — native Rust binary
cargo install vacant               # any platform with a Rust toolchain
uvx vacant google.com              # one-shot, no install (Python wheel)
```

The brew / cargo paths give you the native Rust binary (instant startup, ideal for daily use). `uvx` runs the Python wheel — convenient when you don't want to install anything, slightly slower to start because it boots a Python interpreter.

### Library

```bash
pip install vacant
# or with uv:
uv add vacant
```

```python
from vacant import check_many, Status

results = check_many(["example.com", "anthropic.com", "totally-made-up-zxqv.cat"])
for r in results:
    print(r.domain, r.status.value, r.detail)
```

The on-disk SQLite cache is shared with the Rust CLI — runs against the same `~/.cache/vacant/results.db`, so the brew binary and a Python script see each other's results.

```python
from vacant import DiskCache, check_many

cache = DiskCache()  # default ~/.cache/vacant/results.db
results = check_many(["example.com"], cache=cache)
```

## How it works

`vacant.check_many` calls into the Rust engine via PyO3 (`vacant._core`). The engine:

1. Normalizes the input.
2. Looks up cache; returns hits immediately.
3. Runs a per-zone precheck (length, charset, reserved labels) from the bundled `rules.toml`.
4. For inputs that pass, asks the parent zone's NS directly. NXDOMAIN → available; delegation → registered; ambiguous answers fall back to RDAP.

Cache shape, rules format, and verdict semantics are all the engine's — see [alltuner/vacant](https://github.com/alltuner/vacant) for the source of truth.

## Develop

```bash
just              # menu
just develop      # build the maturin extension into the local venv
just check        # ruff + pytest
just wheel        # build a release wheel locally
```

## License

MIT — see [`LICENSE`](LICENSE).
