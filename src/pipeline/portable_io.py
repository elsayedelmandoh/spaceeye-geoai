"""Small integrity and installation helpers shared by review setup commands."""

import hashlib
from pathlib import Path, PurePosixPath


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def relative_file(name: str) -> Path:
    path = PurePosixPath(name)
    if not name or "\\" in name or ":" in name or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Expected a relative file path: {name}")
    return Path(*path.parts)


def install_files(files: dict[Path, bytes]) -> int:
    """Preflight every collision; never overwrite a different existing file."""
    for path, data in files.items():
        if path.exists() and (not path.is_file() or path.read_bytes() != data):
            raise ValueError(f"Existing file differs: {path}. Use a fresh SPACEEYE_DATA_ROOT; existing work was preserved.")
    count = 0
    for path, data in files.items():
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            count += 1
    return count
