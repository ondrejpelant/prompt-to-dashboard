with source as (

    select * from {{ source('raw', 'orders') }}
    where {{ latest_load('orders') }}

),

renamed as (

    select
        orderkey::integer as order_key,
        customerkey::integer as customer_key,
        storekey::integer as store_key,
        orderdate::date as order_date,
        deliverydate::date as delivery_date,
        currencycode as currency_code,
        _load_id,
        _loaded_at
    from source

)

select * from renamed
