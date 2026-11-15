"""Resolve curated material-first workspace assets in checkouts and wheels."""

from pathlib import Path

from mpi_yellow_belt_data.catalog import _CHECKOUT, PACKAGE_ROOT, relative_file


def asset_file(name: str) -> Path:
    if (_CHECKOUT / "pyproject.toml").is_file():
        return relative_file(_CHECKOUT, name)
    for prefix, folder in (
        ("docs/", "_docs"),
        ("releases/", "_releases"),
        ("notebooks/", "_notebooks"),
        ("models/", "_models"),
    ):
        if name.startswith(prefix):
            return relative_file(PACKAGE_ROOT / folder, name.removeprefix(prefix))
    return relative_file(PACKAGE_ROOT / "_assets", name)


def release_pin() -> Path:
    return asset_file("releases/riverside/2.0.0.json")


def publication_assets() -> dict[str, Path]:
    return {
        "templates/yellow_belt_a3_notebook_template.py": asset_file(
            "notebooks/riverside/a3_v1.py"
        ),
        "templates/yellow_belt_sppm_template.flo": asset_file(
            "models/riverside/current_state.flo"
        ),
    }
