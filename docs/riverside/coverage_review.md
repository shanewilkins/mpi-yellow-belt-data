# Riverside v2 Against the Yellow Belt Learning Map

Review date: 2026-11-06.
Baseline: the learning map before its provisional Yellow Belt planning revision on the same date.
The annotated chapter outline in the book repository carries this review into the next design pass; the crosswalk below preserves its reviewed baseline rather than claiming a fresh audit of every later map revision.
Scope: whether the current case supplies meaningful teaching opportunities and evidence, not whether the draft chapters already teach or assess them sufficiently.
This review proposes additions; it does not change the learning map, model, or dataset identity.
Proposed ADR-0013 in the book repository and ADR-0014 in the book repository capture the subsequent direction for method limits, fair discovery, and complementary evidence design.

## Judgment

Riverside is a strong anchor for bounded investigation, descriptive statistics, data preparation, computational work, and most basic quality tools.
It is not yet a complete evidence package for every Yellow Belt promise.
The main gaps are a clean introductory inferential study, observed task durations, richer stakeholder evidence, and business-case inputs.
These can be supplied through small case-owned evidence packets without enlarging or regenerating the main referral population.

The [learning map](../../book/content/appendices/learning_map.qmd), capability policy in the book repository, and working chapter/objective proposal in `notes/yellow_belt_structure_and_objectives.md` were compared with the [dictionary](data_dictionary.md), [model](model/network.py), [configuration](config/network_v2.yml), [pilot](pilot_v2.md), and actual initial extracts.
The working chapter proposal remains a development plan, not the published sequence or an adopted replacement for the map.
Every mapped capability still requires instruction, guided practice, a less-supported attempt, feedback, and assessable evidence.

## Seven Basic Quality Tools

The current seven-tools chapter names check sheet, histogram, Pareto, cause-and-effect, scatter, control chart, and stratification, also recognizing flowcharting.

| Tool | Meaningful Riverside use | What remains necessary |
|---|---|---|
| Check sheet | Review a bounded set of referral packets or handoffs and tally consistently defined observations. | Supply the observation form, sampling frame, coding rules, and records to inspect. Grouping an existing CSV is not the whole act of designing and using a check sheet. |
| Histogram | Compare administrative-to-clinical readiness, booking delay, or booked appointment waits. | Define the interval, eligible cohort, missingness, and follow-up period. Recent unbooked episodes must not disappear silently. |
| Pareto | Rank complaint themes or the number of episodes involving document requests, clarification, or authorization. | These are recorded themes and activities, not established root causes. Requests can overlap and an authorization request is not inherently a defect. Do not manufacture an 80/20 pattern. |
| Cause-and-effect diagram | Organize hypotheses involving requirements, handoff ownership, capacity, communication, and local accountability. | Distinguish hypotheses from supported findings; enrich the staff and patient evidence rather than supplying a diagram whose branches are declared proven. |
| Scatter diagram | Examine specialty-week demand/capacity and booked waiting, or an appropriately defined travel/outcome comparison. | Preserve the observation unit and time order. A relationship need not be linear, strong, or causal; daily intake workload does not mechanically determine administrative waiting in this model. |
| Control chart | Interpret a supplied chart for a well-defined, reasonably homogeneous process segment. | The map promises Understand for interpretation and no YB construction/selection capability. An instructor must establish subgrouping, baseline, limits, and rules. A run chart alone does not meet this promise. |
| Stratification; complementary flowchart | Compare specialty, source, priority, calendar period, and pilot eligibility; map parallel authorization and clinical review. | Use stable denominators and comparable follow-up, and retain legitimate differences between routes. |

A feasible supplied-chart example exists: affiliated-primary-care referrals ordered July 7–December 14, 2025, grouped by enrollment week, with sufficient time for administrative document requests to be recorded.
There are 23 weekly groups of 898–1,135 referrals; 12.81% have a recorded document request overall.
This is a candidate for instructor review and chart preparation, not a completed demonstration of statistical control.
Do not pool different sources or the pre-centralization recording regime indiscriminately.
Control limits describe process behavior; customer targets are a different quantity ([NIST explanation](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc32.htm)).

## Descriptive Statistics: Strong Existing Evidence

The initial extract already permits counts, proportions, mean, median, standard deviation, quartiles, IQR, five-number summaries, percentiles, histograms, categorical displays, and time-ordered summaries.
It also makes denominators, missing stages, repeated records, pooled populations, and cohort maturity consequential.

