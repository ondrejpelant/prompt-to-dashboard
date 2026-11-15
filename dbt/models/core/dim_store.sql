with stores as (

    select * from {{ ref('stg_store') }}

),

final as (

    select
        store_key,
        store_code,
        description as store_name,
        case when store_key = 999999 then 'Online' else 'Store' end as sales_channel,
        -- The online store has no location; the source fills in "--" and "Online"
        case when store_key != 999999 then country_code end as country_code,
        case when store_key != 999999 then country_name end as country_name,
        case when store_key != 999999 then state end as state,
        square_meters,
        status,
        open_date,
        close_date,
        row_number() over (partition by store_code order by open_date) as version_number,
        row_number() over (partition by store_code order by open_date desc) = 1
            as is_current_version
    from stores

)

select * from final
