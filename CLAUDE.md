# CLAUDE.md – prompt-to-dashboard

Instructions for Claude Code when working in this repository. Read this first, then
`notes/00 Start.md` and `notes/Stav a další kroky.md` for the current state.

## How to work with Ondra (most important)

- **Communicate in Czech**, informal and direct, no filler phrases.
- **Claude writes the solution code.** Since 2026-11-15 Ondra asks Claude to implement steps
  directly ("pokračuj" / "udělej to ty") instead of guiding him to type it. Earlier raw-load
  notes below still describe the guided mode he started in – read them as history, not as the
  current working style.
- **Explain what changed and why**, with Oracle/ODI analogies where they help (restaurant
  analogy in `notes/Architektura.md`). State assumptions and decisions made on his behalf;
  don't just report success.
- **Background:** experienced Oracle / ODI data warehouse developer (SQL, SCD2, ETL).
  Python, Docker, git and the modern data stack are new to him.
- **Commits and pushes happen only when he asks.** When he does ("commit it", "push"), run
  them yourself – don't just suggest a message.
- Notes in `notes/` are his Obsidian vault. Update them only when he asks (he has, to keep
  this file and the roadmap accurate – see the commit that added this line).

## What the project is

A layered data platform: source files → landing zone → Postgres warehouse
(`raw` → `staging` → `core` → `marts`) → Metabase. An LLM agent answers **any** business
question with a dashboard in Metabase.

The goal is **not** to build specific dashboards or answer predefined questions. The goal
is a well-described warehouse (every table, column, metric and business term documented)
so that the agent can answer questions nobody planned for. Model the whole sales process
at the lowest grain (order line), Kimball style, not per report.

## Current state

All six steps of the plan below are built: landing → raw → staging → core → metadata
(descriptions, metrics, glossary) → Metabase + a conversational agent with a chat UI
(`uv run poe app`), plus an evaluation set comparing answers with and without metadata.
Details and what's still open: `notes/Stav a další kroky.md`.

## Stack and layout

| Concern | Tool |
|---|---|
| Python env and packages | uv, Python 3.13 (`.python-version`) |
| Task runner | poethepoet – tasks in `pyproject.toml` |
| Landing | `ingestion/land_source.py` + `ingestion/sources.yml` |
| Raw load | psycopg + Postgres `COPY` (`ingestion/load_raw.py`) |
| Warehouse | PostgreSQL 17 in Docker (`docker-compose.yml`, `.env`) |
| Transformations | dbt-core 1.x (`dbt/`: staging, core, metrics, glossary) |
| BI | Metabase open source in Docker, read-only role `bi_reader` |
| Agent | Custom agent on the Gemini API (`agent/`); ADR-0004/0005/0006 |
| Orchestration | Dagster asset graph, no schedule (`orchestration/`); ADR-0008 |
| Quality | ruff, pre-commit, GitHub Actions (`.github/workflows/ci.yml`) |

Folders: `ingestion/`, `dbt/`, `orchestration/`, `bi/`, `agent/`, `eval/`, `infra/`,
`tools/`, `docs/` (English documentation, ADRs), `notes/` (Czech personal notes).

## Commands

```bash
uv run poe              # list tasks
uv run poe setup        # first-time setup: .env + git hooks
uv run poe land         # download Contoso into data/landing/
uv run poe up           # start Postgres + Metabase (http://localhost:3000)
uv run poe down         # stop containers, keep data
uv run poe lint         # ruff check + format check
uv run poe check        # all pre-commit checks
docker compose ps       # container status (postgres must be "healthy")
docker compose exec -T postgres psql -U warehouse_admin -d warehouse -c "\dn"
```

Ondra uses Windows with Git Bash and PowerShell. `docker compose exec` needs `-T` in Git Bash.

**`uv run poe <task>` always loads `.env` and overrides any value already in the shell**
(unlike `uv run --env-file .env`, which only fills in what isn't already set). A quick
`export POSTGRES_PORT=...` before a poe task to point it at a throwaway container does
**not** work – poe silently puts the real `.env` value back. This bit twice while testing
raw-load/dbt-build/Metabase changes against an isolated container: `poe raw`/`poe build`
quietly ran against Ondra's real warehouse instead, loading the small sample next to the
real one and skewing `staging`'s "newest load" pick until the stray `_load_id` rows were
deleted. To test a poe task against anything other than the real `.env`, back up `.env`,
write a temporary one, run the task, then restore from the backup and diff to confirm.

## Conventions

- Code, README, `docs/` and commit messages in **English**; `notes/` in **Czech**.
- Commit messages: imperative, at most 50 characters ("Pin Metabase to v0.64.3.1").
- Never commit `data/` or `.env`. Secrets come from `.env` via environment variables.
- Line endings LF (`.gitattributes`). Line length 100 (ruff).
- Record significant decisions as ADRs in `docs/adr/` (template `0000-template.md`).
- Before modeling, read `docs/data-profiling.md`: prices are in USD regardless of
  `CurrencyCode`, `product.Price` is today's list price, delivery time exists only for the
  online store, `sales.csv` is only a reconciliation oracle, stores are SCD2 by `StoreCode`.

## Coding guidelines

From [andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills)
(MIT), derived from Andrej Karpathy's observations on LLM coding pitfalls. They bias
toward caution over speed; for trivial tasks, use judgment. Apply them to the code you
write, and to any review of code Ondra writes himself.

### 1. Think before coding

Don't assume. Don't hide confusion. Surface tradeoffs.

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them – don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity first

Minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical changes

Touch only what you must. Clean up only your own mess.

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it – don't delete it.
- Remove imports, variables and functions that your changes made unused; don't remove
  pre-existing dead code unless asked.

The test: every changed line should trace directly to the request.

### 4. Goal-driven execution

Define success criteria. Loop until verified.

- "Add validation" → "Write tests for invalid inputs, then make them pass".
- "Fix the bug" → "Write a test that reproduces it, then make it pass".
- "Refactor X" → "Ensure tests pass before and after".

For multi-step tasks, state a brief plan:

```text
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```
