# Transformations (dbt)

Planned for phases 3–5. The dbt project will live here and build the warehouse layers in Postgres:

| Layer | Schema | Purpose |
|---|---|---|
| Staging | `staging` | 1:1 with raw tables: types, naming, deduplication, basic tests |
| Core | `core` | Kimball star schema: conformed dimensions, facts with declared grain, SCD2 |
| Marts | `marts` | Business-facing tables with contracts and full column documentation |

All model and column descriptions are written here, in YAML, and are the single source of truth
for metadata. They are synced to Metabase so the LLM and the BI tool see the same definitions.
