"""Bootstrap a fresh Metabase container for CI: create the admin user and an API key.

Ondra set his own Metabase admin account up once, by hand, through the UI - that account
and its API key then live on in the app database forever, so bi/sync_metabase.py can just
assume an API key already exists. A CI run starts from an empty container every time, with
no admin account and nobody there to click through the setup wizard, so this script drives
the same wizard through its API instead.

Only ever run this against a container that has never been set up (has-user-setup: false);
it exists solely so CI has something to put in METABASE_API_KEY, and is useless afterwards.

Usage:
    uv run python -m bi.ci_setup >> "$GITHUB_ENV"
"""

import json
import os
import urllib.request

ADMIN_EMAIL = "ci@example.com"
ADMIN_PASSWORD = "ci-only-not-a-real-secret-123!"  # the container is destroyed after the job


def call(method: str, path: str, body: dict | None = None, session: str | None = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if session is not None:
        headers["X-Metabase-Session"] = session
    request = urllib.request.Request(
        f"http://localhost:{os.environ['METABASE_PORT']}/api{path}",
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers=headers,
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        text = response.read()
        return json.loads(text) if text else {}


def main() -> None:
    properties = call("GET", "/session/properties")
    if properties["has-user-setup"]:
        raise SystemExit("Metabase already has a user; this script is for a fresh container only")

    setup = call(
        "POST",
        "/setup",
        {
            "token": properties["setup-token"],
            "user": {
                "first_name": "CI",
                "last_name": "Bot",
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
            },
            "prefs": {"site_name": "CI", "allow_tracking": False},
        },
    )
    session = setup["id"]

    groups = call("GET", "/permissions/group", session=session)
    admin_group = next(g["id"] for g in groups if g["magic_group_type"] == "admin")
    api_key = call("POST", "/api-key", {"name": "ci", "group_id": admin_group}, session=session)

    print(f"METABASE_API_KEY={api_key['unmasked_key']}")


if __name__ == "__main__":
    main()
