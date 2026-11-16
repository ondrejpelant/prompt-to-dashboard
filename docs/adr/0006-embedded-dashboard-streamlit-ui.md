# ADR-0006: Embed the dashboard via a Metabase public link, built with Streamlit

- **Status:** Accepted
- **Date:** 2026-11-16

## Context

ADR-0005 made the agent a conversation but left it running in a terminal, with the dashboard
opened separately in Metabase. The intended product is a chat window: the user describes a
problem, the agent answers in words, and the dashboard that backs the answer is visible right
there, not behind a second window the user has to find and open.

## Options considered

**Showing the dashboard**

1. **Link only** – simplest, no change to Metabase, but breaks the single-window experience the
   product is supposed to deliver.
2. **Embedded iframe** – the dashboard renders next to the chat. Metabase needs either public
   sharing (a link that needs no sign-in, enabled per dashboard) or signed embedding (a shared
   secret signs a short-lived token, no public link exists). Public sharing is one API call and
   nothing to manage; signed embedding is more setup for a guarantee that matters once the app is
   reachable by more than its own user.

**Chat UI technology**

1. **Streamlit** – a Python script becomes a web app; `st.chat_message`/`st.chat_input` are built
   for exactly this; an iframe is one function call. No JavaScript, consistent with the rest of
   the project being Python-only.
2. **Gradio** – similar trade-off, more oriented at exposing a single function as a demo than at
   a multi-turn conversation with side content.
3. **A hand-built web app (FastAPI + HTML/JS)** – full control, but a second language and a
   second set of patterns (routing, templating, state) for a one-person project.

## Decision

- **Public sharing.** `agent/dashboard.py` turns on Metabase's `enable-public-sharing` setting
  and requests a public link for each dashboard it creates; the link needs no Metabase login.
  Only this app's own generated dashboards are ever made public.
- **Streamlit** renders the chat (`agent/app.py`, `uv run poe app`): the conversation in one
  column, the dashboard's public link in an iframe (`streamlit.components.v1.iframe`) in the
  other. A query string that changes on every turn forces the iframe to reload after a follow-up
  changes the dashboard's cards.
- `Conversation.ask` returns only the words of the answer; it no longer builds a "Dashboard: ..."
  line itself, so each caller (the terminal tools, the Streamlit app) decides how to show the
  dashboard - a printed link, or the embedded iframe.

## Consequences

- Anyone who learns a dashboard's public link (a random UUID) can view it without logging in to
  Metabase. Acceptable for a project that runs only on the user's own machine; revisit before any
  shared or hosted deployment (switch to signed embedding, or keep dashboards link-only).
- One Streamlit session holds one open warehouse connection and one `Conversation` for as long as
  the browser tab is open; conversations are not persisted (same as ADR-0005) and there is no
  multi-user access control - fine for a single local user, not for a shared deployment.
- The terminal tools (`uv run poe ask` / `chat`) keep working unchanged, now printing the
  dashboard's admin link rather than the model returning it inline.
- **Revisit** when the agent needs to be reachable by more than the one person running it
  locally.
