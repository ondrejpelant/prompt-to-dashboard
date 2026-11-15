-- SCD2 check: every store (store_code) has exactly one current version.
-- Returns stores that break the rule; passes when there are none.
select store_code
from {{ ref('dim_store') }}
group by store_code
having count(*) filter (where is_current_version) != 1