| Specialty | Mean booked wait, days | Median | Standard deviation | P90 |
|---|---|---|---|---|
| Cardiology | 9.80 | 10 | 1.81 | 12 |
| Gastroenterology | 13.71 | 14 | 2.51 | 16 |
| Neurology | 42.47 | 37 | 19.85 | 75 |
| Orthopedics | 6.68 | 7 | 1.49 | 8 |
| Endocrinology | 48.85 | 45 | 25.65 | 89 |
| Pulmonology | 16.94 | 18 | 4.21 | 22 |

Here booked wait means appointment date minus booking date, among episodes with a booked appointment in the initial extract, including known future appointments.
It is not referral-to-care time for all patients.
The review used Polars' sample standard deviation and default nearest-interpolation P90; chapter instruction must state its chosen quantile convention.
The teaching opportunity is the different account supplied by center, spread, and tail, not a demand that every project report all measures.

Complaint frequencies are 912 callback, 867 unclear-next-step, 835 appointment-access, and 809 repeat-information records.
That relatively flat ranking is useful evidence against assuming that a Pareto plot must reveal one dominant category.
The underlying text consists of four recurring synthetic formulations, so it is weak material for learning qualitative interpretation or eliciting Kano classifications.

## Inference: Useful Openings, but Incomplete Coverage

The full extract is close to a census of recorded referral episodes for its specified period.
It does not need a sampling interval merely to describe those recorded episodes.
Inference needs a target beyond that description: a sampled review population, future operation under stated conditions, or an explicit experimental/null model.
Large record counts do not remove missingness, changing conditions, or dependence.
The initial 102,187 referral records include 35,092 records beyond the first occurrence of their patient identifiers; referral and patient counts are different units, and independence requires justification rather than assumption.

The initial review table has 792 sampled episodes: 471 internal-care confirmations, 63 outside-care confirmations, 42 confirmed declines, and 216 unable-to-confirm findings.
This is a useful opening for sample versus population, classification uncertainty, and proportion estimation under a specified review protocol.
The review date precedes the extract cutoff and only referrals already available by the review date are eligible.
A confidence interval for the proportion with confirmed outside care is not automatically an interval for all actual outside care; unresolved findings and cohort age remain consequential.
This proportion example also does not by itself satisfy the planned objective of an interval for a mean or mean difference.

