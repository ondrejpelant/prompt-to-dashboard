"""Answer a business question with a dashboard in Metabase.

Usage:
    uv run poe ask "monthly net revenue by product category in 2024"
"""

import sys

from agent.dashboard import create_dashboard
from agent.planner import make_plan
from agent.warehouse import build_context, connect


def main() -> None:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        raise SystemExit('Usage: uv run poe ask "<question>"')

    with connect() as conn:
        plan = make_plan(question, build_context(conn), conn)

    print(f"{plan.title}\n{plan.description}")
    if not plan.cards:
        return
    for card in plan.cards:
        print(f"  [{card.chart}] {card.title}")
    print(create_dashboard(plan, question))


if __name__ == "__main__":
    main()
