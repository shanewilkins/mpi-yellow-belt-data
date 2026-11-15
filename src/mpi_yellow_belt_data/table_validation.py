"""Optional, non-destructive acceptance rules for preserved Riverside v1 evidence."""

from pathlib import Path

import pandera.polars as pa
import polars as pl

from mpi_yellow_belt_data.cases.riverside.model.referrals import (
    INSURANCE_CLASSES,
    REFERRAL_SOURCES,
    SERVICE_LINES,
)
from mpi_yellow_belt_data.catalog import CaseError, check_dataset, dataset_directory


def category(values: list[str]) -> pa.Column:
    return pa.Column(pl.String, checks=pa.Check.isin(values))


SCHEMA = pa.DataFrameSchema(
    {
        "referral_id": pa.Column(
            pl.String, unique=True, checks=pa.Check.str_matches(r"^RV-\d{4}$")
        ),
        "order_date": pa.Column(pl.Date),
        "service_line": category(list(SERVICE_LINES)),
        "referral_source": category(list(REFERRAL_SOURCES)),
        "priority": category(["routine", "urgent"]),
        "authorization_required": category(["yes", "no"]),
        "completeness_status": category(["complete", "incomplete"]),
        "insurance_class": category(list(INSURANCE_CLASSES)),
        "booking_pathway": category(
            ["point_of_care", "central_queue_callback", "specialty_review_queue"]
        ),
        "status": category(
            [
                "completed",
                "closed_no_visit",
                "returned_for_clarification",
                "pending_review",
                "authorization_pending",
                "closed_external",
                "awaiting_patient_response",
            ]
        ),
        "status_update_days": pa.Column(pl.Int64, checks=pa.Check.in_range(0, 6)),
        "first_contact_date": pa.Column(pl.Date),
        "reminder_sent_date": pa.Column(pl.Date, nullable=True),
        "scheduled_date": pa.Column(pl.Date, nullable=True),
        "appointment_date": pa.Column(pl.Date, nullable=True),
        "lead_time_days": pa.Column(pl.Int64, nullable=True, checks=pa.Check.gt(0)),
        "booked_flag": category(["yes", "no"]),
        "visit_outcome": category(["completed", "no_show", "cancelled", "not_booked"]),
        "network_outcome": category(
            [
                "completed_in_network",
                "closed_without_visit",
                "pending_in_network",
                "completed_outside_system",
            ]
        ),
        "patient_barrier_reason": category(
            [
                "none",
                "transportation",
                "work_schedule",
                "forgot",
                "cost_concern",
                "symptoms_improved",
                "prefers_outside_system",
                "insurance_network",
                "earlier_external_access",
                "unreachable",
            ]
        ),
        "delay_reason": category(
            [
                "capacity_constraint",
                "ready_to_schedule",
                "patient_unreachable",
                "patient_preference_shift",
                "missing_information",
                "authorization_pending",
                "outside_system_leakage",
                "provider_review_queue",
            ]
        ),
    },
    name="riverside_preserved_v1",
    strict=True,
    ordered=True,
    coerce=False,
)


def require(frame: pl.DataFrame, invalid: pl.Expr, rule: str) -> None:
    failures = frame.filter(invalid.fill_null(True))
    if failures.height:
        raise CaseError(
            f"{rule}: {failures.height} invalid referrals; examples: {failures['referral_id'].head(5).to_list()}"
        )


def validate_frame(frame: pl.DataFrame) -> None:
    """Validate this synthetic profile without inferring a v2 observation cutoff."""
    try:
        SCHEMA.validate(frame, lazy=True)
    except (pa.errors.SchemaError, pa.errors.SchemaErrors) as error:
        raise CaseError(f"Riverside v1 table schema: {error}") from error
    if frame.is_empty():
        raise CaseError("Riverside v1 evidence is empty")
    order = pl.col("order_date")
    booked = pl.col("booked_flag") == "yes"
    for name in ("scheduled_date", "appointment_date", "lead_time_days"):
        require(
            frame,
            pl.col(name).is_not_null() != booked,
            "Booking fields and population disagree",
        )
    require(
        frame,
        (pl.col("visit_outcome") != "not_booked") != booked,
        "Visit outcome and booking population disagree",
    )
    require(frame, pl.col("first_contact_date") < order, "Contact precedes referral")
    require(
        frame,
        pl.col("reminder_sent_date").is_not_null()
        & (pl.col("reminder_sent_date") < order),
        "Reminder precedes referral",
    )
    # v1 lead time means order-to-booking, not order-to-care.
    require(
        frame.filter(booked),
        (pl.col("lead_time_days") != (pl.col("scheduled_date") - order).dt.total_days())
        | (pl.col("appointment_date") <= pl.col("scheduled_date")),
        "Booking lead time or appointment chronology disagrees",
    )
    require(
        frame,
        (pl.col("visit_outcome") == "completed")
        != (pl.col("network_outcome") == "completed_in_network"),
        "Completed-care outcomes disagree",
    )
    require(
        frame,
        (pl.col("visit_outcome") == "completed") != (pl.col("status") == "completed"),
        "Completed status disagrees",
    )


def validate_tables(directory: Path) -> dict[str, int]:
    try:
        frame = pl.read_csv(
            directory / "riverside_referrals.csv",
            try_parse_dates=True,
            infer_schema_length=None,
        )
    except pl.exceptions.PolarsError as error:
        raise CaseError(f"Cannot parse Riverside v1 table: {error}") from error
    validate_frame(frame)
    return {"referrals": frame.height}


def validate_release(*, root: Path | None = None) -> dict[str, int]:
    check_dataset("riverside", root=root)
    return validate_tables(dataset_directory("riverside", root=root))
