{#
  Composite primary key check: fails for every combination of the given columns
  that occurs more than once.
      data_tests:
        - unique_combination:
            arguments:
              columns: [order_key, line_number]
#}
{% test unique_combination(model, columns) %}

select {{ columns | join(', ') }}
from {{ model }}
group by {{ columns | join(', ') }}
having count(*) > 1

{% endtest %}
