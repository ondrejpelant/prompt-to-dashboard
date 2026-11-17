---
tags: [rozcestnik]
---
# prompt-to-dashboard

Datová platforma: zdrojová data → sklad v Postgresu → dobře popsané tabulky → LLM agent, který na **libovolnou** business otázku odpoví dashboardem v Metabase.

> [!important] Cíl
> Nestavíme konkrétní dashboardy. Stavíme dobře popsaný sklad a agenta, který odpoví i na otázky, které nikdo předem neplánoval.

## Kde právě jsem

→ [[Stav a další kroky]]
Rozpracováno: [[Raw load - zadání|Raw load]], krok 1 – připojení k Postgresu z Pythonu.

## Mapa trezoru

**Přehled**
- [[Architektura]] – restaurace, vrstvy a co už stojí
- [[Data Contoso]] – co je v datech a na co si dát pozor
- [[Slovník pojmů]]
- [[Tahák příkazů]]
- [[Deník]] – co se kdy udělalo

**Jak fungují jednotlivé části** (vysvětleno jednoduše)
1. [[Git]]
2. [[Python, uv a venv]]
3. [[poe]]
4. [[Landing zóna]]
5. [[Docker]]
6. [[Kontroly kvality]]

**Pro Clauda**
- [[Claude kontext]] – co je `CLAUDE.md` a jak s Claudem pracujeme

**Dokumentace v repu** (anglicky)
- [[README|README projektu]]
- [[docs/data-profiling|Profilace dat]]
- [[docs/adr/README|ADR – záznamy rozhodnutí]]
- [Kompletní průvodce stavem projektu](https://claude.ai/artifact/WQ1GXNCZenv2sSmKyHrzz7) – podrobný rozbor každého souboru řádek po řádku (claude.ai)
- GitHub: [ondrejpelant/prompt-to-dashboard](https://github.com/ondrejpelant/prompt-to-dashboard)
