import requests
import pandas as pd
from datetime import datetime, timedelta

API_KEY = "ae254a7d1525e4c02c7c6b119f2a7e8f"
LAT = 53.3498
LON = -6.2603

# Define your year range
start_date = datetime(2025, 2, 15)
end_date = datetime(2026, 2, 14)

all_data = []
current = start_date

while current < end_date:
    next_month = current + timedelta(days=30)

    start_ts = int(current.timestamp())
    end_ts = int(min(next_month, end_date).timestamp())

    print(f"Downloading: {current.date()}")

    url = "https://history.openweathermap.org/data/2.5/history/city"
    params = {
        "lat": LAT,
        "lon": LON,
        "type": "hour",
        "start": start_ts,
        "end": end_ts,
        "appid": API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "list" in data:
        all_data.extend(data["list"])
    else:
        print("Error:", data)

    current = next_month

df = pd.json_normalize(all_data)
df.to_csv("dublin_last_year_hourly.csv", index=False)

print("Finished. Saved dublin_last_year_hourly.csv")
