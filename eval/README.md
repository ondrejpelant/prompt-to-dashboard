# Evaluation

`questions.yml` holds a fixed set of business questions with reference SQL; `run_eval.py`
(`uv run poe eval`) asks the agent each one, runs its SQL as the read-only role and checks that
every number the reference SQL produces shows up in the agent's results. Run with
`--no-metadata` for the baseline (table and column names only, no descriptions, metrics or
glossary) to see how much the documentation is worth. Results are written to `eval/results/`.

Only the numbers from the SQL cards are checked, not the words of the agent's answer (its
verdict on a question such as "is this true?") – that is not measured yet.
