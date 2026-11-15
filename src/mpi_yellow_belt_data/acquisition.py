"""Explicit local evidence acquisition against the unchanged adopted v2 pin."""

import shutil
import tempfile
from pathlib import Path

from mpi_yellow_belt_data.cases.riverside.model.evidence import check
from mpi_yellow_belt_data.catalog import CaseError
from mpi_yellow_belt_data.resources import release_pin


def acquire(source: Path, destination: Path) -> Path:
    """Adopt a supplied directory; never fetch, regenerate, or overwrite implicitly."""
    if destination.exists() or destination.is_symlink():
        raise CaseError(f"Destination already exists: {destination}")
    check(source, pin=release_pin())
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".riverside-acquire-", dir=destination.parent
    ) as temp:
        payload = Path(temp) / "payload"
        shutil.copytree(source, payload, symlinks=True)
        check(payload, pin=release_pin())
        if destination.exists() or destination.is_symlink():
            raise CaseError(f"Destination already exists: {destination}")
        payload.rename(destination)
    return destination
