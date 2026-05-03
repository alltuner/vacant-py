from dataclasses import dataclass
from pathlib import Path

from vacant import _core
from vacant.checker import Result, Status


def default_path() -> Path:
    return Path(_core.DiskCache.default_path())


@dataclass(frozen=True)
class CachedEntry:
    domain: str
    zone: str
    status: Status
    detail: str
    checked_at: int


class DiskCache:
    """Read-through wrapper around the vacant SQLite cache.

    Same on-disk format as the vacant CLI's DiskCache; safe to share.
    """

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path is not None else default_path()
        self._inner = _core.DiskCache(str(self.path))

    def get(self, domain: str, *, ttl: float) -> CachedEntry | None:
        row = self._inner.get(domain, ttl)
        if row is None:
            return None
        return CachedEntry(
            domain=row["domain"],
            zone=row["zone"],
            status=Status(row["status"]),
            detail=row["detail"],
            checked_at=row["checked_at"],
        )

    def put(self, result: Result) -> None:
        if result.status is Status.UNKNOWN or not result.domain:
            return
        self._inner.put(result.domain, result.zone, result.status.value, result.detail)
