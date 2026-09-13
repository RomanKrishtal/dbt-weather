{{ config(materialized='table') }}

SELECT 
  city_id,
  city_name,
  latitude,
  longitude,
  loaded_at
FROM {{ ref('silver_dim_cities') }}
WHERE city_id IS NOT NULL