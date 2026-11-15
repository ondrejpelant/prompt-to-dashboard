"""Connect Metabase to the warehouse and give it the documentation.

Metabase reads the core schema through the read-only role (BI_DB_USER). Table and
column descriptions and the joins between tables are not pushed from here: dbt
writes them into Postgres as comments and primary/foreign keys, and Metabase picks
them up during its schema sync. This script makes sure the connection exists,
triggers the sync, verifies the result and loads the business glossary
(dbt/metadata/glossary.yml) into the Metabase glossary.

Idempotent: the first run adds the database and the terms, later runs update them.

Usage:
    uv run poe metabase
"""

import json
import os
import time
import urllib.request
from pathlib import Path

import yaml

GLOSSARY_FILE = Path(__file__).resolve().parent.parent / "dbt" / "metadata" / "glossary.yml"
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


def missing_metadata(metadata: dict) -> list[str]:
    """What Metabase does not know yet: descriptions and the joins of fact tables."""
    missing = []
    for table in metadata["tables"]:
        name = f"{table['schema']}.{table['name']}"
        if table["initial_sync_status"] != "complete":
            missing.append(f"{name} (not synced yet)")
        if not table.get("description"):
            missing.append(name)
        missing += [
            f"{name}.{field['name']}" for field in table["fields"] if not field.get("description")
        ]
        has_foreign_keys = any(field.get("fk_target_field_id") for field in table["fields"])
        if table["name"].startswith("fct_") and not has_foreign_keys:
            missing.append(f"foreign keys of {name}")
    return missing


def sync_and_wait(database_id: int) -> dict:
    # The sync runs in the background and picks up foreign keys last, so poll until
    # everything is there instead of reading the metadata once.
    api("POST", f"/database/{database_id}/sync_schema")
    deadline = time.monotonic() + SYNC_TIMEOUT_SECONDS
    while True:
        metadata = api("GET", f"/database/{database_id}/metadata")
        missing = missing_metadata(metadata)
        if metadata["tables"] and not missing:
            return metadata
        if time.monotonic() > deadline:
            raise SystemExit(
                f"Still missing in Metabase after {SYNC_TIMEOUT_SECONDS} s: "
                f"{', '.join(missing) or 'all tables'}"
            )
        time.sleep(3)


def sync_glossary() -> None:
    terms = yaml.safe_load(GLOSSARY_FILE.read_text(encoding="utf-8"))["terms"]
    existing = {entry["term"]: entry for entry in api("GET", "/glossary")["data"]}
    created = updated = 0
    for term in terms:
        definition = " ".join(term["definition"].split())
        if term.get("synonyms"):
            definition += f" Also called: {', '.join(term['synonyms'])}."
        definition += f" See: {', '.join(term['see'])}."
        body = {"term": term["term"], "definition": definition}
        entry = existing.get(term["term"])
        if entry is None:
            api("POST", "/glossary", body)
            created += 1
        elif entry["definition"] != definition:
            api("PUT", f"/glossary/{entry['id']}", body)
            updated += 1
    print(f"glossary: {len(terms)} terms ({created} created, {updated} updated)")


def main() -> None:
    database_id = ensure_database()
    metadata = sync_and_wait(database_id)
    for table in sorted(metadata["tables"], key=lambda t: t["name"]):
        fields = table["fields"]
        foreign_keys = sum(1 for field in fields if field.get("fk_target_field_id"))
        print(
            f"  {table['schema']}.{table['name']}: {len(fields)} columns described, "
            f"{foreign_keys} foreign keys"
        )
    sync_glossary()


if __name__ == "__main__":
    main()
