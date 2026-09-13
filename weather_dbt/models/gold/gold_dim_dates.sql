{{ config(materialized='table') }}

SELECT 
  date_id,
  date,
  year,
  month,
  day,
  day_of_week,
  day_type,
  loaded_at
FROM {{ ref('silver_dim_dates') }}
WHERE date_id IS NOT NULL