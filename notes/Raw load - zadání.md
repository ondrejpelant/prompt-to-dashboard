---
tags: [ukol, raw-load]
stav: hotovo
---
# Raw load – zadání

Zpět na [[Stav a další kroky]]

V restauraci je to **nosič**: vezme dodávku z rampy ([[Landing zóna]]), krabici po krabici ji odnese do skladu a na polici napíše, z které dodávky je.

Technicky: skript `ingestion/load_raw.py` vezme 8 CSV z nejnovějšího loadu v `data/landing/` a nahraje je do tabulek ve schématu `raw` v Postgresu.

## Rozhodnutí

| Rozhodnutí | Proč |
|---|---|
| Knihovna **psycopg** + Postgres příkaz **COPY** | standardní spojení Pythonu s Postgresem; COPY je hromadné nahrání, obdoba SQL*Loaderu. dlt by skryl, co se děje. |
| Všechny sloupce v `raw` jako **text** | raw = kopie zdroje „jak přišel“; typy řeší až staging, nahrání nespadne na formátu |
| 3 auditní sloupce: `_load_id`, `_source_file`, `_loaded_at` | štítek na polici: z které dodávky, z kterého souboru, kdy |
| **Idempotence** – stejný load podruhé nic nezdvojí | stejné pravidlo jako u skladníka na rampě |
| Kontrola: počet řádků v tabulce = `records` v manifestu | důkaz, že se nic neztratilo |
| Hesla z `.env` přes proměnné prostředí | nikdy nejsou v kódu ani na GitHubu |

## Kroky

- [x] 1. Připojit se z Pythonu k Postgresu
- [x] 2. Najít nejnovější load a přečíst jeho manifest
- [x] 3. Vytvořit schéma `raw` a jednu tabulku podle hlavičky CSV
- [x] 4. Nahrát do ní jeden soubor
- [x] 5. Přidat auditní sloupce
- [x] 6. Projít všech 8 souborů a zkontrolovat počty řádků
- [x] 7. Idempotence – opakované spuštění nic nezdvojí
- [x] 8. Tlačítko `poe raw`, lint, commit

## Krok 1: připojení k Postgresu

**a) Přidej psycopg do nákupního seznamu**

```bash
uv add "psycopg[binary]"
```

`[binary]` = verze se vším přibaleným, do Windows nic dalšího instalovat nemusíš.

**b) Vytvoř `ingestion/load_raw.py`** a opiš ručně:

```python
import os

import psycopg


def main() -> None:
    conn = psycopg.connect(
        host="localhost",
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )
    with conn:
        row = conn.execute("select version()").fetchone()
        print(row[0])


if __name__ == "__main__":
    main()
```

| Kus kódu | Co dělá |
|---|---|
| `import os` | čtení proměnných prostředí (hodnoty z `.env`) |
| `psycopg.connect(...)` | otevře spojení se skladem; adresa `localhost`, zbytek z `.env` |
| `os.environ["POSTGRES_PORT"]` | přečte hodnotu; když chybí, spadne s `KeyError` – hned víš, co chybí |
| `with conn:` | spojení se na konci samo zavře |
| `conn.execute("select version()")` | pošle SQL do Postgresu |
| `.fetchone()` / `row[0]` | první řádek výsledku / jeho první sloupec |
| `if __name__ == "__main__":` | spusť `main()`, jen když soubor spouštím přímo |

**c) Spusť**

```bash
uv run --env-file .env python -m ingestion.load_raw
```

`--env-file .env` = „otevři obálku s hesly a dej je skriptu“. Docker musí běžet a Postgres být `healthy`.

Čekám výstup typu `PostgreSQL 17.x on x86_64-pc-linux-gnu, …`.
