---
tags: [jak-to-funguje]
---
# Python, uv a venv

Zpět na [[00 Start]]

| V projektu | Jednoduše |
|---|---|
| **Python** | kuchař |
| **balíčky** (`py7zr`, `pyyaml`, …) | nářadí z obchodu |
| **`.venv`** | kufřík s nářadím jen pro tenhle projekt |
| **`pyproject.toml`** | nákupní seznam („aspoň verze 0.22“) |
| **`uv.lock`** | účtenka s přesnými verzemi – každý koupí totéž |
| **`.python-version`** | kterého kuchaře chceme: Python 3.13 |
| **uv** | pomocník: sbalí kufřík a pustí kuchaře do práce |

`uv run …` = „uv, zkontroluj kufřík podle účtenky a spusť tohle“.

## Co jsem se naučil

- `uv run python --version` → `Python 3.13.13`. uv si sám všiml `.python-version` a kufřík přebalil.
- `uv tree` ukazuje strom: na seznamu je 5 věcí, v kufříku 28 kusů, protože nářadí potřebuje další nářadí.
- `(group: dev)` je nářadí jen pro vývojáře (poe, pre-commit, ruff). Samotný landing potřebuje jen `py7zr` a `pyyaml`.
- Proč 3.13 a ne 3.14: Python 3.14 podporuje dbt až od verze 1.12.
