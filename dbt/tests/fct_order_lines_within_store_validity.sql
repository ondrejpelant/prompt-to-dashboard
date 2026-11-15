-- Every order line must point to the store version that was open on the order date.
-- Returns lines sold before the version opened or after it closed; passes when there are none.
select
    fct.order_key,
    fct.line_number,
    fct.order_date,
    stores.store_key,
    stores.open_date,
    stores.close_date
from {{ ref('fct_order_lines') }} as fct
inner join {{ ref('dim_store') }} as stores
    on fct.store_key = stores.store_key
where
    fct.order_date < stores.open_date
    or fct.order_date > stores.close_date
