# ADR-0001: Use the Contoso V2 dataset as the first source

- **Status:** Accepted
- **Date:** 2026-10-14

## Context

The project is about the platform, not the data: a layered warehouse, governed metadata and an LLM
building dashboards. The first dataset still has to support that work:

- several related tables, so a dimensional model is a real design task
- hierarchies and enough attributes for meaningful dashboards
- multiple years, so incremental loads can be simulated
- a license that allows a public repository
- **downloadable by a script without accounts or tokens**, so anyone – and CI – can rebuild the
  project from `git clone`

## Options considered

1. **Olist Brazilian E-Commerce (Kaggle)** – real, anonymised marketplace data in 9 tables with
  genuine quality problems. Requires a Kaggle account or API token to download and carries a
  non-commercial license.
2. **UCI Online Retail II** – real transaction data with authentic mess (cancellations, negative
  quantities, missing customers), CC BY 4.0, direct download. A single table with 8 columns and no
  product categories – too thin for an LLM to build interesting dashboards on.
3. **Maven Analytics "Global Electronics Retailer"** – the same Contoso data, but the download
  requires signing in.
4. **Contoso V2 from SQLBI** – synthetic retail data in 8 related tables, published as GitHub
  release assets under the MIT license, available in several sizes.

## Decision

Use **Contoso V2**: `csv-100k.7z` (~93k orders, 2016–2025) for development and `csv-10k.7z`
(~1.7k orders) for CI. Both are pinned by checksum in `ingestion/sources.yml`.

`sales.csv` is landed (the landing zone keeps everything as delivered) but **is not used as a
modeling source**: it is a ready-made fact table that would bypass the warehouse layers. It serves as
a reconciliation oracle – the core fact table must match it row for row.

## Consequences

- No secrets are needed to fetch data; CI runs the real ingestion end to end.
- The MIT license allows small extracts to be committed as test fixtures if that becomes useful.
- Five currencies with daily rates, product hierarchies, store history and a separate online
  channel give realistic modeling and metric-definition problems (see
  [data profiling](../data-profiling.md)).
- **Drawback:** the data is synthetic and referentially clean, so staging has fewer structural
  problems to fix than real data would. The project compensates by focusing on semantic pitfalls,
  which are what an LLM gets wrong.
- **Revisit** when a second domain is added to prove the platform is dataset-agnostic; Olist is the
  natural candidate.
