# Ingestion

Gets source data into the platform. Two steps, two responsibilities:

| Step | Status | What it does |
|---|---|---|
| **Landing** (`land_source.py`) | done | Downloads a source and stores the files exactly as delivered |
| **Raw load** | planned (phase 2) | Loads landed files into the `raw` schema in Postgres, with audit columns |

## Landing zone contract

```
data/landing/<source>/load_id=<UTC timestamp>/
    <source files, unchanged, read-only>
    _manifest.json
```

- **Integrity** – every source is pinned by the sha256 of its archive in [`sources.yml`](sources.yml).
  If the publisher changes the file, landing fails instead of silently loading different data.
- **Immutability** – landed files are read-only and never overwritten. Reprocessing always starts
  from here, so any downstream layer can be rebuilt from scratch.
- **Idempotency** – landing content that is already present is a no-op; `--force` lands it again.
- **Atomicity** – files are extracted to a temporary folder and moved into place only after all
  checks pass. A failed run leaves nothing behind.
- **Traceability** – `_manifest.json` records the URL, license, checksums, record counts and column
  headers of every file. Headers make schema drift between loads easy to detect.

## Usage

```bash
make land                       # contoso_100k (default)
make land SOURCE=contoso_10k    # small variant used in CI
uv run python -m ingestion.land_source contoso_100k --force
```

## Adding a source

Add an entry to [`sources.yml`](sources.yml) with its URL, pinned `sha256`, archive type
(`7z` or `zip`), format and the list of files you expect. No code change is needed for
file-based sources.
