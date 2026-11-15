"""Riverside v2 learner starter; run from a prepared evidence workspace."""

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path

    import marimo as mo
    import polars as pl

    return Path, mo, pl


@app.cell
def _(Path, mo, pl):
    import json

    workspace = Path(__file__).resolve().parent
    evidence = json.loads((workspace / "evidence.json").read_text())
    referrals = pl.scan_csv(workspace / "data/referrals.csv")
    events = pl.scan_csv(workspace / "data/events.csv")
    mo.md(
        f"# Riverside: begin with the records\n\nThis is the **{evidence['release']}** extract, available as of **{evidence['as_of']}**. Read the data dictionary before interpreting missing events or unfinished episodes."
    )
    return events, referrals


@app.cell
def _(events, pl, referrals):
    first_admin_record = (
        events.filter(pl.col("event_type") == "admin_complete")
        .group_by("referral_id")
        .agg(pl.col("occurred_date").min().alias("first_recorded_admin_completion"))
    )
    joined = referrals.join(first_admin_record, on="referral_id", how="left")
    # A left join retains episodes without this recorded event.
    # Null does not establish that the administrative work never happened.
    joined.head(12).collect()
    return


@app.cell
def _(mo):
    mo.md("""
    Choose a population and a question before adding a summary.
    Which episodes had enough follow-up time for the outcome you want to measure?
    What would you need to learn from the team or a patient before interpreting a missing record?

    Keep your scope, definitions, joins, checks, and revisions together in this notebook.
    Compare plausible explanations and propose a bounded investigation under Dana's leadership.
    """)
    return


if __name__ == "__main__":
    app.run()
