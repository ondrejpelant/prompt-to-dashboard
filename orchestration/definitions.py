"""The pipeline as one Dagster asset graph: landing -> raw -> dbt -> Metabase sync.

Each asset is a thin wrapper around the exact function its "poe" task already calls -
no pipeline logic lives here twice (see ADR-0008). Run it with:

    uv run poe dagster

then open the UI it prints and materialize everything with one click. There is no
schedule: nothing here runs unattended yet - trigger a run by hand when you want fresh
data, same as running the poe tasks one by one. The agent and chat UI are interactive,
not a batch step, so they are not part of this graph.
"""

from pathlib import Path

from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetSpec,
    Definitions,
    MaterializeResult,
    asset,
    multi_asset,
)
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

from bi import sync_metabase
from ingestion import land_source, load_raw

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = "contoso_100k"
# The 8 tables ingestion/load_raw.py loads - one dbt source each (dbt/models/staging/_sources.yml).
# dagster-dbt's default asset key for a dbt source is ["<schema>", "<table>"], so a spec with
# that same key here is what makes raw_tables the one asset dbt's own lineage already points to.
RAW_TABLES = [
    "currencyexchange",
    "customer",
    "date",
    "orderrows",
    "orders",
    "product",
    "sales",
    "store",
]

dbt_project = DbtProject(project_dir=REPO_ROOT / "dbt", profiles_dir=REPO_ROOT / "dbt")
dbt_project.prepare_if_dev()


def run_step(step: str, action) -> None:
    """A script's SystemExit (its normal way of failing) must fail this asset, not the
    whole Dagster process - Dagster only treats a plain Exception that way."""
    try:
        action()
    except SystemExit as error:
        raise Exception(f"{step} failed: {error}") from error


@asset(description="Download the newest Contoso release into data/landing/ (uv run poe land)")
def landed_source() -> None:
    run_step(
        "land",
        lambda: land_source.land(
            land_source.Source.load(DEFAULT_SOURCE), land_source.DEFAULT_LANDING_ROOT
        ),
    )


@multi_asset(
    specs=[AssetSpec(key=AssetKey(["raw", table]), deps=[landed_source]) for table in RAW_TABLES],
    description="Load the newest landed load into raw, with its audit columns (uv run poe raw)",
)
def raw_tables():
    run_step("raw", lambda: load_raw.load(DEFAULT_SOURCE))
    for table in RAW_TABLES:
        yield MaterializeResult(asset_key=AssetKey(["raw", table]))


@dbt_assets(manifest=dbt_project.manifest_path)
def core_warehouse(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


@asset(
    deps=[core_warehouse],
    description=(
        "Connect Metabase to the warehouse and check it sees every description and "
        "key (uv run poe metabase)"
    ),
)
def metabase_sync() -> None:
    run_step("metabase", sync_metabase.main)


defs = Definitions(
    assets=[landed_source, raw_tables, core_warehouse, metabase_sync],
    resources={"dbt": DbtCliResource(project_dir=dbt_project)},
)
