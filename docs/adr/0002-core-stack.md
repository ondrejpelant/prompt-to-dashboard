# ADR-0002: Use PostgreSQL, dbt and Metabase as the core stack

- **Status:** Accepted
- **Date:** 2026-10-14

## Context

Constraints: everything must run locally, cost nothing and be reproducible from the repository.
The end goal is a chat window where a request becomes a dashboard in a **self-service BI tool**,
so the user can keep working with it – the dashboard must be a native, editable object, not a
static picture. The LLM must work only on documented marts, and metadata must be written once.

## Options considered

**Warehouse**

1. **DuckDB** – excellent single-file OLAP engine. Only one process can write at a time, and
   Metabase supports it only through a community driver; a server-based BI tool and the pipeline
   would fight over the file lock.
2. **PostgreSQL** – officially supported by every BI tool considered, handles concurrent access,
   and has roles for least-privilege access by the BI tool and the agent.

**BI tool**

1. **Metabase (open source)** – AI features are available in the free edition with your own model
   provider; official MCP server and REST API; metrics, glossary and column metadata the agent can
   use.
2. **Lightdash** – dbt-native and dashboards-as-code, but AI agents are only in the paid cloud.
3. **Apache Superset** – only community MCP servers and heavier to operate.
4. **Custom renderer (Streamlit + Vega-Lite)** – full control, but no self-service exploration
   afterwards, which is the point of the project.

**Transformations and semantic layer**

1. **dbt-core 1.x** – SQL models, tests, snapshots (SCD2), contracts and YAML documentation in one
   place. Pinned below 2.0 until the v2 runtime and the Postgres adapter are stable.
2. **SQLMesh** – strong alternative, smaller ecosystem.
3. **MetricFlow** as a separate semantic layer – dropped: Metabase already holds metrics and
   descriptions, and a second semantic layer would mean defining metrics twice.

## Decision

- **PostgreSQL 17** as the warehouse (schemas `raw`, `staging`, `core`, `marts`).
- **dbt-core 1.x** with `dbt-postgres` for transformations, tests and documentation.
- **Metabase open source** as the BI tool, with its application database in the same Postgres
  instance (separate database and login role).
- **dlt** for the raw load and **Dagster** for orchestration, confirmed when those phases start.
- How the LLM talks to Metabase (custom agent through the MCP server vs. the built-in Metabot) is
  **not decided here** – it will get its own ADR in phase 7.

## Consequences

- dbt YAML is the single source of truth for descriptions; a sync step must push them to Metabase,
  otherwise the two drift apart. Editing metadata in the Metabase UI is out of bounds.
- Dashboards are stored in Metabase's application database, not in git. An export step is needed to
  version them.
- Postgres is a row store; at this data volume (hundreds of thousands of rows) that is irrelevant.
- DuckDB stays useful for ad-hoc profiling of landed files.
- **Revisit** the warehouse choice if the data volume grows by orders of magnitude.
