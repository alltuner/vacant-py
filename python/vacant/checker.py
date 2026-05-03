import enum
from dataclasses import dataclass
from importlib.resources import files
from typing import TYPE_CHECKING

from vacant import _core

if TYPE_CHECKING:
    from vacant.disk_cache import DiskCache


class Status(enum.Enum):
    AVAILABLE = "available"
    REGISTERED = "registered"
    RESERVED = "reserved"
    INVALID = "invalid"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Result:
    input: str
    domain: str
    zone: str
    status: Status
    detail: str = ""
    from_cache: bool = False


_rules_loaded = False


def _ensure_rules_loaded() -> None:
    global _rules_loaded
    if _rules_loaded:
        return
    _core.load_rules(str(files("vacant") / "rules.toml"))
    _rules_loaded = True


def _coerce_cache(cache: "DiskCache | str | None"):
    if cache is None:
        return None
    inner = getattr(cache, "_inner", None)
    if inner is not None:
        return inner
    path = getattr(cache, "path", None)
    if path is not None:
        return _core.DiskCache(str(path))
    return _core.DiskCache(str(cache))


def check_many(
    domains: list[str],
    *,
    timeout: float = 4.0,
    concurrency: int = 64,
    cache: "DiskCache | str | None" = None,
    cache_ttl: float = 86_400.0,
) -> list[Result]:
    """Check a batch of domains end-to-end via the vacant engine. Order preserved."""
    _ensure_rules_loaded()
    rust_cache = _coerce_cache(cache)
    rows = _core.check_many(
        list(domains),
        concurrency=concurrency,
        timeout=timeout,
        cache=rust_cache,
        cache_ttl=cache_ttl,
    )
    return [_to_result(r) for r in rows]


def check(
    domain: str,
    *,
    timeout: float = 4.0,
    cache: "DiskCache | str | None" = None,
    cache_ttl: float = 86_400.0,
) -> Result:
    return check_many(
        [domain],
        timeout=timeout,
        concurrency=1,
        cache=cache,
        cache_ttl=cache_ttl,
    )[0]


def _to_result(row: dict) -> Result:
    return Result(
        input=row["input"],
        domain=row["domain"],
        zone=row["zone"],
        status=Status(row["status"]),
        detail=row["detail"],
        from_cache=row["from_cache"],
    )
