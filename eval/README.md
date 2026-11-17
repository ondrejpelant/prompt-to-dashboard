# Evaluation

`questions.yml` holds direct business questions with reference SQL; `claims.yml` holds claims to
verify ("X has been rising – is this true?") with a reference SQL *and* a correct verdict
(yes/no/partly). `run_eval.py` (`uv run poe eval`) asks the agent each one, runs its SQL as the
read-only role and checks that every number the reference SQL produces shows up in the agent's
results. For claims it also checks that the agent's written conclusion opens with the right
verdict – the one place this evaluation looks at the agent's words, not only its SQL.

```bash
uv run poe eval                   # questions.yml, with metadata
uv run poe eval --no-metadata     # questions.yml, baseline
uv run poe eval --claims          # claims.yml, with metadata
uv run poe eval --claims --no-metadata
uv run poe eval --only stores     # one question or claim
uv run poe eval --check           # only the reference SQL, no model calls
```

Results are written to `eval/results/<model>-<mode>.json` and resume where a run left off if the
model's free-tier daily quota runs out mid-run.
