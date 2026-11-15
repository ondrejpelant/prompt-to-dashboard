with source as (

    select * from {{ source('raw', 'orderrows') }}
    where {{ latest_load('orderrows') }}

),

renamed as (

    select
        orderkey::integer as order_key,
        linenumber::integer as line_number,
        productkey::integer as product_key,
        quantity::integer as quantity,
        unitprice::numeric as unit_price,
        netprice::numeric as net_price,
        unitcost::numeric as unit_cost,
        _load_id,
        _loaded_at
    from source

)

select * from renamed
