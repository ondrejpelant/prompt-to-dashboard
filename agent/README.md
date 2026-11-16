# LLM agent

A chat interface where a natural-language request becomes a dashboard in Metabase, shown
alongside the conversation. The agent works only on documented marts in `core`, through the
read-only role `bi_reader` (see `bi/`). Integration approach, model and chat UI are recorded in
[ADR-0004](../docs/adr/0004-custom-agent-with-gemini.md),
[ADR-0005](../docs/adr/0005-conversational-agent.md) and
[ADR-0006](../docs/adr/0006-embedded-dashboard-streamlit-ui.md).

| Module | Role |
|---|---|
| `warehouse.py` | Read-only connection and the context built from table/column descriptions, metrics and the glossary |
| `planner.py` | The two model calls: a dashboard plan (SQL cards, proven to run), and the conclusion written from their results |
| `dashboard.py` | Creates or updates the conversation's dashboard in Metabase; a public link for the embedded iframe |
| `conversation.py` | One conversation: history, the current plan and dashboard |
| `ask.py` / `chat.py` | One-shot and terminal entry points (`uv run poe ask` / `uv run poe chat`) |
| `app.py` | The chat UI: `uv run poe app` opens it at <http://localhost:8501> |
