with source as (

    select * from {{ source('raw', 'product') }}
    where {{ latest_load('product') }}

),

renamed as (

    select
        productkey::integer as product_key,
        -- Text on purpose: the code has leading zeros (0101001)
        productcode as product_code,
        productname as product_name,
        manufacturer,
        brand,
        color,
        weightunit as weight_unit,
        weight::numeric as weight,
        cost::numeric as unit_cost,
        price::numeric as list_price,
        categorykey::integer as category_key,
        categoryname as category_name,
        subcategorykey::integer as subcategory_key,
        subcategoryname as subcategory_name,
        _load_id,
        _loaded_at
    from source

)

select * from renamed
