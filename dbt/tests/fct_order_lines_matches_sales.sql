-- Reconciliation: the fact must equal the source's ready-made sales file row for row.
-- Returns rows that are in one of them but not in the other; passes when there are none.
with fact as (

    select
        order_key, line_number, order_date, delivery_date, customer_key, store_key,
        product_key, quantity, unit_price, net_price, unit_cost, currency_code, exchange_rate
    from {{ ref('fct_order_lines') }}

),

sales as (

    select
        order_key, line_number, order_date, delivery_date, customer_key, store_key,
        product_key, quantity, unit_price, net_price, unit_cost, currency_code, exchange_rate
    from {{ ref('stg_sales') }}

)

(select 'only in fact' as side, * from fact except select 'only in fact', * from sales)
union all
(select 'only in sales' as side, * from sales except select 'only in sales', * from fact)
