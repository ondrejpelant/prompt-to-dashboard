"""Answer one business question with a dashboard in Metabase.

Usage:
    uv run poe ask "monthly net revenue by product category in 2024"

For a conversation with follow-up questions use `uv run poe chat`.
"""

import sys

from agent.conversation import Conversation
from agent.warehouse import connect


def main() -> None:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        raise SystemExit('Usage: uv run poe ask "<question>"')
    with connect() as conn:
        conversation = Conversation(conn)
        print(conversation.ask(question))
        if conversation.dashboard:
            print(f"\nDashboard: {conversation.dashboard.url}")


if __name__ == "__main__":
    main()
