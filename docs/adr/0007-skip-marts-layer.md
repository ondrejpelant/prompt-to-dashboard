# ADR-0007: Skip the `marts` layer; Metabase and the agent read `core` directly

- **Status:** Accepted
- **Date:** 2026-11-17

## Context

ADR-0002 named four schemas: `raw`, `staging`, `core`, `marts` - the last one meant to hold
"business-facing tables with contracts and full column documentation" in front of the star
schema. Steps 1-6 of the project plan built `raw`, `staging` and `core`; the metadata step
(descriptions, metrics, glossary) and the Metabase/agent connection attached directly to `core`
instead, and `marts` was never built. This ADR records that as the accepted state rather than
an oversight the project still owes itself.

`core` already has what a `marts` layer was meant to add: primary and foreign keys enforced by
Postgres, a description on every table and column, and dbt tests (keys, relationships,
reconciliation against the source's own `sales.csv`). What it does not have is a contract: dbt
would not refuse to build a change that breaks `core`'s shape.

## Options considered

1. **Build `marts` now, as planned** - a thin layer in front of `core` (one view per table, or a
   copy) carrying dbt contracts, so `core` could change underneath without breaking Metabase
   questions or the agent's queries. Cost: another schema, another thing the Metabase sync and
   the agent's read-only role have to reach, another set of models to keep in step with `core` -
   for one source and one person, with no second consumer `core`'s shape has ever broken.
2. **Keep `core` as the only layer exposed to BI and the agent** (what is actually built). The
   gap: a breaking change to `core` (a renamed or dropped column, a changed grain) would not fail
   the build - it would just reach Metabase and the agent, who would find out by breaking.
3. **Add dbt contracts to `core` directly**, without a separate schema - gets the main safety net
   (the build fails loudly on a breaking change) without a second layer to maintain.

## Decision

Keep `core` as the single layer Metabase and the agent read. Do not build `marts`. Revisit
option 3 (contracts on `core`) when `core` actually needs to change in a way that could break
dashboards or the agent's understanding of the schema - add the contract scoped to that change,
rather than speculatively now.

This revises the schema list in ADR-0002's Decision (`raw`, `staging`, `core`, `marts`) to drop
`marts`; the rest of that ADR (PostgreSQL, dbt-core, Metabase) is unchanged.

## Consequences

- One fewer schema, one fewer thing for the dbt build and the Metabase sync to maintain.
- No contract enforcement yet: a breaking dbt change to `core` is not caught at build time. Today
  the dbt tests on `core` and the read-only `bi_reader` role are what stands in for that.
- `README.md` and `dbt/README.md` already described `core` as the layer read directly; this ADR
  is what makes that an explicit decision instead of just the current state.
- **Revisit** when a change to `core` could break Metabase questions or the agent's queries: add
  dbt contracts to `core`, or build a thin `marts`/contract layer then.
