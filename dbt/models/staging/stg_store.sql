with source as (

    select * from {{ source('raw', 'store') }}
    where {{ latest_load('store') }}

),

renamed as (

    select
        storekey::integer as store_key,
        storecode::integer as store_code,
        geoareakey::integer as geo_area_key,
        countrycode as country_code,
        countryname as country_name,
        state,
        opendate::date as open_date,
        closedate::date as close_date,
        description,
        squaremeters::integer as square_meters,
        -- The source leaves status empty for active stores, and for one closed store (630)
        case
            when status is not null then status
            when closedate is not null then 'Closed'
            else 'Active'
        end as status,
        _load_id,
        _loaded_at
    from source

)

select * from renamed
