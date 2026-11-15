# Riverside: Next-Version Design Decisions

Status: initial v2 implementation completed locally on 2026-11-05; the decisions below govern its development.
This is the continuity reference for forthcoming case development.
The maintained version 1.0.0 dataset and its generator remain the current teaching evidence.
The [v2 specification](specification_v2.md), rewritten scenario, and linked local artifact implement the expanded case; existing publication computations retain their version-1 pin during migration.

## Institution and Starting Problem

Riverside is a capable US regional health system anchored by a substantial regional referral hospital, with affiliated primary-care sites and specialist practices.
It serves a dispersed population extending well beyond its immediate community, where convenient alternatives may be limited.
The author's experience of Western Baptist Hospital in Paducah, Kentucky, informs this institutional shape; Riverside is a fictional institution.

Customer complaints initiate the investigation.
The recurring experience is having to chase a referral without knowing who owns the next step or whether anything is happening.
Promised callbacks, conflicting accounts from different offices, and repeated patient calls provide the starting evidence.
The investigation must distinguish responsiveness, referral progress, timely access to appropriate care, and the reliability of Riverside's knowledge about what happened.

Timely access to appropriate care is the primary aim.
Network retention, staff workload, financial consequences, and reliable documentation remain important and may pull decisions in different directions.
A patient receiving timely care outside Riverside can experience a good outcome while the organization loses revenue or fails to document completion.

### Working Footprint and Scale

The design target is approximately **100,000 new outpatient referral episodes annually across the participating specialty network**, rather than across only the six teaching specialties.
The hospital's regional reach and outpatient network must support this workload; its home city's population and inpatient bed count alone do not establish referral demand.

| Component | Working design assumption |
|---|---|
| Main hospital | Approximately 450 beds; the region's principal referral center. |
| Regional network | Approximately 40–50 outpatient locations, including primary care, specialty offices, and other services. |
| Specialty breadth | Approximately 25–30 specialties; cardiology, gastroenterology, neurology, orthopedics, endocrinology, and pulmonology supply the principal teaching investigations. |
| Catchment | Approximately 500,000 people across a dispersed, multi-county region. |
| Incoming workload | Approximately 100,000 new outpatient referral episodes per year, with affiliated and independent referring practices contributing to demand. |

These are fictional planning assumptions, subject to a coherent demand and capacity model.
They replace the earlier, smaller proposal of a 300-bed hospital with 24,000 annual referrals.
The earlier estimate of eight coordinators is also withdrawn; staffing must be derived from the larger workload and the work performed.
Exact practice counts, specialty shares, staffing, and referral-source mix remain to be developed.

The proposed observation period is 18 months: six months before centralization, six months after centralization for the initial investigation, three months for investigation and pilot implementation, and three months of follow-up.
At the target rate, this implies roughly 100,000 new episodes in the initial twelve-month evidence and 150,000 across the full period, plus inherited cases.
This timeline remains provisional; calendar dates, inherited queue size, and evidence-release timing are not yet settled.

The proposed coverage is new outpatient referral episodes directed to participating Riverside specialties, including referrals from affiliated and independent practices, other specialties, and appropriate emergency-department outpatient follow-up.
Established-patient follow-ups, inpatient consultations, emergency transfers, and procedure-only orders are outside the proposed initial scope.
A new clinical question about an established patient can create a new episode.
An episode is distinct from a patient, an incoming document, a contact attempt, or an appointment event.

Learners should have access to the broader referral population while choosing a bounded investigation within it.
Use linked operational records and repeatable analysis to motivate the computing tools; do not inflate event counts merely to exceed Excel's limits.
Event volume should follow from the modeled work.

## Centralization and Ambiguity

Centralization was a reasonable response to uneven local practices, fragile staffing coverage, and inconsistent tracking.
Its consequences deserve investigation.
The case must leave open whether changing process rules, demand, capacity, increased visibility, or interacting conditions explain the complaints.
The chronology alone must not establish that centralization caused the problem.

### Agreed Boundary of Centralization

The central referral office owns intake, administrative completeness checks, tracking, and initial patient contact.
Specialty practices retain clinical review and control of appointment availability.
The detailed arrangements for booking, follow-up, and escalation remain to be developed.

Administrative completeness and clinical readiness are separate judgments.
The central office can verify that required documents and fields are present; a specialty reviewer determines whether the information and workup support an appropriate clinical next step.
A referral can therefore pass an administrative check and still require clinical clarification or additional workup.
This distinction is a Riverside design decision informed by the comparisons below, rather than a claim that every source uses these terms or this exact division of responsibility.

The case should make these judgments and handoffs available for investigation without treating disagreement as evidence of incompetence.
Whether different understandings of referral status contribute to the complaints remains a mechanism to develop and test against other explanations.
The data design should preserve the distinction between administrative processing, clinical review, appointment scheduling, and receipt of care; exact statuses and timestamps remain undecided.

