{{ config(materialized='table') }}

SELECT 
  weather_code,
  description,
  loaded_at
FROM {{ ref('silver_dim_weather_codes') }}
WHERE weather_code IS NOT NULL