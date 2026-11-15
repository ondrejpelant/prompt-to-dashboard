-- A store with a close date must not be Active, and an Active store has no close date.
-- Returns the rows that break the rule; the test passes when there are none.
select store_key, status, close_date
from {{ ref('stg_store') }}
where (close_date is not null) = (status = 'Active')