Learners may choose and justify a bounded scope within the broader case evidence.
Several explanations and intervention choices may be defensible.
Assessment should examine the reasoning, evidence, assumptions, and consequences supporting a recommendation.
The worked case should achieve meaningful but partial improvement, with remaining constraints and questions for another cycle.

## Process Mechanisms and Incentives

The agreed direction combines three interacting mechanisms: different meanings of referral readiness, variation in capacity across specialties, and differences between recorded status and actual patient progress.
Their strength and interaction should vary across specialties and referring practices.
Exact rules, frequencies, and effects remain to be developed before generating data.

| Mechanism | Situation to model | Investigation it supports |
|---|---|---|
| Different meanings of readiness | Administrative checks pass, but specialty review requires clarification or additional workup; responsibility for the next action can be unclear. | Locate waiting and repeat work; examine requirements, handoffs, and follow-up ownership. |
| Uneven capacity | Some episodes move through intake promptly but encounter limited appointment availability; others wait earlier. | Distinguish waiting before review, before booking, and between booking and care; examine differences hidden by averages. |
| Recorded status differs from progress | Outside care, directly arranged appointments, or a patient's decision not to proceed may leave central records unresolved. | Assess what records establish, seek corroborating evidence, and distinguish timely care from documented closure. |

Incentives help explain why these patterns can persist despite competent people working hard.
The central tension is local completion versus patient progress: each office can meet its own expectations while a patient remains between steps.
A second tension is timely access versus network retention, especially when outside care is available sooner.

| Group | Pressure or expectation to develop | Possible consequence to investigate |
|---|---|---|
| Central intake | Process incoming referrals promptly and manage queue age and size. | Forwarding a complete packet can count as progress before responsibility for the next action is accepted. |
| Referring practices | Keep visits moving and complete referral orders alongside current patient care. | Sending the order becomes the practical endpoint; later information requests compete with today's patients. |
| Specialty practices | Protect scarce appointments, maintain productivity, and obtain necessary clinical information. | Holding a referral for review or workup makes sense locally while extending the patient's wait. |
| System leadership | Improve access, retain patients within Riverside, and manage costs. | Staff may continue pursuing an internal appointment when an outside option could be sooner. |
| Patients | Obtain appropriate care while managing work, travel, cost, and uncertainty. | Patients may seek care elsewhere or stop pursuing a referral, leaving Riverside's account incomplete. |

These pressures are fictional design choices, not findings established by the published comparisons.
Use ordinary accountability, workload, and limited visibility to make them plausible; explicit financial bonuses or deliberate manipulation are not required.
The underlying pressures should persist across the centralization date, while responsibilities, visibility, and their consequences may change.
Elaine can sincerely support timely care while also being accountable for retention and cost.

Potential pilots include clearer handoff ownership and better visibility into outside-care outcomes, but no intervention is selected yet.
Learners should examine whether a proposed target improves patient progress or moves work and delay elsewhere.
Neither a preferred countermeasure nor one hidden causal explanation should determine assessment success.

Next, develop a few contrasting referral journeys and a mechanism-and-evidence table covering actions, reasons, recorded traces, unknowns, and plausible bounded pilots.
These will inform the data specification without predetermining learners' conclusions.

## Agreed Cast

| Name | Role | Place in the investigation |
|---|---|---|
| Dana Whitaker | Black Belt | Leads and coaches the investigation; supports access, reviews reasoning, and helps with escalation. |
| Morgan Ellis | Yellow Belt team member | The learner's narrative counterpart; contributes analysis, proposes a bounded scope, and develops recommendations with teammates. |
| Tasha Reed | Central referral coordinator | Brings knowledge of queues, exceptions, and daily workarounds. |
| Marisol Vega | Referring-clinic representative | Brings knowledge of the work before and after a referral leaves the clinic. |
| Ben Holloway | Specialty scheduling representative | Brings knowledge of review, appointment availability, and scheduling constraints. |
| Ruth Bennett | Patient-relations representative | Brings complaint evidence and helps the team obtain patients' accounts directly. |
| Elaine Porter | Operations sponsor | Provides organizational authority and can approve a bounded operational pilot. |

Use first names in most scenes and introduce surnames naturally.
Keep names and responsibilities consistent across chapters, artifacts, and exercises.
Personal histories, temperaments, relationships, and distinct voices remain to be developed through discussion.

Dana's expertise does not supply complete knowledge of the local process or its causes.
Knowledge is distributed across the team, and direct patient accounts remain part of the evidence.
Ruth's summaries do not replace patients' voices.

