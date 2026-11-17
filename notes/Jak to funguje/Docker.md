---
tags: [jak-to-funguje]
---
# Docker

Zpět na [[00 Start]] · Plán budovy: `docker-compose.yml`, hesla: `.env`

Docker dává Postgres a Metabase jako **hotové spotřebiče v krabici** – nic se neinstaluje do Windows.

| V projektu | Jednoduše |
|---|---|
| **Image** (`postgres:17`, `metabase/metabase:v0.64.3.1`) | model spotřebiče z katalogu |
| **Kontejner** | vybalený, zapojený, běžící kus |
| **Volume** `pgdata` | spíž mimo spotřebič – data přežijí výměnu kontejneru |
| **Port** `3000` / `5432` | okénko ve zdi: jídelna (Metabase) / sklad (Postgres) |
| **`docker-compose.yml`** | plán budovy |
| **`.env`** | obálka s hesly |
| **Healthcheck** | kontrola, že lednice už chladí – Metabase čeká na `healthy` Postgres |
| **Init skript** `infra/postgres/init/…` | jednorázové zařízení při kolaudaci: založí DB `metabase` |
| **WSL2** | pozemek, na kterém budova na Windows stojí |

## Databáze v Postgresu

| Databáze | K čemu |
|---|---|
| `warehouse` | náš sklad – zatím jen prázdné schéma `public` |
| `metabase` | Metabase si sem ukládá účty a dashboardy (založil init skript) |
| `postgres`, `template0`, `template1` | systémové, nesahat |

Jeden server Postgresu = víc oddělených databází (podobně jako PDB v Oracle). Uživatel (role) a schéma jsou v Postgresu **dvě různé věci**.

## Co jsem se naučil

- Bez WSL2 Docker nenaběhne (`failed to connect to the docker API`).
- Po startu PC chvíli počkat: nejdřív naběhne engine, pak Postgres (`the database system is starting up`). Ověřit `docker compose ps` → `(healthy)`.
- Změna verze Metabase: Docker vyměnil jen Metabase, Postgresu se nedotkl. Účet v Metabase přežil, protože je v Postgresu.
- `restart: unless-stopped` – kontejnery se po startu Dockeru zapnou samy.
