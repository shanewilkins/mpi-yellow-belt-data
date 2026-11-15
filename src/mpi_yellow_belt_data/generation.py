"""Explicit v1 experiments; the maintained synthetic mechanism is unchanged."""

import csv
import json
import sys
import tempfile
from pathlib import Path

from mpi_yellow_belt_data.catalog import (
    CaseError,
    case_contract,
    check_dataset,
    generation_config,
    sha256,
    source_file,
)
from mpi_yellow_belt_data.contracts import RiversideConfig


def generate(case_id: str, *, output: Path, seed: int | None = None) -> Path:
    definition = case_contract(case_id)
    config = generation_config(case_id)
    if seed is not None:
        config = RiversideConfig.model_validate({**config.model_dump(), "seed": seed})
    if output.exists() or output.is_symlink():
        raise CaseError(f"Generation destination already exists: {output}")
    from mpi_yellow_belt_data.cases.riverside.model.referrals import generate_rows
    from mpi_yellow_belt_data.table_validation import validate_tables

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".riverside-generate-", dir=output.parent
    ) as temporary:
        stage = Path(temporary) / "payload"
        stage.mkdir()
        records = generate_rows(seed=config.seed)
        with (stage / "riverside_referrals.csv").open("x", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
        validate_tables(stage)
        (stage / "generation.json").write_text(
            json.dumps(
                {
                    "case_id": case_id,
                    "configuration": generation_config(case_id).model_dump(mode="json"),
                    "seed_override": seed,
                    "python": sys.version,
                    "runtime_versions": {},
                    "source_sha256": {
                        name: sha256(source_file(case_id, name))
                        for name in definition.sources
                    },
                    "files": {
                        path.name: sha256(path) for path in sorted(stage.iterdir())
                    },
                    "status": "unpublished generation; compare before adopting as a dataset version",
                },
                indent=2,
            )
            + "\n"
        )
        if output.exists() or output.is_symlink():
            raise CaseError(f"Generation destination already exists: {output}")
        stage.rename(output)
    return output


def compare_generation(case_id: str, output: Path, *, root: Path | None = None) -> bool:
    manifest = check_dataset(case_id, root=root)
    return bool(manifest["files"]) and all(
        (output / item["path"]).is_file()
        and sha256(output / item["path"]) == item["sha256"]
        for item in manifest["files"]
    )
