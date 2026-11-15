"""Connect Metabase to the warehouse and check that it sees the documentation.

Metabase reads the core schema through the read-only role (BI_DB_USER). Table and
column descriptions are not pushed from here: dbt writes them into Postgres as
comments and Metabase picks them up during its schema sync. This script only makes
sure the connection exists, triggers the sync and verifies the result.

Idempotent: the first run adds the database, later runs update its connection details.

Usage:
    uv run poe metabase
"""

import json
import os
import time
import urllib.request

DATABASE_NAME = "Warehouse"
# Metabase runs in Docker next to Postgres, so it reaches it by service name and
# container port, not through localhost and the port published to the host.
WAREHOUSE_HOST = "postgres"
WAREHOUSE_PORT = 5432
SYNC_TIMEOUT_SECONDS = 180


def api(method: str, path: str, body: dict | None = None) -> dict:
    request = urllib.request.Request(
        f"http://localhost:{os.environ['METABASE_PORT']}/api{path}",
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"x-api-key": os.environ["METABASE_API_KEY"], "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def ensure_database() -> int:
    payload = {
        "name": DATABASE_NAME,
        "engine": "postgres",
        "details": {
            "host": WAREHOUSE_HOST,
            "port": WAREHOUSE_PORT,
            "dbname": os.environ["POSTGRES_DB"],
            "user": os.environ["BI_DB_USER"],
            "password": os.environ["BI_DB_PASSWORD"],
            "ssl": False,
        },
    }
    for database in api("GET", "/database")["data"]:
        if database["name"] == DATABASE_NAME:
            api("PUT", f"/database/{database['id']}", payload)
            print(f"database '{DATABASE_NAME}' already connected (id {database['id']}), updated")
            return database["id"]
    database = api("POST", "/database", payload)
    print(f"database '{DATABASE_NAME}' connected (id {database['id']})")
    return database["id"]


def sync_and_wait(database_id: int) -> dict:
    api("POST", f"/database/{database_id}/sync_schema")
    deadline = time.monotonic() + SYNC_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        metadata = api("GET", f"/database/{database_id}/metadata")
        tables = metadata["tables"]
        if tables and all(table["initial_sync_status"] == "complete" for table in tables):
            return metadata
        time.sleep(3)
    raise SystemExit(f"Metabase did not finish syncing within {SYNC_TIMEOUT_SECONDS} s")


def main() -> None:
    database_id = ensure_database()
    metadata = sync_and_wait(database_id)

    missing = []
    for table in sorted(metadata["tables"], key=lambda t: t["name"]):
        fields = table["fields"]
        described = sum(1 for field in fields if field.get("description"))
        print(f"  {table['schema']}.{table['name']}: {described}/{len(fields)} columns described")
        if not table.get("description"):
            missing.append(f"{table['schema']}.{table['name']}")
        missing += [
            f"{table['schema']}.{table['name']}.{field['name']}"
            for field in fields
            if not field.get("description")
        ]
    if missing:
        raise SystemExit(f"Missing descriptions in Metabase: {', '.join(missing)}")
    print("every table and column has a description in Metabase")


if __name__ == "__main__":
    main()
