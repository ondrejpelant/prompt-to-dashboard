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
