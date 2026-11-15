"""Create a bounded contributor readout and inspectable journey excerpts."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl


def review(directory: Path, output: Path) -> dict:
    if output.exists():
        raise ValueError(f"Destination already exists: {output}")
    manifest = json.loads((directory / "manifest.json").read_text())
    config = manifest["provenance"]["config"]
    initial = pl.read_csv(directory / "initial/referrals.csv")
    events = pl.read_csv(directory / "initial/events.csv")
    appointments = pl.read_csv(directory / "initial/appointments.csv")
    truth = pl.read_csv(directory / "reference/model_truth.csv")
    audit = pl.read_csv(directory / "initial/audit.csv")
    stages = events.group_by("referral_id").agg(
        pl.col("occurred_date")
        .filter(pl.col("event_type") == "admin_complete")
        .min()
        .alias("admin"),
        pl.col("occurred_date")
        .filter(pl.col("event_type") == "clinical_ready")
        .min()
        .alias("ready"),
    )
    joined = (
        initial.join(stages, on="referral_id", how="left")
        .join(appointments, on="referral_id", how="left")
        .with_columns(
            (pl.col("ready").str.to_date() - pl.col("admin").str.to_date())
            .dt.total_days()
            .alias("admin_to_ready_days"),
            (
                pl.col("appointment_date").str.to_date()
                - pl.col("booked_date").str.to_date()
            )
            .dt.total_days()
            .alias("booking_to_appointment_days"),
        )
    )
    outside_reports = set(
        events.filter(pl.col("event_type") == "outside_care_reported")["referral_id"]
    )
    outside_reviews = audit.filter(
        pl.col("finding") == "outside_care_confirmed"
    ).filter(~pl.col("referral_id").is_in(list(outside_reports)))

    def choose(frame: pl.DataFrame) -> str:
        if frame.is_empty():
            raise ValueError("Required contrasting journey absent")
        return frame.sort("referral_id")["referral_id"][0]

    selected = {
        "administrative_complete_but_clinical_work_remains": choose(
            joined.filter(
                (pl.col("order_date") >= "2025-07-01")
                & (pl.col("admin_to_ready_days") >= 14)
                & pl.col("specialty").is_in(
                    [
                        "cardiology",
                        "gastroenterology",
                        "neurology",
                        "orthopedics",
                        "endocrinology",
                        "pulmonology",
                    ]
                )
            )
        ),
        "specialty_capacity_wait": choose(
            joined.filter(
                (pl.col("specialty") == "neurology")
                & (pl.col("booking_to_appointment_days") >= 28)
            )
        ),
        "outside_care_found_by_review": choose(outside_reviews),
        "prompt_internal_care": choose(
            joined.filter(
                (pl.col("inherited") == 0)
                & (pl.col("outcome") == "completed")
                & (pl.col("admin_to_ready_days") <= 3)
                & (pl.col("booking_to_appointment_days") <= 8)
            )
        ),
        "future_appointment_outcome_unknown": choose(
            joined.filter(
                (pl.col("appointment_date") > "2025-12-31")
                & pl.col("outcome").is_null()
            )
        ),
    }
    summary = json.loads((directory / "reference/summary.json").read_text())
    planning_hours = (
        config["coordination_fte"]
        * config["coordination_productive_hours_per_year"]
        * 1.5
    )
    eligible_truth = truth.filter(
        pl.col("referral_id").is_in(initial["referral_id"].to_list())
    )
    actual_outside = eligible_truth.filter(
        (pl.col("outcome_at_end") == "outside") & (pl.col("care_date") <= "2025-12-31")
    )
    summary.update(
        {
            "coordination_planning_hours_18_months": planning_hours,
            "modeled_fraction_of_planning_hours": round(
                summary["coordination_hours"] / planning_hours, 3
            ),
            "initial_new_referrals": initial.filter(pl.col("inherited") == 0).height,
            "initial_inherited_referrals": initial.filter(
                pl.col("inherited") == 1
            ).height,
            "initial_actual_outside_care_contributor_only": actual_outside.height,
            "initial_recorded_outside_care_reports": len(outside_reports),
            "initial_review_confirmations_without_outside_report": outside_reviews.height,
            "initial_waits_by_specialty": joined.group_by("specialty")
            .agg(
                pl.len().alias("episodes"),
                pl.col("admin_to_ready_days")
                .median()
                .alias("median_observed_admin_to_ready_days"),
                pl.col("booking_to_appointment_days")
                .median()
                .alias("median_booked_wait_days"),
                pl.col("booking_to_appointment_days")
                .quantile(0.9)
                .alias("p90_booked_wait_days"),
            )
            .sort("specialty")
            .to_dicts(),
            "journeys": selected,
            "interpretation_limits": "Descriptive synthetic model checks; conditional waits exclude missing stages and unbooked cases. They are not causal estimates or a required learner conclusion.",
        }
    )
    # Same two-month enrollment windows, each with at least 30 days of follow-up.
    # These selected-site contrasts are descriptive, not a causal estimate.
    followup_refs = pl.read_csv(directory / "followup/referrals.csv")
    followup_events = pl.read_csv(directory / "followup/events.csv")
    followup_appointments = pl.read_csv(directory / "followup/appointments.csv")
    observed_stages = followup_events.group_by("referral_id").agg(
        pl.col("occurred_date")
        .filter(pl.col("event_type") == "admin_complete")
        .min()
        .alias("admin"),
        pl.col("occurred_date")
        .filter(pl.col("event_type") == "clinical_review")
        .min()
        .alias("review"),
    )
    pilot_population = (
        followup_refs.filter(
            pl.col("source_site").is_in(config["pilot"]["source_sites"])
            & pl.col("specialty").is_in(config["pilot"]["specialties"])
        )
        .join(observed_stages, on="referral_id", how="left")
        .join(followup_appointments, on="referral_id", how="left")
        .with_columns(
            (pl.col("review").str.to_date() - pl.col("admin").str.to_date())
            .dt.total_days()
            .alias("handoff_days"),
            (
                pl.col("appointment_date").str.to_date()
                - pl.col("booked_date").str.to_date()
            )
            .dt.total_days()
            .alias("booked_wait_days"),
            (
                (pl.col("outcome") == "completed")
                & (
                    (
                        pl.col("appointment_date").str.to_date()
                        - pl.col("order_date").str.to_date()
                    ).dt.total_days()
                    <= 30
                )
            )
            .fill_null(False)
            .alias("documented_internal_care_within_30_days"),
        )
    )
    pilot_readout = {}
    for name, first, last in (
        ("baseline", "2026-01-01", "2026-02-28"),
        ("pilot", "2026-04-01", "2026-05-31"),
    ):
        cohort = pilot_population.filter(
            pl.col("order_date").is_between(pl.lit(first), pl.lit(last))
        )
        pilot_readout[name] = {
            "enrollment_start": first,
            "enrollment_end": last,
            "episodes": cohort.height,
            "paired_handoff_records": cohort["handoff_days"].count(),
            "median_admin_to_review_days": cohort["handoff_days"].median(),
            "median_booked_wait_days": cohort["booked_wait_days"].median(),
            "documented_internal_care_within_30_days": cohort[
                "documented_internal_care_within_30_days"
            ].sum(),
        }
    summary["worked_pilot_descriptive_comparison"] = pilot_readout
    output.mkdir(parents=True)
    (output / "readout.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    ids = list(selected.values())
    for table in ("referrals", "events", "appointments", "audit", "complaints"):
        frame = pl.read_csv(directory / "initial" / f"{table}.csv")
        frame.filter(pl.col("referral_id").is_in(ids)).write_csv(
            output / f"journey_{table}.csv"
        )
    return {
        "initial_new_referrals": summary["initial_new_referrals"],
        "coordination_hours": summary["coordination_hours"],
        "planning_hours": planning_hours,
        "journeys": selected,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(review(args.directory, args.output), indent=2))
