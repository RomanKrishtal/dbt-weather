{{ config(materialized='view') }}

SELECT 
  CAST(weather_code AS INT) as weather_code,
  description,
  loaded_at
FROM {{ ref('bronze_dim_weather_codes') }}
WHERE weather_code IS NOT NULL
  AND description IS NOT NULL