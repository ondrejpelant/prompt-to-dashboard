"""Show a plan in Metabase: the answer as text on top, one native SQL question per card."""

import os
from dataclasses import dataclass, field

from agent.planner import Card, Plan
from bi.sync_metabase import DATABASE_NAME, api

COLLECTION_NAME = "Agent dashboards"
GRID_WIDTH = 24


@dataclass
class Dashboard:
    """The dashboard of one conversation; follow-ups rewrite it instead of adding new ones."""

    id: int
    card_ids: list[int] = field(default_factory=list)

    @property
    def url(self) -> str:
        return f"http://localhost:{os.environ['METABASE_PORT']}/dashboard/{self.id}"


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
        dimensions = [card.x, card.series] if card.series else [card.x]
        return {"graph.dimensions": dimensions, "graph.metrics": card.y}
    if card.chart == "pie":
        return {"pie.dimension": card.x, "pie.metric": card.y[0]}
    return {}


def text_dashcard(text: str) -> dict:
    """A text box across the whole width; Metabase stores it as a card-less dashcard."""
    height = max(3, len(text) // 150 + 2)
    return {
        "card_id": None,
        "row": 0,
        "col": 0,
        "size_x": GRID_WIDTH,
        "size_y": height,
        "visualization_settings": {
            "text": text,
            "virtual_card": {
                "name": None,
                "display": "text",
                "visualization_settings": {},
                "dataset_query": {},
                "archived": False,
            },
        },
    }


def layout(cards: list[Card], first_row: int) -> list[dict]:
    """Numbers in a row of four on top, charts and tables two per row below them."""
    positions = []
    row, col, row_height = first_row, 0, 0
    for card in sorted(cards, key=lambda c: c.chart != "scalar"):
        width, height = (6, 3) if card.chart == "scalar" else (12, 7)
        if col + width > GRID_WIDTH or (col > 0 and height != row_height):
            row, col = row + row_height, 0
        positions.append({"card": card, "row": row, "col": col, "size_x": width, "size_y": height})
        col, row_height = col + width, height
    return positions


def save_dashboard(
    plan: Plan, answer: str, question: str, dashboard: Dashboard | None = None
) -> Dashboard:
    """Create the conversation's dashboard, or replace its content on a follow-up."""
    database_id = warehouse_database_id()
    collection_id = ensure_collection()
    details = {"name": plan.title, "description": f"{plan.description}\n\nRequest: {question}"}
    if dashboard is None:
        created = api("POST", "/dashboard", {**details, "collection_id": collection_id})
        dashboard = Dashboard(id=created["id"])
    old_card_ids = dashboard.card_ids

    answer_box = text_dashcard(answer)
    dashcards = [{"id": -1, **answer_box}]
    dashboard.card_ids = []
    for index, position in enumerate(layout(plan.cards, first_row=answer_box["size_y"]), start=2):
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
        dashboard.card_ids.append(question_card["id"])
        dashcards.append({"id": -index, "card_id": question_card["id"], **position})

    # Sending the full list replaces what was on the dashboard before
    api("PUT", f"/dashboard/{dashboard.id}", {**details, "dashcards": dashcards})
    for card_id in old_card_ids:
        api("PUT", f"/card/{card_id}", {"archived": True})
    return dashboard
