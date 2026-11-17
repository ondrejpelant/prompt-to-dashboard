# Orchestration

`definitions.py` is the pipeline as one Dagster asset graph: landing → `raw` → the dbt models
and tests in `staging`/`core` → the Metabase sync. Each asset is a thin wrapper around the exact
function its `poe` task already calls (see [ADR-0008](../docs/adr/0008-orchestration-with-dagster.md))
- no pipeline logic lives here twice.

```bash
uv run poe dagster
```

opens Dagster's local UI; materialize everything from there with one click. `dagster-dbt`
builds one asset per dbt model and test straight from dbt's own manifest, with dbt's lineage,
so a failed dbt test stops the Metabase sync from running on broken data.

There is no schedule or sensor: nothing here runs unattended. Trigger a run by hand when you
want fresh data, same as running the `poe` tasks one by one - this just adds the dependency
graph and the fail-fast guarantee. The agent and chat UI are not part of this graph; they are
interactive, not a batch step.
