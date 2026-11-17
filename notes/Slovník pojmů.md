---
tags: [prehled]
---
# Slovník pojmů

Zpět na [[00 Start]]

| Pojem | Jednoduše | Kde ho potkáš |
|---|---|---|
| Repozitář (repo) | složka s celou historií změn; historie je ve skryté `.git` | celý projekt |
| Commit | uložená pozice ve hře s popiskem | `git commit` – [[Git]] |
| Push / pull | poslat uložené pozice na GitHub / stáhnout je | `git push` |
| Balíček (závislost) | nářadí z obchodu, které kód používá | `pyproject.toml` |
| `.venv` | kufřík s nářadím jen pro tenhle projekt | [[Python, uv a venv]] |
| `uv.lock` | účtenka s přesnými verzemi nářadí | [[Python, uv a venv]] |
| uv | pomocník, který sbalí kufřík a spustí kuchaře | `uv run …` |
| poe | dálkový ovladač s tlačítky | `uv run poe …` – [[poe]] |
| Landing zóna | rampa, kam data přijdou přesně tak, jak je zdroj dodal | `data/landing/` – [[Landing zóna]] |
| SHA-256 (pečeť) | 64znakový otisk souboru; změna bajtu změní celou pečeť | `sources.yml` |
| Manifest | protokol o převzetí dodávky | `_manifest.json` |
| Idempotence | opakované spuštění nic nezdvojí | `poe land` |
| Atomicita | buď celé, nebo nic; nikdy napůl | `poe land` |
| Image | model spotřebiče z katalogu, např. `postgres:17` | [[Docker]] |
| Kontejner | vybalený a zapojený běžící spotřebič | `docker compose ps` |
| Volume | spíž mimo spotřebič; data přežijí výměnu kontejneru | `pgdata` |
| Port | okénko ve zdi budovy (`3000` jídelna, `5432` sklad) | `docker-compose.yml` |
| Healthcheck | kontrola, že lednice už chladí | `(healthy)` |
| `.env` | obálka s hesly; nikdy na GitHub | [[Docker]] |
| WSL2 | pozemek, na kterém stojí Docker na Windows | |
| pre-commit | kuchař ochutná, než pošle jídlo na pult | [[Kontroly kvality]] |
| CI | hygienická inspekce na GitHubu po každém pushi | [[Kontroly kvality]] |
| ADR | krátký záznam jednoho rozhodnutí | `docs/adr/` |
| Raw / staging / core / marts | vrstvy skladu od surových dat po hotové tabulky | [[Architektura]] |
