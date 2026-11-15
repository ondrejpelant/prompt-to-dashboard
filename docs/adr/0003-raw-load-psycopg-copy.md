# ADR-0003: Use psycopg and COPY for the raw load

- **Status:** Accepted
- **Date:** 2026-11-15

## Context

The raw load moves the eight CSV files of the newest landed load into the `raw` schema in
Postgres. ADR-0002 named **dlt** for this step, "confirmed when the phase starts". The source is a
set of static, clean CSV files with a manifest (columns, record counts, checksums), so there is no
API pagination, schema drift or incremental extraction to handle. The project is also a learning
project: each layer should be understandable down to the SQL that runs.

## Options considered

1. **dlt** – declarative pipelines, schema inference, load state and incremental loading for
   free. It hides the SQL, infers types (raw should keep the source as delivered) and adds its own
   state tables; most of what it offers is not needed for static files.
2. **psycopg + Postgres `COPY`** – about a hundred lines of Python. `COPY` is the standard bulk
   load of Postgres, every statement is visible, and there is no extra framework to learn or pin.
   Idempotency and audit columns have to be written by hand.
3. **dbt seeds** – meant for small reference tables, slow for hundreds of thousands of rows and
   mixes loading with transformation.

## Decision

`ingestion/load_raw.py` loads the files with **psycopg 3 and `COPY`**; dlt is not used.

- **One table per file**, named after the file (`store.csv` → `raw.store`), created from the CSV
  header.
- **Every source column is `text`.** Raw is a copy of the source as delivered; types are assigned
  in staging, so a load never fails on a format.
- **Column names are lowercased** (`StoreKey` → `storekey`) so that they need no double quotes in
  SQL. Readable names (`store_key`) are assigned in staging.
- **Three audit columns:** `_load_id` (the landing load), `_source_file` and `_loaded_at`.
- **`COPY` into a temporary table, then `insert … select`** into the raw table, because `COPY`
  cannot add constant values such as the load id.
- **Idempotency by `_load_id`:** a file whose load id is already in its table is skipped.
- **Row counts are checked against the manifest** on every run, and the whole load is one
  transaction: either the complete load is in `raw`, or nothing.

## Consequences

- The load is transparent and has one small dependency (`psycopg[binary]`).
- Unquoted empty CSV fields arrive as `NULL`, not as empty strings (the default of `COPY` in CSV
  format).
- Raw tables are append-only per load: a newer landed load is stored next to the older one.
  Staging must select the newest `_load_id`.
- A new or renamed source column is not picked up by `create table if not exists`; the load then
  fails on the insert and the table has to be migrated by hand.
- The part of ADR-0002 that names dlt for the raw load is superseded by this record.
- **Revisit** when a source appears that needs what dlt is good at: an API, incremental
  extraction or a drifting schema (for example the Czech National Bank exchange rates).
