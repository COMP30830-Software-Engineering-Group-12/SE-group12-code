import pickle
from datetime import datetime
from pathlib import Path
from typing import Any
from component_py_file.db_request import get_station_by_id, request_hourly_forecast
import numpy as np

import warnings

warnings.filterwarnings(
    "ignore",
    message="X does not have valid feature names"
)


MODEL_PATH = Path("component_py_file/bike_availability_model.pkl")

_model = None


def get_prediction_model():
    global _model

    if _model is None:
        with open(MODEL_PATH, "rb") as f:
            _model = pickle.load(f)

    return _model


def prediction_by_id(station_id: int) -> dict[str, Any] | None:
    """
    Predict future hourly bike availability for a given station.

    Returns:
        {
            "station": {...},
            "predictions": [
                {
                    "time_forecast": "...",
                    "predicted_bikes": 12,
                },
                ...
            ]
        }

    Returns None if station not found or no forecast data available.
    """

    station = get_station_by_id(station_id)
    if station is None:
        return None

    forecast_rows = request_hourly_forecast(limit=11)
    if not forecast_rows:
        return None
    forecast_rows = forecast_rows[1:]
    
    model = get_prediction_model()
    predictions = []

    station_feature_id = station["station_number"]
    station_capacity = station.get("capacity") or 0

    for row in forecast_rows:
        forecast_time_str = row.get("time_forecast")
        if not forecast_time_str:
            continue

        try:
            forecast_dt = datetime.fromisoformat(forecast_time_str)
        except ValueError:
            continue

        temperature = row.get("temp") or 0
        humidity = row.get("humidity") or 0
        wind_speed = row.get("wind_speed") or 0

        precipitation = row.get("rain_1h") or 0

        input_features = [
            station_feature_id,
            temperature,
            humidity,
            wind_speed,
            precipitation,
            forecast_dt.hour,
            forecast_dt.weekday(),
        ]

        input_array = np.array(input_features, dtype=float).reshape(1, -1)
        raw_prediction = model.predict(input_array)[0]

        predicted_bikes = int(round(raw_prediction))

        predicted_bikes = max(0, predicted_bikes)
        if station_capacity > 0:
            predicted_bikes = min(predicted_bikes, station_capacity)

        predictions.append({
            "time_forecast": forecast_time_str,
            "dt_txt": row.get("dt_txt"),
            "predicted_bikes": predicted_bikes,
        })

    return {
        "station": station,
        "predictions": predictions,
    }

