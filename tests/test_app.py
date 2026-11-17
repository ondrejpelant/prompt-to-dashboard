"""Smoke tests for the chat UI (agent/app.py), run with Streamlit's own AppTest.

Conversation and the warehouse connection are faked: these tests are about the UI
wiring (does a question render, does a dashboard render once there is one), not about
the model or the database - that's what agent/conversation.py and eval/ are for.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parent.parent / "agent" / "app.py"


class FakeDashboard:
    id = 1
    url = "http://localhost:3000/dashboard/1"

    def embed_url(self) -> str:
        return "http://localhost:3000/embed/dashboard/fake-token"


class FakeConversation:
    """Stands in for agent.conversation.Conversation: same shape, no model or DB calls."""

    def __init__(self, conn):
        self.conn = conn
        self.turns: list[tuple[str, str]] = []
        self.dashboard: FakeDashboard | None = None

    def ask(self, question: str) -> str:
        answer = f"Echo: {question}"
        self.turns.append((question, answer))
        self.dashboard = FakeDashboard()
        return answer


def run_app() -> AppTest:
    with (
        patch("agent.warehouse.connect", return_value=MagicMock()),
        patch("agent.conversation.Conversation", FakeConversation),
    ):
        at = AppTest.from_file(str(APP_PATH))
        at.run()
        return at


def test_starts_with_no_dashboard_yet():
    at = run_app()
    assert not at.exception
    assert any("Ask a question" in info.value for info in at.info)


def test_asking_a_question_renders_both_chat_bubbles():
    at = run_app()
    with (
        patch("agent.warehouse.connect", return_value=MagicMock()),
        patch("agent.conversation.Conversation", FakeConversation),
    ):
        at.chat_input[0].set_value("How is revenue?").run()

    assert not at.exception
    messages = {m.name: m.markdown[0].value for m in at.chat_message}
    assert messages["user"] == "How is revenue?"
    assert messages["assistant"] == "Echo: How is revenue?"


def test_a_follow_up_keeps_both_turns_in_the_chat():
    at = run_app()
    with (
        patch("agent.warehouse.connect", return_value=MagicMock()),
        patch("agent.conversation.Conversation", FakeConversation),
    ):
        at.chat_input[0].set_value("First question").run()
        at.chat_input[0].set_value("Second question").run()

    assert not at.exception
    user_messages = [m.markdown[0].value for m in at.chat_message if m.name == "user"]
    assert user_messages == ["First question", "Second question"]
