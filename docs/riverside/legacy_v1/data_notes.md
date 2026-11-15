# Riverside Case Data

This directory holds the shared synthetic Riverside case dataset used in Yellow Belt.

Files:

- `riverside_referrals.csv`: canonical shared case dataset with one row per referral.

The current version contains a six-month synthetic cohort with 1484 referrals.
It is large enough to make yield, leakage, insurance, and booking-pathway comparisons feel operationally plausible without becoming unwieldy for Yellow Belt notebook work.

Yellow Belt usage pattern:

1. Keep the shared case file in the repository as a stable teaching source.
2. Pull or download the file into a learner project such as `riverside-project/data/raw/`.
3. Preserve downstream notes, summaries, and transforms outside the shared source location.

The main CSV is intentionally tidy in the practical Yellow Belt sense:

- one row per referral,
- one column per variable,
- one value per cell.

Key teaching fields now include:

- referral creation and pathway fields such as `order_date`, `referral_source`, and `booking_pathway`,
- current-state and delay fields such as `status`, `status_update_days`, `first_contact_date`, and `delay_reason`,
- booking and completion fields such as `booked_flag`, `scheduled_date`, `appointment_date`, `lead_time_days`, and `visit_outcome`,
- leakage and barrier fields such as `network_outcome`, `patient_barrier_reason`, and `reminder_sent_date`.

This is synthetic instructional data.
It is designed to support shell inspection, notebook import, descriptive analysis, and later A3 work without using real patient information.
