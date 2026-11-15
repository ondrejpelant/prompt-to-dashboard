-- SCD2 check: two versions of the same store (store_code) must not be valid on the same day.
-- Returns overlapping pairs; passes when there are none.
select
    earlier.store_code,
    earlier.store_key as earlier_store_key,
    later.store_key as later_store_key
from {{ ref('dim_store') }} as earlier
inner join {{ ref('dim_store') }} as later
    on
        earlier.store_code = later.store_code
        and earlier.open_date < later.open_date
where earlier.close_date is null or earlier.close_date >= later.open_date
