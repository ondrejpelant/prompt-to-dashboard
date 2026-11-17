---
tags: [data]
---
# Data Contoso

Zpět na [[00 Start]] · Podrobnosti: [[docs/data-profiling|Profilace dat]] · Proč tenhle dataset: [[docs/adr/0001-dataset-contoso-v2|ADR-0001]]

Syntetická data maloobchodu s elektronikou od SQLBI, licence MIT. Stahuje se bez přihlášení.

## Tabulky (varianta 100k)

| Soubor | Řádků | Jeden řádek = | Klíč |
|---|---:|---|---|
| `orders.csv` | 93 470 | hlavička objednávky | `OrderKey` |
| `orderrows.csv` | 223 974 | řádek objednávky | `OrderKey` + `LineNumber` |
| `customer.csv` | 104 990 | zákazník | `CustomerKey` |
| `product.csv` | 2 517 | produkt | `ProductKey` |
| `store.csv` | 74 | verze obchodu | `StoreKey` |
| `currencyexchange.csv` | 100 450 | denní kurz páru měn | `Date` + `FromCurrency` + `ToCurrency` |
| `date.csv` | 4 018 | kalendářní den | `Date` |
| `sales.csv` | 223 974 | hotová fakta (orders + orderrows) | jen kontrolní vzor, ne zdroj |

Objednávky: 18. 5. 2016 – 31. 12. 2025, 8 zemí, 5 měn, 8 kategorií produktů.

## Pasti, které musí popis dat zachytit

| | Past | Co z toho plyne |
|---|---|---|
| S1 | Všechny ceny jsou v USD bez ohledu na `CurrencyCode` | místní měna = USD × kurz k datu objednávky |
| S2 | `NetPrice` je po slevě, `UnitPrice` před | hrubé a čisté tržby definovat zvlášť |
| S3 | `product.Price` je dnešní ceník | tržby jen z řádků objednávek |
| S4 | Doba doručení existuje jen u online obchodu | metrika jen pro online kanál |
| S6 | Registrovaní zákazníci (104 990) vs. nakupující (52 189) | dvě různé metriky |
| S7 | `sales.csv` je hotová fakt tabulka | nepoužívat jako zdroj |
| Q2 | `StoreCode` se opakuje u restrukturalizovaných obchodů | `dim_store` jako SCD2 |
| Q3 | `customer.Age` je zamrzlý snímek | věk počítat z `Birthday` |
