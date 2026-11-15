with source as (

    select * from {{ source('raw', 'customer') }}
    where {{ latest_load('customer') }}

),

renamed as (

    select
        customerkey::integer as customer_key,
        geoareakey::integer as geo_area_key,
        startdt::date as start_date,
        enddt::date as end_date,
        continent,
        gender,
        title,
        givenname as given_name,
        middleinitial as middle_initial,
        surname,
        streetaddress as street_address,
        city,
        state as state_code,
        statefull as state_name,
        zipcode as zip_code,
        country as country_code,
        countryfull as country_name,
        birthday::date as birth_date,
        age::integer as age_at_snapshot,
        occupation,
        company,
        vehicle,
        latitude::numeric as latitude,
        longitude::numeric as longitude,
        _load_id,
        _loaded_at
    from source

)

select * from renamed
