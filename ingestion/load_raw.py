import csv
import json
import os
from pathlib import Path

import psycopg
from psycopg import sql

LANDING_ROOT = Path(__file__).resolve().parent.parent / "data" / "landing"
SOURCE = "contoso_100k"
RAW_SCHEMA = "raw"


def latest_load_dir(source: str) -> Path:
    # load_id is a UTC timestamp (20261014T134835Z), so the alphabetical maximum is the newest
    load_dirs = sorted((LANDING_ROOT / source).glob("load_id=*"))
    if not load_dirs:
        raise SystemExit(f"No load found for {source}; run 'uv run poe land {source}' first")
    return load_dirs[-1]


def read_manifest(load_dir: Path) -> dict:
    return json.loads((load_dir / "_manifest.json").read_text(encoding="utf-8"))


def read_header(csv_path: Path) -> list[str]:
    with csv_path.open(encoding="utf-8", newline="") as f:
        return next(csv.reader(f))


def text_column_defs(columns: list[str]) -> sql.Composed:
    # Column names are lowercased so that they work in SQL without double quotes
    return sql.SQL(", ").join(
        sql.SQL("{} text").format(sql.Identifier(column.lower())) for column in columns
    )


def create_raw_table(conn: psycopg.Connection, table: str, columns: list[str]) -> None:
    conn.execute(sql.SQL("create schema if not exists {}").format(sql.Identifier(RAW_SCHEMA)))
    conn.execute(
        sql.SQL(
            "create table if not exists {} ("
            "{}, "
            "_load_id text not null, "
            "_source_file text not null, "
            "_loaded_at timestamptz not null default now())"
        ).format(sql.Identifier(RAW_SCHEMA, table), text_column_defs(columns))
    )


def load_csv(
    conn: psycopg.Connection, table: str, csv_path: Path, columns: list[str], load_id: str
) -> int:
    # COPY cannot add constant values, so the file goes to a temporary table first
    stage = sql.Identifier(f"stage_{table}")
    column_names = sql.SQL(", ").join(sql.Identifier(column.lower()) for column in columns)
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("create temp table {} ({}) on commit drop").format(
                stage, text_column_defs(columns)
            )
        )
        copy_sql = sql.SQL("copy {} from stdin (format csv, header true)").format(stage)
        with csv_path.open("rb") as f, cur.copy(copy_sql) as copy:
            while data := f.read(1024 * 1024):
                copy.write(data)
        cur.execute(
            sql.SQL("insert into {} ({}, _load_id, _source_file) select {}, %s, %s from {}").format(
                sql.Identifier(RAW_SCHEMA, table), column_names, column_names, stage
            ),
            (load_id, csv_path.name),
        )
        return cur.rowcount


def count_rows(conn: psycopg.Connection, table: str, load_id: str) -> int:
    row = conn.execute(
        sql.SQL("select count(*) from {} where _load_id = %s").format(
            sql.Identifier(RAW_SCHEMA, table)
        ),
        (load_id,),
    ).fetchone()
    return row[0]


def main() -> None:
    load_dir = latest_load_dir(SOURCE)
    manifest = read_manifest(load_dir)
    load_id = manifest["load_id"]
    print(f"source: {manifest['source']}, load_id: {load_id}")

    conn = psycopg.connect(
        host="localhost",
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )
    with conn:
        for file in manifest["files"]:
            csv_path = load_dir / file["name"]
            table = csv_path.stem
            columns = read_header(csv_path)
            create_raw_table(conn, table, columns)
            # Idempotency: a load that is already in the table is not loaded again
            already_loaded = count_rows(conn, table, load_id) > 0
            if not already_loaded:
                load_csv(conn, table, csv_path, columns, load_id)
            rows = count_rows(conn, table, load_id)
            if rows != file["records"]:
                raise RuntimeError(
                    f"{RAW_SCHEMA}.{table}: {rows} rows for load {load_id}, "
                    f"manifest says {file['records']}"
                )
            status = "already loaded, skipped" if already_loaded else "loaded"
            print(f"  {RAW_SCHEMA}.{table}: {rows} rows OK ({status})")


if __name__ == "__main__":
    main()
