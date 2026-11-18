---
tags: [stav]
aktualizovano: 2026-11-17
---
# Stav a další kroky

Zpět na [[00 Start]]

## Hotovo

- [x] Výběr datasetu – Contoso V2 ([[Data Contoso]])
- [x] Kostra repa, licence, README, ADR
- [x] Landing zóna – `uv run poe land` ([[Landing zóna]])
- [x] CI na GitHubu ([[Kontroly kvality]])
- [x] Makefile nahrazen poe tlačítky ([[poe]])
- [x] Python zafixovaný na 3.13 ([[Python, uv a venv]])
- [x] WSL2 + Docker Desktop, Postgres a Metabase běží ([[Docker]])
- [x] Metabase zafixovaná na `v0.64.3.1` – můj první vlastní commit
- [x] Obsidian trezor a `CLAUDE.md` ([[Claude kontext]])
- [x] Raw load – `uv run poe raw`, idempotentní, ADR-0003
- [x] Staging – view nad `raw`, typy a čitelné názvy, jen nejnovější load
- [x] Core – hvězda `fct_order_lines` + 4 dimenze, SCD2 u prodejen
- [x] Popis dat – komentáře v Postgresu, `dbt/metadata/metrics.yml` a `glossary.yml`
- [x] Metabase připojená přes `bi_reader`, vidí popisy i vazby
- [x] Agent – rozhovor (ne jen jedna otázka), odpověď slovně + dashboard, `uv run poe chat`
- [x] Chatovací okno – Streamlit, dashboard vložený v iframu, `uv run poe app`
- [x] Zkušební sada 20 otázek, `uv run poe eval` – s popisy 20/20, bez nich 17/20
- [x] CI – `poe land` + `poe raw` + `poe build` + `poe metabase` na GitHubu (bez volání modelu)
- [x] Zkušební sada měří i slovní verdikt tvrzení (`eval/claims.yml`) – s popisy 5/6, bez nich 1/6
- [x] Orchestrace – celý pipeline (land → raw → dbt → Metabase sync) jako jeden graf v Dagsteru,
  `uv run poe dagster`, ADR-0008

## Plán projektu

Sklad nestavíme na konkrétní otázky, ale jako obecný popsaný model celého prodeje.

| # | Krok | Restaurace | Stav |
|---|---|---|---|
| 1 | **Raw load** – CSV z landingu do schématu `raw` | krabice z rampy do skladu | ✅ |
| 2 | **Staging** – typy, názvy, čištění | suroviny vybalit a omýt | ✅ |
| 3 | **Core** – hvězda pro celý prodej | suroviny roztřídit do polic | ✅ |
| 4 | **Popis dat** – každá tabulka, sloupec, metrika, pojem | štítek na každé surovině | ✅ |
| 5 | **Metabase + agent** – odpověď na libovolnou otázku | kuchař vaří na objednávku | ✅ |
| 6 | **Test** – zkušební otázky se známou odpovědí | ochutnávka | ✅ |

Nad rámec plánu přibyl i rozhovor (ne jen jedna otázka) a chatovací okno se vloženým dashboardem.

## Právě teď

Plán (kroky 1–6) i všechny dřívější drobnosti jsou hotové. Čeká se na další zadání.

## Vyřešené drobnosti

- [x] Rozhodnuto o vrstvě `marts` – ADR-0007: záměrně vynechána, Metabase a agent čtou `core`
  přímo. Revize, až bude potřeba `core` měnit bez rizika rozbití dashboardů.
- [x] Veřejné odkazy na dashboardy nahrazeny podepsanými tokeny s platností 10 minut (ADR-0009).
  Žádný starý veřejný odkaz už nefunguje (public sharing vypnuté).
- [x] Automatické testy pro `agent/dashboard.py` a `agent/app.py` – `uv run poe test` (pytest),
  19 testů, žádná živá databáze ani model (Metabase API a `Conversation` jsou ve testech mock).
