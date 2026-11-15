# Riverside specialist referrals

Start with [the rewritten scenario](scenario.md), [v2 data dictionary](data_dictionary.md), and [provenance](provenance.md).
The [specification](specification_v2.md) implements the [design decisions and cast](design_v2.md), including workload assumptions, mechanisms, and evidence limits.
The [Yellow Belt coverage review](coverage_review.md) records a full baseline comparison with the learning map and identifies the additional teaching evidence needed.
The proposed Yellow Belt workflow contract in the book repository connects the belt promise, A3 artifacts, and FLO/lss4py support requests.
The annotated Yellow Belt outline in the book repository develops that comparison into chapter investigations, objectives, evidence dependencies, and A3 handoffs.
Implementation and configuration live under `src/mpi_yellow_belt_data/cases/riverside/`; maintained notebooks and FLO files live under `notebooks/riverside/` and `models/riverside/`.

## Version 2: Regional Referral Network

The generated local artifact contains 150,000 new episodes plus 2,000 inherited records across 27 specialties, with dated extracts for the initial investigation, investigation update, and follow-up.
Its release manifest is pinned in [../../releases/riverside/2.0.0.json](../../releases/riverside/2.0.0.json).
Bulk data are ignored by Git; a clean checkout can reproduce them using the locked environment.
Generation requires a new destination and does not change version 1.

```console
uv run --locked --extra generation mpi-yellow-belt-data generate riverside --dataset-version 2.0.0 --output data/cases/riverside/2.0.0
uv run --locked --extra generation mpi-yellow-belt-data check riverside --dataset-version 2.0.0
uv run --locked --extra generation mpi-yellow-belt-data prepare riverside --dataset-version 2.0.0 --output /tmp/riverside-v2-learner
```

Preparation copies only the initial extract by default, excluding later evidence and model truth.
Use `--release investigation` or `--release followup` with a new workspace when that evidence becomes available; the follow-up workspace includes the [worked pilot note](pilot_v2.md).
The prepared workspace contains a marimo starter and an environment declaration pinned to the installed analysis packages.

For a structural sample, use `--sample 600 --output /tmp/riverside-v2-sample` with the generator.
Samples are labeled experiments and do not reproduce full-scale queue congestion.
For contributor readouts and five contrasting journey excerpts, see [reference/README.md](reference/README.md).
No remote dataset artifact or public download has been published.

## Version 1: Existing Publication Consumers

This repository owns the v1 and v2 Riverside implementation and evidence definitions.
The book consumes a hash-pinned wheel and retains publication mappings and compatibility imports.

`case.yml` continues to pin version 1.0.0 for existing publication computations and `mpi-book cases` commands without an explicit version.
Its single-table schema, 1,484-row dataset, aliases, and generator remain preserved.
Version-1 learner preparation selects the notes under [legacy_v1/](legacy_v1/), rather than applying the v2 scenario and dictionary to old evidence.

From the repository root:

```console
uv run --locked --extra generation mpi-yellow-belt-data check riverside
```

This checks version 1 local evidence without downloading or regenerating it.
See the case guide in the book repository for generation and bundles.
Publication-only notebooks stay in book/notebooks/; reusable templates stay in templates/.
