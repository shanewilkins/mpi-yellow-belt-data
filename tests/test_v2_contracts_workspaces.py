from __future__ import annotations

import json
import runpy
import zipfile

import polars as pl
import pytest

from mpi_yellow_belt_data import workspaces
from mpi_yellow_belt_data.cases.riverside.model.evidence import prepare
from mpi_yellow_belt_data.cases.riverside.model.network import generate, load_config
from mpi_yellow_belt_data.catalog import CaseError, sha256
from mpi_yellow_belt_data.contracts import (
    NetworkConfig,
    NetworkManifest,
    export_schemas,
)
from mpi_yellow_belt_data.resources import release_pin
from mpi_yellow_belt_data.table_validation_v2 import validate_table


@pytest.fixture(scope="module")
def sample(tmp_path_factory):
    output = tmp_path_factory.mktemp("linked") / "artifact"
    generate(output, sample=600)
    return output


@pytest.mark.parametrize(
    "field,value",
    [
        ("seed", True),
        ("audit_probability", -0.1),
        ("audit_probability", float("nan")),
        ("new_episodes", 0),
        ("coordination_fte", 0),
        ("initial_cutoff", "2027-01-01"),
    ],
)
def test_invalid_model_configuration_rejected(field, value):
    config = load_config()
    config[field] = value
    with pytest.raises(ValueError):
        NetworkConfig.model_validate(config)


def test_adopted_manifest_and_schema_exports_stay_compatible():
    import jsonschema

    from mpi_yellow_belt_data.catalog import PACKAGE_ROOT

    raw = json.loads(release_pin().read_text())
    assert (
        NetworkManifest.model_validate(raw).model_dump(mode="json", exclude_unset=True)
        == raw
    )
    jsonschema.validate(raw, NetworkManifest.model_json_schema())
    export_schemas(PACKAGE_ROOT / "schemas", check=True)


def test_stage_preparation_execution_and_personal_backup(sample, tmp_path):
    workspace = prepare(sample, tmp_path / "work")
    identity = workspaces.verify_workspace(workspace)
    assert identity.release == "initial"
    assert not list(workspace.rglob("*truth*"))
    assert ">=3.15,<3.16" in (workspace / "pyproject.toml").read_text()
    _, definitions = runpy.run_path(str(workspace / "investigate.py"))["app"].run()
    assert definitions["referrals"].collect().height > 0
    personal = workspace / "investigate.py"
    personal.write_text(personal.read_text() + "\n# My investigation note\n")
    workspaces.verify_workspace(workspace)
    backup = workspaces.export_work(workspace, tmp_path / "backup.zip")
    with zipfile.ZipFile(backup) as archive:
        assert b"My investigation note" in archive.read("investigate.py")
        assert json.loads(archive.read("backup-receipt.json"))["workspace"][
            "course_version"
        ]
    with pytest.raises(ValueError, match="already exists"):
        prepare(sample, workspace)
    with pytest.raises(CaseError, match="already exists"):
        workspaces.export_work(workspace, backup)
    (workspace / "data/referrals.csv").write_text("damaged")
    with pytest.raises(CaseError, match="evidence changed"):
        workspaces.verify_workspace(workspace)


def test_stage_archive_requires_pin_and_preserves_work(sample, tmp_path, monkeypatch):
    prepared = prepare(sample, tmp_path / "prepared")
    bundle = workspaces.export_work(prepared, tmp_path / "stage.zip")
    index = tmp_path / "stages.json"
    index.write_text(json.dumps({"stages": {"initial": {"sha256": sha256(bundle)}}}))
    monkeypatch.setattr(workspaces, "asset_file", lambda name: index)
    target = workspaces.prepare_archive(bundle, tmp_path / "work")
    assert workspaces.verify_workspace(target).release == "initial"
    with pytest.raises(CaseError, match="already exists"):
        workspaces.prepare_archive(bundle, target)
    bundle.write_bytes(bundle.read_bytes() + b"tamper")
    with pytest.raises(CaseError, match="checksum"):
        workspaces.prepare_archive(bundle, tmp_path / "bad")


def test_archive_traversal_and_personal_symlinks_rejected(
    sample, tmp_path, monkeypatch
):
    bundle = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr("../escape", "bad")
    index = tmp_path / "stages.json"
    index.write_text(json.dumps({"stages": {"initial": {"sha256": sha256(bundle)}}}))
    monkeypatch.setattr(workspaces, "asset_file", lambda name: index)
    with pytest.raises(ValueError, match="relative path"):
        workspaces.prepare_archive(bundle, tmp_path / "bad")
    assert not (tmp_path / "escape").exists()
    monkeypatch.undo()
    workspace = prepare(sample, tmp_path / "work")
    (workspace / "outside").symlink_to(index)
    with pytest.raises(CaseError, match="symlink"):
        workspaces.export_work(workspace, tmp_path / "backup.zip")


def test_structurally_plausible_bad_categories_and_capacity_are_rejected(
    sample, tmp_path
):
    path = tmp_path / "capacity.csv"
    frame = pl.read_csv(sample / "initial/capacity.csv")
    frame.with_columns(pl.lit(-1).alias("new_patient_slots")).write_csv(path)
    with pytest.raises(CaseError, match="invalid capacity"):
        validate_table(path, "capacity", specialties=set(load_config()["specialties"]))
    frame.with_columns(
        pl.when(pl.col("specialty") == "cardiology")
        .then(pl.lit("unknown"))
        .otherwise(pl.col("specialty"))
        .alias("specialty")
    ).write_csv(path)
    with pytest.raises(CaseError, match="unknown specialty"):
        validate_table(path, "capacity", specialties=set(load_config()["specialties"]))


def test_backing_up_a_prepared_archive_has_one_current_receipt(
    sample, tmp_path, monkeypatch
):
    prepared = prepare(sample, tmp_path / "prepared")
    bundle = workspaces.export_work(prepared, tmp_path / "stage.zip")
    index = tmp_path / "stages.json"
    index.write_text(json.dumps({"stages": {"initial": {"sha256": sha256(bundle)}}}))
    monkeypatch.setattr(workspaces, "asset_file", lambda name: index)
    restored = workspaces.prepare_archive(bundle, tmp_path / "restored")
    backup = workspaces.export_work(restored, tmp_path / "personal.zip")
    with zipfile.ZipFile(backup) as archive:
        assert archive.namelist().count("backup-receipt.json") == 1
