#!/usr/bin/env python3
"""Generate the synthetic Riverside referral dataset used in Yellow Belt."""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20260617
ROW_COUNT = 1484
START_DATE = date(2025, 10, 1)
END_DATE = date(2026, 3, 31)

SERVICE_LINES = {
    "cardiology": 0.20,
    "gastroenterology": 0.19,
    "neurology": 0.18,
    "orthopedics": 0.17,
    "endocrinology": 0.14,
    "pulmonology": 0.12,
}

REFERRAL_SOURCES = {
    "family_medicine": 0.29,
    "internal_medicine": 0.22,
    "urgent_care": 0.17,
    "ed_followup": 0.13,
    "outside_provider": 0.11,
    "pediatrics": 0.08,
}

INSURANCE_CLASSES = {
    "commercial": 0.43,
    "medicare": 0.26,
    "medicaid": 0.19,
    "self_pay": 0.12,
}

SERVICE_BASE_LEAD = {
    "cardiology": 8,
    "gastroenterology": 11,
    "neurology": 14,
    "orthopedics": 10,
    "endocrinology": 12,
    "pulmonology": 13,
}

SERVICE_APPOINTMENT_GAP = {
    "cardiology": 9,
    "gastroenterology": 11,
    "neurology": 14,
    "orthopedics": 10,
    "endocrinology": 12,
    "pulmonology": 13,
}


def weighted_choice(rng: random.Random, weighted_values: dict[str, float]) -> str:
    values = list(weighted_values)
    weights = list(weighted_values.values())
    return rng.choices(values, weights=weights, k=1)[0]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def booking_pathway(
    rng: random.Random,
    order_date: date,
    authorization_required: str,
    completeness_status: str,
) -> str:
    if order_date < date(2026, 1, 1):
        weights = {
            "point_of_care": 0.54,
            "central_queue_callback": 0.34,
            "specialty_review_queue": 0.12,
        }
    else:
        weights = {
            "point_of_care": 0.17,
            "central_queue_callback": 0.61,
            "specialty_review_queue": 0.22,
        }

    if authorization_required == "yes":
        weights["point_of_care"] *= 0.45
        weights["specialty_review_queue"] *= 1.35
    if completeness_status == "incomplete":
        weights["point_of_care"] *= 0.35
        weights["central_queue_callback"] *= 1.10
        weights["specialty_review_queue"] *= 1.45

    total = sum(weights.values())
    normalized = {key: value / total for key, value in weights.items()}
    return weighted_choice(rng, normalized)


def format_date(value: date | None) -> str:
    return value.isoformat() if value else ""


