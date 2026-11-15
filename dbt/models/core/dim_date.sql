with dates as (

    select * from {{ ref('stg_date') }}

),

final as (

    select
        date_day,
        date_key,
        year,
        quarter,
        year_quarter,
        year_quarter_number,
        month_number,
        month_name,
        month_short_name,
        year_month,
        year_month_short,
        year_month_number,
        day_of_week_number,
        day_of_week_name,
        day_of_week_short_name,
        is_working_day,
        working_day_number
    from dates

)

select * from final
