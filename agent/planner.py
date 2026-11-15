"""Turn a question into a dashboard plan: cards with SQL that is proven to run."""

import os
from typing import Literal

import psycopg
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

DEFAULT_MODEL = "gemini-2.5-flash"
MAX_ATTEMPTS = 3

SYSTEM_INSTRUCTION = """\
You are a data analyst. You answer a business question with a dashboard built from SQL
queries on a PostgreSQL data warehouse.

Rules:
- Use only the tables and columns listed in the context, always with the schema prefix
  (core.fct_order_lines). Never invent a table or a column.
- When a metric from the context fits, use its expression exactly as written. When a
  term from the glossary fits, follow its definition.
- Join the fact to a dimension on the key they share (customer_key, store_key,
  product_key; order_date = dim_date.date_day).
- Each card is one SELECT statement without a trailing semicolon. Give every output
  column a short, readable lowercase alias.
- Round money to whole units and ratios to 4 decimals. Order the result the way it
  should be read (time ascending, rankings descending) and limit rankings to what was
  asked for, or to 10.
- Choose the chart: "scalar" for one number, "line" for a development over time, "bar"
  for a comparison across categories, "pie" for shares of a whole with few categories,
  "table" for anything else. For line, bar and pie set x to the alias of the category
  or time column and y to the aliases of the numeric columns.
- Build 1 to 6 cards. Start with the card that answers the question most directly; add
  more only if they help to understand the answer.
- Write titles and descriptions in the language of the question. Say in the dashboard
  description which definitions you used (for example net revenue in USD).
- If the question cannot be answered from the context, return no cards and explain why
  in the dashboard description.
"""


class Card(BaseModel):
    title: str
    description: str = Field(description="One sentence: what the card shows and how it is defined.")
    sql: str
    chart: Literal["scalar", "line", "bar", "pie", "table"]
    x: str | None = Field(default=None, description="Alias of the category or time column.")
    y: list[str] = Field(default_factory=list, description="Aliases of the numeric columns.")


class Plan(BaseModel):
    title: str
    description: str
    cards: list[Card]


def check_card(conn: psycopg.Connection, card: Card) -> str | None:
    """Run the card's SQL as the read-only role; return what is wrong with it, if anything."""
    sql = card.sql.strip().rstrip(";")
    if ";" in sql:
        return "The SQL must be a single statement."
    try:
        cursor = conn.execute(f"select * from (\n{sql}\n) as card limit 1")
    except psycopg.Error as error:
        return f"The SQL failed: {error}".strip()
    columns = [column.name for column in cursor.description]
    if cursor.fetchone() is None:
        return "The SQL returned no rows."
    if card.chart in ("line", "bar", "pie"):
        unknown = [name for name in [card.x, *card.y] if name not in columns]
        if card.x is None or not card.y or unknown:
            return f"x and y must be output columns of the SQL ({', '.join(columns)})."
    return None


def make_plan(question: str, context: str, conn: psycopg.Connection) -> Plan:
    # System instructions and JSON schemas need the v1beta API; the SDK defaults to v1
    client = genai.Client(
        api_key=os.environ["GEMINI_API_KEY"],
        http_options=types.HttpOptions(api_version="v1beta"),
    )
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=Plan,
        temperature=0,
    )
    prompt = f"{context}\n\n# Question\n\n{question}"
    for attempt in range(1, MAX_ATTEMPTS + 1):
        response = client.models.generate_content(
            model=os.environ.get("GEMINI_MODEL", DEFAULT_MODEL), contents=prompt, config=config
        )
        plan = Plan.model_validate_json(response.text)
        problems = [
            f"Card '{card.title}': {problem}\nSQL: {card.sql}"
            for card in plan.cards
            if (problem := check_card(conn, card))
        ]
        if not problems:
            return plan
        print(f"attempt {attempt}: {len(problems)} card(s) need fixing")
        prompt = (
            f"{context}\n\n# Question\n\n{question}\n\n"
            f"# Your previous answer\n\n{plan.model_dump_json()}\n\n"
            "# Problems to fix\n\n" + "\n\n".join(problems) + "\n\nReturn the corrected plan."
        )
    raise SystemExit("The model did not produce working SQL:\n\n" + "\n\n".join(problems))
