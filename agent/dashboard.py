"""Create a Metabase dashboard from a plan: one native SQL question per card."""

import os

from agent.planner import Card, Plan
from bi.sync_metabase import DATABASE_NAME, api

COLLECTION_NAME = "Agent dashboards"
GRID_WIDTH = 24


def warehouse_database_id() -> int:
    for database in api("GET", "/database")["data"]:
        if database["name"] == DATABASE_NAME:
            return database["id"]
    raise SystemExit(f"Metabase has no database '{DATABASE_NAME}'; run 'uv run poe metabase'")


def ensure_collection() -> int:
    for collection in api("GET", "/collection"):
        if collection["name"] == COLLECTION_NAME and not collection.get("archived"):
            return collection["id"]
    return api("POST", "/collection", {"name": COLLECTION_NAME})["id"]


def visualization_settings(card: Card) -> dict:
    if card.chart in ("line", "bar"):
        return {"graph.dimensions": [card.x], "graph.metrics": card.y}
    if card.chart == "pie":
        return {"pie.dimension": card.x, "pie.metric": card.y[0]}
    return {}


def layout(cards: list[Card]) -> list[dict]:
    """Numbers in a row of four on top, charts and tables two per row below them."""
    positions = []
    row = col = row_height = 0
    for card in sorted(cards, key=lambda c: c.chart != "scalar"):
        width, height = (6, 3) if card.chart == "scalar" else (12, 7)
        if col + width > GRID_WIDTH or (col > 0 and height != row_height):
            row, col = row + row_height, 0
        positions.append({"card": card, "row": row, "col": col, "size_x": width, "size_y": height})
        col, row_height = col + width, height
    return positions


def create_dashboard(plan: Plan, question: str) -> str:
    database_id = warehouse_database_id()
    collection_id = ensure_collection()
    dashboard = api(
        "POST",
        "/dashboard",
        {
            "name": plan.title,
            "description": f"{plan.description}\n\nQuestion: {question}",
            "collection_id": collection_id,
        },
    )
    dashcards = []
    for index, position in enumerate(layout(plan.cards), start=1):
        card = position.pop("card")
        question_card = api(
            "POST",
            "/card",
            {
                "name": card.title,
                "description": card.description,
                "collection_id": collection_id,
                "display": card.chart,
                "visualization_settings": visualization_settings(card),
                "dataset_query": {
                    "type": "native",
                    "database": database_id,
                    "native": {"query": card.sql.strip().rstrip(";")},
                },
            },
        )
        dashcards.append({"id": -index, "card_id": question_card["id"], **position})
    api("PUT", f"/dashboard/{dashboard['id']}", {"dashcards": dashcards})
    return f"http://localhost:{os.environ['METABASE_PORT']}/dashboard/{dashboard['id']}"
