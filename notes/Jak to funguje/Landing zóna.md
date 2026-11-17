---
tags: [jak-to-funguje]
---
# Landing zóna

Zpět na [[00 Start]] · Kód: `ingestion/land_source.py`, dodací listy: `ingestion/sources.yml`

Landing je **rampa** a `land_source.py` je **skladník**. Po `uv run poe land` udělá:

1. **Přečte dodací list** v `sources.yml`: odkud dodávku vzít, jakou má pečeť (SHA-256), jaké krabice v ní musí být.
2. **Zkontroluje, jestli ji už nepřevzal.** Stejná pečeť v dřívějším protokolu → „already landed“ a konec.
3. **Otevře zadní místnost** – dočasnou složku, kterou nikdo nevidí.
4. **Přiveze dodávku** – stáhne archiv z GitHubu SQLBI.
5. **Zkontroluje pečeť.** Nesedí → dodávku odmítne (`ERROR … checksum mismatch`).
6. **Vybalí a spočítá krabice** – rozbalí, ověří všech 8 souborů, zapíše velikost, otisk, sloupce, počet řádků.
7. **Sepíše protokol** `_manifest.json`.
8. **Zamkne a vynese na rampu** – soubory jen pro čtení, celá složka najednou jako `load_id=…`.

Když se cokoli pokazí v krocích 3–7, zadní místnost se vyhodí a na rampě nic nezůstane.

```text
data/landing/contoso_100k/load_id=20261014T134835Z/
    currencyexchange.csv, customer.csv, … (8 CSV, jen pro čtení)
    _manifest.json
```

## Co jsem se naučil

- Druhé `uv run poe land` → `already landed … skipping`. To je **idempotence**.
- `load_id=20261014T134835Z` je čas v UTC (`Z`), tedy 15:48 našeho času.
- `-r--r--r--` v `ls -l` = jen pro čtení. CSV mají datum dodavatele, manifest datum převzetí.
- Pokus s pokaženou pečetí u `contoso_10k`: `expected …c68, got …c67` → odmítnuto, na rampě nic.
- V manifestu: pečeť archivu `f05a4a9010e6…`, `orders.csv` má 93 470 záznamů.
