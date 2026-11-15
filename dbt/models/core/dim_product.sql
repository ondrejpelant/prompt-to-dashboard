with products as (

    select * from {{ ref('stg_product') }}

),

final as (

    select
        product_key,
        product_code,
        product_name,
        brand,
        manufacturer,
        color,
        category_key,
        category_name,
        subcategory_key,
        subcategory_name,
        weight,
        weight_unit,
        unit_cost as current_unit_cost,
        list_price as current_list_price
    from products

)

select * from final
