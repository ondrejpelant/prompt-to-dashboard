---
tags: [tahak]
---
# Tahák příkazů

Zpět na [[00 Start]]. Vše spouštěj ze složky `C:\Users\Ondra\prompt-to-dashboard`.

## Ráno: rozjetí

1. Spusť **Docker Desktop** a počkej na *Engine running*.
2. `docker compose ps` – Postgres musí mít `(healthy)`. Když má `health: starting`, chvíli počkej.
3. Metabase: http://localhost:3000

## poe tlačítka

| Příkaz | Co udělá |
|---|---|
| `uv run poe` | vypíše všechna tlačítka |
| `uv run poe -d <tlačítko>` | ukáže nanečisto, co by tlačítko udělalo |
| `uv run poe up` | nastartuje Postgres a Metabase |
| `uv run poe down` | vypne kontejnery, data zůstanou |
| `uv run poe reset` | ⚠️ vypne kontejnery **a smaže data** |
| `uv run poe logs` | logy kontejnerů (konec Ctrl+C) |
| `uv run poe land` | stáhne Contoso 100k do landing zóny |
| `uv run poe land contoso_10k` | malá varianta |
| `uv run poe lint` | kontrola stylu kódu |
| `uv run poe format` | oprava stylu kódu |
| `uv run poe check` | všechny kontroly z pre-commitu |

## Git

| Příkaz | Co udělá |
|---|---|
| `git status` | co se změnilo (nic nemění) |
| `git diff` | jak přesně se soubory změnily |
| `git add <soubor>` | vybere soubor do příští uložené pozice |
| `git commit -m "Popisek"` | uloží pozici (anglicky, rozkazovací způsob, do 50 znaků) |
| `git push` | pošle commity na GitHub |
| `git log --oneline` | historie commitů |
| `git restore <soubor>` | vrátí soubor do stavu posledního commitu |

## Postgres

```bash
docker compose exec -T postgres psql -U warehouse_admin -d warehouse -c "\l"
docker compose exec -T postgres psql -U warehouse_admin -d warehouse -c "\dn"
```

`\l` = seznam databází, `\dn` = schémata, `\dt raw.*` = tabulky ve schématu `raw`. `-T` je potřeba v Git Bash.

Připojení z DBeaveru: `localhost`, port `5432`, databáze `warehouse`, uživatel `warehouse_admin`, heslo z `.env`.

## Python

| Příkaz | Co udělá |
|---|---|
| `uv run python --version` | verze Pythonu v projektu (3.13) |
| `uv tree` | strom nářadí v kufříku |
| `uv add <balíček>` | přidá nářadí do seznamu, účtenky i kufříku |
| `uv run --env-file .env python -m <modul>` | spustí skript s hodnotami z `.env` |
