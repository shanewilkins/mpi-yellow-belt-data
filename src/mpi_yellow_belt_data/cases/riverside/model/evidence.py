"""Validate and prepare Riverside v2 evidence without exposing later releases."""

from __future__ import annotations

import csv
import importlib.metadata
import json
import shutil
import tempfile
from pathlib import Path

from mpi_yellow_belt_data.catalog import _parse, relative_file, sha256
from mpi_yellow_belt_data.contracts import NetworkManifest
from mpi_yellow_belt_data.resources import asset_file
from mpi_yellow_belt_data.tables_v2 import TABLES, TRUTH_FIELDS
from mpi_yellow_belt_data.workspaces import write_workspace_identity


def rows(path: Path):
    with path.open(newline="", encoding="utf-8") as stream:
        yield from csv.DictReader(stream)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def check(directory: Path, *, pin: Path | None = None) -> dict:
    manifest_path = relative_file(directory, "manifest.json")
    if pin:
        require(
            sha256(manifest_path) == sha256(pin), "Manifest differs from pinned release"
        )
    manifest = _parse(
        NetworkManifest, json.loads(manifest_path.read_text()), manifest_path
    ).model_dump(mode="json", exclude_unset=True)
    require(
        manifest["case_id"] == "riverside"
        and manifest["data_schema"] == "riverside-linked-v2",
        "Wrong case or schema",
    )
    declared = {"manifest.json"}
    for item in manifest["files"]:
        name = item["path"]
        require(name not in declared, f"Duplicate manifest path: {name}")
        declared.add(name)
        path = relative_file(directory, name)
        require(
            path.stat().st_size == item["bytes"] and sha256(path) == item["sha256"],
            f"Checksum mismatch: {name}",
        )
        if "rows" in item:
            with path.open(newline="", encoding="utf-8") as stream:
                reader = csv.reader(stream)
                require(next(reader) == item["columns"], f"Columns differ: {name}")
                require(
                    sum(1 for _ in reader) == item["rows"], f"Row count differs: {name}"
                )
    require(
        {
            p.relative_to(directory).as_posix()
            for p in directory.rglob("*")
            if p.is_file()
        }
        == declared,
        "Undeclared or missing dataset files",
    )
    require(
        not any(p.is_symlink() for p in directory.rglob("*")), "Symlink in artifact"
    )
    config = manifest["provenance"]["config"]
    require(
        manifest["provenance"]["releases"]
        == {
            "initial": config["initial_cutoff"],
            "investigation": config["investigation_cutoff"],
            "followup": config["end_date"],
        },
        "Unexpected release identity or cutoff",
    )
    expected_files = {
        f"{release}/{table}.csv"
        for release in ("initial", "investigation", "followup")
        for table in TABLES
    }
    expected_files |= {
        "reference/model_truth.csv",
        "reference/daily_capacity.csv",
        "reference/summary.json",
        "manifest.json",
    }
    require(declared == expected_files, "Unexpected evidence inventory")
    report = {}
    for release, cutoff in sorted(
        manifest["provenance"]["releases"].items(), key=lambda item: item[1]
    ):
        refs = {}
        for row in rows(directory / release / "referrals.csv"):
            rid = row["referral_id"]
            require(rid not in refs, f"Duplicate referral: {rid}")
            require(
                row["order_date"] <= row["record_available_date"] <= cutoff,
                "Future referral leaked",
            )
            refs[rid] = row
        events = set()
        for row in rows(directory / release / "events.csv"):
            rid = row["referral_id"]
            require(rid in refs, f"Orphan event: {rid}")
            require(row["event_id"] not in events, "Duplicate event")
            events.add(row["event_id"])
            require(
                refs[rid]["order_date"]
                <= row["occurred_date"]
                <= row["recorded_date"]
                <= cutoff,
                "Event chronology or release leak",
            )
        appointments = set()
        for row in rows(directory / release / "appointments.csv"):
            require(row["referral_id"] in refs, "Orphan appointment")
            require(row["appointment_id"] not in appointments, "Duplicate appointment")
            appointments.add(row["appointment_id"])
            require(
                refs[row["referral_id"]]["order_date"] <= row["booked_date"] <= cutoff
                and row["booked_date"] < row["appointment_date"],
                "Booking chronology",
            )
            require(
                bool(row["outcome"]) == bool(row["outcome_recorded_date"]),
                "Partial outcome record",
            )
            if row["outcome"]:
                require(
                    row["appointment_date"] <= row["outcome_recorded_date"] <= cutoff,
                    "Future outcome leaked",
                )
        for table, key, date_field in (
            ("complaints", "complaint_id", "received_date"),
            ("audit", "audit_id", "review_date"),
        ):
            ids = set()
            for row in rows(directory / release / f"{table}.csv"):
                require(
                    row["referral_id"] in refs and row[key] not in ids,
                    f"Orphan or duplicate {table}",
                )
                ids.add(row[key])
                require(
                    refs[row["referral_id"]]["order_date"] <= row[date_field] <= cutoff,
                    f"Future {table} leaked",
                )
                if table == "audit" and row["care_date"]:
                    require(
                        row["care_date"] <= row["review_date"],
                        "Audit reveals future care",
                    )
        for row in rows(directory / release / "capacity.csv"):
            require(row["date"] <= cutoff, "Future capacity leaked")
            require(
                0 <= int(row["reserved_slots"]) <= int(row["new_patient_slots"]),
                "Specialty capacity exceeded",
            )
        report[release] = {
            "referrals": len(refs),
            "events": len(events),
            "appointments": len(appointments),
        }
    truth = {}
    for row in rows(directory / "reference/model_truth.csv"):
        rid = row["referral_id"]
        require(rid not in truth, "Duplicate model truth")
        truth[rid] = row
        require(
            not row["clinical_ready_date"]
            or row["admin_complete_date"] <= row["clinical_ready_date"],
            "Readiness chronology",
        )
        require(
            not row["booked_date"] or row["clinical_ready_date"] <= row["booked_date"],
            "Booked before clinical readiness",
        )
    require(set(truth) == set(refs), "Truth and final extract populations differ")
    require(
        len(refs) == config["new_episodes"] + config["inherited_episodes"],
        "Population conservation",
    )
    require(
        sum(int(r["inherited"]) for r in refs.values()) == config["inherited_episodes"],
        "Inherited population differs",
    )
    for row in rows(directory / "reference/daily_capacity.csv"):
        require(
            0 <= int(row["reserved_slots"]) <= int(row["new_patient_slots"]),
            "Specialty capacity exceeded",
        )
    # Every learner table has an explicit schema; no model truth is appended.
    for table, fields in TABLES.items():
        with (directory / "initial" / f"{table}.csv").open() as stream:
            require(
                next(csv.reader(stream)) == fields,
                f"Unexpected learner fields: {table}",
            )
    with (directory / "reference/model_truth.csv").open() as stream:
        require(next(csv.reader(stream)) == TRUTH_FIELDS, "Unexpected truth fields")
    return report


