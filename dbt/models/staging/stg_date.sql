with source as (

    select * from {{ source('raw', 'date') }}
    where {{ latest_load('date') }}

),

renamed as (

    select
        date::date as date_day,
        datekey::integer as date_key,
        year::integer as year,
        yearquarter as year_quarter,
        yearquarternumber::integer as year_quarter_number,
        quarter,
        yearmonth as year_month,
        yearmonthshort as year_month_short,
        yearmonthnumber::integer as year_month_number,
        month as month_name,
        monthshort as month_short_name,
        monthnumber::integer as month_number,
        dayofweek as day_of_week_name,
        dayofweekshort as day_of_week_short_name,
        dayofweeknumber::integer as day_of_week_number,
        workingday::integer::boolean as is_working_day,
        workingdaynumber::integer as working_day_number,
        _load_id,
        _loaded_at
    from source

)

select * from renamed
