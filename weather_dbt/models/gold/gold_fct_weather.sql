{{ config(materialized='view') }}

SELECT 
  weather_id,
  city,
  latitude,
  longitude,
  timestamp,
  date_id,
  hour,
  weather_code,
  temperature_celsius,
  apparent_temperature_celsius,
  humidity_percent,
  wind_speed_kmh,
  wind_direction_degrees,
  wind_gusts_kmh,
  precipitation_mm,
  cloud_cover_percent,
  pressure_hpa,
  visibility_meters,
  ingestion_time
FROM {{ ref('silver_fct_weather') }}
WHERE weather_id IS NOT NULL
  AND temperature_celsius IS NOT NULL
  AND humidity_percent IS NOT NULL