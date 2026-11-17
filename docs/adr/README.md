# Architecture decision records

Each significant decision gets a short record: context, options, decision, consequences.
Copy [`0000-template.md`](0000-template.md) for a new one; never rewrite an accepted record –
supersede it with a new one.

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-dataset-contoso-v2.md) | Use the Contoso V2 dataset as the first source | Accepted |
| [0002](0002-core-stack.md) | Use PostgreSQL, dbt and Metabase as the core stack | Accepted |
| [0003](0003-raw-load-psycopg-copy.md) | Use psycopg and COPY for the raw load | Accepted |
| [0004](0004-custom-agent-with-gemini.md) | Build a custom agent that writes SQL and creates Metabase dashboards | Accepted |
| [0005](0005-conversational-agent.md) | Make the agent a conversation that answers in words and one dashboard | Accepted |
| [0006](0006-embedded-dashboard-streamlit-ui.md) | Embed the dashboard via a Metabase public link, built with Streamlit | Accepted |
| [0007](0007-skip-marts-layer.md) | Skip the `marts` layer; Metabase and the agent read `core` directly | Accepted |
| [0008](0008-orchestration-with-dagster.md) | Use Dagster for orchestration, as an asset graph with no schedule | Accepted |