def prepare(
    directory: Path, output: Path, *, release: str = "initial", pin: Path | None = None
) -> Path:
    """Copy one dated release, never truth or later evidence, into a workspace."""
    check(directory, pin=pin)
    require(release in {"initial", "investigation", "followup"}, "Unknown release")
    require(
        not output.exists() and not output.is_symlink(), "Destination already exists"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".riverside-learner-", dir=output.parent
    ) as temporary:
        stage = Path(temporary) / "workspace"
        shutil.copytree(directory / release, stage / "data")
        for name in ("scenario.md", "data_dictionary.md"):
            shutil.copyfile(asset_file("docs/riverside/" + name), stage / name)
        shutil.copyfile(
            asset_file("docs/riverside/learner_provenance.md"), stage / "provenance.md"
        )
        if release == "followup":
            shutil.copyfile(
                asset_file("docs/riverside/pilot_v2.md"), stage / "pilot.md"
            )
        shutil.copyfile(
            asset_file("notebooks/riverside/investigate.py"), stage / "investigate.py"
        )
        requirements = [
            f"{name}=={importlib.metadata.version(name)}"
            for name in ("marimo", "polars")
        ]
        (stage / "pyproject.toml").write_text(
            '[project]\nname = "riverside-v2-investigation"\nversion = "0.0.0"\nrequires-python = ">=3.15,<3.16"\ndependencies = '
            + json.dumps(requirements, indent=2)
            + "\n"
        )
        selected = json.loads((directory / "manifest.json").read_text())
        (stage / "evidence.json").write_text(
            json.dumps(
                {
                    "case_id": "riverside",
                    "version": selected["version"],
                    "release": release,
                    "as_of": selected["provenance"]["releases"][release],
                    "parent_manifest_sha256": sha256(directory / "manifest.json"),
                    "files": [
                        item
                        for item in selected["files"]
                        if item["path"].startswith(release + "/")
                    ],
                },
                indent=2,
            )
            + "\n"
        )
        (stage / "README.md").write_text(
            f"# Riverside investigation\n\nEvidence release: {release}.\nRead scenario.md and data_dictionary.md.\nRun `uv sync`, then `uv run marimo edit investigate.py` to open the starter.\nKeep uv.lock with the investigation. Initial setup needs package access or a populated cache.\nPersonal work under ignored work/ is not backed up by Git. Use mpi-yellow-belt-data export-work to save it outside this checkout.\nFor updates, use a fresh course checkout beside this one and transfer personal work deliberately.\nThe starter shows how to join records; it does not select a cause or intervention.\n"
        )
        shutil.copyfile(asset_file("LICENSE.md"), stage / "LICENSE.md")
        (stage / ".python-version").write_text("3.15\n")
        write_workspace_identity(
            stage,
            case_id="riverside",
            dataset_version=selected["version"],
            release=release,
            manifest_sha256=sha256(directory / "manifest.json"),
        )
        if output.exists() or output.is_symlink():
            raise ValueError(f"Destination already exists: {output}")
        stage.rename(output)
    return output


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--pin", type=Path)
    parser.add_argument("--prepare", type=Path)
    parser.add_argument(
        "--release", default="initial", choices=["initial", "investigation", "followup"]
    )
    args = parser.parse_args()
    if args.prepare:
        print(prepare(args.directory, args.prepare, release=args.release, pin=args.pin))
    else:
        print(json.dumps(check(args.directory, pin=args.pin), indent=2))


if __name__ == "__main__":
    main()
