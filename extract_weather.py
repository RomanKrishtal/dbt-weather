import requests
import pandas as pd
from datetime import datetime, timezone
from databricks import sql
from dotenv import load_dotenv
import os

load_dotenv()

# ---------------------------------------------------------
# Databricks connection
# ---------------------------------------------------------

hostname = os.getenv("DATABRICKS_HOST")
http_path = os.getenv("DATABRICKS_HTTP_PATH")
token = os.getenv("DATABRICKS_TOKEN")

if not hostname:
    raise ValueError("DATABRICKS_HOST is missing from .env")
if not http_path:
    raise ValueError("DATABRICKS_HTTP_PATH is missing from .env")
if not token:
    raise ValueError("DATABRICKS_TOKEN is missing from .env")

hostname = hostname.replace("https://", "").rstrip("/")

print(f"Connecting to Databricks: {hostname}")

connection = sql.connect(
    server_hostname=hostname,
    http_path=http_path,
    access_token=token,
)

cursor = connection.cursor()

# ---------------------------------------------------------
# Cities
# ---------------------------------------------------------

cities = {
    "London": {"lat": 51.5085, "lon": -0.1257},
    "New York": {"lat": 40.7128, "lon": -74.0060},
    "Tokyo": {"lat": 35.6762, "lon": 139.6503},
    "Sydney": {"lat": -33.8688, "lon": 151.2093},
    "Paris": {"lat": 48.8566, "lon": 2.3522},
}

# ---------------------------------------------------------
# API Setup
# ---------------------------------------------------------

api_url = "https://api.open-meteo.com/v1/forecast"
useful_vars = "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,wind_gusts_10m,precipitation,weather_code,cloud_cover,pressure_msl,visibility,apparent_temperature"

all_data = []

# ---------------------------------------------------------
# Extract Weather Data
# ---------------------------------------------------------

print("\nFetching weather data from Open-Meteo API...")

for city_name, coords in cities.items():
    try:
        print(f"Fetching {city_name}...")

        params = {
            "latitude": coords["lat"],
            "longitude": coords["lon"],
            "past_days": 10,
            "hourly": useful_vars,
            "timezone": "UTC",
        }

        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()

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

        for i in range(len(times)):
            record = {
                "city": city_name,
                "latitude": coords["lat"],
                "longitude": coords["lon"],
                "timestamp": times[i],
                "temperature_celsius": temps[i],
                "humidity_percent": humidity[i],
                "wind_speed_kmh": wind_speed[i],
                "wind_direction_degrees": wind_direction[i],
                "wind_gusts_kmh": wind_gusts[i],
                "precipitation_mm": precipitation[i],
                "weather_code": weather_code[i],
                "cloud_cover_percent": cloud_cover[i],
                "pressure_hpa": pressure[i],
                "visibility_meters": visibility[i],
                "apparent_temperature_celsius": apparent_temp[i],
                "ingestion_time": datetime.now(timezone.utc).isoformat(),
            }
            all_data.append(record)

        print(f"  ✅ {city_name}: {len(times)} records")

    except Exception as e:
        print(f"  ❌ Error: {e}")

# ---------------------------------------------------------
# Convert to DataFrame
# ---------------------------------------------------------

df = pd.DataFrame(all_data)
print(f"\nTotal records collected: {len(df)}")

if df.empty:
    print("No data collected!")
    cursor.close()
    connection.close()
    raise SystemExit

# ---------------------------------------------------------
# Create Table & Insert Data
# ---------------------------------------------------------

try:
    print("\nCreating/checking Databricks table...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_raw (
            city STRING,
            latitude DOUBLE,
            longitude DOUBLE,
            timestamp STRING,
            temperature_celsius DOUBLE,
            humidity_percent INT,
            wind_speed_kmh DOUBLE,
            wind_direction_degrees INT,
            wind_gusts_kmh DOUBLE,
            precipitation_mm DOUBLE,
            weather_code INT,
            cloud_cover_percent INT,
            pressure_hpa DOUBLE,
            visibility_meters INT,
            apparent_temperature_celsius DOUBLE,
            ingestion_time STRING
        )
        USING DELTA
    """)

    print("✅ Table ready.")

    # Fast bulk insert
    print(f"\nWriting {len(df)} records to Databricks...")

    values_list = []
    for _, row in df.iterrows():
        temp = row["temperature_celsius"] if row["temperature_celsius"] is not None else "NULL"
        humidity = row["humidity_percent"] if row["humidity_percent"] is not None else "NULL"
        wind_speed = row["wind_speed_kmh"] if row["wind_speed_kmh"] is not None else "NULL"
        wind_dir = row["wind_direction_degrees"] if row["wind_direction_degrees"] is not None else "NULL"
        gusts = row["wind_gusts_kmh"] if row["wind_gusts_kmh"] is not None else "NULL"
        precip = row["precipitation_mm"] if row["precipitation_mm"] is not None else "NULL"
        weather = row["weather_code"] if row["weather_code"] is not None else "NULL"
        cloud = row["cloud_cover_percent"] if row["cloud_cover_percent"] is not None else "NULL"
        pressure = row["pressure_hpa"] if row["pressure_hpa"] is not None else "NULL"
        visibility = row["visibility_meters"] if row["visibility_meters"] is not None else "NULL"
        apparent = row["apparent_temperature_celsius"] if row["apparent_temperature_celsius"] is not None else "NULL"

        value_tuple = f"('{row['city']}', {row['latitude']}, {row['longitude']}, '{row['timestamp']}', {temp}, {humidity}, {wind_speed}, {wind_dir}, {gusts}, {precip}, {weather}, {cloud}, {pressure}, {visibility}, {apparent}, '{row['ingestion_time']}')"
        values_list.append(value_tuple)

    values_sql = ",\n".join(values_list)
    cursor.execute(f"INSERT INTO weather_raw VALUES {values_sql}")

    print("✅ Data written to Databricks table: weather_raw")
    connection.commit()

except Exception as e:
    print(f"❌ Error: {e}")

finally:
    cursor.close()
    connection.close()

print("\n✅ Done!")
print(f"Total records: {len(all_data)}")