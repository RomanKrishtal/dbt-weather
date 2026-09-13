{{ config(materialized='table') }}

SELECT 
  ROW_NUMBER() OVER (ORDER BY timestamp) as weather_id,
  city,
  latitude,
  longitude,
  CAST(timestamp AS TIMESTAMP) as timestamp,
  CAST(DATE_FORMAT(CAST(timestamp AS DATE), 'yyyyMMdd') AS STRING) as date_id,
  HOUR(CAST(timestamp AS TIMESTAMP)) as hour,
  CAST(weather_code AS INT) as weather_code,
  CAST(temperature_celsius AS DOUBLE) as temperature_celsius,
  CAST(apparent_temperature_celsius AS DOUBLE) as apparent_temperature_celsius,
  CAST(humidity_percent AS INT) as humidity_percent,
  CAST(wind_speed_kmh AS DOUBLE) as wind_speed_kmh,
  CAST(wind_direction_degrees AS INT) as wind_direction_degrees,
  CAST(wind_gusts_kmh AS DOUBLE) as wind_gusts_kmh,
  CAST(precipitation_mm AS DOUBLE) as precipitation_mm,
  CAST(cloud_cover_percent AS INT) as cloud_cover_percent,
  CAST(pressure_hpa AS DOUBLE) as pressure_hpa,
  CAST(visibility_meters AS INT) as visibility_meters,
  ingestion_time
FROM {{ source('raw', 'weather_raw') }}
ORDER BY timestamp