# ADR-0005: Make the agent a conversation that answers in words and one dashboard

- **Status:** Accepted
- **Date:** 2026-11-16

## Context

ADR-0004 built a one-shot agent: a question becomes a dashboard. The intended product is
self-service BI without report building: the user describes a problem in plain language ("net
revenue has been falling in recent years - check whether that is true"), and the agent answers
and shows the evidence. That needs three things the one-shot agent lacks: a verdict in words,
follow-up questions, and an honest answer when the data cannot support the question.

## Options considered

**Answer**

1. **Dashboard only** – the user reads the verdict off the charts. Does not answer "is it true?".
2. **Words and dashboard** – the model reads the query results and writes the answer; the
   dashboard is the evidence. The results (aggregated numbers) are sent to the model provider.

**Follow-ups**

1. **A new dashboard per message** – simple, but a conversation litters Metabase.
2. **One dashboard per conversation** – a follow-up rewrites it; a new topic is a new
   conversation.

## Decision

- Each message gets one of three outcomes, chosen by the model: **answer** (dashboard and
  words), **clarify** (one question back, only when no sensible default exists) or **decline**
  (the warehouse does not hold what is needed; say what is missing and offer the closest thing
  it can answer). The agent never approximates a concept the data does not contain.
- An answer takes **two model calls**: the plan (SQL cards, proven to run), then the conclusion
  written from the first rows of each card's result.
- The conclusion is shown in the chat and as a **text box at the top of the dashboard**.
- **One dashboard per conversation.** On a follow-up the model returns the complete new state
  of the dashboard; the old cards are archived.
- The conversation is kept in memory for the session; `uv run poe chat` is a terminal chat until
  the user interface is designed.

## Consequences

- Aggregated query results now leave the machine, not only questions and metadata. Fine for the
  synthetic, MIT-licensed Contoso data; with real data use a paid API tier (no training on
  inputs) or a local model.
- Each answer costs two model calls instead of one.
- The conclusion can still misread the numbers; the dashboard next to it is the check, and the
  evaluation should later judge conclusions as well as SQL.
- Conversations are not stored; closing the chat ends them. The dashboards stay in Metabase.
- **Revisit** when the chat interface is designed (where the dashboard is shown, how
  conversations are saved).
