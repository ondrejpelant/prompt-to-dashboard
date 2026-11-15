with source as (

    select * from {{ source('raw', 'currencyexchange') }}
    where {{ latest_load('currencyexchange') }}

),

renamed as (

    select
        date::date as rate_date,
        fromcurrency as from_currency,
        tocurrency as to_currency,
        exchange::numeric as exchange_rate,
        _load_id,
        _loaded_at
    from source

)

select * from renamed
