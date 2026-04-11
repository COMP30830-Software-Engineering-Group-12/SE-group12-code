import pickle
from datetime import datetime, timedelta
import numpy as np
from data_scraping import fetch_weather_forecast_data_hourly


with open("bike_availability_model.pkl", "rb") as f:
    model = pickle.load(f)


def get_weather_one_hour_ahead() -> dict | None:
    data = fetch_weather_forecast_data_hourly()

    if not data or "list" not in data or len(data["list"]) == 0:
        return None

    slot = data["list"][0]

    return {
        "temperature": slot["main"]["temp"],
        "humidity": slot["main"]["humidity"],
        "wind_speed": slot["wind"]["speed"],
        "precipitation": slot.get("rain", {}).get("3h", 0),
        "summary": slot["weather"][0]["description"]
    }


def predict_bikes_one_hour_ahead(station: dict) -> dict | None:
    weather = get_weather_one_hour_ahead()

    if weather is None:
        return None

    future_time = datetime.now() + timedelta(hours=1)

    input_features = [
        station["station_id"],
        weather["temperature"],
        weather["humidity"],
        weather["wind_speed"],
        weather["precipitation"],
        future_time.hour,
        future_time.weekday(),
    ]

    input_array = np.array(input_features).reshape(1, -1)
    prediction = model.predict(input_array)[0]

    predicted_bikes = max(0, int(round(prediction)))

    return {
        "predicted_bikes": predicted_bikes,
        "weather_summary": weather["summary"],
    }