# Riverside v2 Data Dictionary

Schema: `riverside-linked-v2`.
Dates use ISO `YYYY-MM-DD` and calendar-day precision; they do not establish within-day ordering.
Empty cells mean unavailable or inapplicable information, not zero elapsed time or a negative finding.
Files are not sorted histories.

Each release contains the following tables, cumulative through its cutoff: `initial` through 2025-12-31, `investigation` through 2026-03-31, and `followup` through 2026-06-30.
Do not concatenate the releases as independent populations.
Some appointment outcomes become known in later releases.

## referrals.csv — One Row per Referral Episode

| Field | Meaning |
|---|---|
| `referral_id` | Unique episode key; join other tables on this field. |
| `patient_id` | Synthetic patient identifier; a patient may have several episodes. |
| `order_date` | Date ordered, including pre-window dates for inherited records. |
| `source_site` | AP affiliated primary care, IP independent practice, ED emergency department, SP another specialty service. |
| `source_type` | `affiliated_primary_care`, `independent_practice`, `ed_followup`, or `other_specialty`. |
| `specialty` | Requested receiving specialty; includes 27 services. |
| `priority` | `routine` or `urgent` outpatient request; emergency transfers are excluded. |
| `travel_minutes` | Approximate one-way travel time for the episode. |
| `inherited` | 1 for an open record carried into the window; 0 for a new episode. |
| `record_available_date` | First availability in these extracts; inherited records enter at window start. |

No omniscient completion or cause label is included.
The inherited population is selected because its records were open; it is not a complete late-2024 cohort.

## events.csv — One Row per Recorded Activity

| Field | Meaning |
|---|---|
| `event_id` | Unique recorded activity identifier; gaps do not quantify missing work. |
| `referral_id` | Episode key. |
| `occurred_date` | Date the recorded activity happened. |
| `recorded_date` | Date Riverside recorded it; determines availability in an extract. |
| `event_type` | Activity category listed below. |
| `owner` | Team performing or reporting the activity; does not establish acceptance of the next task. |
| `detail` | Category-specific detail, such as contact result or appointment date. |

Categories are `order_received`, `documents_requested`, `documents_received`, `admin_complete`, `contact_attempt`, `clinical_review`, `clinical_clarification_requested`, `clinical_response_received`, `clinical_ready`, `authorization_requested`, `authorization_received`, `booking_requested`, `appointment_booked`, `reminder_sent`, `internal_visit`, `no_show`, `cancelled`, `patient_declined`, `awaiting_response`, and `outside_care_reported`.
Contact detail is `reached` or `no_answer`; an attempt is not necessarily successful contact.
Booking detail gives the appointment date.
An outside-care event records a report of care already received; its occurrence date is the reporting action, not the care date.
Use corroborating reviews where available to distinguish those dates.

Administrative completion does not imply clinical readiness, booking, or care.
Some pre-centralization events are absent; retained events can have recording delays.
Sort by occurrence date to study activity and recording date to reconstruct available information.
The latest event is not a complete clinical status definition: workstreams can overlap.

## appointments.csv — One Row per First Internal Appointment

| Field | Meaning |
|---|---|
| `appointment_id` | Unique first-appointment key. |
| `referral_id` | Episode key. |
| `booked_date` | Date the appointment was arranged. |
| `appointment_date` | Offered date; can lie beyond the cutoff. |
| `outcome` | `completed`, `no_show`, or `cancelled` when recorded; otherwise blank. |
| `outcome_recorded_date` | Date the outcome became recorded information; blank when unavailable. |

The model includes one first internal appointment per booked episode, without rebooking or cancellation backfill.
A blank outcome for a future appointment is expected.
Booking delay and waiting from booking to the appointment are different quantities.
Booking capture here is more complete than the older activity history, so an absent booking event does not establish that no appointment was booked.

## complaints.csv — One Row per Complaint Record

Fields are `complaint_id`, `referral_id`, `received_date`, `theme`, and `patient_account`.
Themes are `unclear_next_step`, `repeat_information`, `callback`, and `appointment_access`.
An episode can have multiple complaints.
Accounts use recurring synthetic formulations; they are not unique transcribed interviews, a representative survey, or a complete count of dissatisfied patients.

## audit.csv — One Row per Sampled Review

Fields are `audit_id`, `referral_id`, `review_date`, `finding`, `evidence_source`, and `care_date`.
Findings are `outside_care_confirmed`, `internal_care_confirmed`, `declined_confirmed`, or `unable_to_confirm_care`.
Evidence sources are `patient_followup`, `visit_record`, and `record_review`.
Care date is present only for confirmed care.
Three review rounds sample eligible referrals independently, including unresolved cases; cumulative extracts retain earlier reviews and episodes can recur.
Inability to confirm care does not confirm that no care occurred.

## capacity.csv — One Row per Specialty per Calendar Day

Fields are `date`, `specialty`, `new_patient_slots`, and `reserved_slots`.
These are new-patient slots after other clinical obligations, not total provider capacity.
Weekend counts are zero; capacity varies by specialty and season.
Reserved slots include subsequently cancelled or missed appointments because this model does not backfill them.
Extracts cover dates through the cutoff, not the entire future calendar.

## Contributor Reference Evidence

The full development artifact also contains `reference/model_truth.csv`, `reference/daily_capacity.csv`, and `reference/summary.json`.
These are excluded from prepared learner workspaces.
Truth distinguishes simulated readiness, care, reporting, pilot delivery, and handling work; dates beyond the final cutoff are censored.
It is for verification, not required learner conclusions.
The contributor specification in the Riverside case repository documents simulation rules and limitations.