def generate_rows(*, seed: int = SEED) -> list[dict[str, str]]:
    rng = random.Random(seed)

    dates = []
    current = START_DATE
    while current <= END_DATE:
        dates.append(current)
        current += timedelta(days=1)

    date_weights = []
    for current_date in dates:
        weekday_weight = {
            0: 1.25,
            1: 1.20,
            2: 1.18,
            3: 1.12,
            4: 1.05,
            5: 0.36,
            6: 0.20,
        }[current_date.weekday()]
        month_weight = 1.0
        if current_date.month in {1, 2, 3}:
            month_weight = 1.22
        date_weights.append(weekday_weight * month_weight)

    sampled_dates = sorted(rng.choices(dates, weights=date_weights, k=ROW_COUNT))
    rows: list[dict[str, str]] = []

    for index, order_date in enumerate(sampled_dates, start=1):
        service_line = weighted_choice(rng, SERVICE_LINES)
        referral_source = weighted_choice(rng, REFERRAL_SOURCES)
        insurance_class = weighted_choice(rng, INSURANCE_CLASSES)

        urgent_probability = 0.19
        if referral_source == "ed_followup":
            urgent_probability += 0.16
        if service_line in {"cardiology", "pulmonology"}:
            urgent_probability += 0.03
        priority = "urgent" if rng.random() < urgent_probability else "routine"

        auth_probability = 0.29
        if insurance_class == "medicaid":
            auth_probability += 0.12
        if insurance_class == "commercial":
            auth_probability += 0.05
        if service_line in {"cardiology", "neurology", "endocrinology"}:
            auth_probability += 0.04
        authorization_required = "yes" if rng.random() < auth_probability else "no"

        incomplete_probability = 0.12
        if referral_source == "outside_provider":
            incomplete_probability += 0.10
        if referral_source == "urgent_care":
            incomplete_probability += 0.04
        completeness_status = (
            "incomplete" if rng.random() < incomplete_probability else "complete"
        )

        pathway = booking_pathway(
            rng, order_date, authorization_required, completeness_status
        )

        first_contact_days = max(
            0,
            round(
                rng.gauss(
                    {
                        "point_of_care": 0.8,
                        "central_queue_callback": 3.2,
                        "specialty_review_queue": 4.8,
                    }[pathway],
                    1.3,
                )
            ),
        )
        first_contact_date = order_date + timedelta(days=first_contact_days)

        book_probability = {
            "point_of_care": 0.93,
            "central_queue_callback": 0.80,
            "specialty_review_queue": 0.72,
        }[pathway]
        if authorization_required == "yes":
            book_probability -= 0.09
        if completeness_status == "incomplete":
            book_probability -= 0.19
        if insurance_class == "medicaid":
            book_probability -= 0.05
        if insurance_class == "self_pay":
            book_probability -= 0.07
        if order_date >= date(2026, 1, 1) and pathway != "point_of_care":
            book_probability -= 0.03
        if priority == "urgent":
            book_probability += 0.05
        book_probability = clamp(book_probability, 0.40, 0.97)

        booked_flag = "yes" if rng.random() < book_probability else "no"

        reminder_sent_date: date | None = None
        scheduled_date: date | None = None
        appointment_date: date | None = None
        lead_time_days = ""
        visit_outcome = "not_booked"
        network_outcome = "pending_in_network"
        patient_barrier_reason = "none"
        status = "pending_review"
        delay_reason = "provider_review_queue"
        status_update_days = max(0, min(6, first_contact_days + rng.randint(0, 2)))

        if booked_flag == "yes":
            mean_lead = SERVICE_BASE_LEAD[service_line]
            if pathway == "central_queue_callback":
                mean_lead += 4
            elif pathway == "specialty_review_queue":
                mean_lead += 6
            if authorization_required == "yes":
                mean_lead += 3
            if completeness_status == "incomplete":
                mean_lead += 4
            if order_date >= date(2026, 1, 1) and pathway != "point_of_care":
                mean_lead += 2
            if priority == "urgent":
                mean_lead -= 2

            lead_value = max(1, round(rng.gauss(mean_lead, 3.8)))
            scheduled_date = order_date + timedelta(days=lead_value)

            appointment_gap = max(
                1, round(rng.gauss(SERVICE_APPOINTMENT_GAP[service_line], 4.5))
            )
            appointment_date = order_date + timedelta(days=lead_value + appointment_gap)
            lead_time_days = str(lead_value)

            if (
                lead_value >= 7
                or appointment_gap >= 9
                or insurance_class in {"medicaid", "self_pay"}
            ):
                reminder_sent_date = order_date + timedelta(
                    days=lead_value + appointment_gap - rng.randint(1, 3)
                )

            completion_probability = 0.86
            if pathway == "central_queue_callback":
                completion_probability -= 0.05
            if pathway == "specialty_review_queue":
                completion_probability -= 0.08
            if insurance_class == "medicaid":
                completion_probability -= 0.07
            if insurance_class == "self_pay":
                completion_probability -= 0.11
            if authorization_required == "yes":
                completion_probability -= 0.03
            if reminder_sent_date is not None:
                completion_probability += 0.03
            completion_probability = clamp(completion_probability, 0.52, 0.95)

            outcome_roll = rng.random()
            if outcome_roll < completion_probability:
                visit_outcome = "completed"
                network_outcome = "completed_in_network"
                status = "completed"
                delay_reason = (
                    "capacity_constraint" if lead_value >= 14 else "ready_to_schedule"
                )
            elif outcome_roll < completion_probability + 0.07:
                visit_outcome = "no_show"
                network_outcome = "closed_without_visit"
                status = "closed_no_visit"
                patient_barrier_reason = rng.choices(
                    ["transportation", "work_schedule", "forgot", "cost_concern"],
                    weights=[0.24, 0.28, 0.30, 0.18],
                    k=1,
                )[0]
                delay_reason = "patient_unreachable"
            else:
                visit_outcome = "cancelled"
                network_outcome = "closed_without_visit"
                status = "closed_no_visit"
                patient_barrier_reason = rng.choices(
                    [
                        "symptoms_improved",
                        "cost_concern",
                        "prefers_outside_system",
                        "work_schedule",
                    ],
                    weights=[0.18, 0.24, 0.28, 0.30],
                    k=1,
                )[0]
                delay_reason = "patient_preference_shift"
        else:
            reminder_due_days = max(first_contact_days + 4, 5)
            if rng.random() < 0.71:
                reminder_sent_date = order_date + timedelta(days=reminder_due_days)

            unresolved_roll = rng.random()
            if completeness_status == "incomplete":
                status = rng.choices(
                    ["returned_for_clarification", "pending_review", "closed_no_visit"],
                    weights=[0.57, 0.28, 0.15],
                    k=1,
                )[0]
                delay_reason = "missing_information"
                patient_barrier_reason = "none"
            elif authorization_required == "yes" and unresolved_roll < 0.46:
                status = "authorization_pending"
                delay_reason = "authorization_pending"
                patient_barrier_reason = "none"
            elif unresolved_roll < 0.22:
                status = "closed_external"
                network_outcome = "completed_outside_system"
                delay_reason = "outside_system_leakage"
                patient_barrier_reason = rng.choices(
                    [
                        "prefers_outside_system",
                        "insurance_network",
                        "earlier_external_access",
                    ],
                    weights=[0.32, 0.34, 0.34],
                    k=1,
                )[0]
            elif unresolved_roll < 0.42:
                status = "awaiting_patient_response"
                delay_reason = "patient_unreachable"
                patient_barrier_reason = rng.choices(
                    ["unreachable", "work_schedule", "transportation", "cost_concern"],
                    weights=[0.42, 0.20, 0.17, 0.21],
                    k=1,
                )[0]
            elif unresolved_roll < 0.56:
                status = "closed_no_visit"
                network_outcome = "closed_without_visit"
                delay_reason = "patient_preference_shift"
                patient_barrier_reason = rng.choices(
                    ["symptoms_improved", "cost_concern", "prefers_outside_system"],
                    weights=[0.22, 0.31, 0.47],
                    k=1,
                )[0]
            else:
                status = "pending_review"
                delay_reason = "provider_review_queue"
                patient_barrier_reason = "none"

        rows.append(
            {
                "referral_id": f"RV-{index:04d}",
                "order_date": format_date(order_date),
                "service_line": service_line,
                "referral_source": referral_source,
                "priority": priority,
                "authorization_required": authorization_required,
                "completeness_status": completeness_status,
                "insurance_class": insurance_class,
                "booking_pathway": pathway,
                "status": status,
                "status_update_days": str(status_update_days),
                "first_contact_date": format_date(first_contact_date),
                "reminder_sent_date": format_date(reminder_sent_date),
                "scheduled_date": format_date(scheduled_date),
                "appointment_date": format_date(appointment_date),
                "lead_time_days": lead_time_days,
                "booked_flag": booked_flag,
                "visit_outcome": visit_outcome,
                "network_outcome": network_outcome,
                "patient_barrier_reason": patient_barrier_reason,
                "delay_reason": delay_reason,
            }
        )

    return rows


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    rows = generate_rows(seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
