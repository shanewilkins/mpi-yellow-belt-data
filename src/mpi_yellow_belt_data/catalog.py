"""Typed course discovery and local integrity checks without numerical dependencies."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError
from yaml.resolver import BaseResolver

from mpi_yellow_belt_data.contracts import (
    CaseDefinition,
    DatasetManifest,
    RiversideConfig,
    safe_relative_path,
)

PACKAGE_ROOT = Path(__file__).resolve().parent
CASE_ROOT = PACKAGE_ROOT / "cases"
_CHECKOUT = PACKAGE_ROOT.parents[1]
DATA_ROOT = (
    _CHECKOUT / "data"
    if (_CHECKOUT / "pyproject.toml").is_file()
    else PACKAGE_ROOT / "_data"
)
DOCS_ROOT = (
    _CHECKOUT / "docs"
    if (_CHECKOUT / "pyproject.toml").is_file()
    else PACKAGE_ROOT / "_docs"
)
CASE_IDS = ("riverside",)


class CaseError(ValueError):
    """A missing, unsafe, changed, or invalid course resource."""


class _UniqueLoader(yaml.SafeLoader):
    pass


def _mapping(loader: _UniqueLoader, node: yaml.nodes.MappingNode) -> dict:
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        if not isinstance(key, str) or key in result:
            raise CaseError(
                f"Duplicate or non-string YAML key at line {key_node.start_mark.line + 1}: {key}"
            )
        result[key] = loader.construct_object(value_node, deep=True)
    return result


_UniqueLoader.add_constructor(BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def _yaml(path: Path) -> object:
    try:
        return yaml.load(path.read_text(), Loader=_UniqueLoader)
    except (yaml.YAMLError, CaseError) as error:
        raise CaseError(f"Invalid YAML in {path}: {error}") from error


def _parse[T: BaseModel](model: type[T], value: object, source: Path) -> T:
    try:
        return model.model_validate(value)
    except ValidationError as error:
        raise CaseError(f"Invalid contract in {source}: {error}") from error


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative_file(root: Path, name: str) -> Path:
    try:
        safe_relative_path(name)
    except ValueError as error:
        raise CaseError(f"Unsafe relative path: {name}") from error
    root = root.resolve()
    candidate = root / name
    if any(p.is_symlink() for p in (candidate, *candidate.parents)):
        raise CaseError(f"Symlink is not a course input: {name}")
    if not candidate.is_file() or not candidate.resolve().is_relative_to(root):
        raise CaseError(f"Missing course input: {candidate}")
    return candidate


def source_file(case_id: str, name: str) -> Path:
    if case_id not in CASE_IDS:
        raise CaseError(f"Unknown Yellow Belt case: {case_id}")
    return relative_file(
        (DOCS_ROOT if name.endswith(".md") else CASE_ROOT) / case_id, name
    )


def case_contract(case_id: str) -> CaseDefinition:
    path = source_file(case_id, "case.yml")
    value = _parse(CaseDefinition, _yaml(path), path)
    if value.id != case_id:
        raise CaseError(f"Case identity mismatch: {case_id}")
    for name in value.sources:
        source_file(case_id, name)
    return value


def case_definition(case_id: str) -> dict[str, Any]:
    """Compatibility dictionary projection; internal callers use case_contract."""
    return case_contract(case_id).model_dump(mode="json", exclude_unset=True)


def generation_config(case_id: str = "riverside") -> RiversideConfig:
    path = source_file(case_id, "config/baseline.yml")
    return _parse(RiversideConfig, _yaml(path), path)


def list_cases() -> list[dict[str, Any]]:
    return [case_definition(case_id) for case_id in CASE_IDS]


def dataset_directory(case_id: str, *, root: Path | None = None) -> Path:
    pin = case_contract(case_id).dataset
    if pin is None:
        raise CaseError(f"{case_id} is a model-only case")
    return (DATA_ROOT if root is None else root) / case_id / pin.version


def manifest_contract(
    case_id: str, *, root: Path | None = None, directory: Path | None = None
) -> DatasetManifest:
    pin = case_contract(case_id).dataset
    if pin is None:
        raise CaseError(f"{case_id} is a model-only case")
    location = (
        directory if directory is not None else dataset_directory(case_id, root=root)
    )
    if location.is_symlink():
        raise CaseError(f"Dataset directory is a symlink: {location}")
    path = relative_file(location, "manifest.json")
    if sha256(path) != pin.manifest_sha256:
        raise CaseError(f"Dataset manifest checksum mismatch: {case_id}")
    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        raise CaseError(f"Invalid JSON in {path}: {error}") from error
    manifest = _parse(DatasetManifest, raw, path)
    if (manifest.case_id, manifest.version) != (case_id, pin.version):
        raise CaseError(f"Dataset identity mismatch: {case_id}")
    return manifest


def check_dataset(
    case_id: str, *, root: Path | None = None, directory: Path | None = None
) -> dict[str, Any]:
    if case_contract(case_id).dataset is None:
        return {"case_id": case_id, "files": [], "status": "model-only"}
    location = (
        directory if directory is not None else dataset_directory(case_id, root=root)
    )
    manifest = manifest_contract(case_id, root=root, directory=location)
    declared = {"manifest.json", *(item.path for item in manifest.files)}
    for item in manifest.files:
        asset = relative_file(location, item.path)
        if asset.stat().st_size != item.bytes or sha256(asset) != item.sha256:
            raise CaseError(f"Dataset file checksum mismatch: {item.path}")
        if "columns" in item.model_fields_set:
            with asset.open(newline="", encoding="utf-8") as stream:
                rows = csv.reader(stream)
                if next(rows, []) != item.columns or sum(1 for _ in rows) != item.rows:
                    raise CaseError(f"Dataset table shape mismatch: {item.path}")
    if {
        str(p.relative_to(location).as_posix())
        for p in location.rglob("*")
        if p.is_file()
    } != declared or any(p.is_symlink() for p in location.rglob("*")):
        raise CaseError(f"Undeclared files or symlinks in dataset: {case_id}")
    return manifest.model_dump(mode="json", exclude_unset=True)


def dataset_file(case_id: str, filename: str, *, root: Path | None = None) -> Path:
    check_dataset(case_id, root=root)
    manifest = manifest_contract(case_id, root=root)
    if filename not in {item.path for item in manifest.files}:
        raise CaseError(f"Undeclared dataset file: {case_id}/{filename}")
    return relative_file(dataset_directory(case_id, root=root), filename)


def dataset_inputs(case_id: str, *, root: Path | None = None) -> tuple[Path, ...]:
    definition = case_contract(case_id)
    inputs = [
        Path(__file__),
        PACKAGE_ROOT / "contracts.py",
        source_file(case_id, "case.yml"),
        *(source_file(case_id, name) for name in definition.sources),
    ]
    if definition.dataset is not None:
        directory = dataset_directory(case_id, root=root)
        # The package carries the adopted pin, even for an unprepared override root.
        manifest = manifest_contract(case_id)
        inputs.extend(
            [
                directory / "manifest.json",
                *(directory / item.path for item in manifest.files),
            ]
        )
    return tuple(inputs)
