{#
  Raw tables are append-only per load. This filter keeps only the newest load:
      select ... from {{ source('raw', 'store') }} where {{ latest_load('store') }}
  _load_id is a UTC timestamp, so the maximum is the newest.
#}
{% macro latest_load(table_name) -%}
    _load_id = (select max(_load_id) from {{ source('raw', table_name) }})
{%- endmacro %}
