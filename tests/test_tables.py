from datetime import date

import polars as pl
import pytest

from mpi_yellow_belt_data import catalog, generation
from mpi_yellow_belt_data.table_validation import validate_frame, validate_release


@pytest.fixture
def frame():
    return pl.read_csv(
        catalog.dataset_file("riverside", "riverside_referrals.csv"),
        try_parse_dates=True,
        infer_schema_length=None,
    )


def test_preserved_evidence_and_legitimate_missingness(frame):
    before = frame.clone()
    assert frame["scheduled_date"].null_count() == 391
    assert frame["reminder_sent_date"].null_count() > 0
    assert frame.filter(pl.col("appointment_date") > date(2026, 3, 31)).height > 0
    validate_frame(frame)
    assert frame.equals(before)
    assert validate_release() == {"referrals": 1484}


@pytest.mark.parametrize(
    "mutation",
    [
        lambda f: f.drop("referral_id"),
        lambda f: f.with_columns(pl.lit("maybe").alias("booked_flag")),
        lambda f: pl.concat([f, f.head(1)]),
        lambda f: f.with_columns(pl.col("lead_time_days").cast(pl.String)),
        lambda f: f.with_columns(pl.lit(-1).alias("status_update_days")),
        lambda f: f.with_columns(pl.lit(None, dtype=pl.String).alias("referral_id")),
        lambda f: f.with_columns(pl.lit(0).alias("unexpected")),
    ],
)
def test_structure_rejects_corruption(frame, mutation):
    with pytest.raises(catalog.CaseError, match="table schema"):
        validate_frame(mutation(frame))


@pytest.mark.parametrize(
    "mutation,message",
    [
        (
            lambda f: f.with_columns(
                pl.lit(None, dtype=pl.Date).alias("scheduled_date")
            ),
            "population",
        ),
        (
            lambda f: f.with_columns(
                (pl.col("lead_time_days") + 1).alias("lead_time_days")
            ),
            "lead time",
        ),
        (
            lambda f: f.with_columns(
                pl.col("scheduled_date").alias("appointment_date")
            ),
            "chronology",
        ),
        (
            lambda f: f.with_columns(
                pl.lit(date(2020, 1, 1)).alias("first_contact_date")
            ),
            "Contact",
        ),
        (
            lambda f: f.with_columns(
                pl.lit("completed_in_network").alias("network_outcome")
            ),
            "outcomes",
        ),
        (lambda f: f.with_columns(pl.lit("completed").alias("status")), "status"),
    ],
)
def test_plausible_shapes_with_inconsistent_claims_fail(frame, mutation, message):
    with pytest.raises(catalog.CaseError, match=message):
        validate_frame(mutation(frame))


def test_full_regeneration_preserves_selected_csv_and_experiments_are_distinct(
    tmp_path,
):
    output = generation.generate("riverside", output=tmp_path / "preserved")
    assert generation.compare_generation("riverside", output)
    assert not (output / "manifest.json").exists()
    with pytest.raises(catalog.CaseError, match="already exists"):
        generation.generate("riverside", output=output)
    other = generation.generate("riverside", output=tmp_path / "experiment", seed=43)
    assert not generation.compare_generation("riverside", other)


def test_invalid_generated_evidence_is_not_exposed(tmp_path, monkeypatch):
    from mpi_yellow_belt_data.cases.riverside.model import referrals

    original = referrals.generate_rows

    def broken(**kwargs):
        records = original(**kwargs)
        records[0]["lead_time_days"] = "10000"
        return records

    monkeypatch.setattr(referrals, "generate_rows", broken)
    output = tmp_path / "invalid"
    with pytest.raises(catalog.CaseError):
        generation.generate("riverside", output=output)
    assert not list(tmp_path.iterdir())
