"""One conversation with the agent: it remembers what was said and owns one dashboard."""

import psycopg

from agent.dashboard import Dashboard, save_dashboard
from agent.planner import Plan, conclude, make_plan, read_results
from agent.warehouse import build_context


class Conversation:
    def __init__(self, conn: psycopg.Connection) -> None:
        self.conn = conn
        self.context = build_context(conn)
        self.turns: list[tuple[str, str]] = []
        self.plan: Plan | None = None
        self.dashboard: Dashboard | None = None

    def history(self) -> str:
        """What the model needs to understand a follow-up."""
        if not self.turns:
            return ""
        lines = [f"User: {question}\nAnalyst: {reply}" for question, reply in self.turns]
        if self.plan is not None:
            lines.append(f"Current dashboard (JSON):\n{self.plan.model_dump_json()}")
        return "\n\n".join(lines)

    def ask(self, question: str) -> str:
        """Answer one message; returns the text to show to the user."""
        history = self.history()
        plan = make_plan(question, self.context, self.conn, history)
        if plan.action != "answer":
            self.turns.append((question, plan.message))
            return plan.message

        answer = conclude(question, plan, read_results(self.conn, plan), history)
        self.dashboard = save_dashboard(plan, answer, question, self.dashboard)
        self.plan = plan
        self.turns.append((question, answer))
        return f"{answer}\n\nDashboard: {self.dashboard.url}"
