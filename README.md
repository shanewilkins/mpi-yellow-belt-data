# Yellow Belt course materials

This repository owns Riverside's simulation, evidence definitions, documentation, investigation starters, and FLO model.
The book consumes a separately built, hash-pinned package; students use a tagged Git checkout and its committed lockfile.
The current source and stage archives are local migration candidates; a public course tag and download locations have not yet been published.

## Student workspace

Clone the selected course tag when it is published, then prepare its environment:

```console
git clone --branch <course-tag> https://github.com/shanewilkins/mpi-yellow-belt-data.git
cd mpi-yellow-belt-data
uv sync --locked --extra learner --no-dev
```

Obtain the selected dated evidence archive explicitly from the course release.
The small `releases/riverside/learner-stages.json` index pins each archive's checksum.
Initial archives contain only the initial six tables, supporting notes, and starter, excluding later extracts and contributor truth.

```console
uv run --locked --extra learner --no-dev mpi-yellow-belt-data prepare riverside --dataset-version 2.0.0 --archive /path/to/riverside-initial.zip --output work/riverside/initial
uv run --locked --extra learner --no-dev marimo edit work/riverside/initial/investigate.py
```

Edit your personal copy under `work/` and save it in marimo.
Close and reopen the same file to continue.
Keep supplied evidence unchanged; place transformed tables and outputs beside your personal investigation.
An absent recorded event does not prove that an activity never happened.
The initial, investigation, and follow-up extracts are cumulative populations, not independent batches to concatenate.

After the environment and evidence are prepared, use `uv run --offline --locked --extra learner --no-dev` for offline work.
Setup requires package access or a populated cache; opening a notebook never fetches or regenerates evidence.

## Backups and updates

Ignored personal work is not backed up by upstream Git.
Export it to a separate backup location:

```console
uv run --locked --extra learner --no-dev mpi-yellow-belt-data export-work work/riverside/initial --output /path/to/backups/riverside-initial.zip
```

The export records course/evidence identities, original input hashes, and current personal-file hashes.
It refuses existing destinations and symlinks.
Keep backups outside the checkout and test that you can reopen your saved notebook.
For a course update, clone the new tag beside the old checkout, set up its environment, and prepare its selected evidence into a new work directory.
Transfer personal work deliberately and retain the prior workspace and backup.
Do not replace an active investigation with `git pull` or overwrite it with a new starter.
Prepare investigation/follow-up archives into separate directories as they become available.

## Maintainer boundaries

The base package provides typed Pydantic authoring contracts, discovery, and integrity checks without notebook/numerical/table-validation imports.
The optional validation capability adds Pandera/Polars table acceptance; generation validates before exposing completed output.
Small v1 evidence is packaged; bulk v2 data and stage ZIPs remain outside ordinary Git source and the wheel.
The adopted v2 manifest is unchanged; regenerated provenance is distinct from that adopted identity.
See [contract scope](docs/contracts.md) and the [Riverside dictionary](docs/riverside/data_dictionary.md).
