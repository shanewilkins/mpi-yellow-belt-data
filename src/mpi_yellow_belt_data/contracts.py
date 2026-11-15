"""Typed Yellow Belt authoring contracts; legacy v1 exchange schemas stay frozen."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator
from pydantic.json_schema import SkipJsonSchema

Digest = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Identifier = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$")]
Version = Annotated[str, Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")]
NonNegative = Annotated[float, Field(ge=0, allow_inf_nan=False)]
Positive = Annotated[float, Field(gt=0, allow_inf_nan=False)]
PositiveInt = Annotated[int, Field(gt=0)]
Count = Annotated[int, Field(ge=0)]
Probability = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]


def safe_relative_path(value: str) -> str:
    pure = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or ":" in value
        or pure.is_absolute()
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        raise ValueError("must be a confined relative path")
    return value


RelativePath = Annotated[str, AfterValidator(safe_relative_path)]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, validate_default=True)


class DatasetPin(Contract):
    version: Version
    manifest_sha256: Digest


class Archive(Contract):
    url: Annotated[str, Field(pattern=r"^https://")]
    sha256: Digest


class CaseDefinition(Contract):
    schema_version: Annotated[int, Field(ge=1, le=1)]
    id: Literal["riverside"]
    title: Annotated[str, Field(min_length=1)]
    kind: Literal["synthetic"]
    sources: Annotated[
        list[RelativePath], Field(min_length=1, json_schema_extra={"uniqueItems": True})
    ]
    chapters: list[str]
    dataset: DatasetPin | None
    entry_points: dict[str, RelativePath]
    # Defaults support internal use; exclude_unset preserves the v1 dictionary API.
    archive: Archive | SkipJsonSchema[None] = None
    aliases: dict[str, RelativePath] = Field(default_factory=dict)
    learner_files: dict[RelativePath, RelativePath] = Field(default_factory=dict)

    @model_validator(mode="after")
    def unique_sources(self) -> Self:
        if len(self.sources) != len(set(self.sources)):
            raise ValueError("sources must be unique")
        if "archive" in self.model_fields_set and self.archive is None:
            raise ValueError("archive must be an object when supplied")
        return self


class DatasetFile(Contract):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        validate_default=True,
        json_schema_extra={
            "dependentRequired": {"rows": ["columns"], "columns": ["rows"]}
        },
    )
    path: RelativePath
    sha256: Digest
    bytes: Count
    rows: Count = 0
    columns: list[str] = Field(
        default_factory=list, json_schema_extra={"uniqueItems": True}
    )

    @model_validator(mode="after")
    def paired_table_shape(self) -> Self:
        if ("rows" in self.model_fields_set) != ("columns" in self.model_fields_set):
            raise ValueError("rows and columns must be supplied together")
        if len(self.columns) != len(set(self.columns)):
            raise ValueError("columns must be unique")
        return self


class RiversideConfig(Contract):
    seed: Count
    # These dimensions are fixed in the maintained v1 generator, not tunable inputs.
    row_count: Literal[1484]
    start_date: Literal["2025-10-01"]
    end_date: Literal["2026-03-31"]


class PreservedProvenance(Contract):
    baseline_source_commit: Annotated[str, Field(pattern=r"^[a-f0-9]{40}$")]
    baseline_lockfile_sha256: Digest
    baseline_receipt: RelativePath
    classification: Literal["synthetic"]
    generation: RiversideConfig
    runtime_versions: Annotated[
        dict[str, Annotated[str, Field(min_length=1)]], Field(min_length=1)
    ]


class DatasetManifest(Contract):
    schema_version: Annotated[int, Field(ge=1, le=1)]
    case_id: Literal["riverside"]
    version: Literal["1.0.0"]
    data_schema: Literal["riverside-preserved-v1"]
    observation_window: Annotated[str, Field(min_length=1)]
    provenance: PreservedProvenance
    files: Annotated[list[DatasetFile], Field(min_length=1, max_length=1)]

    @model_validator(mode="after")
    def expected_file(self) -> Self:
        if self.files[0].path != "riverside_referrals.csv":
            raise ValueError("v1 requires exactly riverside_referrals.csv")
        return self


class PilotConfig(Contract):
    source_sites: Annotated[list[str], Field(min_length=1)]
    specialties: Annotated[list[str], Field(min_length=1)]
    fidelity: Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
    additional_minutes_per_episode: Annotated[float, Field(ge=0, allow_inf_nan=False)]


class NetworkConfig(Contract):
    seed: Count
    base_source_revision: Annotated[str, Field(pattern=r"^[a-f0-9]{40}$")]
    annual_referrals: PositiveInt
    new_episodes: PositiveInt
    inherited_episodes: Count
    start_date: str
    centralization_date: str
    initial_cutoff: str
    investigation_cutoff: str
    pilot_date: str
    end_date: str
    affiliated_sites: PositiveInt
    independent_practices: PositiveInt
    primary_care_clinician_fte: PositiveInt
    primary_care_visits_per_day: PositiveInt
    clinical_days_per_year: PositiveInt
    coordination_fte: PositiveInt
    coordination_productive_hours_per_year: PositiveInt
    source_weights: dict[
        Literal[
            "affiliated_primary_care",
            "independent_practice",
            "ed_followup",
            "other_specialty",
        ],
        PositiveInt,
    ]
    specialties: Annotated[
        dict[str, Annotated[list[int | float], Field(min_length=3, max_length=3)]],
        Field(min_length=1),
    ]
    pilot: PilotConfig
    audit_probability: Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]

    @model_validator(mode="after")
    def relationships(self) -> Self:
        from datetime import date
        from math import isfinite

        dates = [
            date.fromisoformat(getattr(self, name))
            for name in (
                "start_date",
                "centralization_date",
                "initial_cutoff",
                "investigation_cutoff",
                "pilot_date",
                "end_date",
            )
        ]
        if dates != sorted(dates) or dates[3] >= dates[4]:
            raise ValueError("Invalid observation/implementation chronology")
        if (
            sum(value[0] for value in self.specialties.values()) != 100
            or sum(self.source_weights.values()) != 100
        ):
            raise ValueError("Specialty and source shares must sum to 100")
        if set(self.source_weights) != {
            "affiliated_primary_care",
            "independent_practice",
            "ed_followup",
            "other_specialty",
        }:
            raise ValueError("Missing source population")
        for weight, slots, clarification in self.specialties.values():
            if (
                any(
                    isinstance(v, bool) or not isfinite(v)
                    for v in (weight, slots, clarification)
                )
                or weight <= 0
                or slots <= 0
                or int(slots) != slots
                or not 0 <= clarification <= 1
            ):
                raise ValueError("Invalid specialty parameters")
        if not set(self.pilot.specialties) <= self.specialties.keys():
            raise ValueError("Unknown pilot specialty")
        if len(self.pilot.source_sites) != len(set(self.pilot.source_sites)):
            raise ValueError("Duplicate pilot source site")
        if any(
            not site.startswith("AP")
            or not site[2:].isdigit()
            or not 1 <= int(site[2:]) <= self.affiliated_sites
            for site in self.pilot.source_sites
        ):
            raise ValueError("Unknown pilot source site")
        return self


class NetworkProvenance(Contract):
    classification: Literal["synthetic"]
    source_revision: Annotated[str, Field(pattern=r"^[a-f0-9]{40}$")]
    source_revision_note: str
    python: str
    runtime_versions: dict[str, str]
    config: NetworkConfig
    source_sha256: dict[RelativePath, Digest]
    lockfile_sha256: Digest | None
    releases: dict[Literal["initial", "investigation", "followup"], str]


class NetworkManifest(Contract):
    schema_version: Literal[1]
    case_id: Literal["riverside"]
    version: Literal["2.0.0", "2.0.0-experiment"]
    data_schema: Literal["riverside-linked-v2"]
    observation_window: str
    provenance: NetworkProvenance
    files: Annotated[list[DatasetFile], Field(min_length=21, max_length=21)]

    @model_validator(mode="after")
    def release_identity(self) -> Self:
        config = self.provenance.config
        if self.provenance.releases != {
            "initial": config.initial_cutoff,
            "investigation": config.investigation_cutoff,
            "followup": config.end_date,
        }:
            raise ValueError("Unexpected release identity or cutoff")
        names = [file.path for file in self.files]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate manifest path")
        return self


SCHEMA_MODELS: dict[str, type[BaseModel]] = {
    "riverside-network-config-v2.json": NetworkConfig,
    "riverside-network-dataset-v2.json": NetworkManifest,
    "yellow-belt-case-v1.json": CaseDefinition,
    "yellow-belt-dataset-v1.json": DatasetManifest,
    "riverside-config-v1.json": RiversideConfig,
}


def export_schemas(directory: Path, *, check: bool = False) -> None:
    for filename, model in SCHEMA_MODELS.items():
        expected = (
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n"
        )
        destination = directory / filename
        if check:
            if not destination.is_file() or destination.read_text() != expected:
                raise ValueError(f"Generated schema is stale: {destination}")
        else:
            directory.mkdir(parents=True, exist_ok=True)
            destination.write_text(expected)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    export_schemas(Path(__file__).parent / "schemas", check=args.check)


if __name__ == "__main__":
    main()
