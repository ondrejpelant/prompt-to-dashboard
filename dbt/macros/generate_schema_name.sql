{#
  By default dbt builds a model with "+schema: staging" into "<target schema>_staging".
  The warehouse layers have fixed schema names (staging, core, marts), so use the
  configured schema name as it is.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
