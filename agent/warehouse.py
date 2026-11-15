"""Read-only access to the warehouse for the agent, and the context it gives the model."""

import os
from pathlib import Path

import psycopg
import yaml

METADATA_DIR = Path(__file__).resolve().parent.parent / "dbt" / "metadata"
SCHEMA = "core"
STATEMENT_TIMEOUT = "30s"


def connect() -> psycopg.Connection:
    """Connect as the read-only role: the role, not the prompt, is the safety boundary."""
    return psycopg.connect(
        host="localhost",
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["BI_DB_USER"],
        password=os.environ["BI_DB_PASSWORD"],
        autocommit=True,
        options=f"-c statement_timeout={STATEMENT_TIMEOUT} -c default_transaction_read_only=on",
    )


def describe_tables(conn: psycopg.Connection) -> str:
    """Tables and columns with their descriptions, read from the Postgres comments."""
    rows = conn.execute(
        """
        select
            c.relname,
            obj_description(c.oid),
            a.attname,
            format_type(a.atttypid, a.atttypmod),
            col_description(c.oid, a.attnum)
        from pg_class c
        join pg_namespace n on n.oid = c.relnamespace
        join pg_attribute a on a.attrelid = c.oid and a.attnum > 0 and not a.attisdropped
        where n.nspname = %s and c.relkind = 'r'
        order by c.relname, a.attnum
        """,
        (SCHEMA,),
    ).fetchall()
    lines = []
    current_table = None
    for table, table_comment, column, data_type, column_comment in rows:
        if table != current_table:
            current_table = table
            lines.append(f"\nTABLE {SCHEMA}.{table}\n{one_line(table_comment)}\nColumns:")
        lines.append(f"- {column} ({data_type}): {one_line(column_comment)}")
    return "\n".join(lines).strip()


def describe_metrics() -> str:
    metrics = yaml.safe_load((METADATA_DIR / "metrics.yml").read_text(encoding="utf-8"))["metrics"]
    return "\n".join(
        f"- {m['name']} ({m['label']}, unit: {m['unit']}): {m['expression']} "
        f"from {SCHEMA}.{m['table']}. {one_line(m['description'])}"
        for m in metrics
    )


def describe_glossary() -> str:
    terms = yaml.safe_load((METADATA_DIR / "glossary.yml").read_text(encoding="utf-8"))["terms"]
    return "\n".join(
        f"- {t['term']} (also: {', '.join(t['synonyms'])}): {one_line(t['definition'])}"
        for t in terms
    )


def build_context(conn: psycopg.Connection) -> str:
    return (
        f"# Tables\n\n{describe_tables(conn)}\n\n"
        f"# Metrics\n\n{describe_metrics()}\n\n"
        f"# Glossary\n\n{describe_glossary()}"
    )


def one_line(text: str | None) -> str:
    return " ".join((text or "").split())
