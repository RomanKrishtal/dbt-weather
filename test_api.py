import requests
import pandas as pd
from datetime import datetime
from databricks import sql
import os
from dotenv import load_dotenv

load_dotenv()

hostname = os.getenv("DATABRICKS_HOST")
http_path = os.getenv("DATABRICKS_HTTP_PATH")
token = os.getenv("DATABRICKS_TOKEN")

connection = sql.connect(
    server_hostname=hostname,
    http_path=http_path,
    personal_access_token=token,
)

cursor = connection.cursor()

# Data
cities = {
    "London": {"lat": 51.5085, "lon": -0.1257, "country": "UK"},
    "New York": {"lat": 40.7128, "lon": -74.0060, "country": "USA"},
    "Tokyo": {"lat": 35.6762, "lon": 139.6503, "country": "Japan"},
    "Sydney": {"lat": -33.8688, "lon": 151.2093, "country": "Australia"},
    "Paris": {"lat": 48.8566, "lon": 2.3522, "country": "France"},
}

# Weather code meanings
weather_codes = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
}

api_url = "https://api.open-meteo.com/v1/forecast"
useful_vars = "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,wind_gusts_10m,precipitation,weather_code,cloud_cover,pressure_msl,visibility,apparent_temperature"

print("=" * 60)
print("CREATING DIMENSION TABLES")
print("=" * 60)

# ========== DIM 1: dim_cities ==========
print("\n1. Creating dim_cities...")

cities_data = []
city_mapping = {}

for idx, (city_name, info) in enumerate(cities.items(), start=1):
    city_mapping[city_name] = idx
    cities_data.append({
        "city_id": idx,
        "city_name": city_name,
        "latitude": info["lat"],
        "longitude": info["lon"],
        "country": info["country"],
        "loaded_at": datetime.utcnow().isoformat()
    })

cursor.execute("DROP TABLE IF EXISTS dim_cities")
cursor.execute("""
    CREATE TABLE dim_cities (
        city_id INT,
        city_name STRING,
        latitude DOUBLE,
        longitude DOUBLE,
        country STRING,
        loaded_at STRING
    )
    USING DELTA
""")

for row in cities_data:
    cursor.execute(f"""
        INSERT INTO dim_cities VALUES (
            {row['city_id']},
            '{row['city_name']}',
            {row['latitude']},
            {row['longitude']},
            '{row['country']}',
            '{row['loaded_at']}'
        )
    """)

print(f"   ✅ Created with {len(cities_data)} cities")

# ========== DIM 2: dim_weather_codes ==========
print("\n2. Creating dim_weather_codes...")

cursor.execute("DROP TABLE IF EXISTS dim_weather_codes")
cursor.execute("""
    CREATE TABLE dim_weather_codes (
        weather_code INT,
        description STRING,
        loaded_at STRING
    )
    USING DELTA
""")

loaded_at = datetime.utcnow().isoformat()
for code, description in weather_codes.items():
    cursor.execute(f"""
        INSERT INTO dim_weather_codes VALUES (
            {code},
            '{description}',
            '{loaded_at}'
        )
    """)

print(f"   ✅ Created with {len(weather_codes)} weather codes")

# ========== DIM 3: dim_dates ==========
print("\n3. Creating dim_dates...")

cursor.execute("DROP TABLE IF EXISTS dim_dates")
cursor.execute("""
    CREATE TABLE dim_dates (
        date_id STRING,
        date DATE,
        year INT,
        month INT,
        day INT,
        day_of_week INT,
        loaded_at STRING
    )
    USING DELTA
""")

# Generate dates for past 10 days
from datetime import timedelta
today = datetime.utcnow()
for i in range(10, -1, -1):
    date = today - timedelta(days=i)
    date_id = date.strftime("%Y%m%d")
    
    cursor.execute(f"""
        INSERT INTO dim_dates VALUES (
            '{date_id}',
            CAST('{date.strftime("%Y-%m-%d")}' AS DATE),
            {date.year},
            {date.month},
            {date.day},
            {date.weekday()},
            '{loaded_at}'
        )
    """)

print(f"   ✅ Created with 11 dates")

# ========== FACT TABLE ==========
print("\n" + "=" * 60)
print("FETCHING WEATHER DATA & CREATING FACT TABLE")
print("=" * 60)

