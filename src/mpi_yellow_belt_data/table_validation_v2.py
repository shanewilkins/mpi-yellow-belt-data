"""Optional structural acceptance of typed linked evidence, preserving domain checks."""

from pathlib import Path

import pandera.polars as pa
import polars as pl

from mpi_yellow_belt_data.cases.riverside.model.evidence import check
from mpi_yellow_belt_data.catalog import CaseError
from mpi_yellow_belt_data.tables_v2 import TABLES, TRUTH_FIELDS


def text(
    *, nullable: bool = False, unique: bool = False, values: list[str] | None = None
) -> pa.Column:
    return pa.Column(
        pl.String,
        nullable=nullable,
        unique=unique,
        checks=pa.Check.isin(values) if values else None,
    )


def integer(*, binary: bool = False) -> pa.Column:
    return pa.Column(
        pl.Int64, checks=pa.Check.isin([0, 1]) if binary else pa.Check.ge(0)
    )


def day(*, nullable: bool = False) -> pa.Column:
    return pa.Column(pl.Date, nullable=nullable)


COLUMNS = {
    "referrals": {
        "referral_id": text(unique=True),
        "patient_id": text(),
        "order_date": day(),
        "source_site": text(),
        "source_type": text(
            values=[
                "affiliated_primary_care",
                "independent_practice",
                "ed_followup",
                "other_specialty",
            ]
        ),
        "specialty": text(),
        "priority": text(values=["routine", "urgent"]),
        "travel_minutes": integer(),
        "inherited": integer(binary=True),
        "record_available_date": day(),
    },
    "events": {
        "event_id": text(unique=True),
        "referral_id": text(),
        "occurred_date": day(),
        "recorded_date": day(),
        "event_type": text(
            values=[
                "order_received",
                "documents_requested",
                "documents_received",
                "admin_complete",
                "contact_attempt",
                "clinical_review",
                "clinical_clarification_requested",
                "clinical_response_received",
                "clinical_ready",
                "authorization_requested",
                "authorization_received",
                "booking_requested",
                "appointment_booked",
                "reminder_sent",
                "internal_visit",
                "no_show",
                "cancelled",
                "patient_declined",
                "awaiting_response",
                "outside_care_reported",
            ]
        ),
        "owner": text(),
        "detail": text(nullable=True),
    },
    "appointments": {
        "appointment_id": text(unique=True),
        "referral_id": text(unique=True),
        "booked_date": day(),
        "appointment_date": day(),
        "outcome": text(nullable=True, values=["completed", "no_show", "cancelled"]),
        "outcome_recorded_date": day(nullable=True),
    },
    "complaints": {
        "complaint_id": text(unique=True),
        "referral_id": text(),
        "received_date": day(),
        "theme": text(
            values=[
                "unclear_next_step",
                "repeat_information",
                "callback",
                "appointment_access",
            ]
        ),
        "patient_account": text(),
    },
    "audit": {
        "audit_id": text(unique=True),
        "referral_id": text(),
        "review_date": day(),
        "finding": text(
            values=[
                "outside_care_confirmed",
                "internal_care_confirmed",
                "declined_confirmed",
                "unable_to_confirm_care",
            ]
        ),
        "evidence_source": text(
            values=["patient_followup", "visit_record", "record_review"]
        ),
        "care_date": day(nullable=True),
    },
    "capacity": {
        "date": day(),
        "specialty": text(),
        "new_patient_slots": integer(),
        "reserved_slots": integer(),
    },
    "model_truth": {
        **{name: day(nullable=True) for name in TRUTH_FIELDS if name.endswith("_date")},
        "referral_id": text(unique=True),
        "outcome_at_end": text(),
        "pilot_delivered": integer(binary=True),
        "coordination_minutes": pa.Column(
            pl.Float64, checks=[pa.Check.ge(0), pa.Check.lt(float("inf"))]
        ),
    },
}
# The exchange determines order, including the contributor truth table.
COLUMNS["model_truth"] = {name: COLUMNS["model_truth"][name] for name in TRUTH_FIELDS}
SCHEMAS = {
    name: pa.DataFrameSchema(
        columns,
        name=f"riverside_linked_v2_{name}",
        strict=True,
        ordered=True,
        coerce=False,
        unique=["date", "specialty"] if name == "capacity" else None,
    )
    for name, columns in COLUMNS.items()
}


def validate_table(path: Path, name: str, *, specialties: set[str]) -> None:
    schema = SCHEMAS[name]
    # Parsing declares CSV types; dataframe validation never fills/coerces/repairs.
    types = {field: column.dtype.type for field, column in COLUMNS[name].items()}
    try:
        frame = pl.read_csv(path, schema_overrides=types, infer_schema_length=None)
        schema.validate(frame, lazy=True)
    except (
        pl.exceptions.PolarsError,
        pa.errors.SchemaError,
        pa.errors.SchemaErrors,
    ) as error:
        raise CaseError(f"{path}: invalid {name} table: {error}") from error
    if (
        "specialty" in frame.columns
        and not set(frame["specialty"].unique().to_list()) <= specialties
    ):
        raise CaseError(f"{path}: unknown specialty")
    if name == "audit":
        confirmed = pl.col("finding").is_in(
            ["outside_care_confirmed", "internal_care_confirmed"]
        )
        if frame.filter(confirmed != pl.col("care_date").is_not_null()).height:
            raise CaseError(f"{path}: finding and care-date availability disagree")


def validate(directory: Path, *, pin: Path | None = None) -> dict:
    import json

    report = check(directory, pin=pin)
    manifest = json.loads((directory / "manifest.json").read_text())
    specialties = set(manifest["provenance"]["config"]["specialties"])
    for release in ("initial", "investigation", "followup"):
        for name in TABLES:
            validate_table(
                directory / release / f"{name}.csv", name, specialties=specialties
            )
    validate_table(
        directory / "reference/model_truth.csv", "model_truth", specialties=specialties
    )
    validate_table(
        directory / "reference/daily_capacity.csv", "capacity", specialties=specialties
    )
    return report
