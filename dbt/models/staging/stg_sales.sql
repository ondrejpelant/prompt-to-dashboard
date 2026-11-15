with source as (

    select * from {{ source('raw', 'sales') }}
    where {{ latest_load('sales') }}

),

renamed as (

    select
        orderkey::integer as order_key,
        linenumber::integer as line_number,
        orderdate::date as order_date,
        deliverydate::date as delivery_date,
        customerkey::integer as customer_key,
        storekey::integer as store_key,
        productkey::integer as product_key,
        quantity::integer as quantity,
        unitprice::numeric as unit_price,
        netprice::numeric as net_price,
        unitcost::numeric as unit_cost,
        currencycode as currency_code,
        exchangerate::numeric as exchange_rate,
        _load_id,
        _loaded_at
    from source

)

select * from renamed
