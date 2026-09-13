{{ config(materialized='table') }}

SELECT 
  CAST(DATE_FORMAT(CAST(timestamp AS DATE), 'yyyyMMdd') AS STRING) as date_id,
  CAST(timestamp AS DATE) as date,
  YEAR(timestamp) as year,
  MONTH(timestamp) as month,
  DAY(timestamp) as day,
  DAYOFWEEK(timestamp) - 1 as day_of_week,
  CURRENT_TIMESTAMP() as loaded_at
FROM (
  SELECT DISTINCT CAST(timestamp AS DATE) as timestamp
  FROM {{ source('raw', 'weather_raw') }}
)
ORDER BY timestamp