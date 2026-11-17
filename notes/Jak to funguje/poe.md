---
tags: [jak-to-funguje]
---
# poe

Zpět na [[00 Start]] · Všechna tlačítka v [[Tahák příkazů]]

poe je **dálkový ovladač s tlačítky**. Místo dlouhého příkazu zmáčkneš krátké jméno. Funguje stejně na Windows, v Linuxu i v CI – proto nahradil Makefile.

Tlačítka jsou v `pyproject.toml`, v sekcích `[tool.poe.tasks.<jméno>]`.

| Druh tlačítka | Co dělá | Příklad |
|---|---|---|
| `cmd` | pošle jeden příkaz | `land` → `python -m ingestion.land_source` |
| `sequence` | zmáčkne víc věcí po sobě | `up` → `env`, pak `docker compose up -d` |
| `script` | zavolá funkci v Pythonu | `env` → `ensure_env()` v `tools/devtasks.py` |

```toml
[tool.poe.tasks.up]
help = "Start Postgres and Metabase (Metabase on http://localhost:3000)"
sequence = ["env", { cmd = "docker compose up -d" }]
```

`"env"` v uvozovkách = „nejdřív zmáčkni tlačítko env“.

## Co jsem se naučil

- `uv run poe` vypíše tlačítka. „No task specified“ není chyba.
- `uv run poe -d up` ukáže nanečisto, co by se stalo.
- Pozor na `reset` – jako jediné maže data.
