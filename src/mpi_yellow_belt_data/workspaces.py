"""Curated v1 workspaces and non-overwriting personal-work backups."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Literal

from mpi_yellow_belt_data.catalog import (
    CaseError,
    check_dataset,
    dataset_directory,
    sha256,
)
from mpi_yellow_belt_data.contracts import Contract, Digest
from mpi_yellow_belt_data.resources import asset_file


class WorkspaceIdentity(Contract):
    schema_version: Literal[1] = 1
    case_id: Literal["riverside"]
    course_version: str
    dataset_version: str
    release: Literal["legacy_v1", "initial", "investigation", "followup"]
    parent_manifest_sha256: Digest
    input_sha256: dict[str, Digest]


def write_workspace_identity(
    stage: Path,
    *,
    case_id: str,
    dataset_version: str,
    release: str,
    manifest_sha256: str,
) -> None:
    identity = WorkspaceIdentity.model_validate(
        {
            "case_id": case_id,
            "course_version": importlib.metadata.version("mpi-yellow-belt-data"),
            "dataset_version": dataset_version,
            "release": release,
            "parent_manifest_sha256": manifest_sha256,
            "input_sha256": {
                p.relative_to(stage).as_posix(): sha256(p)
                for p in sorted(stage.rglob("*"))
                if p.is_file()
            },
        }
    )
    (stage / "course-workspace.json").write_text(
        identity.model_dump_json(indent=2) + "\n"
    )


def prepare_v1(*, output: Path, root: Path | None = None) -> Path:
    manifest = check_dataset("riverside", root=root)
    if output.exists() or output.is_symlink():
        raise CaseError(f"Learner destination already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".riverside-v1-work-", dir=output.parent
    ) as temp:
        stage = Path(temp) / "workspace"
        stage.mkdir()
        materials = {
            "notebooks/riverside/a3_v1.py": "notebooks/riverside_a3.py",
            "models/riverside/current_state.flo": "models/current_state.flo",
            "LICENSE.md": "LICENSE.md",
            **{
                f"docs/riverside/legacy_v1/{name}": name
                for name in ("scenario.md", "data_dictionary.md", "provenance.md")
            },
        }
        for source, destination in materials.items():
            target = stage / destination
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(asset_file(source), target)
        directory = dataset_directory("riverside", root=root)
        shutil.copytree(directory, stage / "data/riverside")
        requirements = [
            f"{name}=={importlib.metadata.version(name)}"
            for name in ("marimo", "polars", "numpy", "scipy", "matplotlib", "flo-lang")
        ]
        (stage / "pyproject.toml").write_text(
            '[project]\nname = "riverside-investigation"\nversion = "0.0.0"\nrequires-python = ">=3.15,<3.16"\ndependencies = '
            + json.dumps(requirements, indent=2)
            + "\n"
        )
        (stage / ".python-version").write_text("3.15\n")
        (stage / "README.md").write_text(
            "# Riverside v1 investigation\n\nRead scenario.md and data_dictionary.md.\nRun `uv sync`, then `uv run marimo edit notebooks/riverside_a3.py`.\nKeep your notebook, evidence, and uv.lock together.\nBack up this personal workspace; ignored work is not backed up by upstream Git.\nFor updates, use a fresh course checkout and transfer your work deliberately.\n"
        )
        write_workspace_identity(
            stage,
            case_id="riverside",
            dataset_version=manifest["version"],
            release="legacy_v1",
            manifest_sha256=sha256(directory / "manifest.json"),
        )
        if output.exists() or output.is_symlink():
            raise CaseError(f"Learner destination already exists: {output}")
        stage.rename(output)
    return output


def export_work(workspace: Path, output: Path) -> Path:
    workspace = workspace.resolve()
    identity = WorkspaceIdentity.model_validate_json(
        (workspace / "course-workspace.json").read_text()
    )
    if output.resolve().is_relative_to(workspace):
        raise CaseError("Backup must be outside the personal workspace")
    if output.exists() or output.is_symlink():
        raise CaseError(f"Backup destination already exists: {output}")
    files = []
    for path in sorted(workspace.rglob("*")):
        if any(
            part in {".venv", "__pycache__", ".git", "__marimo__"}
            for part in path.relative_to(workspace).parts
        ):
            continue
        if path.is_symlink():
            raise CaseError(f"Refusing symlink in personal backup: {path}")
        if (
            path.is_file()
            and path.relative_to(workspace).as_posix() != "backup-receipt.json"
        ):
            files.append(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation never overwrites a previous backup. Clean up failed writes.
    try:
        with (
            output.open("xb") as stream,
            zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive,
        ):
            current = {}
            for path in files:
                name = path.relative_to(workspace).as_posix()
                data = path.read_bytes()
                archive.writestr(name, data)
                current[name] = hashlib.sha256(data).hexdigest()
            archive.writestr(
                "backup-receipt.json",
                json.dumps(
                    {
                        "workspace": identity.model_dump(mode="json"),
                        "current_sha256": current,
                    },
                    indent=2,
                )
                + "\n",
            )
    except FileExistsError:
        raise
    except BaseException:
        output.unlink(missing_ok=True)
        raise
    return output


def verify_workspace(workspace: Path) -> WorkspaceIdentity:
    from mpi_yellow_belt_data.catalog import relative_file

    identity = WorkspaceIdentity.model_validate_json(
        (workspace / "course-workspace.json").read_text()
    )
    for name, digest in identity.input_sha256.items():
        # Personal notebooks/notes may change; supplied evidence remains immutable.
        if (
            name.startswith("data/")
            and sha256(relative_file(workspace, name)) != digest
        ):
            raise CaseError(f"Supplied evidence changed: {name}")
    return identity


def prepare_archive(archive: Path, output: Path, *, release: str = "initial") -> Path:
    """Prepare an explicitly supplied, course-pinned, curated stage archive."""
    from mpi_yellow_belt_data.contracts import safe_relative_path

    if output.exists() or output.is_symlink():
        raise CaseError(f"Learner destination already exists: {output}")
    index = json.loads(asset_file("releases/riverside/learner-stages.json").read_text())
    pin = index["stages"][release]
    if sha256(archive) != pin["sha256"]:
        raise CaseError("Learner archive checksum mismatch")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".riverside-stage-", dir=output.parent
    ) as temp:
        stage = Path(temp) / "workspace"
        stage.mkdir()
        with zipfile.ZipFile(archive) as bundle:
            names = set()
            for entry in bundle.infolist():
                name = safe_relative_path(entry.filename)
                if name in names or (entry.external_attr >> 16) & 0o170000 == 0o120000:
                    raise CaseError(f"Unsafe/duplicate learner archive entry: {name}")
                names.add(name)
                path = stage / name
                path.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(entry) as source, path.open("xb") as target:
                    shutil.copyfileobj(source, target)
        identity = verify_workspace(stage)
        expected = {
            f"data/{name}.csv"
            for name in (
                "referrals",
                "events",
                "appointments",
                "complaints",
                "audit",
                "capacity",
            )
        }
        actual = {
            p.relative_to(stage).as_posix()
            for p in (stage / "data").rglob("*")
            if p.is_file()
        }
        if (
            identity.release != release
            or actual != expected
            or any(
                "truth" in name
                or name.startswith(
                    ("reference/", "followup/", "investigation/", "initial/")
                )
                for name in names
            )
        ):
            raise CaseError("Learner archive has wrong stage or uncurated evidence")
        if output.exists() or output.is_symlink():
            raise CaseError(f"Learner destination already exists: {output}")
        stage.rename(output)
    return output