weather_data = []
weather_id = 1

for city_name, info in cities.items():
    try:
        print(f"\nFetching {city_name}...")
        
        params = {
            "latitude": info["lat"],
            "longitude": info["lon"],
            "past_days": 10,
            "hourly": useful_vars,
            "timezone": "UTC"
        }
        
        response = requests.get(api_url, params=params, timeout=10)
        
        if response.status_code != 200:
            continue
        
        data = response.json()
        hourly = data["hourly"]
        
        times = hourly["time"]
        temps = hourly["temperature_2m"]
        humidity = hourly["relative_humidity_2m"]
        wind_speed = hourly["wind_speed_10m"]
        wind_direction = hourly["wind_direction_10m"]
        wind_gusts = hourly["wind_gusts_10m"]
        precipitation = hourly["precipitation"]
        weather_code = hourly["weather_code"]
        cloud_cover = hourly["cloud_cover"]
        pressure = hourly["pressure_msl"]
        visibility = hourly["visibility"]
        apparent_temp = hourly["apparent_temperature"]
        
        city_id = city_mapping[city_name]
        
        for i in range(len(times)):
            timestamp = times[i]
            date_id = timestamp.split("T")[0].replace("-", "")
            
            weather_data.append({
                "weather_id": weather_id,
                "city_id": city_id,
                "date_id": date_id,
                "weather_code": int(weather_code[i]),
                "hour": int(timestamp.split("T")[1].split(":")[0]),
                "temperature_celsius": round(temps[i], 2),
                "apparent_temperature_celsius": round(apparent_temp[i], 2),
                "humidity_percent": int(humidity[i]),
                "wind_speed_kmh": round(wind_speed[i], 2),
                "wind_direction_degrees": int(wind_direction[i]),
                "wind_gusts_kmh": round(wind_gusts[i], 2),
                "precipitation_mm": round(precipitation[i], 2),
                "cloud_cover_percent": int(cloud_cover[i]),
                "pressure_hpa": round(pressure[i], 2),
                "visibility_meters": int(visibility[i]),
                "ingestion_time": datetime.utcnow().isoformat()
            })
            weather_id += 1
        
        print(f"   ✅ {city_name}: {len(times)} records")
        
    except Exception as e:
        print(f"   Error: {e}")

# Create fact table
print("\n" + "=" * 60)
print("WRITING FACT TABLE TO DATABRICKS")
print("=" * 60)

cursor.execute("DROP TABLE IF EXISTS fct_weather")
cursor.execute("""
    CREATE TABLE fct_weather (
        weather_id INT,
        city_id INT,
        date_id STRING,
        weather_code INT,
        hour INT,
        temperature_celsius DOUBLE,
        apparent_temperature_celsius DOUBLE,
        humidity_percent INT,
        wind_speed_kmh DOUBLE,
        wind_direction_degrees INT,
        wind_gusts_kmh DOUBLE,
        precipitation_mm DOUBLE,
        cloud_cover_percent INT,
        pressure_hpa DOUBLE,
        visibility_meters INT,
        ingestion_time STRING
    )
    USING DELTA
""")

for row in weather_data:
    cursor.execute(f"""
        INSERT INTO fct_weather VALUES (
            {row['weather_id']},
            {row['city_id']},
            '{row['date_id']}',
            {row['weather_code']},
            {row['hour']},
            {row['temperature_celsius']},
            {row['apparent_temperature_celsius']},
            {row['humidity_percent']},
            {row['wind_speed_kmh']},
            {row['wind_direction_degrees']},
            {row['wind_gusts_kmh']},
            {row['precipitation_mm']},
            {row['cloud_cover_percent']},
            {row['pressure_hpa']},
            {row['visibility_meters']},
            '{row['ingestion_time']}'
        )
    """)

cursor.close()
connection.close()

print(f"\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"\n✅ dim_cities: {len(cities_data)} rows")
print(f"✅ dim_weather_codes: {len(weather_codes)} rows")
print(f"✅ dim_dates: 11 rows")
print(f"✅ fct_weather: {len(weather_data)} rows")
print(f"\nTotal tables created: 4")
print(f"Professional star schema deployed! 🌟")