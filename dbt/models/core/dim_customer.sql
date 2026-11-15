-- Primary key in the database: checked by Postgres and read by Metabase
{{ config(post_hook="alter table {{ this }} add primary key (customer_key)") }}

with customers as (

    select * from {{ ref('stg_customer') }}

),

final as (

    select
        customer_key,
        given_name || ' ' || surname as full_name,
        given_name,
        surname,
        title,
        gender,
        birth_date,
        occupation,
        company,
        vehicle,
        street_address,
        city,
        zip_code,
        state_code,
        state_name,
        country_code,
        country_name,
        continent,
        latitude,
        longitude
    from customers

)

select * from final
