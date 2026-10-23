import os
import shutil
import pandas as pd
import requests

# 1. create the required new folder structure
os.makedirs("data/nac-dataset-4months", exist_ok=True)
os.makedirs("data/nac-dataset-12months", exist_ok=True)
os.makedirs("data/reference", exist_ok=True)
os.makedirs("src", exist_ok=True)

print("📁 folder structure created successfully: data/nac-dataset-4months and data/nac-dataset-12months")

# 2. mapping dictionary for district codes to their real administrative capital names
ZONE_MAPPING = {
    "Z01": "Government_District",
    "Z02": "CBD_Central_Business_District",
    "Z03": "R3_Al_Maqsad",
    "Z04": "R7_Residential",
    "Z05": "R8_Residential",
    "Z06": "Green_River"
}

def localize_zones_in_df(df, zone_col="zone_id"):
    """update district codes to the real administrative capital names"""
    if zone_col in df.columns:
        df[zone_col] = df[zone_col].map(ZONE_MAPPING).fillna(df[zone_col])
    return df

# 3. function to fetch real cairo weather data for 2026 from the open-meteo api
# (capital coordinates: 30.01, 31.75)
def fetch_cairo_weather_2026():
    print("🌤️ fetching real weather data for the administrative capital (2026) from the open-meteo api...")
    url = (
        "https://archive-api.open-meteo.com/v1/archive?"
        "latitude=30.01&longitude=31.75&"
        "start_date=2026-01-01&end_date=2026-12-31&"
        "hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"
    )
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            hourly_data = data.get("hourly", {})
            df_weather = pd.DataFrame({
                "timestamp": pd.to_datetime(hourly_data.get("time")),
                "temperature_c": hourly_data.get("temperature_2m"),
                "humidity_pct": hourly_data.get("relative_humidity_2m"),
                "wind_speed_ms": hourly_data.get("wind_speed_10m")
            })
            df_weather.to_csv("data/reference/cairo_weather_2026.csv", index=False)
            print("✅ weather data saved successfully to data/reference/cairo_weather_2026.csv")
            return df_weather
        else:
            print("⚠️ unable to reach the weather api; seasonal weather simulation will be used.")
            return None
    except Exception as e:
        print(f"⚠️ error while fetching weather data: {e}")
        return None

weather_df = fetch_cairo_weather_2026()