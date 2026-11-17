# BI layer (Metabase)

`sync_metabase.py` (`uv run poe metabase`) connects Metabase to the warehouse through the
read-only role `bi_reader` and checks that it picked up every table/column description and the
primary/foreign keys from Postgres during its own schema sync. It also pushes the business
glossary (`dbt/metadata/glossary.yml`) into Metabase's glossary.

Table and column descriptions, metrics and keys are never pushed from here: dbt writes
descriptions and keys into Postgres (see `dbt/dbt_project.yml`), and Metabase reads them on
sync. This script only connects, triggers the sync and verifies the result.

Not built: exporting dashboard definitions so dashboards made in Metabase are versioned in git.
