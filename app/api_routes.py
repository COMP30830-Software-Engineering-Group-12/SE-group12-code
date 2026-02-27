import os
import requests
from flask import Blueprint, jsonify, request
from sqlalchemy import text
from .db import get_db

main = Blueprint("main", __name__)

# -----------------------------------
# Test route
# -----------------------------------
@main.route("/")
def home():
    return "Dublin Bike Scheme App Running"

@main.route("/api/health")
def health():
    return jsonify({"status": "ok"})


# -----------------------------------
# STORED BIKES (From Database)
# -----------------------------------
@main.route("/api/stored/bikes")
def stored_bikes():
    engine = get_db()

    query = text("""
        SELECT
          s.station_number,
          s.contract_name,
          s.name,
          s.address,
          s.station_lat,
          s.station_long,
          s.capacity,
          st.time_updated,
          st.status,
          st.available_bikes,
          st.available_stands
        FROM bike_station s
        JOIN (
          SELECT b1.*
          FROM bike_station_status b1
          JOIN (
            SELECT station_number, MAX(time_updated) AS max_time
            FROM bike_station_status
            GROUP BY station_number
          ) latest
          ON b1.station_number = latest.station_number
          AND b1.time_updated = latest.max_time
        ) st
        ON s.station_number = st.station_number;
    """)

    rows = engine.execute(query).fetchall()
    return jsonify(stations=[dict(r._mapping) for r in rows])


# -----------------------------------
# STORED WEATHER - CURRENT
# -----------------------------------
@main.route("/api/stored/weather/current")
def stored_weather_current():
    engine = get_db()

    query = text("""
        SELECT *
        FROM weather_current
        ORDER BY time_updated DESC
        LIMIT 1;
    """)

    row = engine.execute(query).fetchone()
    return jsonify(current=dict(row._mapping) if row else None)


# -----------------------------------
# STORED WEATHER - HOURLY
# -----------------------------------
@main.route("/api/stored/weather/hourly")
def stored_weather_hourly():
    engine = get_db()
    limit = request.args.get("limit", default=12, type=int)

    query = text("""
        SELECT *
        FROM weather_forecast_hourly
        ORDER BY time_forecast ASC
        LIMIT :limit;
    """)

    rows = engine.execute(query, {"limit": limit}).fetchall()
    return jsonify(hourly=[dict(r._mapping) for r in rows])


# -----------------------------------
# STORED WEATHER - DAILY
# -----------------------------------
@main.route("/api/stored/weather/daily")
def stored_weather_daily():
    engine = get_db()
    limit = request.args.get("limit", default=7, type=int)

    query = text("""
        SELECT *
        FROM weather_forecast_daily
        ORDER BY time_forecast ASC
        LIMIT :limit;
    """)

    rows = engine.execute(query, {"limit": limit}).fetchall()
    return jsonify(daily=[dict(r._mapping) for r in rows])


# -----------------------------------
# LIVE BIKES (JCDECAUX)
# -----------------------------------
@main.route("/api/live/bikes")
def live_bikes():
    api_key = os.getenv("JCDECAUX_API_KEY")
    contract = os.getenv("JCDECAUX_CONTRACT", "dublin")

    if not api_key:
        return jsonify({"error": "JCDECAUX_API_KEY not set"}), 500

    url = "https://api.jcdecaux.com/vls/v1/stations"
    r = requests.get(url, params={"apiKey": api_key, "contract": contract}, timeout=15)
    r.raise_for_status()

    return jsonify(r.json())


# -----------------------------------
# LIVE WEATHER
# -----------------------------------
@main.route("/api/live/weather")
def live_weather():
    api_key = os.getenv("OPENWEATHER_API_KEY")
    city = os.getenv("OPENWEATHER_CITY", "Dublin,IE")

    if not api_key:
        return jsonify({"error": "OPENWEATHER_API_KEY not set"}), 500

    url = "https://api.openweathermap.org/data/2.5/weather"
    r = requests.get(url, params={"q": city, "appid": api_key, "units": "metric"}, timeout=15)
    r.raise_for_status()

    return jsonify(r.json())
