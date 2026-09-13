{{ config(materialized='view') }}

SELECT 
  date_id,
  date,
  year,
  month,
  day,
  day_of_week,
  CASE 
    WHEN day_of_week IN (5, 6) THEN 'Weekend'
    ELSE 'Weekday'
  END as day_type,
  loaded_at
FROM {{ ref('bronze_dim_dates') }}
WHERE date_id IS NOT NULL