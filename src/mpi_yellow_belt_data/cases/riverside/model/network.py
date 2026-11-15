"""Riverside v2 operating model, independent of publication infrastructure.

Simulate episodes and finite specialty appointment inventories; emit separate
dated observations and contributor truth. See specification_v2.md for limits.
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import random
import tempfile
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml

from mpi_yellow_belt_data.catalog import _yaml
from mpi_yellow_belt_data.contracts import NetworkConfig
from mpi_yellow_belt_data.resources import _CHECKOUT
from mpi_yellow_belt_data.tables_v2 import TABLES, TRUTH_FIELDS

HOME = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = HOME / "config/network_v2.yml"
DAY = timedelta(days=1)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def load_config(path: Path = DEFAULT_CONFIG) -> dict:
    config = _yaml(path)
    NetworkConfig.model_validate(config)
    assert isinstance(config, dict)
    return config


def advance(value: date, days: int = 0) -> date:
    value += days * DAY
    while value.weekday() >= 5:
        value += DAY
    return value


class SlotCalendar:
    """Finite new-patient slots, allocated in booking-request order.

    Later requests can fill earlier gaps. Cancellations do not release slots in
    this version; it models first offers, not a complete scheduling optimizer.
    """

    def __init__(self, config: dict):
        self.config = config
        self.used: Counter = Counter()

    def capacity(self, specialty: str, day: date) -> int:
        if day.weekday() >= 5:
            return 0
        slots = self.config["specialties"][specialty][1]
        # Different seasonal capacity pressures; independent of centralization.
        if specialty in {
            "neurology",
            "endocrinology",
            "rheumatology",
        } and day.month in {11, 12, 1}:
            slots = max(1, round(slots * 0.8))
        if specialty in {"cardiology", "pulmonology"} and day.month in {7, 8}:
            slots = max(1, round(slots * 0.9))
        return slots

    def reserve(self, specialty: str, earliest: date) -> date:
        candidate = advance(earliest)
        while self.used[specialty, candidate] >= self.capacity(specialty, candidate):
            candidate = advance(candidate, 1)
        self.used[specialty, candidate] += 1
        return candidate


def episode_dates(config: dict, rng: random.Random) -> list[tuple[date, bool]]:
    start = date.fromisoformat(config["start_date"])
    end = date.fromisoformat(config["end_date"])
    days = [start + i * DAY for i in range((end - start).days + 1)]
    weights = [
        (1 if d.weekday() < 5 else 0.08) * (1.12 if d.month in {1, 2, 11, 12} else 1)
        for d in days
    ]
    new = [
        (d, False) for d in rng.choices(days, weights=weights, k=config["new_episodes"])
    ]
    inherited = [
        (start - rng.randint(1, 90) * DAY, True)
        for _ in range(config["inherited_episodes"])
    ]
    return sorted(inherited + new)


class Extracts:
    def __init__(self, root: Path, config: dict):
        self.root = root
        self.cutoffs = {
            "initial": date.fromisoformat(config["initial_cutoff"]),
            "investigation": date.fromisoformat(config["investigation_cutoff"]),
            "followup": date.fromisoformat(config["end_date"]),
        }
        self.streams = []
        self.writers = {}
        self.rows = Counter()
        for release in self.cutoffs:
            (root / release).mkdir()
            for table, fields in TABLES.items():
                stream = (root / release / f"{table}.csv").open(
                    "x", newline="", encoding="utf-8"
                )
                self.streams.append(stream)
                writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
                writer.writeheader()
                self.writers[release, table] = writer

    def emit(self, table: str, available: date, row: dict) -> None:
        for release, cutoff in self.cutoffs.items():
            if available <= cutoff:
                self.writers[release, table].writerow(row)
                self.rows[release, table] += 1

    def appointment(self, row: dict) -> None:
        for release, cutoff in self.cutoffs.items():
            if row["booked_date"] <= cutoff:
                visible = dict(row)
                if row["outcome_recorded_date"] > cutoff:
                    visible["outcome"] = ""
                    visible["outcome_recorded_date"] = ""
                self.writers[release, "appointments"].writerow(visible)
                self.rows[release, "appointments"] += 1

    def close(self) -> None:
        for stream in self.streams:
            stream.close()


def simulate(root: Path, config: dict) -> dict:
    rng = random.Random(config["seed"])
    start = date.fromisoformat(config["start_date"])
    central = date.fromisoformat(config["centralization_date"])
    pilot_start = date.fromisoformat(config["pilot_date"])
    end = date.fromisoformat(config["end_date"])
    extracts = Extracts(root, config)
    calendar = SlotCalendar(config)
    counts: Counter = Counter()
    minutes: Counter = Counter()
    booking_requests: list[tuple[date, str, str, bool, int, bool, dict[str, Any]]] = []
    truth: list[dict[str, Any]] = []
    event_number = 0
    observed_counts: Counter = Counter()
    eligible_from = {}

    def event(
        rid: str,
        when: date,
        kind: str,
        owner: str,
        detail: str = "",
        lag: int | None = None,
    ) -> date:
        nonlocal event_number
        event_number += 1
        # Old histories are less complete. Absence is not absence of action.
        if (
            when < central
            and kind
            not in {"order_received", "internal_visit", "outside_care_reported"}
            and rng.random() < 0.3
        ):
            return when
        recorded = when + (rng.randint(0, 3) if lag is None else lag) * DAY
        extracts.emit(
            "events",
            recorded,
            dict(
                zip(
                    TABLES["events"],
                    (f"EV{event_number:08d}", rid, when, recorded, kind, owner, detail),
                    strict=True,
                )
            ),
        )
        observed_counts[kind] += recorded <= end
        return recorded

    for number, (ordered, inherited) in enumerate(episode_dates(config, rng), 1):
        rid = f"RV2-{number:07d}"
        specialty = rng.choices(
            list(config["specialties"]),
            weights=[v[0] for v in config["specialties"].values()],
        )[0]
        source = rng.choices(
            list(config["source_weights"]),
            weights=list(config["source_weights"].values()),
        )[0]
        if source == "affiliated_primary_care":
            site = f"AP{rng.randint(1, config['affiliated_sites']):02d}"
        elif source == "independent_practice":
            # A few frequent senders, a long tail of occasional senders.
            site = f"IP{rng.choices(range(1, config['independent_practices'] + 1), weights=[1 / i**0.65 for i in range(1, config['independent_practices'] + 1)])[0]:02d}"
        else:
            site = "ED01" if source == "ed_followup" else f"SP{rng.randint(1, 27):02d}"
        urgent = rng.random() < (0.3 if source == "ed_followup" else 0.08)
        travel = rng.choices([15, 35, 65, 100, 145], weights=[25, 30, 25, 15, 5])[
            0
        ] + rng.randint(0, 14)
        available = start if inherited else ordered
        eligible_from[rid] = available
        received = advance(available)
        pilot_eligible = (
            ordered >= pilot_start
            and site in config["pilot"]["source_sites"]
            and specialty in config["pilot"]["specialties"]
        )
        pilot = pilot_eligible and rng.random() < config["pilot"]["fidelity"]
        counts["inherited" if inherited else "new"] += 1
        counts[f"specialty:{specialty}"] += not inherited
        counts[f"source:{source}"] += not inherited
        counts["pilot_eligible"] += pilot_eligible
        counts["pilot_delivered"] += pilot
        extracts.emit(
            "referrals",
            available,
            dict(
                zip(
                    TABLES["referrals"],
                    (
                        rid,
                        f"PT{rng.randint(1, max(1, round(config['new_episodes'] * 0.75))):07d}",
                        ordered,
                        site,
                        source,
                        specialty,
                        "urgent" if urgent else "routine",
                        travel,
                        int(inherited),
                        available,
                    ),
                    strict=True,
                )
            ),
        )
        intake_owner = (
            "central_intake" if ordered >= central else "local_referral_staff"
        )
        event(
            rid,
            received,
            "order_received",
            intake_owner,
            "inherited_open_record" if inherited else "new_episode",
            lag=0,
        )
        admin = advance(received, rng.randint(0, 3))
        work = 6.0
        if rng.random() < (0.29 if source == "independent_practice" else 0.13):
            event(
                rid, admin, "documents_requested", intake_owner, "administrative_check"
            )
            admin = advance(admin, rng.randint(2, 14))
            event(rid, admin, "documents_received", "referring_practice")
            work += 9
        event(rid, admin, "admin_complete", intake_owner)
        contact = advance(received, rng.randint(0, 4))
        contacted = False
        for attempt in range(rng.randint(1, 3)):
            result = (
                "reached" if rng.random() < (0.8 if attempt else 0.65) else "no_answer"
            )
            contacted |= result == "reached"
            event(rid, contact, "contact_attempt", intake_owner, result)
            work += 4 if result == "reached" else 2
            if contacted:
                break
            contact = advance(contact, rng.randint(2, 5))
        handoff = rng.randint(1, 3) if pilot else rng.randint(1, 7)
        reviewed = advance(admin, handoff)
        event(rid, reviewed, "clinical_review", "specialty", "review_started")
        ready = reviewed
        if rng.random() < config["specialties"][specialty][2]:
            event(
                rid,
                reviewed,
                "clinical_clarification_requested",
                "specialty",
                "clinical_question_or_workup",
            )
            ready = advance(reviewed, rng.randint(3, 18))
            event(rid, ready, "clinical_response_received", "referring_practice")
            work += 10
        event(rid, ready, "clinical_ready", "specialty")
        if rng.random() < 0.24:
            auth = advance(admin, rng.randint(2, 16))
            event(rid, admin, "authorization_requested", "authorization_team")
            event(rid, auth, "authorization_received", "authorization_team")
            ready_to_book = max(ready, auth)
            work += 5
        else:
            ready_to_book = ready
        work += config["pilot"]["additional_minutes_per_episode"] if pilot else 0
        requested = advance(max(ready_to_book, contact), rng.randint(0, 4))
        # Dispositions depend on patient choices and contact, not an oracle
        # delay_reason column. Inherited cases are unresolved at window start.
        choice = rng.random()
        outcome = (
            "outside"
            if choice < 0.09
            else "declined"
            if choice < 0.15
            else "unresolved"
            if not contacted and choice < 0.5
            else "internal"
        )
        record: dict[str, Any] = {
            "referral_id": rid,
            "admin_complete_date": admin,
            "clinical_ready_date": ready,
            "booked_date": "",
            "care_date": "",
            "terminal_date": "",
            "outcome_at_end": outcome,
            "outside_documented_date": "",
            "pilot_delivered": int(pilot),
            "coordination_minutes": work,
        }
        if outcome == "internal":
            booking_requests.append(
                (requested, rid, specialty, urgent, travel, pilot, record)
            )
        elif outcome in {"outside", "declined"}:
            terminal = advance(requested, rng.randint(3, 24))
            record["terminal_date"] = terminal
            if outcome == "outside":
                record["care_date"] = terminal
                if rng.random() < (0.75 if pilot else 0.35):
                    documented = event(
                        rid,
                        advance(terminal, rng.randint(2, 35)),
                        "outside_care_reported",
                        "referring_practice",
                        "patient_or_external_office_report",
                    )
                    record["outside_documented_date"] = documented
            else:
                event(rid, terminal, "patient_declined", intake_owner, "patient_report")
        else:
            event(rid, requested, "awaiting_response", intake_owner)

        # Complaint propensity depends on lived friction, not an assigned cause.
        friction = (ready - received).days
        if rng.random() < min(
            0.15, 0.008 + friction * 0.0015 + (0.025 if not contacted else 0)
        ):
            complaint_day = advance(received, rng.randint(8, max(9, friction + 12)))
            theme, account = rng.choice(
                [
                    (
                        "unclear_next_step",
                        "I have called both offices and still do not know who will call me.",
                    ),
                    (
                        "repeat_information",
                        "The clinic says it sent the paperwork. The other office says it needs more.",
                    ),
                    (
                        "callback",
                        "I was expecting a call and arranged my work around it. I need to know what happens next.",
                    ),
                ]
            )
            extracts.emit(
                "complaints",
                complaint_day,
                dict(
                    zip(
                        TABLES["complaints"],
                        (f"CP{number:07d}", rid, complaint_day, theme, account),
                        strict=True,
                    )
                ),
            )
        truth.append(record)

    # Allocate appointments in request order, never in original order-date order.
    for requested, rid, specialty, urgent, travel, _pilot, record in sorted(
        booking_requests
    ):
        event(rid, requested, "booking_requested", "specialty")
        appointment = calendar.reserve(
            specialty, advance(requested, 1 if urgent else 7)
        )
        record["booked_date"] = requested
        event(
            rid,
            requested,
            "appointment_booked",
            "specialty",
            appointment.isoformat(),
            lag=0,
        )
        event(
            rid,
            max(requested, advance(appointment - 3 * DAY)),
            "reminder_sent",
            "specialty",
        )
        no_show = min(0.22, 0.06 + travel / 1800)
        roll = rng.random()
        outcome = (
            "completed"
            if roll >= no_show + 0.07
            else "no_show"
            if roll < no_show
            else "cancelled"
        )
        recorded = event(
            rid,
            appointment,
            "internal_visit" if outcome == "completed" else outcome,
            "specialty",
            lag=1,
        )
        extracts.appointment(
            dict(
                zip(
                    TABLES["appointments"],
                    (f"AT-{rid}", rid, requested, appointment, outcome, recorded),
                    strict=True,
                )
            )
        )
        record["terminal_date"] = appointment
        record["outcome_at_end"] = outcome
        record["care_date"] = appointment if outcome == "completed" else ""
        record["coordination_minutes"] += 5
        if (appointment - requested).days > 28 and rng.random() < 0.09:
            when = advance(requested, 12)
            extracts.emit(
                "complaints",
                when,
                dict(
                    zip(
                        TABLES["complaints"],
                        (
                            f"CP-AT-{rid}",
                            rid,
                            when,
                            "appointment_access",
                            "They offered me a date, but I am worried about how long I have to wait.",
                        ),
                        strict=True,
                    )
                ),
            )

    # Small independent record reviews supply imperfect corroboration. They are
    # sampled from each release's eligible population, including unresolved cases.
    for release, cutoff in extracts.cutoffs.items():
        review = advance(cutoff - 10 * DAY)
        for record in truth:
            rid = record["referral_id"]
            if (
                eligible_from[rid] > review
                or rng.random() >= config["audit_probability"]
            ):
                continue
            care = record["care_date"]
            terminal = record["terminal_date"]
            if care and care <= review:
                finding = (
                    "outside_care_confirmed"
                    if record["outcome_at_end"] == "outside"
                    else "internal_care_confirmed"
                )
                evidence = (
                    "patient_followup"
                    if finding.startswith("outside")
                    else "visit_record"
                )
            elif (
                terminal
                and terminal <= review
                and record["outcome_at_end"] == "declined"
            ):
                finding, evidence, care = "declined_confirmed", "patient_followup", ""
            else:
                finding, evidence, care = "unable_to_confirm_care", "record_review", ""
            extracts.emit(
                "audit",
                review,
                dict(
                    zip(
                        TABLES["audit"],
                        (f"AU-{release}-{rid}", rid, review, finding, evidence, care),
                        strict=True,
                    )
                ),
            )

    (root / "reference").mkdir()
    with (root / "reference/model_truth.csv").open(
        "x", newline="", encoding="utf-8"
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=TRUTH_FIELDS, lineterminator="\n")
        writer.writeheader()
        for record in truth:
            minutes["all"] += record["coordination_minutes"]
            terminal = record["terminal_date"]
            if not terminal or terminal > end:
                record["outcome_at_end"] = "pending_at_end"
            for field in (
                "admin_complete_date",
                "clinical_ready_date",
                "booked_date",
                "care_date",
                "terminal_date",
                "outside_documented_date",
            ):
                if record[field] and record[field] > end:
                    record[field] = ""
            counts[f"outcome:{record['outcome_at_end']}"] += 1
            writer.writerow(record)
    with (root / "reference/daily_capacity.csv").open(
        "x", newline="", encoding="utf-8"
    ) as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["date", "specialty", "new_patient_slots", "reserved_slots"])
        for offset in range((end - start).days + 1):
            day = start + offset * DAY
            for specialty in config["specialties"]:
                values = [
                    day,
                    specialty,
                    calendar.capacity(specialty, day),
                    calendar.used[specialty, day],
                ]
                writer.writerow(values)
                extracts.emit(
                    "capacity", day, dict(zip(TABLES["capacity"], values, strict=True))
                )
    extracts.close()
    return {
        "counts": dict(sorted(counts.items())),
        "extract_rows": {f"{r}/{t}": n for (r, t), n in sorted(extracts.rows.items())},
        "coordination_hours": round(minutes["all"] / 60, 1),
        "observed_events": dict(sorted(observed_counts.items())),
    }


def generate(
    output: Path,
    *,
    config_path: Path = DEFAULT_CONFIG,
    sample: int | None = None,
    seed: int | None = None,
) -> dict:
    """Atomically create a new immutable local artifact; samples are experiments."""
    if output.exists() or output.is_symlink():
        raise ValueError(f"Destination already exists: {output}")
    config = load_config(config_path)
    if sample is not None:
        if sample <= 0:
            raise ValueError("Sample must be positive")
        scale = sample / config["new_episodes"]
        config["inherited_episodes"] = max(
            1, round(config["inherited_episodes"] * scale)
        )
        config["new_episodes"] = sample
    if seed is not None:
        config["seed"] = seed
    NetworkConfig.model_validate(config)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".riverside-v2-", dir=output.parent
    ) as temporary:
        stage = Path(temporary) / "payload"
        stage.mkdir()
        summary = simulate(stage, config)
        (stage / "reference/summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n"
        )
        files = []
        for path in sorted(stage.rglob("*")):
            if not path.is_file():
                continue
            item = {
                "path": path.relative_to(stage).as_posix(),
                "sha256": digest(path),
                "bytes": path.stat().st_size,
            }
            if path.suffix == ".csv":
                with path.open(newline="", encoding="utf-8") as stream:
                    reader = csv.reader(stream)
                    item["columns"] = next(reader)
                    item["rows"] = sum(1 for _ in reader)
            files.append(item)
        manifest = {
            "schema_version": 1,
            "case_id": "riverside",
            "version": "2.0.0"
            if sample is None and seed is None
            else "2.0.0-experiment",
            "data_schema": "riverside-linked-v2",
            "observation_window": f"{config['start_date']} through {config['end_date']}; inherited cases precede start",
            "provenance": {
                "classification": "synthetic",
                "source_revision": config["base_source_revision"],
                "source_revision_note": "Working source hashes below identify changes beyond the base revision.",
                "python": platform.python_version(),
                "runtime_versions": {"pyyaml": yaml.__version__},
                "config": config,
                "source_sha256": {
                    "model/network.py": digest(Path(__file__)),
                    "config/network_v2.yml": digest(config_path),
                },
                "lockfile_sha256": digest(_CHECKOUT / "uv.lock")
                if (_CHECKOUT / "uv.lock").exists()
                else None,
                "releases": extract_cutoffs(config),
            },
            "files": files,
        }
        (stage / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        )
        from mpi_yellow_belt_data.table_validation_v2 import validate

        validate(stage)
        if output.exists() or output.is_symlink():
            raise ValueError(f"Destination already exists: {output}")
        stage.rename(output)
    return summary


def extract_cutoffs(config: dict) -> dict[str, str]:
    return {
        "initial": config["initial_cutoff"],
        "investigation": config["investigation_cutoff"],
        "followup": config["end_date"],
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--sample", type=int)
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()
    summary = generate(
        args.output, config_path=args.config, sample=args.sample, seed=args.seed
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
