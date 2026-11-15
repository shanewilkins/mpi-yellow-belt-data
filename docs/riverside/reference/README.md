# Riverside v2 Contributor Readout

The [acceptance readout](acceptance_v2/readout.json) records generated counts, a workload check, and descriptive waiting-time summaries.
The small `journey_*.csv` files in the same directory are exact initial-extract excerpts for five contrasting episodes.
They are retained in Git so contributors can inspect concrete histories without generating the bulk artifact.
They are deliberately selected examples, not a representative sample or required learner conclusions.

| Journey | Episode | What the initial evidence permits us to inspect |
|---|---|---|
| Administrative completeness followed by clinical work | RV2-0051638 | Gastroenterology: administrative completion July 4; clinical clarification July 7; clinical readiness July 24; appointment August 7. |
| Waiting for specialty capacity | RV2-0016469 | Neurology: booked March 18 for April 15, after earlier clinical clarification; more than one interval contributes to total waiting. |
| Outside care found through review | RV2-0001810 | A December review confirms January outside care; the activity extract has no outside-care report for the episode. It is an inherited record. |
| Prompt internal care | RV2-0002001 | Cardiology: ordered January 1, booked January 2, visit January 9; some pre-centralization activity entries are absent. |
| An outcome not yet available | RV2-0072213 | Rheumatology: booked October 24 for January 5; the December extract correctly leaves the outcome blank. |

The initial population contains 100,187 new episodes plus 2,000 inherited records.
The full follow-up population has 152,000 episodes and 1,329,989 recorded activities.
Those event counts describe one cumulative extract; do not add the three release counts as if they were distinct activities.

Modeled coordination work totals 47,443.7 hours against a provisional 50,400-hour allowance over 18 months, or approximately 94%.
This leaves little headroom for omitted exception handling and supports further staffing investigation rather than proving staffing adequacy.
The initial readout also distinguishes 8,418 simulated outside-care episodes by the cutoff from 2,764 recorded outside-care reports.
That comparison uses contributor truth; learners must work with available reports and sampled corroboration.

Regenerate the readout into a new directory:

```console
uv run --locked python -m mpi_yellow_belt_data.reference.readout data/cases/riverside/2.0.0 --output /tmp/riverside-v2-readout
```

Conditional stage waits exclude episodes with missing stage records; booked waiting times exclude unbooked episodes.
The tables do not establish causation or support comparing immature and mature cohorts without adjustment.
The worked pilot is a limited, nonrandom rollout; use the follow-up evidence to assess partial improvement and remaining constraints, not to infer a universal remedy.

The worked comparison uses the same four sites and two specialties, with January–February enrollment before the pilot and April–May enrollment during it.
Both windows allow at least 30 days of follow-up by June 30.
Median recorded administrative-completion-to-review time falls from 5 to 3 days; median waiting from booking to the offered appointment changes from 18 to 17 days.
Documented internal care within 30 days is 110 of 331 episodes before and 116 of 339 during the pilot, approximately 33% and 34%.
These descriptive results illustrate a local handoff improvement with substantial remaining access constraints; they do not establish a causal effect or count all appropriate outside care.

## Verification

The local full artifact passes pinned-manifest checks, file hashes and shapes, population reconciliation, key uniqueness, foreign keys, date ordering, release cutoffs, and specialty slot limits.
The [check receipt](acceptance_v2/checks.json) records the three extract populations.
The focused case/model and compatibility suite passes 37 tests, covering deterministic sample reproduction, overwrite refusal, corrupted evidence, future-outcome leakage, pilot eligibility, learner curation, version dispatch, and preserved version-1 operations.
Ruff and type checks pass on the changed Python surfaces.
The prepared marimo starter executes against all 102,187 initial records.
These checks validate the implemented synthetic model and affected interfaces, not empirical realism or the entire book's publication pipeline.
