#!/usr/bin/env bash
# Runs once, on the first start of an empty Postgres volume.
# Creates a separate login role and database for Metabase's own metadata,
# so the BI tool never shares credentials with the warehouse admin.
set -euo pipefail

psql -v ON_ERROR_STOP=1 \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  -v mb_user="$METABASE_DB_USER" \
  -v mb_pass="$METABASE_DB_PASSWORD" <<'SQL'
CREATE ROLE :"mb_user" LOGIN PASSWORD :'mb_pass';
CREATE DATABASE metabase OWNER :"mb_user";
SQL
