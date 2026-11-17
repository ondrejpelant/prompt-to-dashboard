# ADR-0008: Use Dagster for orchestration, as an asset graph with no schedule

- **Status:** Accepted
- **Date:** 2026-11-17

## Context

ADR-0002 named Dagster for orchestration but left it "confirmed when those phases start." Steps
1-6 of the project plan are done and run as separate `poe` tasks (`land`, `raw`, `build`,
`metabase`), each triggered by hand. Nothing ties them together: running `build` before `raw`
just builds `staging`/`core` on stale data, and a `dbt build` that fails a test does not stop
`poe metabase` from syncing whatever `core` already has to Metabase. Nothing today is actually
unattended - Ondra runs these when he wants fresh data - so the gap is a dependency graph and a
fail-fast guarantee, not a scheduler.

## Options considered

1. **Dagster** - assets, not tasks: `dagster-dbt` turns every dbt model and test into its own
   asset straight from dbt's manifest, with the lineage dbt already knows about. A local dev UI
   (`dagster dev`) shows the whole graph and runs it with one click, stopping on a failed asset
   (or a failed dbt test) before anything downstream runs. The closest thing in the ODI world is
   a Load Plan: one picture of what depends on what, run in that order, stopping on failure.
2. **Prefect** - a comparable Python orchestrator, but task-based rather than asset-based; no
   integration that turns dbt's own model graph into its graph the way `dagster-dbt` does.
3. **One script or `poe` task chaining the existing commands** (`poe land && poe raw && poe
   build && poe metabase`) - no new dependency, and `&&` already stops on the first failure. But
   it has no graph: dbt's dozens of models and tests stay one opaque `build` step, with no
   picture of lineage and no way to see which asset is stale without rerunning everything.

## Decision

**Dagster**, scoped to an asset graph only - no schedule, no sensor:

- `orchestration/definitions.py` defines assets for `landed_source` and `raw_tables` (thin
  wrappers that call the exact same functions `poe land`/`poe raw` do - no logic duplicated),
  the dbt models and tests in `staging`/`core` (via `dagster-dbt`, generated from dbt's own
  manifest), and `metabase_sync` (wraps `poe metabase`), depending on every `core` asset.
- Run it from Dagster's local UI, `uv run poe dagster`, materializing everything with one click.
  `dagster-dbt` already stops the dbt assets on a failed test, and `metabase_sync` depends on
  every `core` asset, so a failed dbt test blocks it the same way.
- The agent and chat UI are not part of this graph: they are interactive, not a batch step.
- No schedule or sensor: nothing here needs to run unattended yet. Add one if that changes.

## Consequences

- A sizeable new dependency (`dagster`, `dagster-webserver`, `dagster-dbt`) for a project whose
  bar is "runs locally, costs nothing" - justified here because it buys exactly the thing the
  project's whole premise cares about: not letting broken data reach Metabase or the agent.
- `dagster-dbt` needs a generated `manifest.json`; `definitions.py` regenerates it on `dagster
  dev` startup (`DbtProject.prepare_if_dev()`), so it never goes stale by hand.
- The individual `poe` tasks still work standalone for a quick manual step; Dagster is for
  running the whole chain at once with dependency order and fail-fast.
- **Revisit** if a real schedule or external trigger (a freshness SLA, data arriving
  unattended) is ever needed - add a Dagster schedule or sensor then.
