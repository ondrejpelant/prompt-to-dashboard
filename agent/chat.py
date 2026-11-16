"""Talk to the agent in the terminal.

Describe a problem in plain language; the agent answers in words and shows the
evidence on one Metabase dashboard, which follow-up questions keep refining.

Usage:
    uv run poe chat
"""

from agent.conversation import Conversation
from agent.warehouse import connect


def main() -> None:
    print("Ask about the sales data. An empty line or Ctrl+C ends the conversation.\n")
    with connect() as conn:
        conversation = Conversation(conn)
        while True:
            try:
                question = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not question:
                break
            answer = conversation.ask(question)
            dashboard_line = (
                f"\nDashboard: {conversation.dashboard.url}" if conversation.dashboard else ""
            )
            print(f"\n{answer}{dashboard_line}\n")


if __name__ == "__main__":
    main()
