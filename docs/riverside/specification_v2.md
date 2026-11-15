# Riverside v2: Model and Evidence Specification

This is the contributor specification for dataset 2.0.0, implementing the [agreed design](design_v2.md).
The maintained version-1 publication pin remains separate while its chapter computations are migrated.

## Population, Demand, and Capacity

Generate 150,000 new outpatient referral episodes from 2025-01-01 through 2026-06-30, plus 2,000 inherited unresolved records ordered in the preceding 90 days.
The inherited records are a selected open population, not a representative pre-window cohort.
Patient identifiers can recur across episodes; document, contact, and appointment counts are not referral counts.
The generator uses a fixed seed, a weekday-weighted calendar, and modest winter demand variation.
It does not force each calendar year to contain exactly 100,000 arrivals.

The fictional institution has approximately 450 beds, a catchment of 500,000, and 48 outpatient locations: 24 affiliated primary-care sites and 24 shared specialty/other locations.
Twenty-seven specialty services share those locations.
Sixty independent practices send referrals with unequal frequencies.
The six principal teaching specialties account for 53% of expected episodes.
Source shares are 52% affiliated primary care, 38% independent practices, 6% emergency-department follow-up, and 4% other specialties.

The affiliated network has 110 primary-care clinician equivalents.
At 18 encounters per day over 210 clinical days, that is 415,800 encounters annually; approximately 52,000 referrals to participating services imply 12.5 referral episodes per 100 encounters.
This is a workload assumption, not a referral-rate estimate for an actual institution.
Independent practices contribute approximately 633 episodes per practice per year on average, with substantial variation.
For an empirical scale comparison, Patel et al. report 160,243 annual specialist referral orders from a network with more than 700,000 encounters, retaining 90,437 orders after restricting practices and specialties and excluding procedures ([2018 study](https://pmc.ncbi.nlm.nih.gov/articles/PMC5910374/)).
Originating orders and Riverside's incoming episodes have different boundaries; the comparison supports order of magnitude rather than direct calibration.

Specialty new-patient slot inventories are finite and allocated in booking-request order.
The configuration specifies daily weekday slots by specialty; neurology, endocrinology, and rheumatology have winter reductions, and cardiology and pulmonology have summer reductions.
No capacity step is imposed at centralization.
Routine offers begin at least seven calendar days after booking, urgent offers at least one, advanced to a weekday.
There is no separate protected urgent inventory, clinical safety model, cancellation backfill, or rebooking after nonattendance in this version.
Capacity represents new-patient slots after other clinical obligations, not all specialist appointments.

Coordination planning assumes 24 coordinator equivalents, supported by two supervisors and shared authorization/registration services.
At 1,400 productive hours per coordinator per year, the 18-month planning allowance is 50,400 coordinator hours.
Modeled handling minutes include intake, document requests, contacts, clarification follow-up, authorization coordination, booking coordination, and the pilot increment.
The generated summary compares modeled work with that allowance.
It excludes training, leave coverage, all complaint handling, and some exceptions; it is a plausibility check rather than a staffing optimization.
Administrative waits are sampled durations, not the output of a coordinator-resource queue simulation.

## Mechanisms and Recorded Evidence

| Process rule | Recorded trace | Limitation |
|---|---|---|
| Missing administrative information triggers a document request; independent-office submissions have a higher modeled probability. | Document-request, response, and administrative-completion events. | All modeled document requests eventually resolve; this does not represent every real failure mode. |
| Specialist clinical review follows administrative completion and can request clarification or workup. | Review, clarification, response, and readiness events. | Administrative completeness does not imply clinical readiness; recording can lag action. |
| Some episodes require authorization alongside clinical review. | Authorization request and receipt. | No payer-specific denial or appeals model is implemented. |
| Finite specialty slots constrain first appointments. | Booking events, appointment records, and daily capacity extracts. | Case mix, clinical severity, and appointment duration are simplified. |
| Patient decisions and communication affect whether an episode proceeds internally. | Contact attempts, decline reports, some outside-care reports, and sampled record reviews. | Outside care can occur without Riverside learning of it. |
| Pre-centralization activity histories are less complete. | Some historical events are absent; retained events can be recorded later. | Missing events cannot be interpreted as proof that work did not occur. |

The model does not export a learner-facing cause label or omniscient outcome column.
Referral attributes, recorded events, dated appointments, complaints, and sparse corroborating reviews are separate tables.
Complaint accounts are synthetic recurring formulations, not unique verbatim interviews; the complaint table is neither a representative patient survey nor an exhaustive description of dissatisfaction.
Record reviews sample eligible referrals independently at each review round, including unresolved cases, but cannot establish care for all selected episodes.

## Chronology and Pilot

Centralization begins 2025-07-01, changing the intake owner and record completeness without automatically worsening process performance.
The initial extract closes on 2025-12-31; the investigation update closes on 2026-03-31; follow-up closes on 2026-06-30.
Each is cumulative and limited to information recorded by its cutoff.
Files are not guaranteed to be in chronological order; analysts must sort by the appropriate date.
Future appointment dates may be visible after booking, while their eventual outcomes remain blank until recorded.

The worked pilot begins 2026-04-01 for cardiology and gastroenterology referrals from AP01–AP04.
The selected sites are a convenience rollout, not randomized controls.
An explicit handoff check reduces the administrative-completion-to-review interval for 80% of eligible episodes; outside-care reporting is more likely for those episodes, and coordination work increases by two minutes.
The pilot does not add specialist slots or remove clinical clarification requirements.
These are author-selected simulation rules, not an empirical treatment-effect estimate.
The follow-up data offer one worked intervention; other bounded countermeasures remain defensible and assessment must examine evidence and reasoning.
Analyses must account for changing cohort maturity and may not treat an unadjusted before/after comparison as a causal estimate.

## Artifact and Reproduction Contract

The generator writes a new destination atomically and refuses an existing path.
The full local artifact includes three dated extracts and a contributor-only reference directory containing simulated truth, capacity, and a summary.
The manifest records schemas, row counts, hashes, configuration, Python version, lockfile hash, and source fingerprints beyond the base Git revision.
Reference source remains inspectable; it is not an answer key governing assessment.
Learner preparation copies one selected extract, the case notes, and the starter notebook, excluding reference truth and later extracts.
Reduced samples exercise record structure and chronology; their sparse demand does not reproduce full-scale queue congestion.
Bulk generated files stay outside ordinary Git history; the pinned manifest and small journey excerpts are tracked.
No remote artifact host or public download is selected by this local development step.

## Threshold Story Drafting Notes

- Adult problem: on January 8, 2026, Morgan must help Ruth answer a patient's question about who owns the next step before a promised three o'clock call. The chapter has a planning allowance of approximately 4,000 words.
- Existing competence: Morgan can reconstruct a process and compare accounts, but does not yet have a reproducible joined evidence trail.
- Conceptual need and material carrier: an administrative completion entry, a specialty review entry, and a complaint refer to the same episode but support different claims.
- Distributed knowledge: Tasha knows the intake work, Ben the clinical-review boundary, Marisol the referring office, Ruth the patient's account, Elaine the resource constraints, and Dana the investigation method.
- Project-role continuity: Morgan drafts the investigation and coordinates evidence checks; Dana reviews/coaches the reasoning; frontline representatives check the process account; Elaine arranges access to responsible managers and helps resolve barriers. The relevant process owner and functional approvers must participate before a pilot; the story does not silently make Dana or Elaine the owner of every operating process.
- Choice and consequence: Morgan reconstructs the immediate handoff, confirms responsibilities with Marisol, Ben, and Tasha, and accepts a bounded investigation; Ruth keeps the promised call without promising an appointment.
- Instructional boundary: the opening establishes the need for joined evidence; formal data work belongs in the computation chapters.
- Character movement and residue: Morgan revises the map and recognizes that following one episode differs from establishing a network pattern; the team retains a named follow-up commitment while the patient still waits for care.
- Computing need: Morgan can use spreadsheets, but the combination of repeated records and an older summary with unrecoverable filters creates a need for explicit, reproducible steps without declaring Excel incapable of holding the referral table.
- Dated-record continuity: the working extract closes December 31, 2025; an appointment scheduled for January 5, 2026 has no outcome in that extract even though its date precedes the meeting. A later record is needed to establish what happened.
- Evidence boundary: the opening incident and dialogue are composite fiction consistent with the process design, not a verbatim interview or an exact transcription of a selected dataset episode; no pilot result or later extract is known to the characters.
