from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from mpi_yellow_belt_data.cases.riverside.model.evidence import check, prepare, rows
from mpi_yellow_belt_data.cases.riverside.model.network import (
    DEFAULT_CONFIG,
    SlotCalendar,
    digest,
    generate,
    load_config,
)


@pytest.fixture
def sample(tmp_path):
    destination = tmp_path / "sample"
    generate(destination, sample=600)
    return destination


def test_sample_conservation_dates_and_reproducibility(sample, tmp_path):
    report = check(sample)
    assert report["followup"]["referrals"] == 608
    assert report["initial"]["referrals"] < report["investigation"]["referrals"] < 608
    second = tmp_path / "second"
    generate(second, sample=600)
    first_manifest = json.loads((sample / "manifest.json").read_text())
    second_manifest = json.loads((second / "manifest.json").read_text())
    assert first_manifest == second_manifest
    with pytest.raises(ValueError, match="already exists"):
        generate(sample, sample=600)


def test_finite_slots_include_seasonal_capacity_and_weekends():
    from datetime import date

    calendar = SlotCalendar(load_config())
    day = date(2025, 11, 7)  # Friday
    slots = calendar.capacity("neurology", day)
    assert slots < load_config()["specialties"]["neurology"][1]
    offers = [calendar.reserve("neurology", day) for _ in range(slots + 1)]
    assert offers.count(day) == slots
    assert offers[-1] == date(2025, 11, 10)


def test_prepare_excludes_truth_and_later_releases(sample, tmp_path):
    workspace = prepare(sample, tmp_path / "learner")
    assert {p.name for p in (workspace / "data").iterdir()} == {
        "referrals.csv",
        "events.csv",
        "appointments.csv",
        "complaints.csv",
        "audit.csv",
        "capacity.csv",
    }
    assert not list(workspace.rglob("*truth*"))
    assert not (workspace / "followup").exists()
    assert (
        json.loads((workspace / "evidence.json").read_text())["as_of"] == "2025-12-31"
    )


def refresh_manifest(directory: Path, name: str):
    path = directory / name
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    item = next(item for item in manifest["files"] if item["path"] == name)
    item.update(sha256=digest(path), bytes=path.stat().st_size)
    manifest_path.write_text(json.dumps(manifest))


def test_validator_rejects_future_outcome_even_with_updated_checksums(sample):
    path = sample / "initial/appointments.csv"
    records = list(rows(path))
    records[0]["outcome"] = "completed"
    records[0]["outcome_recorded_date"] = "2026-01-01"
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    refresh_manifest(sample, "initial/appointments.csv")
    with pytest.raises(ValueError, match="Future outcome"):
        check(sample)


def test_validator_rejects_corruption_and_wrong_pin(sample, tmp_path):
    wrong_pin = tmp_path / "wrong.json"
    wrong_pin.write_text("{}")
    with pytest.raises(ValueError, match="pinned release"):
        check(sample, pin=wrong_pin)
    with (sample / "initial/referrals.csv").open("a") as stream:
        stream.write("corrupt\n")
    with pytest.raises(ValueError, match="Checksum mismatch"):
        check(sample)


def test_pilot_changes_only_eligible_episodes(tmp_path):
    import yaml

    config = load_config()
    config["pilot"]["source_sites"] = [f"AP{i:02d}" for i in range(1, 25)]
    config["pilot"]["specialties"] = list(config["specialties"])
    config["pilot"]["fidelity"] = 1
    config_path = tmp_path / "config.yml"
    config_path.write_text(yaml.safe_dump(config))
    destination = tmp_path / "pilot"
    generate(destination, sample=600, config_path=config_path)
    refs = {r["referral_id"]: r for r in rows(destination / "followup/referrals.csv")}
    treated = [
        r
        for r in rows(destination / "reference/model_truth.csv")
        if r["pilot_delivered"] == "1"
    ]
    assert treated
    assert all(
        refs[r["referral_id"]]["order_date"] >= "2026-04-01"
        and refs[r["referral_id"]]["source_type"] == "affiliated_primary_care"
        for r in treated
    )
    assert load_config(DEFAULT_CONFIG)["new_episodes"] == 150000
