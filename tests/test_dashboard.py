"""Unit tests for agent/dashboard.py: pure layout/formatting logic, plus the calls it
makes to Metabase's API - checked against a fake api() instead of a live Metabase."""

import jwt
import pytest

import agent.dashboard as dashboard
from agent.planner import Card, Plan


def make_card(**overrides) -> Card:
    defaults = {
        "title": "Net revenue",
        "description": "Net revenue in USD.",
        "sql": "select 1",
        "chart": "scalar",
    }
    return Card(**{**defaults, **overrides})


class TestVisualizationSettings:
    def test_bar_chart_uses_x_and_y(self):
        card = make_card(chart="bar", x="year", y=["net_revenue_usd"])
        assert dashboard.visualization_settings(card) == {
            "graph.dimensions": ["year"],
            "graph.metrics": ["net_revenue_usd"],
        }

    def test_bar_chart_with_series_adds_second_dimension(self):
        card = make_card(chart="bar", x="year", y=["net_revenue_usd"], series="channel")
        settings = dashboard.visualization_settings(card)
        assert settings["graph.dimensions"] == ["year", "channel"]

    def test_pie_chart_uses_dimension_and_one_metric(self):
        card = make_card(chart="pie", x="channel", y=["orders"])
        assert dashboard.visualization_settings(card) == {
            "pie.dimension": "channel",
            "pie.metric": "orders",
        }

    def test_scalar_and_table_have_no_special_settings(self):
        assert dashboard.visualization_settings(make_card(chart="scalar")) == {}
        assert dashboard.visualization_settings(make_card(chart="table")) == {}


class TestTextDashcard:
    def test_has_no_card_id_and_spans_the_full_width(self):
        box = dashboard.text_dashcard("short answer")
        assert box["card_id"] is None
        assert box["size_x"] == dashboard.GRID_WIDTH
        assert box["visualization_settings"]["text"] == "short answer"

    def test_height_grows_with_the_text(self):
        short = dashboard.text_dashcard("x" * 10)
        long = dashboard.text_dashcard("x" * 1000)
        assert long["size_y"] > short["size_y"]


class TestLayout:
    def test_scalars_come_before_charts_regardless_of_input_order(self):
        cards = [make_card(chart="bar"), make_card(chart="scalar")]
        positions = dashboard.layout(cards, first_row=0)
        assert [p["card"].chart for p in positions] == ["scalar", "bar"]

    def test_four_scalars_fit_one_row_then_wrap(self):
        cards = [make_card(chart="scalar") for _ in range(5)]
        positions = dashboard.layout(cards, first_row=0)
        rows = {p["row"] for p in positions[:4]}
        assert rows == {0}
        assert positions[4]["row"] > 0

    def test_starts_at_the_given_first_row(self):
        positions = dashboard.layout([make_card(chart="scalar")], first_row=5)
        assert positions[0]["row"] == 5

    def test_non_scalar_cards_are_two_per_row(self):
        cards = [make_card(chart="table") for _ in range(2)]
        positions = dashboard.layout(cards, first_row=0)
        assert positions[0]["row"] == positions[1]["row"]
        assert positions[0]["col"] != positions[1]["col"]


class FakeApi:
    """Records every call made through dashboard.api and answers canned responses."""

    def __init__(self, responses: dict):
        self.calls: list[tuple[str, str, dict | None]] = []
        self.responses = responses

    def __call__(self, method: str, path: str, body: dict | None = None):
        self.calls.append((method, path, body))
        key = (method, path.split("?")[0])
        if key in self.responses:
            return self.responses[key]
        if path.startswith("/card") and method == "POST":
            return {"id": 100 + len(self.calls)}
        return None


@pytest.fixture(autouse=True)
def _reset_embedding_secret_cache():
    dashboard._embedding_secret = None
    yield
    dashboard._embedding_secret = None


