---
tags: [jak-to-funguje]
---
# Kontroly kvality

Zpět na [[00 Start]] · Nastavení: `.pre-commit-config.yaml`, `.github/workflows/ci.yml`

**pre-commit = kuchař ochutná, než pošle jídlo na pult.** Běží u mě při `git commit`, drobnosti sám opraví (mezery, konec souboru, styl kódu), nepustí soubor nad 1 MB ani soukromý klíč. Když něco opraví nebo najde chybu, commit nevznikne → zkontrolovat, `git add`, commit znovu.

**CI = hygienická inspekce na GitHubu.** Běží po každém `git push` na čistém cizím počítači:
1. kontrola stylu (`poe lint`),
2. stažení `contoso_10k` dvakrát – podruhé musí říct „already landed“,
3. kontrola `docker-compose.yml`.

Výsledek: GitHub → záložka **Actions** (zelená fajfka / červený křížek).

| | pre-commit | CI |
|---|---|---|
| Kde | u mě | na GitHubu |
| Kdy | `git commit` | `git push` |
| Opravuje | ano, drobnosti | ne, jen hlásí |
| Obejít | jde (`--no-verify`), nedělat | nejde |

## Co jsem se naučil

- Napoprvé si pre-commit stahuje nástroje, pak už je rychlý.
- **Skipped** = kontrola se na daný typ souboru nevztahuje.
- ruff kontroluje i Python kód uvnitř Markdownu – proto „16 files already formatted“.
- `uv run poe check` pustí všechny kontroly bez commitu.
