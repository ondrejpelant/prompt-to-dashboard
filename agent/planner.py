"""The two model calls of the agent.

make_plan: a request (and the conversation so far) becomes a dashboard plan whose
SQL is proven to run - or a clarifying question, or a refusal when the data cannot
answer it.
conclude: the results of the plan's queries become the answer in words.
"""

import os
from typing import Literal

import psycopg
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

DEFAULT_MODEL = "gemini-2.5-flash"
MAX_ATTEMPTS = 3
MAX_RESULT_ROWS = 40

PLAN_INSTRUCTION = """\
You are a data analyst in a conversation with a business user. You answer with a
dashboard built from SQL queries on a PostgreSQL data warehouse. The user never builds
reports; they describe a problem in plain language and you show the evidence.

Choose the action:
- "answer": build the dashboard. This is the default. To verify a claim ("is it true
  that ..."), build cards that show the evidence over the relevant period.
- "clarify": ask one short question in "message", with no cards. Only when you cannot
  choose a sensible metric or period without the user. When a reasonable default
  exists, use it and state it in the dashboard description instead of asking.
- "decline": when the warehouse does not contain what is needed (for example cash
  flow, budgets, stock levels, profit after all costs). Never approximate a concept
  the data does not hold. In "message" say what is missing and offer the closest
  thing the data can answer. No cards.

In a follow-up, return the complete new state of the current dashboard: keep the
cards that are still relevant and change or add what the user asks for.

Rules for the SQL and the cards:
- Use only the tables and columns listed in the context, always with the schema prefix
  (core.fct_order_lines). Never invent a table or a column.
- When a metric from the context fits, use its expression exactly as written. When a
  term from the glossary fits, follow its definition.
- Join the fact to a dimension on the key they share (customer_key, store_key,
  product_key; order_date = dim_date.date_day).
- Each card is one SELECT statement without a trailing semicolon. Give every output
  column a short, readable lowercase alias.
- When the glossary says a term is ambiguous, show every meaning as its own card.
- Round money totals to whole units, averages and other non-money values to 2
  decimals, and ratios to 4 decimals. Order the result the way it should be read
  (time ascending, rankings descending) and limit rankings to what was asked for, or
  to 10.
- Choose the chart: "scalar" for one number, "line" for a development over time, "bar"
  for a comparison across categories, "pie" for shares of a whole with few categories,
  "table" for anything else. For line, bar and pie set x to the alias of the category
  or time column and y to the aliases of the numeric columns. When a line or bar chart
  is split by a second category (one row per time and category), set series to the
  alias of that category column.
- Build 1 to 6 cards. Start with the card that answers the request most directly; add
  more only if they help to understand the answer.
- Write the title, descriptions and message in the language of the user. Say in the
  dashboard description which definitions you used (for example net revenue in USD).
"""

CONCLUSION_INSTRUCTION = """\
You are a data analyst. You get a business user's request and the results of the
queries on the dashboard that was built for it. Write the answer.

- Start with the direct answer. When the user asked to verify a claim, the very first
  word must be exactly "Yes", "No" or "Partly", matching how true the claim is as a
  whole. Never lead with "No" just because one part of the claim is false while another
  part holds - lead with "Partly" instead, then explain which part is which. Before
  answering, check that your verdict word and your own explanation agree (if the claim
  says a thing is faster/higher/more and your numbers show the opposite, the verdict is
  "No", not "Yes").
- Support it with the specific numbers from the results, with their units and periods.
- Mention the definition used when it matters (for example net revenue in USD), and
  any limit of the data the reader must know to not misread the answer.
- Use only numbers that appear in the results. Do not compute anything the results do
  not show, except simple differences and percentage changes between shown values.
- Speak the language of the business: never mention table, column or metric
  identifiers such as net_amount_usd.
- 3 to 6 sentences of plain text in the language of the user. No SQL, no headings, no
  bullet points.
"""


