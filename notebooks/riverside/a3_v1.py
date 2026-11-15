import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path

    import marimo as mo
    import polars as pl

    return Path, mo, pl


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Yellow Belt A3 Notebook

    Use this notebook to accumulate the evidence, analysis, and decisions that
    support the Yellow Belt A3. Keep interpretation close to the code and output
    that earned it.
    """)
    return


@app.cell
def _(Path):
    data_path = Path("data/riverside/riverside_referrals.csv")
    if not data_path.exists():
        from mpi_yellow_belt_data.catalog import dataset_file

        data_path = dataset_file("riverside", "riverside_referrals.csv")
    return (data_path,)


@app.cell
def _(data_path, pl):
    referrals_raw = pl.read_csv(data_path, null_values="")
    return (referrals_raw,)


@app.cell
def _(mo, referrals_raw):
    mo.vstack(
        [
            mo.md(
                f"""
                **Environment check:** Polars loaded
                `{referrals_raw.height:,}` referral records and
                `{referrals_raw.width}` fields.
                """
            ),
            referrals_raw.select(referrals_raw.columns[:6]).head(),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Box 1 — Background, problem, and impact

    Record the bounded process condition, why it matters now, and the factual
    problem statement. Separate observed conditions from assumed causes.

    ## Box 2 — Voice of the Customer and CTQs

    Preserve stakeholder language, then show how it becomes measurable
    requirements.

    ## Box 3 — Current condition

    Add the FLO map, operational definitions, baseline summaries, subgroup
    comparisons, and time-ordered evidence that describe the current process.

    ## Boxes 4 and 5 — Target and likely causes

    State the target condition and rank likely causal mechanisms against the
    evidence.

    ## Boxes 6 and 7 — Countermeasures and risk review

    Connect proposed countermeasures to likely causes and pressure-test them
    with the introductory FMEA.

    ## Boxes 8 and 9 — Implementation and follow-through

    Name owners, milestones, review measures, remaining risks, and the
    conditions for standardization or revision.
    """)
    return


if __name__ == "__main__":
    app.run()
