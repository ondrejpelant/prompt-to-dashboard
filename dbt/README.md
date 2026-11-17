# Transformations (dbt)

Builds the warehouse layers in Postgres from the raw schema:

| Layer | Schema | Purpose |
|---|---|---|
| Staging | `staging` | 1:1 views on raw tables: types, naming, newest load only, basic tests |
| Core | `core` | Kimball star schema: conformed dimensions, a fact with declared grain, SCD2 store history |

Model and column descriptions live in the model YAML files (`models/*/_*.yml`) and are written
into Postgres as comments on every build (`persist_docs` in `dbt_project.yml`), so Metabase and
any SQL client see the same definitions. `metadata/metrics.yml` and `metadata/glossary.yml` sit
next to the models: metric expressions and business terms, as plain YAML rather than dbt's own
metrics layer (see [ADR-0002](../docs/adr/0002-core-stack.md)).

There is no separate `marts` schema: Metabase and the agent read `core` directly through the
read-only role `bi_reader`. ADR-0002 named `marts` for contracts and full documentation on a
business-facing layer; not built yet – revisit if `core` needs changes that would otherwise
break dashboards.
