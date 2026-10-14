# Data profiling: Contoso V2

Profile of the `contoso_100k` source as landed by `make land`
(archive sha256 `f05a4a90…944b`), done with DuckDB on 2026-10-14.
Findings that matter downstream will be encoded as dbt tests in phase 3, so they are re-checked on
every build rather than living only in this document.

## Files

All files are comma-separated with a header row, UTF-8, ISO dates (`YYYY-MM-DD`) and a decimal point.
Only `store.csv` contains non-ASCII characters (`Franche-Comté`, `La Réunion`, `Thüringen`).

| File | Records | Grain (one row = …) | Primary key |
|---|---:|---|---|
| `orders.csv` | 93,470 | order header | `OrderKey` |
| `orderrows.csv` | 223,974 | order line | `OrderKey` + `LineNumber` |
| `sales.csv` | 223,974 | order line, pre-joined with header and exchange rate | `OrderKey` + `LineNumber` |
| `customer.csv` | 104,990 | customer | `CustomerKey` |
| `product.csv` | 2,517 | product | `ProductKey` (`ProductCode` also unique) |
| `store.csv` | 74 | store **version** | `StoreKey` (`StoreCode` is *not* unique) |
| `currencyexchange.csv` | 100,450 | daily rate for a currency pair | `Date` + `FromCurrency` + `ToCurrency` |
| `date.csv` | 4,018 | calendar day | `Date` |

`ProductCode` has leading zeros (`0101001`) and must be read as text, not as an integer.

## Coverage

- **Orders:** 2016-05-18 to 2025-12-31. Calendar and exchange rates: 2016-01-01 to 2026-12-31.
- **Geography:** customers in 8 countries (US, GB, CA, AU, DE, IT, NL, FR); 74 stores including one
  online store.
- **Currencies:** USD, EUR, CAD, GBP, AUD; daily rates for all 25 pairs, identity pairs included.
- **Products:** 8 categories, 32 subcategories, 11 brands.
- **Customers:** 52,189 of 104,990 (≈ 50 %) placed at least one order.

| Year | Orders | Year | Orders |
|---|---:|---|---:|
| 2016 (from May) | 2,111 | 2021 | 6,693 |
| 2017 | 3,632 | 2022 | 9,756 |
| 2018 | 4,783 | 2023 | 19,145 |
| 2019 | 9,208 | 2024 | 15,899 |
| 2020 | 6,534 | 2025 | 15,709 |

## Integrity checks – all passed

- Primary keys are unique in every file.
- No orphans: every order has a known customer and store, every order line a known order and
  product, and every order has at least one line.
- No order is dated before its store opened or after it closed, and none falls outside the
  customer's `StartDT`–`EndDT` window.
- `sales.csv` equals `orders ⋈ orderrows` exactly (0 differing rows), and its `ExchangeRate` equals
  the `USD → CurrencyCode` rate on `OrderDate` for every row.

The dataset is synthetic and referentially clean. The interesting problems are semantic, not
structural – which is exactly what the governance layer has to handle.

## Data quality findings

| # | Finding | Handling |
|---|---|---|
| Q1 | Store 630 (Utah) has `CloseDate` 2019-11-03 but an empty `Status`. Every other store with a close date is `Closed` or `Restructured`. | Derive status in staging; test that a close date implies a non-active status. |
| Q2 | `StoreCode` is reused: 6 codes have 2–3 `StoreKey`s, each a `Restructured` predecessor plus a successor with a later `OpenDate`. | The source already delivers a type-2 history: `StoreCode` is the business key, `StoreKey` the version key, `OpenDate`/`CloseDate` the validity. Model `dim_store` as SCD2 accordingly. |
| Q3 | `customer.Age` is a frozen snapshot: it equals the age at 2020-12-31 for 94,990 customers and at 2021-12-31 for the other 10,000, so it is wrong for any other date. | Do not expose it; compute age from `Birthday` at order date. |
| Q4 | `GeoAreaKey` (customer and store) points to a geography table that is not shipped. | Drop from marts. |
| Q5 | Empty values: `customer.Company` 105, `product.Weight` 284, `product.WeightUnit` 222, `store.SquareMeters` 1 (online store), `store.Status` 59 (meaning *active*). | Document; map empty `Status` to `Active`. |
| Q6 | The online store (`StoreKey` 999999) has country code `--`. | Map to an explicit *Online* channel instead of a pseudo-country. |

## Semantic findings – pitfalls the metadata must prevent

These are the places where a plausible-looking dashboard would be wrong. Each needs a column
description, a glossary entry or a metric definition, and each becomes an evaluation question.

| # | Finding | Evidence |
|---|---|---|
| S1 | **All prices are in one base currency (USD), whatever the order's `CurrencyCode`.** `CurrencyCode` is the customer's currency; the local amount is the USD amount × the `USD → CurrencyCode` rate on `OrderDate`. Summing prices "per currency" would label US dollars as euros. | For the same product on the same day, USD and EUR orders have identical `UnitPrice` (2,560 pairs, 0 differences). |
| S2 | **`NetPrice` is after discount, `UnitPrice` before.** Gross and net revenue must be defined explicitly. | `NetPrice < UnitPrice` on 61 % of lines; average discount 5.9 %, max 14 %. |
| S3 | **`product.Price` is today's list price, not the historical one.** Revenue must come from order lines, never from `product.Price × Quantity`. | 2,513 of 2,517 products sold at more than one `UnitPrice`; the ratio of `UnitPrice` to `Price` averages 1.14–1.31 in 2016–2023 and exactly 1.00 in 2024–2025. |
| S4 | **Delivery time exists only for the online channel.** Physical stores always deliver on the order date. "Average delivery time" must be scoped to online orders. | Online: 1–17 days, mean 3.25. Stores: always 0. |
| S5 | **The online channel is big:** 38,968 orders (42 %), serving customers in all 8 countries. Store customers always live in the store's country. | — |
| S6 | **"Number of customers" is ambiguous:** registered customers vs. customers who bought something. | 104,990 vs. 52,189. |
| S7 | **`sales.csv` is a ready-made fact table.** Building from it would bypass the warehouse layers. | Use it only as a reconciliation oracle: the core fact must match it row for row. |

## Modeling implications (draft for phase 4)

- **Fact:** `fct_order_lines`, grain = one order line. Measures in USD (gross, net, cost, discount,
  margin) plus local-currency amounts through the exchange rate on the order date.
- **Dimensions:** customer, product (category → subcategory → product), store (SCD2 on
  `StoreCode`), sales channel (online / store), currency, date.
- **Reporting currency:** USD as base; CZK added later through Czech National Bank rates as a
  second source.
- **Incremental loads:** the static files can be replayed month by month (by `OrderDate`) to
  exercise incremental models and late-arriving data.

## Open questions

1. What do `customer.StartDT` / `EndDT` mean? Spans range from 0 days to 66 years and 31,653
   customers have an `EndDT` in the past, yet no order falls outside the window. Not exposed
   until understood.
2. Confirm the USD base currency (S1) against SQLBI's generator documentation.
3. Use the shipped `date.csv` as the date dimension, or generate one in dbt?

## Small variant: `contoso_10k`

Despite the name, it has 1,681 orders and 3,996 order lines (2022-05-21 to 2026-03-21). Customer,
product and store files are the same as in the 100k variant; only the facts, calendar and rates are
smaller. It is used in CI.
