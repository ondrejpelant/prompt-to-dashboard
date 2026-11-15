with order_lines as (

    select * from {{ ref('stg_order_lines') }}

),

orders as (

    select * from {{ ref('stg_orders') }}

),

stores as (

    select * from {{ ref('dim_store') }}

),

customers as (

    select * from {{ ref('dim_customer') }}

),

usd_rates as (

    select * from {{ ref('stg_currency_exchange') }}
    where from_currency = 'USD'

),

final as (

    select
        -- grain: one order line
        order_lines.order_key,
        order_lines.line_number,

        -- dimensions
        orders.order_date,
        orders.customer_key,
        orders.store_key,
        order_lines.product_key,
        orders.currency_code,

        -- order attributes
        orders.delivery_date,
        -- Physical stores hand the goods over on the order date, so only online has a delivery time
        case
            when stores.sales_channel = 'Online' then orders.delivery_date - orders.order_date
        end as delivery_days,
        extract(year from age(orders.order_date, customers.birth_date))::integer
            as customer_age,

        -- unit values, USD
        order_lines.quantity,
        order_lines.unit_price,
        order_lines.net_price,
        order_lines.unit_cost,

        -- line amounts, USD
        order_lines.quantity * order_lines.unit_price as gross_amount_usd,
        order_lines.quantity * (order_lines.unit_price - order_lines.net_price)
            as discount_amount_usd,
        order_lines.quantity * order_lines.net_price as net_amount_usd,
        order_lines.quantity * order_lines.unit_cost as cost_amount_usd,
        order_lines.quantity * (order_lines.net_price - order_lines.unit_cost)
            as margin_amount_usd,

        -- line amounts in the customer's currency
        usd_rates.exchange_rate,
        order_lines.quantity * order_lines.unit_price * usd_rates.exchange_rate
            as gross_amount_local,
        order_lines.quantity * order_lines.net_price * usd_rates.exchange_rate
            as net_amount_local

    from order_lines
    inner join orders
        on order_lines.order_key = orders.order_key
    left join stores
        on orders.store_key = stores.store_key
    left join customers
        on orders.customer_key = customers.customer_key
    left join usd_rates
        on
            orders.order_date = usd_rates.rate_date
            and orders.currency_code = usd_rates.to_currency

)

select * from final