class Card(BaseModel):
    title: str
    description: str = Field(description="One sentence: what the card shows and how it is defined.")
    sql: str
    chart: Literal["scalar", "line", "bar", "pie", "table"]
    x: str | None = Field(default=None, description="Alias of the category or time column.")
    y: list[str] = Field(default_factory=list, description="Aliases of the numeric columns.")
    series: str | None = Field(
        default=None, description="Alias of the column that splits a line or bar chart."
    )


class Plan(BaseModel):
    action: Literal["answer", "clarify", "decline"]
    message: str = Field(
        default="", description="The clarifying question or the reason for declining."
    )
    title: str = Field(default="", description="Dashboard title.")
    description: str = Field(default="", description="What the dashboard shows and how.")
    cards: list[Card] = Field(default_factory=list)


def generate(instruction: str, prompt: str, schema: type[BaseModel] | None = None) -> str:
    # System instructions and JSON schemas need the v1beta API; the SDK defaults to v1
    client = genai.Client(
        api_key=os.environ["PROMPT_TO_DASHBOARD_GEMINI_API_KEY"],
        http_options=types.HttpOptions(api_version="v1beta"),
    )
    config = types.GenerateContentConfig(system_instruction=instruction, temperature=0)
    if schema is not None:
        config.response_mime_type = "application/json"
        config.response_schema = schema
    response = client.models.generate_content(
        model=os.environ.get("GEMINI_MODEL", DEFAULT_MODEL), contents=prompt, config=config
    )
    return response.text


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
        used = [card.x, *card.y] + ([card.series] if card.series else [])
        if card.x is None or not card.y or any(name not in columns for name in used):
            return f"x, y and series must be output columns of the SQL ({', '.join(columns)})."
    return None


def make_plan(question: str, context: str, conn: psycopg.Connection, history: str = "") -> Plan:
    request = f"{context}\n\n"
    if history:
        request += f"# Conversation so far\n\n{history}\n\n"
    request += f"# Request\n\n{question}"
    prompt = request
    for attempt in range(1, MAX_ATTEMPTS + 1):
        plan = Plan.model_validate_json(generate(PLAN_INSTRUCTION, prompt, Plan))
        if plan.action != "answer":
            plan.cards = []
            return plan
        problems = [
            f"Card '{card.title}': {problem}\nSQL: {card.sql}"
            for card in plan.cards
            if (problem := check_card(conn, card))
        ]
        if not plan.cards:
            problems = ["The action is 'answer' but there are no cards."]
        if not problems:
            return plan
        print(f"attempt {attempt}: {len(problems)} problem(s) to fix")
        prompt = (
            f"{request}\n\n# Your previous answer\n\n{plan.model_dump_json()}\n\n"
            "# Problems to fix\n\n" + "\n\n".join(problems) + "\n\nReturn the corrected plan."
        )
    raise SystemExit("The model did not produce working SQL:\n\n" + "\n\n".join(problems))


def read_results(conn: psycopg.Connection, plan: Plan) -> str:
    """The first rows of every card's result, as text for the model."""
    blocks = []
    for card in plan.cards:
        sql = card.sql.strip().rstrip(";")
        cursor = conn.execute(f"select * from (\n{sql}\n) as card limit {MAX_RESULT_ROWS + 1}")
        rows = cursor.fetchall()
        lines = [" | ".join(column.name for column in cursor.description)]
        lines += [" | ".join(str(value) for value in row) for row in rows[:MAX_RESULT_ROWS]]
        if len(rows) > MAX_RESULT_ROWS:
            lines.append(f"... (only the first {MAX_RESULT_ROWS} rows are shown)")
        blocks.append(f"## {card.title}\n{card.description}\n" + "\n".join(lines))
    return "\n\n".join(blocks)


def conclude(question: str, plan: Plan, results: str, history: str = "") -> str:
    prompt = ""
    if history:
        prompt += f"# Conversation so far\n\n{history}\n\n"
    prompt += (
        f"# Request\n\n{question}\n\n"
        f"# Dashboard\n\n{plan.title}\n{plan.description}\n\n"
        f"# Results\n\n{results}"
    )
    return generate(CONCLUSION_INSTRUCTION, prompt).strip()
