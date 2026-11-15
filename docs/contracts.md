# Riverside v1 contract scope

Pydantic is authoritative for this producer's metadata, preserved provenance, and supported generator configuration.
Generated schemas expose structural/scalar requirements; named runtime validators also enforce relationships.
The generic `case-v1.json` and `dataset-v1.json` exchange envelopes remain frozen.

Each CSV row is a synthetic referral episode, keyed by unique `referral_id`.
Order dates cover 2025-10-01 through 2026-03-31; this is not an as-of cutoff on all later activity.
`lead_time_days` means order-to-booking (`scheduled_date`), not order-to-care (`appointment_date`).
Unbooked referrals legitimately lack scheduled date, appointment date, and lead time.
Reminder date may be absent for either booking population.
`not_booked`, `pending_in_network`, and `none` are categories, not missing values.
Validation retains these distinctions, rejects unexpected structure/categories, and reconciles booking populations and chronology without repairing evidence.

Integrity checks identify adopted evidence; optional Pandera/Polars checks examine its meaning.
The maintained v1 generator has fixed population size and date dimensions; only its seed is exposed as an experimental override.
Generated experiments are not adopted releases.
The staged v2 linked tables, cumulative populations, delayed recording, and reference truth require their own profiles in the next slice.
Neither this profile nor its missingness rules may silently govern v2.
