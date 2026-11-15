from __future__ import annotations

import json
import subprocess
import sys

import jsonschema
import pytest
import yaml

from mpi_yellow_belt_data import catalog
from mpi_yellow_belt_data.contracts import (
    CaseDefinition,
    DatasetManifest,
    RiversideConfig,
    export_schemas,
)


def test_base_discovery_does_not_import_optional_stack():
    code = """import sys
from mpi_yellow_belt_data.catalog import list_cases, check_dataset, generation_config
assert list_cases()[0]['id'] == 'riverside'
assert len(check_dataset('riverside')['files']) == 1
generation_config()
assert not {'pandera','polars','numpy','pandas','marimo','jsonschema'} & sys.modules.keys()
"""
    subprocess.run([sys.executable, "-c", code], check=True, cwd="/tmp")


def test_typed_profiles_preserve_existing_dictionaries_and_frozen_envelope():
    raw_case = yaml.safe_load(catalog.source_file("riverside", "case.yml").read_text())
    raw_manifest = json.loads(
        (catalog.dataset_directory("riverside") / "manifest.json").read_text()
    )
    for raw, model, schema in (
        (raw_case, CaseDefinition, "case-v1.json"),
        (raw_manifest, DatasetManifest, "dataset-v1.json"),
    ):
        assert (
            model.model_validate(raw).model_dump(mode="json", exclude_unset=True) == raw
        )
        jsonschema.Draft202012Validator(
            json.loads((catalog.PACKAGE_ROOT / "schemas" / schema).read_text())
        ).validate(raw)
    assert catalog.check_dataset("riverside") == raw_manifest
    export_schemas(catalog.PACKAGE_ROOT / "schemas", check=True)


@pytest.mark.parametrize(
    "field,value",
    [
        ("seed", True),
        ("seed", "1"),
        ("seed", -1),
        ("row_count", 0),
        ("row_count", 1485),
        ("start_date", "2025-09-30"),
        ("end_date", "2026-04-01"),
        ("extra", 1),
    ],
)
def test_unsupported_configuration_is_rejected(field, value):
    values = catalog.generation_config().model_dump()
    values[field] = value
    with pytest.raises(ValueError):
        RiversideConfig.model_validate(values)


@pytest.mark.parametrize(
    "name", ["../escape", "a/../b", "/absolute", "C:/file", "a\\b", "a//b", "./file"]
)
def test_unsafe_paths_rejected(tmp_path, name):
    with pytest.raises(catalog.CaseError):
        catalog.relative_file(tmp_path, name)


def test_missing_explicit_evidence_root_never_falls_back(tmp_path):
    with pytest.raises(catalog.CaseError, match="Missing"):
        catalog.check_dataset("riverside", root=tmp_path)
    inputs = catalog.dataset_inputs("riverside", root=tmp_path)
    assert tmp_path / "riverside/1.0.0/riverside_referrals.csv" in inputs
    assert catalog.PACKAGE_ROOT / "contracts.py" in inputs


def test_duplicate_yaml_keys_are_rejected(tmp_path):
    file = tmp_path / "ambiguous.yml"
    file.write_text("seed: 1\nseed: 2\n")
    with pytest.raises(catalog.CaseError, match="Duplicate"):
        catalog._yaml(file)


def test_schema_freshness_is_read_only(tmp_path):
    export_schemas(tmp_path)
    path = tmp_path / "yellow-belt-case-v1.json"
    path.write_text("{}")
    with pytest.raises(ValueError, match="stale"):
        export_schemas(tmp_path, check=True)
    assert path.read_text() == "{}"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda x: x.update(case_id="washnfold"),
        lambda x: x.update(data_schema="riverside-linked-v2"),
        lambda x: x["provenance"].update(classification="external"),
        lambda x: x["provenance"].pop("baseline_source_commit"),
        lambda x: x["files"][0].update(path="../outside.csv"),
        lambda x: x["files"].append(x["files"][0]),
    ],
)
def test_bad_provenance_and_incompatible_evidence_are_rejected(mutation):
    value = json.loads(
        (catalog.dataset_directory("riverside") / "manifest.json").read_text()
    )
    mutation(value)
    with pytest.raises(ValueError):
        DatasetManifest.model_validate(value)
