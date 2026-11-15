#!/usr/bin/env bash
# Runs once, on the first start of an empty Postgres volume.
# Creates the read-only login role used by Metabase and the LLM agent to query the
# warehouse. The role gets no privileges here: dbt grants it SELECT on the core
# schema on every build (see dbt/dbt_project.yml).
#
# On a volume that already exists, run it by hand once (the double slash keeps
# Git Bash on Windows from rewriting the path):
#   docker compose up -d
#   docker compose exec -T postgres bash //docker-entrypoint-initdb.d/02-create-bi-reader.sh
set -euo pipefail

psql -v ON_ERROR_STOP=1 \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  -v bi_user="$BI_DB_USER" \
  -v bi_pass="$BI_DB_PASSWORD" <<'SQL'
CREATE ROLE :"bi_user" LOGIN PASSWORD :'bi_pass';
SQL
