{% test non_negative(model, column_name) %}
/*
    Custom dbt Generic Test: non_negative
    Returns failing records where the column value is negative (< 0).
    A passing test yields 0 rows.
*/
SELECT
    {{ column_name }} AS failing_value,
    COUNT(*) AS occurrence_count
FROM {{ model }}
WHERE {{ column_name }} < 0
GROUP BY {{ column_name }}

{% endtest %}