The learner operates as a team member under Dana's leadership.
The team can propose a modest operational pilot; larger staffing, clinical-capacity, or organizational changes require escalation and the relevant owners' approval.

## Published Comparisons and Design Rationale

These sources inform the fictional process architecture and operational details.
They do not establish Riverside's causes, expected improvement, or referral volume, and no single example reproduces its proposed arrangement.

### Baptist Health Paducah: Regional Reach Beyond Bed Count

Baptist Health's [Paducah hospital careers profile](https://www.baptisthealth.com/careers/our-locations/paducah) describes a 337-bed hospital with physicians representing more than 40 specialties.
Its [hospital overview](https://www.baptisthealth.com/locations/baptist-health-paducah) describes more than 45 regional points of care.
This comparison informs the relationship between a regional hospital and a broader outpatient network; it does not validate Riverside's proposed referral count, catchment, or bed count.

### San Francisco General Hospital: Specialist Review Before Scheduling

Straus et al. (2011), [*Implementation of an Electronic Referral System for Outpatient Specialty Care*](https://pmc.ncbi.nlm.nih.gov/articles/PMC3243286/), describes an electronic referral system supporting communication between referring clinicians and specialist reviewers, including clarification before scheduling.
Its qualitative implementation findings include favorable perceptions of communication and access alongside increased primary-care workload as tasks shifted from specialists and administrative personnel.

For Riverside, this supports retaining a distinct specialty-review step and examining where work moves when a process changes.
The system is a comparison for clinical coordination; it does not document our exact central-office model or prove that centralization improves access.

### Alberta: Centralized Intake and Different Clinical Responsibilities

Suter et al. (2015), [*Optimizing the interprofessional workforce for centralized intake of patients with osteoarthritis and rheumatoid disease: case study*](https://doi.org/10.1186/s12960-015-0033-3), examines two intake models across three clinics.
The described process includes receiving referrals, checking completeness, requesting missing information, and clinical triage, with variation in whether clinics also perform screening and assessment.
Interviews identify continuing workforce and information-system constraints.

For Riverside, this is a useful reference for specifying tasks and who can perform them, rather than assuming that “centralized intake” defines one fixed organizational model.
These Canadian specialty-specific models centralize more clinical work than Riverside currently proposes; their financing and service context also differ.

### UCSF: Incoming Documents and Referral Records

Odisho et al. (2020), [*Design and development of Referrals Automation, a SMART on FHIR solution to improve patient access to specialty care*](https://doi.org/10.1093/jamiaopen/ooaa036), describes software developed to process incoming specialty-referral faxes, extract information, and create electronic referral records with staff verification.

For Riverside, this supports plausible information-handling details: an electronic record can coexist with faxed documents and manual checks.
This design and development report does not establish that intake automation resolves downstream appointment capacity or access problems.

### Renown Health: A Central Coordination Organization

Alana Liedholm's (2022) [*Department Spotlight: Customer Engagement Center*](https://www.renown.org/blog/department-spotlight-customer-engagement-center) describes central teams handling scheduling, referrals, insurance, and patient outreach across a US health system.
The account reports nearly 200,000 referrals and authorizations combined in the preceding year.

For Riverside, this is an organizational comparison showing the breadth and potential scale of central coordination work.
It is an institutional profile rather than an independent effectiveness evaluation, and its combined activity count is not a count of unique specialty referrals or a suitable direct calibration for Riverside.

Sources consulted on 2026-11-05.
Use these comparisons to inform the process design while leaving the case's interacting mechanisms and defensible interventions open.

## Implementation and Remaining Development

The initial implementation adopts 27 specialties, 24 affiliated primary-care sites, 60 independent referring practices, and 150,000 new episodes plus 2,000 inherited records over January 2025–June 2026.
Centralization begins July 1, 2025; the initial evidence closes December 31, 2025.
The worked pilot begins April 1, 2026 at AP01–AP04 for cardiology and gastroenterology, with follow-up through June 30.
The [specification](specification_v2.md) records the detailed rules and simplifications, and the [reference readout](reference/README.md) supplies counts and contrasting journeys.
These implementation choices make the design reviewable; they are not empirically validated estimates.

- Review specialty shares, capacity constraints, and staffing headroom against the generated evidence.
- Complete a project-role/authority brief: identify accountable process owner(s), Elaine's sponsorship/champion functions and approval limits, clinical/scheduling and data-access decision owners, escalation routes, and sustainment responsibility. The named cast alone does not establish these authorities.
- Develop additional patient accounts and team scenes without treating the complaint sample as representative.
- Migrate existing chapter computations and publication consumers to the linked schema in a separate bounded change.
- Complete the chapter-by-chapter A3 narrative and worked pilot interpretation, retaining alternate defensible investigations.
- Select an artifact host before publishing a bulk dataset download.