def test_ensure_embedding_secret_generates_one_if_unset(monkeypatch):
    fake = FakeApi({("GET", "/setting/embedding-secret-key"): None})
    monkeypatch.setattr(dashboard, "api", fake)

    secret = dashboard.ensure_embedding_secret()

    assert secret
    put_calls = [c for c in fake.calls if c[0] == "PUT"]
    assert ("PUT", "/setting/embedding-secret-key", {"value": secret}) in put_calls
    assert ("PUT", "/setting/enable-embedding-static", {"value": True}) in put_calls


def test_ensure_embedding_secret_reuses_an_existing_one(monkeypatch):
    fake = FakeApi({("GET", "/setting/embedding-secret-key"): "already-set"})
    monkeypatch.setattr(dashboard, "api", fake)

    secret = dashboard.ensure_embedding_secret()

    assert secret == "already-set"
    assert not any(c[0] == "PUT" and "embedding-secret-key" in c[1] for c in fake.calls)


def test_ensure_embedding_secret_is_cached_after_the_first_call(monkeypatch):
    fake = FakeApi({("GET", "/setting/embedding-secret-key"): "already-set"})
    monkeypatch.setattr(dashboard, "api", fake)

    dashboard.ensure_embedding_secret()
    dashboard.ensure_embedding_secret()

    assert len([c for c in fake.calls if "embedding-secret-key" in c[1]]) == 1


def test_embed_url_is_a_token_signed_for_this_dashboard(monkeypatch):
    secret = "test-secret-well-over-32-bytes-long"
    monkeypatch.setattr(dashboard, "ensure_embedding_secret", lambda: secret)
    monkeypatch.setenv("METABASE_PORT", "3000")
    d = dashboard.Dashboard(id=42)

    url = d.embed_url()

    assert url.startswith("http://localhost:3000/embed/dashboard/")
    token = url.rsplit("/", 1)[1]
    payload = jwt.decode(token, secret, algorithms=["HS256"])
    assert payload["resource"] == {"dashboard": 42}
    assert payload["exp"] > 0


def test_save_dashboard_creates_a_text_box_and_one_card_per_plan_card(monkeypatch):
    fake = FakeApi(
        {
            ("GET", "/database"): {"data": [{"name": dashboard.DATABASE_NAME, "id": 7}]},
            ("GET", "/collection"): [{"name": dashboard.COLLECTION_NAME, "id": 9}],
            ("POST", "/dashboard"): {"id": 55},
        }
    )
    monkeypatch.setattr(dashboard, "api", fake)
    monkeypatch.setattr(dashboard, "ensure_embedding_secret", lambda: "test-secret")
    plan = Plan(
        action="answer",
        title="Revenue",
        description="...",
        cards=[make_card(), make_card(title="Orders")],
    )

    result = dashboard.save_dashboard(plan, "the answer", "how is revenue?")

    assert result.id == 55
    assert len(result.card_ids) == 2
    create_payload = next(body for m, p, body in fake.calls if (m, p) == ("POST", "/dashboard"))
    assert create_payload["enable_embedding"] is True
    put_payload = next(body for m, p, body in fake.calls if p == "/dashboard/55")
    assert len(put_payload["dashcards"]) == 3  # text box + 2 cards


def test_save_dashboard_archives_old_cards_on_a_follow_up(monkeypatch):
    fake = FakeApi(
        {
            ("GET", "/database"): {"data": [{"name": dashboard.DATABASE_NAME, "id": 7}]},
            ("GET", "/collection"): [{"name": dashboard.COLLECTION_NAME, "id": 9}],
        }
    )
    monkeypatch.setattr(dashboard, "api", fake)
    existing = dashboard.Dashboard(id=55, card_ids=[1, 2])
    plan = Plan(action="answer", title="Revenue", description="...", cards=[make_card()])

    dashboard.save_dashboard(plan, "a new answer", "and now?", existing)

    archived = [body for m, p, body in fake.calls if p in ("/card/1", "/card/2")]
    assert archived == [{"archived": True}, {"archived": True}]