The worked pilot is nonrandom, covers four selected sites and two specialties, and occurs in a later calendar period.
It supports scientific reasoning, practical-effect interpretation, confounding, fidelity, and cohort comparability.
It does not make every referral an independent randomized treatment assignment.
Nor are two different referral cohorts paired observations simply because one is before and the other after.
Paired t-tests require a meaningful one-to-one pairing; unequal-variance comparisons are a distinct design/method choice ([NIST t-test guidance](https://www.itl.nist.gov/div898/handbook/eda/section3/eda353.htm)).

### Recommended Inferential Companion

Add a small controlled study of referral-office work, such as time to locate the correct next owner using two tracking arrangements.
Specify the unit, sampling/assignment, comparable tasks, order effects, repeated observations, target population, and outcome before generating results.
A counterbalanced paired staff/task study could support mean differences, an instructor-approved t procedure, a confidence interval, and discussion of practical importance.
The same study can be used to illustrate supplied normal-model calculations if suitability is established, rather than pretending pooled referral waits are normally distributed.
This would be a proposed additional study, not evidence that the existing operational pilot was randomized or that its causal effect has been established.

Use a supplied resampling or repeated-sampling exercise to show how sample size and variability affect precision; distinguish standard deviation from standard error.
Confidence refers to the procedure's long-run coverage, not a probability assigned to the realized fixed interval ([NIST interval guidance](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm)).
Keep the planned Lady Tasting Tea investigation as a separate canonical introduction to random allocation and null-model reasoning.
Riverside can then provide transfer, rather than having to impersonate every foundational example.
Independent regression, ANOVA, experimental-design expertise, and general assumption checking remain later-belt capabilities.

## Process and Model Limits That Matter to Teaching

Calendar-day events do not record hands-on processing durations or identify value-added minutes.
Contributor truth contains modeled aggregate coordination minutes, but those are not learner-facing measured stage durations.
Consequently, proper processing-time, process-cycle-efficiency, and cost calculations need an observed-time supplement.
Lead times and intervals between recorded actions are available now; labeling either as touch time would be wrong.

First-pass yield can be taught for a narrow, fully defined packet-check route with adequate recording coverage.
Rolled throughput yield requires explicit stages, branches, conditional denominators, and cohort follow-up.
Multiplying an unconditional booked percentage by an unconditional completed percentage is not a defensible substitute.
Appropriate outside care and a patient's informed decision not to proceed must not automatically become quality defects.

Administrative waiting and handoff durations are sampled from configured ranges; central coordinator queues are not simulated from arriving workload and resource availability.
Specialty appointment capacity is finite and does constrain offers.
Thus the model supports investigation of specialty capacity, but cannot validate a claim that central understaffing caused an observed intake queue through a modeled workload feedback mechanism.
The organizational incentive tensions are narrative/design context, not a quantified employee behavior or retention-policy experiment.

The operational tables are already normalized and consistently coded.
Parsing dates, validation, joining, reshaping, and meaningful missingness are available, but the planned category-standardization exercise needs a small messy office export or teaching fixture.
Do not introduce accidental corruption into the canonical evidence merely to create a cleaning lesson.
Spaghetti diagrams require actual movement evidence and a layout; travel minutes and information handoff arrows do not supply a physical route.

## Additions Recommended Before Freezing the Teaching Sequence

| Evidence packet | Contents | Principal objective anchors from the working plan |
|---|---|---|
| Structured observation | Check sheet, operational definitions, selected inspectable packets, timestamped task observations, and a local layout/movement example where appropriate. | YB06.1–6; YB07.3; YB09.3. |
| Controlled analytical study | Protocol and small measurement dataset with a defensible comparison, mean-based inference, and an instructor-reviewed method. | YB10.3; YB13.3–5; YB14.1–6; YB18.2. Lady Tasting Tea remains a separate investigation under YB13.2. |
| Customer and staff evidence | Varied short accounts, interview/source-selection context, disagreements, and enough elicited requirement evidence for guided Kano work. | YB04.1–6; YB12.1, YB12.4; YB16.2. |
| Business brief | Loaded labor cost, observed work estimates, pilot/training costs, a contribution/capacity explanation, cash-flow timing, and miniature financial statements. | YB05.1–7; YB15.5; YB17.5; YB18.5. |

Also prepare a reviewed control-chart handout, a small deliberately messy export, and appropriate before/after 5S artifacts as chapter materials.
These are small targeted teaching additions; the referral volume is already sufficient.

## Learning-Map Reconciliation

Preserve the inferential promises and supply the evidence needed to teach them responsibly.
Clarify that seven-tools Apply does not override the explicit Understand expectation for control-chart interpretation or introduce independent chart construction at YB.
The existing seven-tools chapter's Analyze objective for control charts exceeds the map and should be reconciled during chapter revision.
Add recognition and use of a supplied method-suitability checklist at YB, while retaining independent assumption assessment at GB.
Distinguish interval calculation/interpretation and supplied precision calculations from independent power/design planning.
Retain guided qualitative evidence capture, basic result checks, bounded intervention review, and introductory FMEA refinements already identified in the working plan.
The present publication order still lacks dedicated chapters for the full planned probability, experimentation, and interval/t-test sequence; case potential does not establish instructional coverage.

## Full Crosswalk

The tables below cover every populated Yellow Belt cell in the baseline learning map reviewed here.
“Existing” means the case supplies an authentic evidence opportunity; it does not mean its instruction, feedback, or assessment is complete.
“Scaffold” means the case is suitable but a teaching procedure or artifact must be authored.
“Add evidence” identifies a missing case input; “Companion” identifies an additional focused investigation.
Mixed judgments distinguish usable elements from missing ones.

### Lean Six Sigma Principles and Tools

| Mapped capability | YB Bloom level | Case evidence | Application or gap |
|---|---|---|---|
| Five Principles of Lean | Apply | Existing | Value, flow, local versus patient progress; develop bounded countermeasures. |
| Respect for People and Kaizen Culture | Apply | Existing | Distributed expertise, staff constraints, patient accounts, and team review. |
| Eight Wastes | Analyze | Existing | Repeat contacts, clarification, waiting, and burdens shifted across offices; avoid calling necessary clinical work waste. |
| 5S | Apply | Add evidence | Supply a concrete work-area or shared-folder example with a before state and proposed upkeep. |
| PDCA Framework | Analyze | Existing | Relate investigation, pilot, check, and next-cycle decisions. |
| A3 Framework | Apply | Existing | Accumulate the bounded argument through nine boxes. |
| Basic Process Mapping | Analyze | Existing | Separate administration, clinical review, authorization, contact, and scheduling. |
| FLO Process Modeling | Apply | Scaffold | Author guided v2 build/validate/render work; the legacy template is not a completed v2 model. |
| Rendered Process Representations | Apply | Scaffold | Compare rendered v2 models with inspectable histories and accounts. |
| Spaghetti Diagrams, SIPOC, and IPO Analysis | Apply | Existing / Add evidence | SIPOC/IPO fit the case; physical movement requires a layout and observation supplement. |
| Seven Basic Quality Tools | Apply | Existing / Scaffold | See tool-by-tool review; add collection materials and a supplied reviewed control chart. |
| Process Metrics | Analyze | Existing / Add evidence | Lead and waiting intervals exist; touch time/PCE need observation, and FPY/RTY need route-specific definitions. |
| Control-Chart Interpretation | Understand | Scaffold | Interpret supplied limits and signals for a justified subgroup; do not require independent construction. |
| Critical-to-Quality Characteristics and Kano Analysis | Apply | Existing / Add evidence | Timely care and communication support CTQs; Kano needs elicited requirement evidence. |
| Customer Value and the Value of Lean Six Sigma | Apply | Existing | Distinguish care, internal retention, documentation, and staff effort. |

### Leading and Managing Projects

| Mapped capability | YB Bloom level | Case evidence | Application or gap |
|---|---|---|---|
| Problem Statements and SMART Goals | Analyze | Existing | Compare observed gaps with causal claims; bound population, measure, and time horizon. |
| Project Selection and Strategic Alignment | Apply | Existing | Choose a bounded service/source slice under the sponsor and Black Belt. |
| Formal Project Scoping and Effort Estimation | Understand | Scaffold | Explain scope and authority with a supplied brief and estimated effort assumptions. |
| Business-Case Construction | Apply | Add evidence | Supply economic inputs rather than substituting retention rhetoric for a financial estimate. |
| Meeting Agendas, Decisions, and Notes | Apply | Scaffold | Use a supplied agenda and record ownership, disagreements, and review dates. |
| Team Selection and Role Definition | Understand | Existing | Named team makes expertise and decision authority inspectable. |
| Running Effective Meetings | Understand | Scaffold | Explain effective and ineffective decisions using team scenes and meeting records. |
| Facilitation | Understand | Scaffold | Work through disagreement without making the Black Belt omniscient. |
| Stakeholder Engagement and Communication | Apply | Existing / Add evidence | Callback and handoffs supply purpose; richer accounts and communication artifacts enable practice. |
| Responsible Improvement and Ethical Judgment | Apply | Existing | Outside-care choices, uncertainty, access burdens, and proportionate authority. |
| Evaluating Unintended Consequences and Stakeholder Impacts | Apply | Existing / Add evidence | Assess redistributed work, retention incentives, and safeguards; add richer stakeholder evidence. |
| Reflective Practice and Learning from Failure | Apply | Scaffold | Require revisions of scope, measure, or causal claim and explain why they changed. |

### Data Understanding

| Mapped capability | YB Bloom level | Case evidence | Application or gap |
|---|---|---|---|
| Structured Process Observation and Data Capture | Analyze | Add evidence | Observation form, selected records, and coverage/definition problems are needed. |
| Baseline Construction from Process Data | Analyze | Existing | Choose periods and cohorts, handle missing history, and distinguish recorded outcomes from care. |
| Obtaining and Importing Datasets | Apply | Existing | Prepared extracts, dictionaries, and explicit release cutoffs. |
| Basic Data Cleaning and Validation | Apply | Existing / Add evidence | Dates, keys, ranges, and missingness are available; a messy export supplies category/duplicate repair. |
| Missing-Data and Data-Quality Strategies | Understand | Existing | Differentiate unrecorded activity, future outcomes, and unconfirmed care. |
| Levels of Measurement and Data Types | Apply | Existing | Identifiers, categories, binary flags, dates, counts, and durations. |
| Summarizing and Grouping Data | Apply | Existing | Referral versus contact counts; grouped service/source summaries. |
| Reshaping Data (Pivots, Melts, and Group Operations) | Apply | Existing | Turn long activity histories into episode features and subgroup tables. |
| Identifying and Handling Outliers | Understand | Existing | Long waits and inherited records require investigation rather than automatic deletion. |
| Interpretation of Tables and Graphs | Analyze | Existing | Different centers/tails, mixed cohorts, incomplete outcomes, and changing definitions. |
| Construction of Data Visualizations | Apply | Existing | Categorical, distribution, relationship, and time-ordered displays. |
| Exploratory Data Analysis | Apply | Existing | Inspect types and populations, compare strata, and formulate further questions. |
| Time-Series Display | Apply | Existing | Daily/weekly referral cohorts, capacity, and declared process dates; retain maturity rules. |
| Qualitative Data Collection and Analysis | Understand | Add evidence | Four repeated complaint formulations do not supply rich accounts or a credible coding exercise. |

### Computational and Data Systems

| Mapped capability | YB Bloom level | Case evidence | Application or gap |
|---|---|---|---|
| Computer and File-System Fundamentals | Apply | Existing / Scaffold | Use the prepared investigation workspace and teach its folders explicitly. |
| Basic Terminal Navigation and Commands | Apply | Existing / Scaffold | Navigate files and launch the prepared notebook through guided instructions. |
| Shell Workflows and Command-Line Tooling | Understand | Scaffold | Explain basic launch and inspection commands without adding automation mastery. |
| marimo Notebook Workflows | Apply | Existing | Starter executes over the real initial extract; exercises and fading support remain to author. |
| Python Programming for Process Analysis | Apply | Existing / Scaffold | Adapt short transformations and explain their inputs/results. |
| Importing and Using Python Packages | Apply | Existing | Use Polars and plotting/statistics packages through supplied patterns. |
| Reproducible Notebook and Script Workflows | Apply | Existing / Scaffold | Trace records and rerun; author the supplied short script and review task. |
| Dependency and Environment Management | Understand | Existing | Explain the managed environment and retained lockfile, not independent toolchain design. |

### Statistical Analysis

| Mapped capability | YB Bloom level | Case evidence | Application or gap |
|---|---|---|---|
| Descriptive Statistics | Apply | Existing | Meaningful center, spread, and tails with explicit populations. |
| Observed Distributions and Descriptive Percentiles | Apply | Existing | Six-service contrasts already provide useful differences; declare quantile convention. |
| The Standard Normal Distribution | Apply | Companion | Use an established normal model or sampling exercise; do not assume pooled waits are normal. |
| Scientific and Experimental Reasoning | Analyze | Existing | Nonrandom rollout, recording changes, missing evidence, and rival explanations are substantive. |
| Hypothesis-Testing Foundations (including the Lady Tasting Tea) | Apply | Companion | Retain the planned tea/randomization investigation and add a bounded Riverside transfer. |
| Student's *t*-Tests | Apply | Companion | Add a design-appropriate mean comparison with supplied suitability guidance; pilot cohorts are not paired or randomized by default. |
| Confidence Intervals and Sample-Size Concepts | Apply | Existing / Companion | The review sample supports proportion examples; add mean/difference intervals and a precision exercise. |
| Type I and Type II Errors | Understand | Companion | Use the explicit null-model study to distinguish false alarms, missed effects, and practical consequences. |
| Scatterplots and Linear Association | Apply | Existing | Define meaningful paired units and discuss weak/nonlinear or confounded relationships. |
| Common Probability Distributions | Understand | Existing / Scaffold | Stratified binary events support simple binomial reasoning; arrivals are not automatically a homogeneous Poisson process. |

### Business Understanding

| Mapped capability | YB Bloom level | Case evidence | Application or gap |
|---|---|---|---|
| Customer and Stakeholder Value | Apply | Existing | Patient progress, staff work, communication, and organizational obligations can conflict. |
| Financial Statements from a Process-Improvement Perspective | Understand | Add evidence | A miniature financial packet is needed; current tables contain no financial statements. |
| Fundamentals of Accounting | Understand | Add evidence | Provide simple revenue, expense, asset, liability, and cash-flow examples. |
| Time Value of Money | Apply | Add evidence | Provide dated costs/benefits and a supplied discount assumption. |
| Return on Investment | Apply | Add evidence | Provide incremental pilot costs, plausible benefits, capacity constraints, and uncertainty. |
| Cost of Quality and Cost of Poor Quality | Apply | Add evidence | Link observed rework/contacts to loaded costs; do not equate all checking or review with failure. |
| Strategic Alignment and Mission Fit | Apply | Existing | Access, continuity, retention, and costs provide a substantive project-selection tension. |
| Benefits Realization and Sustainment | Apply | Existing / Add evidence | Operational follow-up exists; financial benefits, ownership records, and a sustainment plan need additional inputs. |
| Competitive Advantage and Strategic Planning | Understand | Existing / Scaffold | Explain regional access and trust as strategic considerations without inferring market effects from referral counts. |
