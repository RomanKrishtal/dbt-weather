{{ config(materialized='table') }}

SELECT DISTINCT
  CAST(weather_code AS INT) as weather_code,
  CASE 
    WHEN weather_code = 0 THEN 'Clear sky'
    WHEN weather_code = 1 THEN 'Mainly clear'
    WHEN weather_code = 2 THEN 'Partly cloudy'
    WHEN weather_code = 3 THEN 'Overcast'
    WHEN weather_code = 45 THEN 'Fog'
    WHEN weather_code = 48 THEN 'Depositing rime fog'
    WHEN weather_code = 51 THEN 'Light drizzle'
    WHEN weather_code = 53 THEN 'Moderate drizzle'
    WHEN weather_code = 55 THEN 'Dense drizzle'
    WHEN weather_code = 61 THEN 'Slight rain'
    WHEN weather_code = 63 THEN 'Moderate rain'
    WHEN weather_code = 65 THEN 'Heavy rain'
    WHEN weather_code = 71 THEN 'Slight snow'
    WHEN weather_code = 73 THEN 'Moderate snow'
    WHEN weather_code = 75 THEN 'Heavy snow'
    WHEN weather_code = 77 THEN 'Snow grains'
    WHEN weather_code = 80 THEN 'Slight rain showers'
    WHEN weather_code = 81 THEN 'Moderate rain showers'
    WHEN weather_code = 82 THEN 'Violent rain showers'
    WHEN weather_code = 85 THEN 'Slight snow showers'
    WHEN weather_code = 86 THEN 'Heavy snow showers'
    WHEN weather_code = 95 THEN 'Thunderstorm'
    ELSE 'Unknown'
  END as description,
  CURRENT_TIMESTAMP() as loaded_at
FROM {{ source('raw', 'weather_raw') }}
WHERE weather_code IS NOT NULL
ORDER BY weather_code