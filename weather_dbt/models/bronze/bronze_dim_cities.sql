{{ config(materialized='table') }}

SELECT 
  ROW_NUMBER() OVER (ORDER BY city) as city_id,
  city as city_name,
  latitude,
  longitude,
  CURRENT_TIMESTAMP() as loaded_at
FROM (
  SELECT DISTINCT city, latitude, longitude 
  FROM {{ source('raw', 'weather_raw') }}
)
ORDER BY city