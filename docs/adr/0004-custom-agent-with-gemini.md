# ADR-0004: Build a custom agent that writes SQL and creates Metabase dashboards

- **Status:** Accepted
- **Date:** 2026-11-15

## Context

ADR-0002 left open how the LLM turns a question into a dashboard. The warehouse now has a
documented star schema in `core`, metric definitions and a business glossary in
`dbt/metadata/`, and Metabase connected through the read-only role `bi_reader`. The project's
claim is that metadata quality decides how trustworthy the answers are, so we must control – and
later measure – exactly which metadata the model sees. Everything must run locally at no cost.

## Options considered

**Integration**

1. **Custom agent** – a small Python program: question → context from the warehouse metadata →
   SQL → Metabase cards and a dashboard through the REST API. Full control over the prompt, easy
   to evaluate with and without metadata, independent of Metabase's AI features. More code to
   own.
2. **Built-in Metabot** – least code, but little control over the context it uses, metrics would
   have to be re-entered in Metabase's own query format, and it cannot be evaluated in isolation.
3. **Custom agent through the Metabase MCP server** – flexible, but adds a tool-calling loop and
   another moving part before the simple pipeline has been measured.

**Model**

1. **Gemini API, free tier** – no cost, good SQL quality, structured JSON output. Rate limits per
   minute and day; questions are sent to Google.
2. **Claude API** – strongest SQL and tool use, but paid.
3. **Local model through Ollama** – private and free, but noticeably weaker SQL and slow on a
   laptop.

## Decision

- A **custom agent** in `agent/`, started with `uv run poe ask "<question>"`.
- The model gets one context: table and column descriptions read from the Postgres comments (the
  deployed state), plus `metrics.yml` and `glossary.yml`.
- The model returns a **structured plan** (dashboard title, cards with SQL and chart type), not
  free text. Every SQL statement is run against the warehouse as `bi_reader` before anything is
  created; errors go back to the model for a limited number of retries.
- Cards are created in Metabase as **native SQL questions** on a dashboard in the collection
  "Agent dashboards", so the user can open, edit and extend them.
- **Gemini (free tier)** through the `google-genai` SDK; the model name is configurable
  (`GEMINI_MODEL`).

## Consequences

- The agent can only read `core`: the database role, not the prompt, is the safety boundary.
- Metric definitions stay in `dbt/metadata/metrics.yml` as SQL; they are not duplicated in
  Metabase.
- Native SQL cards cannot be edited in Metabase's visual query builder, only as SQL.
- Questions and metadata (not data rows, apart from small samples in error messages) leave the
  machine; the free tier has rate limits that the evaluation must respect.
- The model call is isolated in one module, so another provider can replace Gemini.
- **Revisit** after the evaluation: if accuracy is not good enough, compare models; if users
  need visual editing, generate Metabase's structured queries instead of SQL.
