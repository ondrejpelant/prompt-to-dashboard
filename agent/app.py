"""Chat UI: describe a problem, see the answer and its dashboard side by side.

Usage:
    uv run poe app
"""

import streamlit as st
from streamlit.components.v1 import iframe

from agent.conversation import Conversation
from agent.warehouse import connect

st.set_page_config(page_title="Prompt to dashboard", layout="wide")


def get_conversation() -> Conversation:
    """One warehouse connection and one Conversation per browser session."""
    if "conversation" not in st.session_state:
        st.session_state.conversation = Conversation(connect())
    return st.session_state.conversation


def render_dashboard(conversation: Conversation) -> None:
    dashboard = conversation.dashboard
    if dashboard is None:
        st.info("Ask a question to build the first dashboard.")
        return
    st.link_button("Open in Metabase", dashboard.url)
    # A query string that changes on every turn forces the browser to reload the
    # iframe, so a follow-up's new cards actually show up.
    iframe(f"{dashboard.embed_url}?turn={len(conversation.turns)}", height=800, scrolling=True)


def main() -> None:
    st.title("Ask about the sales data")
    conversation = get_conversation()

    chat_col, dashboard_col = st.columns([2, 3])

    with chat_col:
        for question, answer in conversation.turns:
            with st.chat_message("user"):
                st.write(question)
            with st.chat_message("assistant"):
                st.write(answer)

        if question := st.chat_input("Describe a problem or ask a follow-up..."):
            with st.chat_message("user"):
                st.write(question)
            with st.chat_message("assistant"), st.spinner("Thinking..."):
                conversation.ask(question)
            st.rerun()

    with dashboard_col:
        render_dashboard(conversation)


if __name__ == "__main__":
    main()
