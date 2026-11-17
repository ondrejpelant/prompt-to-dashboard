"""Measure how often the agent answers the evaluation questions correctly.

For each question in eval/questions.yml the agent makes a plan (no dashboard is
created), its SQL is run, and the numbers are compared with the reference answer.
A question passes when every reference number appears somewhere in the results of the
agent's cards, within a small tolerance for rounding. Labels and layout are not judged.

eval/claims.yml instead holds claims to verify ("X has been rising - is this true?").
For those, the agent's written conclusion is also checked: it must open with the
yes/no/partly given as that claim's "verdict" (see CONCLUSION_INSTRUCTION in
agent/planner.py) - this is the one place the evaluation looks at the agent's words,
not only its SQL.

Run it with and without metadata to see what the documentation is worth:

    uv run poe eval                  # tables, metrics and glossary
    uv run poe eval --no-metadata    # table and column names only
    uv run poe eval --claims         # claims.yml instead of questions.yml
    uv run poe eval --only stores    # one question or claim
    uv run poe eval --check          # only run the reference SQL, no model calls

Results are written to eval/results/<model>-<mode>.json, mode being with-metadata,
without-metadata, claims-with-metadata or claims-without-metadata.
"""

import argparse
import json
import os
import time
from decimal import Decimal
from pathlib import Path

import httpx2
import psycopg
import yaml
from google.genai import errors

from agent.planner import DEFAULT_MODEL, Plan, conclude, make_plan, read_results
from agent.warehouse import build_context, connect

EVAL_DIR = Path(__file__).resolve().parent
RELATIVE_TOLERANCE = 0.005
PAUSE_SECONDS = 6  # stay under the per-minute limit of the free tier
RATE_LIMIT_RETRIES = 3


class DailyQuotaExhausted(Exception):
    """The free tier's requests-per-day limit is used up; no point in going on."""


def numbers(conn: psycopg.Connection, sql: str) -> list[float]:
    """All numeric values of a query result, whatever their column or row."""
    rows = conn.execute(f"select * from (\n{sql.strip().rstrip(';')}\n) as q limit 1000").fetchall()
    return [
        float(value)
        for row in rows
        for value in row
        if isinstance(value, int | float | Decimal) and not isinstance(value, bool)
    ]


def matches(expected: float, found: float) -> bool:
    candidates = [expected]
    if 0 < abs(expected) < 1:
        candidates.append(expected * 100)  # a ratio may be shown as a percentage
    return any(abs(found - c) <= RELATIVE_TOLERANCE * abs(c) for c in candidates)


def with_retry(call):
    """Retry a model call on a busy model or a dropped connection; give up on the daily quota."""
    for attempt in range(RATE_LIMIT_RETRIES + 1):
        try:
            return call()
        except errors.APIError as error:
            if "per day" in str(error):
                # Waiting a minute does not help against the daily quota
                raise DailyQuotaExhausted from error
            if error.code not in (429, 503) or attempt == RATE_LIMIT_RETRIES:
                raise
            print(f"    model unavailable ({error.code}), waiting 60 s")
            time.sleep(60)
        except httpx2.RequestError as error:
            # A dropped wifi connection or a DNS hiccup, not a problem with the request
            if attempt == RATE_LIMIT_RETRIES:
                raise
            print(f"    network error ({error}), waiting 60 s")
            time.sleep(60)


def extract_verdict(answer: str) -> str | None:
    """The yes/no/partly the answer opens with, per CONCLUSION_INSTRUCTION - or None."""
    first_word = answer.strip().split(None, 1)[0].strip(".,;:!").lower() if answer.strip() else ""
    return {"yes": "yes", "no": "no", "not": "no", "partly": "partly", "partially": "partly"}.get(
        first_word
    )


def evaluate(question: dict, context: str, conn: psycopg.Connection) -> dict:
    expected = numbers(conn, question["reference_sql"])
    result = {"id": question["id"], "question": question["question"], "expected": expected}
    try:
        plan: Plan = with_retry(lambda: make_plan(question["question"], context, conn))
    except SystemExit as error:
        return {**result, "passed": False, "error": str(error)}

    found = [value for card in plan.cards for value in numbers(conn, card.sql)]
    missing = [e for e in expected if not any(matches(e, f) for f in found)]
    result = {
        **result,
        "missing": missing,
        "cards": [{"title": card.title, "sql": card.sql} for card in plan.cards],
    }

    if "verdict" not in question:
        return {**result, "passed": not missing}

    answer = with_retry(lambda: conclude(question["question"], plan, read_results(conn, plan)))
    verdict = extract_verdict(answer)
    return {
        **result,
        "passed": not missing and verdict == question["verdict"],
        "expected_verdict": question["verdict"],
        "verdict": verdict,
        "answer": answer,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--no-metadata", action="store_true", help="names and types only")
    parser.add_argument("--claims", action="store_true", help="claims.yml instead of questions.yml")
    parser.add_argument("--only", help="id of a single question or claim to run")
    parser.add_argument("--check", action="store_true", help="only run the reference SQL")
    args = parser.parse_args()

    file_name, key = ("claims.yml", "claims") if args.claims else ("questions.yml", "questions")
    questions = yaml.safe_load((EVAL_DIR / file_name).read_text(encoding="utf-8"))[key]
    if args.only:
        questions = [q for q in questions if q["id"] == args.only]

    with connect() as conn:
        if args.check:
            for question in questions:
                verdict = f", verdict: {question['verdict']}" if "verdict" in question else ""
                print(f"{question['id']}: {numbers(conn, question['reference_sql'])}{verdict}")
            return

        mode = ("claims-" if args.claims else "") + (
            "without-metadata" if args.no_metadata else "with-metadata"
        )
        model = os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)
        output = EVAL_DIR / "results" / f"{model}-{mode}.json"
        # Results are saved after every question, so a run stopped by the daily
        # quota continues where it ended the next time it is started.
        results = []
        if output.exists() and not args.only:
            results = json.loads(output.read_text(encoding="utf-8"))["results"]
        done = {result["id"] for result in results}
        context = build_context(conn, with_metadata=not args.no_metadata)
        for question in questions:
            if question["id"] in done:
                continue
            try:
                result = evaluate(question, context, conn)
            except DailyQuotaExhausted:
                raise SystemExit(
                    f"Stopped at '{question['id']}' ({len(results)} done): the daily request "
                    "limit of the model's free tier is used up. Run it again tomorrow to continue."
                ) from None
            results.append(result)
            print(f"  {'PASS' if result['passed'] else 'FAIL'}  {question['id']}")
            if not args.only:
                passed = sum(r["passed"] for r in results)
                summary = {
                    "mode": mode,
                    "model": model,
                    "passed": passed,
                    "total": len(results),
                    "results": results,
                }
                output.parent.mkdir(exist_ok=True)
                output.write_text(
                    json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
                )
            time.sleep(PAUSE_SECONDS)

    passed = sum(result["passed"] for result in results)
    print(f"{model}, {mode}: {passed}/{len(results)} questions answered correctly")


if __name__ == "__main__":
    main()
